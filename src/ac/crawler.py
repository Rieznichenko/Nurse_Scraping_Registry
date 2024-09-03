import datetime
import logging
import re
import time
from typing import Dict, Iterator, List, Optional, Tuple

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebElement

from src import constants as c
from src.ac.constants import CabinClassCodeMapping
from src.base import SeleniumBasedAirlineCrawler
from src.exceptions import CannotContinueSearch, NoSearchResult, OriginNotSelectable
from src.schema import CashFee, Flight, FlightSegment
from src.utils import convert_k_to_float, extract_digits

logger = logging.getLogger(__name__)


class AirCanadaCrawler(SeleniumBasedAirlineCrawler):
    AIRLINE = c.Airline.AirCanada
    REQUIRED_LOGIN = False
    HOME_PAGE_URL = "https://www.aircanada.com/us/en/aco/home.html"

    def _select_oneway(self) -> None:
        self.click_once_presence(
            by=By.XPATH,
            identifier="//div[@id='bkmg-tab-content-flight']//input[@id='bkmgFlights_tripTypeSelector_O']",
            timeout=c.MEDIUM_SLEEP,
        )

    def _select_miles(self) -> None:
        self.click_once_presence(
            by=By.XPATH,
            identifier='//abc-checkbox[contains(@class, "search-type-toggle-checkbox")]'
            '//input[@id="bkmgFlights_searchTypeToggle"]',
            timeout=c.MEDIUM_SLEEP,
        )

    def _select_origin(self, origin: str) -> None:
        try:
            origin_input = self.wait_until_clickable(
                by=By.XPATH,
                identifier="//input[contains(@id, 'bkmgFlights_origin_trip_1')]",
                timeout=c.MEDIUM_SLEEP * 2,
            )
            self.click_element(origin_input)
        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when clicking origin element {e}"
            )
        else:
            origin_input.send_keys(Keys.CONTROL, "a")
            origin_input.send_keys(origin)
            time.sleep(c.LOW_SLEEP)

        try:
            self.click_once_clickable(
                by=By.XPATH,
                identifier='//ul[@id="bkmgFlights_origin_trip_1OptionsPanel"]'
                '/li[1]//div[@class="location-info-main"]',
                timeout=c.MEDIUM_SLEEP * 2,
            )
        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when selecting airport {e}"
            )

    def _select_destination(self, destination: str) -> None:
        destination_input = self.wait_until_visible(
            by=By.XPATH,
            identifier='//input[contains(@id, "bkmgFlights_destination_trip")]',
            timeout=c.LOW_SLEEP,
        )
        destination_input.send_keys(Keys.CONTROL, "a")
        destination_input.send_keys(destination)
        time.sleep(c.LOW_SLEEP)

        self.click_once_clickable(
            by=By.XPATH,
            identifier='//ul[@id="bkmgFlights_destination_trip_1OptionsPanel"]'
            '/li[1]//div[@class="location-info-main"]',
            timeout=c.MEDIUM_SLEEP,
        )

    def _select_date(self, departure_date: datetime.date) -> None:
        self.click_once_clickable(
            by=By.XPATH,
            identifier='//input[@id="bkmgFlights_travelDates_1"]',
            timeout=c.MEDIUM_SLEEP,
        )

        next_mon_btn = self.wait_until_clickable(
            by=By.XPATH, identifier="//button[@id='bkmgFlights_travelDates_1_nextMonth']", timeout=c.MEDIUM_SLEEP
        )
        while True:
            try:
                # self.click_once_clickable(
                #     by=By.XPATH,
                #     identifier=f"//div[@class='abc-calendar-wrapper']//"
                #     f"table[contains(@class, 'abc-calendar-month')]"
                #     f"//td[@data-date={departure_date.day}][@data-month={departure_date.month}]"
                #     f"[@data-year={departure_date.year}]",
                #     timeout=c.LOW_SLEEP,
                # )
                self.click_once_clickable(
                    by=By.XPATH, identifier=f"//div[@id='bkmgFlights_travelDates_1-date-{departure_date.isoformat()}']"
                )
                break
            except (TimeoutException, NoSuchElementException):
                next_mon_btn.click()
            except Exception as e:
                raise e

    def accept_cookie(self):
        try:
            self.find_and_click_element(
                by=By.XPATH,
                identifier='//ngc-cookie-banner//div[contains(@class, "close-cookie")]//button',
            )
        except NoSuchElementException:
            pass

    def _submit(self) -> None:
        self.click_once_clickable(
            by=By.XPATH,
            identifier="//button[@id='bkmgFlights_findButton']",
            timeout=c.MEDIUM_SLEEP,
        )

    def continue_search(self) -> None:
        try:
            self.click_once_clickable(
                by=By.XPATH,
                identifier="//abc-button//button[@id='confirmrewards']",
                timeout=c.MEDIUM_SLEEP,
            )
            logger.info(f"{self.AIRLINE.value}: Close primary cookie box...")

            self.click_once_clickable(
                by=By.XPATH,
                identifier="//mat-dialog-container//kilo-simple-lightbox//div[@id='mat-dialog-title-0']"
                "//span[@aria-label='Close']",
                timeout=c.HIGHEST_SLEEP,
            )
            logger.info(f"{self.AIRLINE.value}: Close secondary cookie box...")
        except (TimeoutException, NoSuchElementException) as e:
            raise CannotContinueSearch(airline=self.AIRLINE, reason=f"{e}")

    def extract_flight_detail(
        self, flight_row_element: WebElement, departure_date: datetime.date
    ) -> List[FlightSegment]:
        logger.info(f"{self.AIRLINE.value}: Extracting Flight Details...")
        flight_segments: List[FlightSegment] = []

        # click detail element
        self.find_and_click_element(
            by=By.XPATH,
            identifier='.//div[contains(@class, "block-body")]//div[contains(@class, "details-row")]'
            '//span[contains(@class, "links")]//a[contains(@class, "detail-link")]',
            from_element=flight_row_element,
        )
        time.sleep(c.LOW_SLEEP)

        flight_segments_elements = self.wait_until_all_visible(
            by=By.XPATH,
            identifier="//mat-dialog-container//kilo-simple-lightbox//"
            "kilo-flight-details-pres//kilo-flight-segment-details-cont",
            timeout=c.HIGH_SLEEP,
        )

        for segment_index, segment_element in enumerate(flight_segments_elements):
            logger.info(f"{self.AIRLINE.value}: Retrieving segment info => index: {segment_index}...")
            segment_items = segment_element.find_elements(By.XPATH, './/div[@class="container"]')
            segment_depart_info_element = segment_items[0]
            segment_departure_time_element = segment_depart_info_element.find_element(
                by=By.XPATH, value='.//div[contains(@class, "flight-timings")]'
            )
            try:
                segment_departure_day_element = segment_depart_info_element.find_element(
                    By.XPATH, './/div[contains(@class, "flight-timings")]//span[contains(@class, "arrival-days")]'
                )
                departure_days_delta = self.get_text(segment_departure_day_element)
                departure_days_delta = int(extract_digits(departure_days_delta))
                segment_departure_date = departure_date + datetime.timedelta(days=departure_days_delta)
            except NoSuchElementException:
                segment_departure_date = departure_date

            segment_departure_time = self.get_text(segment_departure_time_element)

            segment_flights_detail_element = segment_depart_info_element.find_element(
                By.XPATH, './/div[contains(@class, "flight-details-container")]'
            )

            flight_detail_container = segment_flights_detail_element.find_elements(
                By.XPATH, './/div[contains(@class, "d-flex")]'
            )
            depart_airline_info = flight_detail_container[0]
            depart_airline_city_code_element = depart_airline_info.find_elements(By.XPATH, ".//span")[0]
            depart_airline_city = depart_airline_city_code_element.find_element(By.XPATH, ".//strong")
            depart_airline_city = self.get_text(depart_airline_city)
            segment_origin = self.get_text(depart_airline_city_code_element).replace(depart_airline_city, "").strip()
            airline_attributes = flight_detail_container[1]
            airline_info = airline_attributes.find_elements(
                By.XPATH, './/div[contains(@class, "airline-info")]//div[contains(@class, "airline-details")]//span'
            )
            segment_flight_number = self.get_text(airline_info[0])
            segment_carrier = self.get_text(airline_info[1]).replace("| Operated by", "").strip()
            segment_aircraft = self.get_text(airline_info[2])

            segment_arrival_info_element = segment_items[1]
            segment_arrival_time_element = segment_arrival_info_element.find_element(
                By.XPATH, './/div[contains(@class, "flight-timings")]//span[1]'
            )
            segment_arrival_time = self.get_text(segment_arrival_time_element)
            try:
                segment_arrival_day_element = segment_depart_info_element.find_element(
                    By.XPATH, './/div[contains(@class, "flight-timings")]//span[contains(@class, "arrival-days")]'
                )
                arrival_days_delta = self.get_text(segment_arrival_day_element)
                arrival_days_delta = int(extract_digits(arrival_days_delta))
                segment_arrival_date = departure_date + datetime.timedelta(days=arrival_days_delta)
            except NoSuchElementException:
                segment_arrival_date = departure_date

            arrival_airline_city_code_element = segment_arrival_info_element.find_elements(
                By.XPATH, './/div[contains(@class, "flight-details-container")]//span'
            )[0]

            arrival_airline_city = arrival_airline_city_code_element.find_element(By.XPATH, ".//strong")
            arrival_airline_city = self.get_text(arrival_airline_city)

            segment_destination = (
                self.get_text(arrival_airline_city_code_element).replace(arrival_airline_city, "").strip()
            )
            flight_segments.append(
                FlightSegment(
                    origin=segment_origin,
                    destination=segment_destination,
                    departure_date=segment_departure_date.isoformat(),
                    departure_time=segment_departure_time,
                    departure_timezone="",
                    arrival_date=segment_arrival_date.isoformat(),
                    arrival_time=segment_arrival_time,
                    arrival_timezone="",
                    aircraft=segment_aircraft,
                    flight_number=segment_flight_number,
                    carrier=segment_carrier,
                )
            )

        self.find_and_click_element(
            identifier="//mat-dialog-container//div[contains(@class, 'lightbox-container')]"
            "//div[contains(@class, 'header')]//span[contains(@class, 'icon-close')]",
            by=By.XPATH,
        )
        return flight_segments

    @staticmethod
    def extract_currency_and_amount(input_string) -> Optional[Tuple[str, float]]:
        pattern = re.compile(r"([A-Za-z]+) \$([\d,]+(?:\.\d{2})?)")
        match = pattern.match(input_string)

        if match:
            currency = match.group(1)
            amount = float(match.group(2).replace(",", ""))
            return currency, amount
        else:
            return None

    def extract_sub_classes_points(
        self, flight_row_element: WebElement, cabin_class: c.CabinClass = c.CabinClass.Economy
    ) -> Optional[Dict[str, dict]]:
        logger.info(f"{self.AIRLINE.value}: Extracting Sub Sub Classes points...")
        cabin_class_code = CabinClassCodeMapping[cabin_class]
        points_by_fare_names: Dict[str, dict] = {}
        try:
            self.find_and_click_element(
                by=By.XPATH,
                identifier=f".//div[contains(@class, 'cabins-container')]"
                f"//kilo-cabin-cell-pres[contains(@class, 'cabin')]"
                f"[contains(@data-analytics-val, '{cabin_class_code}')]"
                f"//div[contains(@class, 'available-cabin')][contains(@class, 'flight-cabin-cell')]",
                from_element=flight_row_element,
            )
        except NoSuchElementException:
            return None

        fare_names_elements = self.find_elements(
            by=By.XPATH, identifier="//div[contains(@class, 'fare-headers')]//span"
        )
        fare_details_elements = self.find_elements(
            by=By.XPATH, identifier="//div[contains(@class, 'fare-list')]//div[contains(@class, 'fare-list-item')]"
        )
        for fare_name_element, fare_details_element in zip(fare_names_elements, fare_details_elements):
            try:
                fare_name = self.get_text(fare_name_element)
                point_element = self.find_element(
                    by=By.XPATH,
                    identifier=".//div[contains(@class, 'price-container')]//div[contains(@class, 'points')]/span",
                    from_element=fare_details_element,
                )
                points = self.get_text(point_element)
                cash_fee_element = self.find_element(
                    by=By.XPATH,
                    identifier=".//div[contains(@class, 'price-container')]//kilo-price/span",
                    from_element=fare_details_element,
                )
                cash_fee = self.get_text(cash_fee_element)
                currency, amount = self.extract_currency_and_amount(cash_fee)
                points_by_fare_names[fare_name] = {
                    "points": convert_k_to_float(points),
                    "cash_fee": CashFee(
                        amount=currency,
                        currency=amount,
                    ),
                }
            except NoSuchElementException:
                continue
        return points_by_fare_names

    def extract(
        self,
        departure_date: datetime.date,
        cabin_class: c.CabinClass = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        try:
            logger.info(f"{self.AIRLINE.value}: Searching results...")
            flight_search_results = self.wait_until_all_visible(
                by=By.XPATH,
                identifier='//div[@class="page-container"]//kilo-upsell-cont//kilo-upsell-pres'
                '//kilo-upsell-row-cont//div[contains(@class, "upsell-row")]',
                timeout=c.MEDIUM_SLEEP,
            )
        except (NoSuchElementException, TimeoutException):
            raise NoSearchResult(airline=self.AIRLINE)

        provided_cabin_classes = [
            self.get_text(element).lower()
            for element in self.find_elements(by=By.XPATH, identifier="//div[@class='cabin-heading']")
        ]
        if CabinClassCodeMapping[cabin_class] not in provided_cabin_classes:
            raise NoSearchResult(airline=self.AIRLINE)

        logger.info(f"{self.AIRLINE.value}: Found {len(flight_search_results)} flights...")
        for index, flight_search_result in enumerate(flight_search_results):
            logger.info(f"{self.AIRLINE.value}: Retrieving the detail of search item => index: {index}...")

            points_by_fare_names = self.extract_sub_classes_points(flight_search_result, cabin_class)
            if not points_by_fare_names:
                continue

            try:
                segments = self.extract_flight_detail(flight_search_result, departure_date)
            except Exception as e:
                raise e

            for fare_name, points_and_cash in points_by_fare_names.items():
                yield Flight(
                    origin=segments[0].origin,
                    destination=segments[-1].destination,
                    cabin_class=cabin_class.value,
                    airline_cabin_class=fare_name,
                    points=points_and_cash["points"],
                    cash_fee=points_and_cash["cash_fee"],
                    segments=segments,
                )

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: c.CabinClass = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        self.continue_search()
        for flight in self.extract(departure_date, cabin_class):
            yield flight


if __name__ == "__main__":
    import json
    from dataclasses import asdict

    def run(origin, destination, cabin_class):
        start_time = time.perf_counter()
        crawler = AirCanadaCrawler()
        departure_date = datetime.date.today() + datetime.timedelta(days=14)

        flights = list(
            crawler.run(
                origin=origin,
                destination=destination,
                departure_date=departure_date.isoformat(),
                cabin_class=cabin_class,
            )
        )
        end_time = time.perf_counter()

        if flights:
            with open(f"{crawler.AIRLINE.value}-{origin}-{destination}-{cabin_class.value}.json", "w") as f:
                json.dump([asdict(flight) for flight in flights], f, indent=2)
        else:
            print("No result")
        print(f"It took {end_time - start_time} seconds.")

    # run("PVG", "ICN", c.CabinClass.Economy)
    run("JFK", "LHR", c.CabinClass.Economy)
    # run("YVR", "YYZ", c.CabinClass.PremiumEconomy)
    # run("YVR", "YYZ", c.CabinClass.Business)
    # run("KUL", "YYZ", c.CabinClass.First)
