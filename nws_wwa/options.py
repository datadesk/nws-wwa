"""The three files the National Weather Service publishes."""

from __future__ import annotations

from enum import StrEnum


class Feed(StrEnum):
    """One of the three files NWS publishes for current alerts.

    The values are the short names used on the command line and by
    ``get_alert_records``.

    Examples:
        >>> Feed("hazards").file_name
        'current_hazards.tar.gz'
        >>> Feed.ALL.value
        'all'
    """

    ALL = "all"
    HAZARDS = "hazards"
    WARNINGS = "warnings"

    @property
    def file_name(self) -> str:
        """The name of the file on the NWS server.

        Returns:
            The file name, such as "current_all.tar.gz".

        Examples:
            >>> Feed.WARNINGS.file_name
            'current_warnings.tar.gz'
        """
        return f"current_{self.value}.tar.gz"


FEED_LIST = [feed.value for feed in Feed]
"""The short names of the three feeds."""
