import time
from enum import auto

import humps
from tqdm import tqdm

from mstrio import config
from mstrio.api import ai as ai_api
from mstrio.api import objects
from mstrio.project_objects.helpers import (
    EnableForAiErrorReason,
    EnableForAiState,
    EnableForAiStatus,
)
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.enum_helper import AutoUpperName, get_enum_val
from mstrio.utils.version_helper import is_server_min_version

ENABLED_FOR_AI_FLAG_PROPERTY_INDEX = 16
DATASET4BOT_V2_PROPERTY_ID = '70A27C6E239911D5BF2200B0D02A21E0'


class DumpCubesType(AutoUpperName):
    OLAP = auto()
    MTDI = auto()
    SUBSET_REPORT = auto()


class EnableForAiMixin:
    """Mixin adding AI enablement capabilities for project objects."""

    def _resolve_dump_cube_type(self) -> DumpCubesType:
        """Resolve dump cube type from object subtype/type."""
        subtype = getattr(self, 'subtype', None)
        subtype_value = get_enum_val(
            subtype,
            ObjectSubTypes,
            throw_on_unknown=False,
        )

        if subtype_value == ObjectSubTypes.OLAP_CUBE.value:
            return DumpCubesType.OLAP

        if subtype_value == ObjectSubTypes.SUPER_CUBE.value:
            return DumpCubesType.MTDI

        # We check the report type (not only currently supported subtypes
        # 768, 769, 774 as of 26.06), so this will work for any current
        # or future report subtypes.
        object_type = getattr(self, 'type', None)
        if object_type == ObjectTypes.REPORT_DEFINITION:
            return DumpCubesType.SUBSET_REPORT

        # Default to OLAP as in Library
        return DumpCubesType.OLAP

    def enable_for_ai(self) -> bool:
        """Trigger AI enablement for this object.

        Note:
            The object must be published before it can be enabled for AI.

        Returns:
            bool: True if the enablement request was accepted by the server.
        """
        cube_type = self._resolve_dump_cube_type()
        response = ai_api.enable_object_for_ai(
            connection=self.connection,
            object_id=self.id,
            cube_type=cube_type.value,
        )
        return response.ok

    def disable_for_ai(self) -> None:
        """Disable AI for this object."""
        body = [
            {
                'properties': [
                    {
                        'id': ENABLED_FOR_AI_FLAG_PROPERTY_INDEX,
                        'value': 0,
                    }
                ],
                'id': DATASET4BOT_V2_PROPERTY_ID,
            }
        ]
        objects.update_property_set(
            self.connection,
            id=self.id,
            obj_type=self.type.value,
            body=body,
        )

    def get_enable_for_ai_status(
        self, to_dictionary: bool = False
    ) -> dict | EnableForAiState:
        """Fetch AI enablement status for this object.

        Args:
            to_dictionary (bool, optional): If True, returns the result as a
                dictionary. If False, returns a EnableForAiState object.
                Defaults to False.

        Returns:
            dict | EnableForAiState: AI enablement status containing fields
                such as `status`, `reason`, `progress`, `remainingTime`, etc.
        """
        result = ai_api.get_bot_cube_status(self.connection, cube_ids=[self.id]).json()
        status_result = self._extract_cube_status_result(result)

        if to_dictionary:
            return status_result

        return self._parse_bot_cube_status_result(status_result)

    def wait_until_enabled_for_ai(
        self,
        timeout: int | None = None,
        interval: float | None = None,
        to_dictionary: bool = False,
    ) -> dict | EnableForAiState:
        """Poll AI enablement status until completion or timeout.

        Poll the AI enablement status until the object reaches a terminal state
        (READY, FAILED, BASE_CUBE_DECERTIFIED) or the timeout is exceeded.
        Optionally displays progress using a progress bar if configured.

        Args:
            timeout (int, optional): Maximum time in seconds to wait. If None,
                waits indefinitely. Defaults to None.
            interval (float, optional): Time between polling requests in
                seconds. If None, uses the default delay from the configuration.
                Defaults to None.
            to_dictionary (bool, optional): If True, returns the result as a
                dictionary. If False, returns a EnableForAiState object.
                Defaults to False.

        Returns:
            dict | EnableForAiState: Final AI enablement status.

        Raises:
            TimeoutError: If the timeout is exceeded before reaching a terminal
                state.
        """
        start_time = time.time()
        terminal_states = {
            EnableForAiStatus.READY,
            EnableForAiStatus.FAILED,
            EnableForAiStatus.BASE_CUBE_DECERTIFIED,
        }
        poll_interval = (
            interval if interval is not None else config.delay_between_polling
        )
        supports_progress = is_server_min_version(self.connection, '11.5.0900')
        should_display_progress = (
            config.verbose and config.progress_bar and supports_progress
        )

        with tqdm(
            total=100,
            desc='Waiting for AI enablement...',
            disable=not should_display_progress,
            delay=3,
        ) as pbar:
            while True:
                status_result = self.get_enable_for_ai_status(to_dictionary=True)

                # Right after triggering enablement, API usually temporarily
                # does not return status row for this object yet.
                if not status_result:
                    if should_display_progress:
                        pbar.set_postfix_str('waiting for status...')
                else:
                    current_status = self._parse_enable_for_ai_status(
                        status_result.get('status')
                    )

                    progress = status_result.get('progress')
                    if isinstance(progress, int):
                        pbar.n = min(max(progress, 0), 100)
                        pbar.refresh()

                        remaining_time = status_result.get('remainingTime')
                        if remaining_time is not None:
                            pbar.set_postfix_str(f'remaining: {remaining_time}s')
                        else:
                            pbar.set_postfix_str('')

                    if current_status in terminal_states:
                        if to_dictionary:
                            return status_result
                        return self._parse_bot_cube_status_result(status_result)

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        raise TimeoutError(
                            f"AI enablement did not complete within {timeout} "
                            f"seconds."
                        )

                time.sleep(poll_interval)

    def _extract_cube_status_result(self, result: dict) -> dict:
        """Extract status payload for this object from API response."""
        if not isinstance(result, dict):
            return {}

        cubes = result.get('cubes')
        if isinstance(cubes, list):
            for item in cubes:
                if item.get('id') == self.id:
                    return item

        return {}

    @staticmethod
    def _parse_bot_cube_status_result(result: dict) -> EnableForAiState:
        """Convert API response dictionary to EnableForAiState object.

        Args:
            result (dict): Dictionary response from the API.

        Returns:
            EnableForAiState: Parsed status result object.
        """
        status = EnableForAiMixin._parse_enable_for_ai_status(result.get('status'))
        err_reason = EnableForAiMixin._parse_enable_for_ai_reason(result.get("reason"))
        err_code = EnableForAiMixin._parse_enable_for_ai_reason(result.get("errorCode"))

        if err_code is not None and err_code != EnableForAiErrorReason.OK:
            chosen_error = err_code
        elif err_reason is not None and err_reason != EnableForAiErrorReason.OK:
            chosen_error = err_reason
        else:
            chosen_error = EnableForAiErrorReason.OK

        return EnableForAiState(
            id=result.get('id'),
            status=status or EnableForAiStatus.NULL,
            error_reason=chosen_error,
            progress=result.get('progress'),
            remaining_time=result.get('remainingTime'),
            last_updated_at=result.get('lastUpdatedAt'),
            user=result.get('user'),
        )

    @staticmethod
    def _parse_enable_for_ai_status(
        value: str | None,
    ) -> EnableForAiStatus | None:
        """Parse API status string into EnableForAiStatus enum."""
        if not isinstance(value, str):
            return None
        normalized = humps.decamelize(value)
        try:
            return EnableForAiStatus(normalized.strip().lower())
        except ValueError:
            return None

    @staticmethod
    def _parse_enable_for_ai_reason(
        value: str | int | None,
    ) -> "EnableForAiErrorReason | None":
        """Parse API reason value into EnableForAiErrorReason enum.

        Handles:
        - int codes directly (e.g. 0, 10)
        - string formats like "[0]" or "[10] error message" or "10"

        Args:
            value: Reason from API response, as int or str.

        Returns:
            EnableForAiErrorReason enum or None if parsing fails.
        """
        if value is None:
            return None

        if isinstance(value, int):
            try:
                return EnableForAiErrorReason(value)
            except ValueError:
                return EnableForAiErrorReason.UNKNOWN_ERROR

        if not isinstance(value, str):
            return None

        normalized = value.strip()
        if normalized.startswith('['):
            end_bracket = normalized.find(']')
            if end_bracket > 0:
                try:
                    code = int(normalized[1:end_bracket])
                except ValueError:
                    return None
            else:
                return None
        else:
            try:
                code = int(normalized)
            except ValueError:
                return None

        try:
            return EnableForAiErrorReason(code)
        except ValueError:
            return None
