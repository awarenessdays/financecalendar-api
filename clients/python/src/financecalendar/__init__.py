"""Python client for Finance Calendar paid data and Free Developer schedule JSON.

Connect source-aware release data with an account key. Starter US$9.99/year;
current pricing and source terms: https://www.financecalendar.com/pricing/.
The public browser calendar is free. Optional API evaluation is finite.
"""

from .client import (
    DEFAULT_BASE,
    MAX_RANGE_DAYS,
    Client,
    FinanceCalendarError,
    to_dataframe,
)

__version__ = "0.1.3"
__all__ = ["Client", "FinanceCalendarError", "to_dataframe", "DEFAULT_BASE", "MAX_RANGE_DAYS", "__version__"]
