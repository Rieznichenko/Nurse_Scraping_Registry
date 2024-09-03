import datetime
import logging
import re
import csv
import time
from typing import Dict, Iterator, List, Optional, Tuple

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebElement

from src import constants as c
from src.ac.constants import CabinClassCodeMapping
from src.base import SeleniumBasedAirlineCrawler
from src.exceptions import CannotContinueSearch, NoSearchResult, OriginNotSelectable,DestinationNotSelectable
from src.schema import CashFee, Flight, FlightSegment
from src.utils import convert_k_to_float, extract_digits
import random

logger = logging.getLogger(__name__)


class NurseCrawler(SeleniumBasedAirlineCrawler):
    # Constants for this crawler
    AIRLINE = c.Airline.Nurse
    HOME_PAGE_URL = ""  # URL to the home page if applicable
    CARRIER = "nurse"  # Identifier for the carrier

    def _nurse(self, csv_file_name: str, destination: str, keyveld: str) -> None:
        """
        Method to perform scraping for Nurse carrier.
        Saves data into a CSV file named 'output.csv'.

        Args:
            csv_file_name (str): Name of the output CSV file.
            destination (str): Destination parameter for scraping.
            keyveld (str): Key field parameter for scraping.
        """
        # Define the CSV file path and headers
        csv_file_path = f"output.csv"
        csv_header = ["Name", "Facility", "City", "Type", "Practice Information"]

        print("Nurse Scraper Running")

        # Accept terms and conditions by clicking the checkbox
        self.click_once_clickable(
            by=By.XPATH,
            identifier="//input[@id='chkAcceptTerms']",
            timeout=c.HIGHEST_SLEEP * 2,
        )

        # Introduce a random delay to mimic human interaction
        self.random_delay(c.LOWEST_SLEEP, c.LOW_SLEEP * 2)

        # Click the submit button to proceed
        self.click_once_clickable(
            by=By.XPATH,
            identifier="//button[@id='submitButton']",
            timeout=c.HIGHEST_SLEEP * 2,
        )

        # Wait for the page to load completely
        time.sleep(c.DEFAULT_SLEEP)

        # Locate the 'Last Name' input field, click, and enter a placeholder value
        lastname_input_list = self.wait_until_all_visible(
            by=By.XPATH, identifier="//input[@id='LastName']", timeout=c.HIGHEST_SLEEP * 2
        )
        lastname_input_list[0].click()
        lastname_input_list[0].send_keys("aa")

        # Introduce another random delay
        self.random_delay(c.LOWEST_SLEEP, c.LOW_SLEEP * 2)

        # Click the input field for 'NAME'
        self.click_once_clickable(
            by=By.XPATH,
            identifier="//input[@id='NAME']",
            timeout=c.HIGHEST_SLEEP * 2,
        )

        # Introduce a delay before the main data extraction loop
        self.random_delay(c.DEFAULT_SLEEP, c.MEDIUM_SLEEP)

        # Start the scraping loop
        while True:
            # Locate the table containing data using XPath
            select_elements = self.wait_until_all_visible(
                by=By.XPATH,
                identifier="//table[@class='table table-striped']",
                timeout=c.MEDIUM_SLEEP,
            )

            # Find all rows within the table
            rows = select_elements[0].find_elements(By.XPATH, ".//tbody/tr")

            # Iterate over each row to extract data
            for row in rows:
                # Find all cells in the current row
                cells = row.find_elements(By.XPATH, ".//td")

                # Log the extracted data for debugging
                print("name: " + cells[0].text)
                print("facility: " + cells[1].text)
                print("city: " + cells[2].text)
                print("type: " + cells[3].text)
                print("practice_information: " + cells[4].text)

                # Write the extracted data into the CSV file
                with open(csv_file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)

                    # Write header only if the file is empty
                    if file.tell() == 0:
                        writer.writerow(csv_header)

                    # Write the row data
                    writer.writerow(
                        [cells[0].text, cells[1].text, cells[2].text, cells[3].text, cells[4].text]
                    )

            # Introduce a delay before clicking the next button
            self.random_delay(c.LOW_SLEEP * 3, c.DEFAULT_SLEEP)

            # Click the next button to load more rows
            self.click_once_clickable(
                by=By.XPATH,
                identifier="//a[@class='btn btn-default btn-inline-form pull-right']",
                timeout=c.HIGHEST_SLEEP * 2,
            )

        # Indicate completion of the scraping process
        print("Scraper completed")
        self.random_delay(c.HIGHEST_SLEEP * 2)






        

    def random_delay(self, min_seconds, max_seconds):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def send_message(self, driver, settings):
        recipient = settings["recipient"] if settings["mode"] == "static" else random.choice(settings["recipient_list"])
        message_template = random.choice(settings["message_list"])
        message = message_template.replace("[TIME]", datetime.datetime.now().strftime("%B %d, %Y %I:%M:%S %p"))

        self.random_delay(c.MEDIUM_SLEEP * 2, c.HIGH_SLEEP)
        try:
            driver.get("https://voice.google.com/messages")

            self.random_delay(c.HIGH_SLEEP, c.HIGHEST_SLEEP)

            inbox_text_element = self.wait_until_all_visible(
                                    by=By.XPATH, 
                                    identifier="//div[@class='gvMessagingView-conversationListHeader']",
                                    timeout=c.HIGHEST_SLEEP
                                )
                                    
            inbox_text1 = inbox_text_element[0].text.strip()
            inbox_text_element[0].click()
            self.random_delay(c.LOW_SLEEP * 2, c.MEDIUM_SLEEP)

            # input Phone number
            phone_input_elements = self.wait_until_all_visible(
                by=By.XPATH, identifier="//input[@id='mat-mdc-chip-list-input-0']", timeout=c.HIGHEST_SLEEP
            )
            phone_input_elements[0].send_keys(settings["recipient"])

            self.random_delay(c.LOW_SLEEP * 2, c.MEDIUM_SLEEP)

            # Click Phone Number Section
            phone_number_sections = self.wait_until_all_visible(
                by=By.XPATH, identifier="//div[@id='send_to_button-0']", timeout=c.HIGHEST_SLEEP
            )
            phone_number_sections[0].click()
            

            self.random_delay(c.MEDIUM_SLEEP, c.HIGH_SLEEP)

            textarea_element = self.click_once_presence(
                by=By.XPATH,
                identifier="//textarea[@class='cdk-textarea-autosize message-input ng-untouched ng-pristine ng-valid']",
                timeout=c.MEDIUM_SLEEP,
            )
            self.random_delay(c.LOW_SLEEP, c.DEFAULT_SLEEP)
            select_elements = self.wait_until_all_visible(
                            by=By.XPATH,
                            identifier="//textarea[@class='cdk-textarea-autosize message-input ng-untouched ng-pristine ng-valid']",
                            timeout=c.MEDIUM_SLEEP,
                        )

            select_elements[0].send_keys(message)

            self.random_delay(c.LOW_SLEEP, c.DEFAULT_SLEEP)

            # Send message
            self.click_once_clickable(
                by=By.XPATH, identifier="//button[@aria-label='Send message']", timeout=c.MEDIUM_SLEEP
            )

            self.random_delay(c.MEDIUM_SLEEP, c.HIGH_SLEEP)
            print(f"Message sent to {recipient}: {message}")
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            email_list_element = self.wait_until_all_visible(
                by=By.XPATH, identifier="//li[@class='aZvCDf oqdnae W7Aapd zpCp3 SmR8']", timeout=c.HIGHEST_SLEEP
            )
            email_list_element[0].click()

            self.random_delay(c.DEFAULT_SLEEP, c.MEDIUM_SLEEP)

            password_input_list = self.wait_until_all_visible(
                by=By.XPATH, identifier="//input[@name='Passwd']", timeout=c.HIGHEST_SLEEP * 2
            )
            password_input_list[0].click()
            password_input_list[0].send_keys("qweQWE123!@#")
            self.click_once_clickable(by=By.XPATH,
                                    identifier="//div[@id='passwordNext']", 
                                    timeout=c.MEDIUM_SLEEP)
            
            self.random_delay(c.MEDIUM_SLEEP * 2, c.HIGH_SLEEP)

    def _first_item_extract(self, row, csv_file_name:str):
        try:
            productions_elements = self.wait_until_all_visible(
                by=By.XPATH, identifier="//ul[contains(@class, 'srp-results')]/li"
            )
        except:
            pass
        
        try:
            if "AU $" in productions_elements[1].text.strip():
                first_production_element = productions_elements[1]
            elif "AU $" in productions_elements[2].text.strip():
                first_production_element = productions_elements[2]
            else:
                first_production_element = productions_elements[3]
            print("productions_elements_2", first_production_element.text.strip())
        except:
            pass
        # pass
        try:
            ebay_name_elements = first_production_element.find_elements(By.XPATH, ".//span[@role='heading']")
            ebay_name = ebay_name_elements[0].text.strip()
            print("ebay_name", ebay_name)
        except:
            ebay_name = ""

        try:
            seller_info_elements = first_production_element.find_elements(By.XPATH, ".//span[@class='s-item__seller-info-text']")
            seller_info = seller_info_elements[0].text.strip()
            print("seller_info", seller_info)
        except:
            seller_info = ""

        try:
            ebay_price_elements = first_production_element.find_elements(By.XPATH, ".//span[@class='s-item__price']")
            ebay_price = ebay_price_elements[0].text.strip()
            print("ebay_price", ebay_price)
        except:
            ebay_price = ""

        try:
            img_elements = first_production_element.find_elements(By.XPATH, ".//img")
            img_src = img_elements[0].get_attribute("src")
            print("img_src:", img_src)
        except:
            img_src = ""

        try:
            sold_amount_elements = first_production_element.find_elements(By.XPATH, ".//span[@class='s-item__dynamic s-item__quantitySold']")
            sold_amount = sold_amount_elements[0].text.strip()
        except:
            sold_amount = ""
        
        try:
            item_link_elements = first_production_element.find_elements(By.XPATH, ".//a[@class='s-item__link']")
            item_link = item_link_elements[0].get_attribute("href")
        except:
            item_link = ""

        with open(csv_file_name, mode='a', newline='', encoding='utf-8') as file:
            print("csv_file_name:", csv_file_name)
            writer = csv.writer(file)
            writer.writerow([row["Type"], row["Description"], row["Sold"], row["Rating"], row["Price"], row["Origin-Price"], row["Image-Url"], ebay_name, ebay_price, img_src, seller_info, sold_amount, item_link])



    def _lazy_loading(self, type_text: str, csv_file_name: str) -> None:

        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

        # Specify the CSV file path with the current date
        csv_file_path = f"{type_text}_output_{current_date}.csv"
        csv_header = ["Type", "Description", "Sold", "Rating", "Price", "Origin-Price", "Image-Url"]
        
        # while True:
        #     self.scroll_to()
        # Get the initial height of the page
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        # # Scroll the page until the end of the content is reached
        count = 0
        while True:
            count += 1
            # Scroll down to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for the page to load
            time.sleep(c.LOW_SLEEP * 8)

            # Calculate the new height of the page
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Check if the new height is the same as the last height
            if new_height == last_height:
                # If the new height is the same as the last height, the page has finished loading
                break

            if count > 5:
                break
            # If the new height is different from the last height, update the last height and continue scrolling
            last_height = new_height

        # rax_elements = self.wait_until_all_visible(
        #                     by=By.XPATH,
        #                     identifier="//div[@class='rax-view-v2 src-components-TabPanel-index-module__virtualListWrapper--939Y6']/div[@class='rax-view-v2']",
        #                     timeout=c.DEFAULT_SLEEP * 2,
        #                 )

        # rax_elements = self.wait_until_all_visible(
        #     by=By.XPATH, identifier="//div[@id='recyclerview']/div/div[@mod-name='gmod-h5-rax-nn-waterfall']"
        # )

        rax_elements = self.wait_until_all_visible(
            by=By.XPATH, identifier="//div[@id='aec-list-container']//div[@class='swiper swiper-initialized swiper-horizontal swiper-pointer-events swiper-backface-hidden']"
        )
        rax_element = rax_elements[0]
        rax_element.get_attribute("class")
        print("rax_element.get_attribute.class:", rax_element.get_attribute("class"))

        print("rax_element.strip", rax_element.text.strip())
        temp_element = rax_element.find_element(By.XPATH, ".//div[@class='swiper-wrapper']/div[@class='swiper-slide swiper-slide-active']/div[@class='rax-view-v2 src-components-TabPanel-index-module__tabPanel--2Exxi']/div[@class='rax-view-v2 src-components-TabPanel-index-module__virtualListWrapper--939Y6']/div[@class='rax-view-v2']")
        print("temp_element:", temp_element.text.strip())
        # rax-view-v2 src-components-TabPanel-index-module__virtualListWrapper--939Y6
        rax_view_elements = temp_element.find_elements(By.XPATH, ".//div[@class='rax-view-v2']")

        for row_index, row_element in enumerate(rax_view_elements):
            # print("row_element_text:", row_element.text.strip())
            product_elements = row_element.find_elements(By.XPATH, ".//div[@data-spm]")
            for product_index, product_elment in enumerate(product_elements):
                # try:
                print("---------------------")
                product_text = product_elment.text.strip()
                print("product_text:", product_text)
                lines = product_text.strip().split('\n')

                img_elements = product_elment.find_elements(By.XPATH, ".//img[@class='item-card-img']")
                image_url = img_elements[0].get_attribute("src")

                # Extracting each element
                price1 = lines[1]
                price2 = lines[2]
                sold = lines[3]
                rating = lines[4]
                try:
                    description = lines[5]
                except:
                    description = ""

                print("price1:", price1)
                print("price2:", price2)
                print("sold:", sold)
                print("rating:", rating)
                print("description:", description)
                print("image_url:", image_url)

                with open(csv_file_name, mode='a', newline='', encoding='utf-8') as file:
                    print("csv_file_name:", csv_file_name)
                    writer = csv.writer(file)

                    # Check if the file is empty, then write the header
                    # if file.tell() == 0:
                    #     writer.writerow(csv_header)
                    #Type", "Description", "Sold", "Rating", "Price", "Origin-Price
                    # Write the extracted values
                    writer.writerow([type_text, description, sold, rating, price1, price2, image_url])
                # except:
                #     print("exception occured")
                #     continue

    def _save(self) -> None:
        self.click_once_clickable(
            by=By.XPATH,
            identifier="//div[@class='es--saveBtn--w8EuBuy']",
            timeout=c.MEDIUM_SLEEP * 2,
        )

    def _click_tech(self, cnt: int):
        button_elements = self.wait_until_all_visible(
            by=By.XPATH,
            identifier="//div[@class='rax-view-v2 tab-pc-text-item aec-tab-item-hoverable']",
            timeout=c.DEFAULT_SLEEP * 2,
        )

        button_elements[cnt].click()
        type_text = button_elements[cnt].text.strip()
        return type_text

    def _select_coutry(self) -> None:

        button_elements = self.wait_until_all_visible(
                            by=By.XPATH,
                            identifier="//span[@class='comet-icon comet-icon-chevrondown32 base--chevronIcon--25sHdop']",
                            timeout=c.DEFAULT_SLEEP * 3,
                        )

        button_elements[0].click()

        time.sleep(c.LOW_SLEEP * 2)

        select_elements = self.wait_until_all_visible(
                            by=By.XPATH,
                            identifier="//div[@class='select--text--1b85oDo']",
                            timeout=c.DEFAULT_SLEEP * 2,
                        )

        select_elements[0].click()

        time.sleep(c.LOW_SLEEP)
        
        try:
            
            

            print("Click Search Button")
            select_search_elements = self.wait_until_all_visible(
                by=By.XPATH,
                identifier="//div[@class='select--search--20Pss08']",
                timeout=c.MEDIUM_SLEEP * 2)
            select_first_element = select_search_elements[0]
            origin_input = select_first_element.find_elements(By.XPATH, ".//input")[0]
            origin_input.click()
            print("origin_input_attribute:", origin_input.get_attribute("data-spm-anchor-id"))
            print("Clicked Search Button")
            # self.click_element(origin_input)

        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when clicking origin element {e}"
            )
        else:
            origin_input.send_keys(Keys.CONTROL, "a")
            origin_input.send_keys("AUSTRA")
            time.sleep(c.LOW_SLEEP)

        try:

            select_list_elements = self.wait_until_all_visible(
                by=By.XPATH,
                identifier="//div[@class='select--item--32FADYB']",
                timeout=c.MEDIUM_SLEEP * 2)

            select_australia_element = select_list_elements[0]
            select_australia_element.click()

        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when selecting airport {e}"
            )

    def _select_currency(self) -> None:
        
        time.sleep(c.LOW_SLEEP)

        select_elements = self.wait_until_all_visible(
                            by=By.XPATH,
                            identifier="//div[@class='select--text--1b85oDo']",
                            timeout=c.DEFAULT_SLEEP * 2,
                        )

        select_elements[4].click()

        time.sleep(c.LOW_SLEEP)
        
        try:
            
            print("Click Currency Search Button")
            select_currency_search_elements = self.wait_until_all_visible(
                by=By.XPATH,
                identifier="//div[@class='select--search--20Pss08']",
                timeout=c.MEDIUM_SLEEP * 2)
            select_currency_first_element = select_currency_search_elements[4]
            currency_input = select_currency_first_element.find_elements(By.XPATH, ".//input")[0]
            currency_input.click()
            print("currency_input:", currency_input.get_attribute("data-spm-anchor-id"))
            print("Clicked currency_input Search Button")

        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when clicking origin element {e}"
            )
        else:
            currency_input.send_keys(Keys.CONTROL, "a")
            currency_input.send_keys("AUD")
            time.sleep(c.LOW_SLEEP)

        try:

            select_list_elements = self.wait_until_all_visible(
                by=By.XPATH,
                identifier="//div[@class='select--item--32FADYB']",
                timeout=c.MEDIUM_SLEEP * 2)

            select_australia_element = select_list_elements[413]
            select_australia_element.click()
            
        except (TimeoutException, NoSuchElementException) as e:
            raise OriginNotSelectable(
                airline=self.AIRLINE, airport=origin, reason=f"Error happened when selecting airport {e}"
            )
       
    def _submit(self) -> None:
        self.click_once_clickable(
            by=By.XPATH,
            identifier="identifier='//button[contains(@class, 'button-stretch--center')]",
            timeout=c.MEDIUM_SLEEP,
        )
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
            self.click_once_clickable(
                by=By.XPATH,
                identifier="//button[@id='onetrust-accept-btn-handler']",
                timeout=c.HIGH_SLEEP
            )
        except NoSuchElementException:
            print("No accept_cookie")
            pass



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
        for flight in self.extract(departure_date, cabin_class):
            yield flight

# Define your scraping task functions 
def task1(origin, destination, keyveld):
    run(origin, destination, keyveld)

def task2(origin, destination, keyveld):
    run(origin, destination, keyveld)

def task3(origin, destination, keyveld):
    run(origin, destination, keyveld)

if __name__ == "__main__":
    import json
    from dataclasses import asdict

    def run(origin, destination, cabin_class):
        start_time = time.perf_counter()
        crawler = NurseCrawler()
        crawler.HOME_PAGE_URL = f"https://registry.cno.org/"

        departure_date = datetime.date.today() + datetime.timedelta(days=14)
    
        crawler.run(
            origin=origin,
            destination=destination,
            departure_date=departure_date.isoformat(),
            cabin_class=cabin_class,
        )
    
        end_time = time.perf_counter()

        print(f"It took {end_time - start_time} seconds.")

    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    run("", "LAX", 1)