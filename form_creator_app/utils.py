import pytz
from datetime import datetime


def aware_utc_now():
    return pytz.utc.localize(datetime.utcnow())
