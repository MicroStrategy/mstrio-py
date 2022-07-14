from typing import Optional, Union

from tqdm.auto import tqdm


class ProgressBarMixin:
    _progress_bar: tqdm = None

    def _display_progress_bar(
        self,
        desc: str,
        total: Union[int, float],
        unit: Optional[str] = None,
        initial: Union[int, float] = 0,
        bar_format: Optional[str] = None,
        leave: bool = True,
        **kwargs
    ):
        """Create and display progress bar. Needs to be closed with
        `close_progress_bar`, when updates no longer needed.

        Args:
            desc : str, optional
                Prefix for the progressbar.
            total : int or float, optional
                The number of expected iterations. If unspecified, len(iterable)
                is used if possible. If float("inf") or as a last resort, only
                basic progress statistics are displayed (no ETA,
                no progressbar). If gui is True and this parameter needs
                subsequent updating, specify an initial arbitrary large
                positive number, e.g. 9e9.
            unit : str, optional
                String that will be used to define the unit of each iteration
                [default: it].
            bar_format : str, optional
                Specify a custom bar string formatting. May impact performance.
                [default: '{l_bar}{bar}{r_bar}'], where l_bar='{desc}:
                {percentage:3.0f}%|' and r_bar='| {n_fmt}/{total_fmt}
                [{elapsed}<{remaining}, ' '{rate_fmt}{postfix}]'
                Possible vars: l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
                percentage, elapsed, elapsed_s, ncols, nrows, desc, unit, rate,
                rate_fmt, rate_noinv, rate_noinv_fmt, rate_inv, rate_inv_fmt,
                postfix, unit_divisor, remaining, remaining_s, eta.
                Note that a trailing ": " is automatically removed after {desc}
                if the latter is empty.
            initial : int or float, optional
                The initial counter value. Useful when restarting a progress
                bar [default: 0]. If using float, consider specifying {n:.3f} or
                similar in bar_format, or specifying unit_scale.
            """
        self._progress_bar = tqdm(
            total=total,
            desc=desc,
            unit=unit,
            bar_format=bar_format,
            initial=initial,
            leave=leave,
            **kwargs
        )

    def _close_progress_bar(self):
        """Close progress bar when no longer needed. Blocks updates with
        `update_progress_bar_if_needed`."""
        self._progress_bar.close()
        self._progress_bar = None

    def _update_progress_bar_if_needed(
        self, new_description: Optional[str] = None, update_increment: Union[int, float] = 1
    ):
        """Updates the state of the progress bar.
        Use it after `display_progress_bar`.
        Args:
            new_description(str): New description of the progress bar
            update_increment: value used when updating progress bar"""
        if self._progress_bar is not None:
            if new_description is not None:
                self._progress_bar.set_description_str(new_description)
            self._progress_bar.update(update_increment)

    def _set_progress_bar_value(self, new_val: Union[int, float]):
        """Sets the value of the progress bar and refreshes it.
        Use it after `display_progress_bar`.
        Args:
            new_val(Union[int, float]): New value of the progress bar"""
        self._progress_bar.n = new_val
        self._progress_bar.refresh()
