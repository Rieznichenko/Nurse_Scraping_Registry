from .aa.crawler import AmericanAirlineCrawler
from .ac.crawler import AirCanadaCrawler
from .dl.crawler import DeltaAirlineCrawler
from .ha.crawler import HawaiianAirlineCrawler
from .ua.crawler import UnitedAirlineCrawler
from .vs.crawler import VirginAtlanticCrawler
from .constants import Airline

Crawlers = {
    Airline.AmericanAirline: AmericanAirlineCrawler,
    Airline.AirCanada: AirCanadaCrawler,
    Airline.DeltaAirline: DeltaAirlineCrawler,
    Airline.HawaiianAirline: HawaiianAirlineCrawler,
    Airline.UnitedAirline: UnitedAirlineCrawler,
    Airline.VirginAtlantic: VirginAtlanticCrawler
}
