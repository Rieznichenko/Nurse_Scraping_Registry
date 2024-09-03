import datetime
from typing import Optional, Union

from src.types import SmartAirlineType


class CrawlerException(Exception):
    def __str__(self):
        if hasattr(self, "message"):
            return self.message
        else:
            return super().__str__()


class LiveCheckerException(Exception):
    def __init__(
        self,
        airline: SmartAirlineType,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        date: Optional[str] = None,
        data: Optional[str] = None,
    ):
        self.message = f"{airline} ({origin} - {destination}) on {date}: {data}"
        super().__init__(self.message)


class AirportNotSupported(CrawlerException):
    def __init__(self, airline: SmartAirlineType, airport: str):
        self.message = f"{airline} does not support {airport}"
        super().__init__(self.message)


class OnewayNotSelectable(CrawlerException):
    def __init__(self, airline: SmartAirlineType):
        self.message = f"Not able to select One way trip on {airline} "
        super().__init__(self.message)


class OriginNotSelectable(CrawlerException):
    def __init__(self, airline: SmartAirlineType, airport: str, reason: Optional[str] = None):
        self.message = f"Not able to select origin {airport} on {airline} "
        if reason:
            self.message += f"Reasons: {reason}"

        super().__init__(self.message)


class DestinationNotSelectable(CrawlerException):
    def __init__(self, airline: SmartAirlineType, airport: str):
        self.message = f"Not able to select destination {airport} on {airline} "
        super().__init__(self.message)


class MileNotSelectable(CrawlerException):
    def __init__(self, airline: SmartAirlineType):
        self.message = f"Not able to select miles on {airline} "
        super().__init__(self.message)


class DepartureDateNotSelectable(CrawlerException):
    def __init__(self, airline: SmartAirlineType, departure_date: Union[str, datetime.date]):
        self.message = f"Not able to select departure date {departure_date} on {airline} "
        super().__init__(self.message)


class CannotContinueSearch(CrawlerException):
    def __init__(self, airline: SmartAirlineType, reason: Optional[str]):
        self.message = f"Not able to continue search on {airline}"
        if reason:
            self.message += f"Reasons: {reason}"
        super().__init__(self.message)


class NoSearchResult(CrawlerException):
    def __init__(self, airline: SmartAirlineType):
        self.message = f"No Result on {airline}"
        super().__init__(self.message)


class PointNotExtractable(CrawlerException):
    def __init__(self, airline: SmartAirlineType):
        self.message = f"Error occurred while extracting points on {airline}"
        super().__init__(self.message)


class LoginFailed(CrawlerException):
    def __init__(self, airline: SmartAirlineType):
        self.message = f"{airline} authentication failed..."
        super().__init__(self.message)
