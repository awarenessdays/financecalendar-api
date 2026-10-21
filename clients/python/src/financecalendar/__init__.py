"""Python client for the financecalendar.com API.

Economic releases, central bank decisions and exchange holidays, free with
attribution (a visible link to https://www.financecalendar.com wherever the
data appears).
"""

from .client import (
    DEFAULT_BASE,
    MAX_RANGE_DAYS,
    Client,
    FinanceCalendarError,
    to_dataframe,
)

__version__ = "0.1.0"
__all__ = ["Client", "FinanceCalendarError", "to_dataframe", "DEFAULT_BASE", "MAX_RANGE_DAYS", "__version__"]
