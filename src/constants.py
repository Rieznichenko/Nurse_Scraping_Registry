import os
from collections import namedtuple
from enum import Enum

from dotenv import load_dotenv

load_dotenv()
LOWEST_SLEEP = 0.5
LOW_SLEEP = 1
DEFAULT_SLEEP = 5
MEDIUM_SLEEP = 10
HIGH_SLEEP = 30
HIGHEST_SLEEP = 60
RETRY_COUNT = 2
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
AirlineCredential = namedtuple("Credential", ["user_name", "password"])

# Define the JSON constant variable
GOOGLE_PHONE_NUMBER = {
    "email": "yrt5455tyrey@gmail.com",
    "password": "qweQWE123!@#",
    "recovery_email": "matsuograham41@gmail.com",
    "mode": "static",
    "recipient": "+14432962140",
    "recipient_list": [
        "+14432962140",
        "+14038403757"
    ],
    "message_list": [
        "Today is [TIME]",
        "The message was sent at [TIME]. Good night."
    ]
}

class CabinClass(Enum):
    Economy = "economy"
    PremiumEconomy = "premium_economy"
    Business = "business"
    First = "first"


class Airline(Enum):
    AmericanAirline = "AA"
    AirCanada = "AC"
    VirginAtlantic = "VS"
    DeltaAirline = "DL"
    UnitedAirline = "UA"
    HawaiianAirline = "HA"
    WizzairAirline = "Wizzair"
    Click2Mail = "click2mail"
    TransaviaAirline = "Transavia"
    Pspprint = "Pspprint"
    RyanairAirline = "Ryanair"
    VuelingAirline = "Vueling"
    EasyjetAirline = "easyjet"
    LinkedIn = "linkedin"
    Aliexpress = "aliexpress"
    Ebay = "ebay"
    Mexico = "mexico"
    GoogleVoice = "googlevoice"
    Nurse = "nurse"



class AuthenticationRequiredAirline(Enum):
    HawaiianAirline = "HA"


class ResponseFormat(str, Enum):
    Buffered = "Buffered"
    Streaming = "Streaming"


Credentials = {
    AuthenticationRequiredAirline.HawaiianAirline: [
        AirlineCredential(user_name="zachburau", password="Mgoblue16!"),
        AirlineCredential(user_name="jojnson1978yahoo", password="Pancakes123!"),
    ]
}
