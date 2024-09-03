from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FlightSegment:
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    departure_time: Optional[str] = None
    departure_timezone: Optional[str] = None
    arrival_date: Optional[str] = None
    arrival_time: Optional[str] = None
    arrival_timezone: Optional[str] = None
    duration: Optional[str] = None  # This is only required for DL
    aircraft: Optional[str] = None
    flight_number: Optional[str] = None
    carrier: Optional[str] = None


@dataclass
class CashFee:
    amount: Optional[float] = None
    currency: Optional[str] = None


@dataclass
class Flight:
    origin: Optional[str] = None
    destination: Optional[str] = None
    cabin_class: Optional[str] = None
    airline_cabin_class: Optional[str] = None
    points: Optional[float] = None
    cash_fee: Optional[CashFee] = None
    segments: Optional[List[FlightSegment]] = None
    duration: Optional[str] = None  # This is only required for DL
