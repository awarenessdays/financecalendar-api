"""Python client for Finance Calendar paid data and Free Developer schedule JSON.

Connect source-aware release data with an account key. Starter US$4.99/month;
current pricing and source terms: https://www.financecalendar.com/pricing/.
The public browser calendar is free to browse.
"""

from .client import (
    DEFAULT_BASE,
    MAX_RANGE_DAYS,
    Client,
    FinanceCalendarError,
    to_dataframe,
)

__version__ = "0.1.6"
__all__ = ["Client", "FinanceCalendarError", "to_dataframe", "DEFAULT_BASE", "MAX_RANGE_DAYS", "__version__"]
