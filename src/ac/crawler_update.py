import datetime
import logging
from collections import namedtuple

import requests
import re
from src import constants as c
from typing import Iterator, List
from bs4 import BeautifulSoup

from src.ac.constants import CabinClassCodeMapping
from src.base import RequestsBasedAirlineCrawler, logger
from src.constants import Airline, CabinClass
from src.exceptions import LiveCheckerException
from src.schema import CashFee, Flight, FlightSegment
from src.utils import (
    convert_k_to_float
)
FlightTime = namedtuple("FlightTime", ["date", "time", "timezone"])

def parse_datetime(time_format_string: str) -> FlightTime:
    parsed_datetime = datetime.datetime.strptime(time_format_string, "%Y-%m-%dT%H:%M:%S.%f%z")
    return FlightTime(
        date=parsed_datetime.date().isoformat(),
        time=parsed_datetime.time().isoformat(),
        timezone=f"{parsed_datetime.tzinfo}",
    )

class AmericanAirlineZenrowsCrawler(RequestsBasedAirlineCrawler):
    AIRLINE = Airline.AmericanAirline
    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: CabinClass = CabinClass.Economy,
    ) -> Iterator[Flight]:
        try:
            departure_date_str = departure_date.strftime("%Y-%m-%d")
            url = (
                f"https://www.aircanada.com/ca/fr/aco/home/app.html#/search?org1=JFK&dest1=AAL&orgType1=A&destType1=A&departure1=21%2F12%2F2023&marketCode=INT&numberOfAdults=1&numberOfYouth=0&numberOfChildren=0&numberOfInfants=0&numberOfInfantsOnSeat=0&tripType=O&isFlexible=false"
            )
            print("c.ZENROWS_API_KEY")
            print(c.ZENROWS_API_KEY)
            params = {
                "url": url,
                "apikey": c.ZENROWS_API_KEY,
                "js_render": "true",
                "antibot": "true",
                "premium_proxy": "true",
                "wait_for": ".itinerary-info-ctr",
                "block_resources": "image,media,font",
                "json_response": "true",
                "proxy_country": "us"
            }

            print('Before requests')
            response = requests.get("https://api.zenrows.com/v1/", params=params)
            logger.info("Got Zenrows response...")
            print('After requests')
            print(response)

            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()

                # Extract the HTML content from the JSON
                html_content = json_data.get('html', '')

                soup = BeautifulSoup(html_content, "lxml")
                flight_cards = soup.find_all("div", class_="flight-row-count")

                logger.info(f"Found {len(flight_cards)} flights...")

                for index, flight_row_element in enumerate(flight_cards):
                    try:
                        cabin_class_code = CabinClassCodeMapping[cabin_class]
                        button_price_element = flight_row_element.find('button', class_='btn cabin-hover-display', string=f'{cabin_class_code}')
                        price = button_price_element.find('div', class_='display-on-hover').text.strip()
                        print ("price")
                        print (price)
                    except Exception as e:
                        logging.info(f"The detail of search item is not retrieved => index: {index}. error: {e}")
                        continue

        except (LiveCheckerException, Exception) as e:
            raise e

if __name__ == "__main__":
    import json
    import time
    from dataclasses import asdict

    def run(origin, destination, cabin_class):
        start_time = time.perf_counter()
        crawler = AmericanAirlineZenrowsCrawler()
        departure_date = datetime.date.today() + datetime.timedelta(days=14)
        flights = list(
            crawler.run(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
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

    run("JFK", "LAX", CabinClass.Economy)