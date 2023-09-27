from typing import TYPE_CHECKING

from mstrio.utils.entity import Entity

if TYPE_CHECKING:
    from mstrio.object_management.translation import Translation


class TranslationMixin:
    """TranslationMixin class adds translation managing and listing support
    for supported objects."""

    def add_translation(
        self: Entity,
        translations: list['Translation.OperationData'],
    ) -> list['Translation']:
        """Adds translations to the Object.

        Args:
            translations (list[OperationData]): list of translations to be added
                to the Object

        Returns:
            A list of translations for the Object.
        """
        from mstrio.object_management.translation import Translation

        return Translation.add_translation(
            connection=self.connection,
            id=self.id,
            object_type=self._OBJECT_TYPE.value,
            translations=translations,
            project_id=self.project_id if self.project_id else None,
        )

    def alter_translation(
        self: Entity,
        translations: list['Translation.OperationData'],
    ) -> None:
        """Alters translations of the Object.

        Args:
            translations (list[OperationData]): list of translations to be added
                to the Object
        """
        from mstrio.object_management.translation import Translation

        Translation.alter_translation(
            connection=self.connection,
            id=self.id,
            object_type=self._OBJECT_TYPE.value,
            translations=translations,
            project_id=self.project_id if self.project_id else None,
        )

    def remove_translation(
        self: Entity,
        translations: list['Translation.OperationData'],
    ) -> None:
        """Removes translations from the Object.

        Args:
            translations (list[OperationData]): list of translations to be added
                to the Object
        """
        from mstrio.object_management.translation import Translation

        Translation.remove_translation(
            connection=self.connection,
            id=self.id,
            object_type=self._OBJECT_TYPE.value,
            translations=translations,
            project_id=self.project_id if self.project_id else None,
        )

    def list_translations(
        self: Entity, languages: list | None = None, to_dictionary: bool = False
    ) -> list['Translation'] | list[dict]:
        """Lists translations for the Object.

        Args:
            languages (list, optional): list of languages to list the
                translations for, only translations from these languages
                will be listed.
                Languages in the list should be one of the following:
                    - lcid attribute of the language
                    - ID of the language
                    - Language class object
            to_dictionary (bool, optional): If True returns dict, by default
                (False) returns Translation objects

        Returns:
            A list of dictionaries representing translations for the Object or a
            list of Translation Objects."""
        from mstrio.object_management.translation import list_translations

        return list_translations(
            connection=self.connection,
            id=self.id,
            object_type=self._OBJECT_TYPE.value,
            project_id=self.project_id if self.project_id else None,
            languages=languages,
            to_dictionary=to_dictionary,
        )
