import datetime
import logging
import os
import re
import shutil
import stat
import tempfile
import traceback
from typing import Iterator, List, Optional

import undetected_chromedriver as uc
from retry import retry
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from src import constants as c
from src.exceptions import (
    AirportNotSupported,
    CrawlerException,
    DepartureDateNotSelectable,
    DestinationNotSelectable,
    MileNotSelectable,
    NoSearchResult,
    OnewayNotSelectable,
    OriginNotSelectable,
)
from src.proxy import PrivateProxyService, ProxyExtension
from src.schema import Flight
from src.types import SmartCabinClassType, SmartDateType

logger = logging.getLogger(__name__)


class SeleniumBasedCrawler:
    HOME_PAGE_URL = ""

    def __init__(self):
        self._driver = None
        self.proxy_service = PrivateProxyService()
        self._driver_dir = None

    def setup_driver(self):
        logger.info("Setting Web Driver...")
        caps = DesiredCapabilities.CHROME
        caps["pageLoadStrategy"] = "eager"

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--whitelisted-ips=''")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-xss-auditor")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--log-level=3")
        # chrome_options.add_argument(
        #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0"
        # )
        # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False, "profile.default_content_setting_values.notifications": 1}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.headless = False

        # proxy = self.proxy_service.choose_proxy()
        # print("proxy:", proxy)
        # proxy_extension = ProxyExtension(
        #     host=proxy.host,
        #     port=proxy.port,
        #     user=proxy.user,
        #     password=proxy.password,
        # )

        # proxy_extension = ProxyExtension(
        #     host="77.47.247.147",
        #     port =50100,
        #     user="iceworld035",
        #     password="R9XttWsJTR",
        # )
        # http://iceworld035:R9XttWsJTR@77.47.247.147:50100 

        # chrome_options.add_argument(f"--load-extension={proxy_extension.directory}")

        # driver_path = self.duplicate_undetected_driver()
        driver = uc.Chrome(options=chrome_options, desired_capabilities=caps, driver_executable_path=c.CHROME_DRIVER_PATH)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver = driver
        logger.info("Driver is ready")
        return driver

    def quit_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self._driver = None
            self.remove_duplicated_undetected_driver()

    def duplicate_undetected_driver(self) -> str:
        if c.CHROME_DRIVER_PATH:
            logger.info("Duplicating undetected driver")
            self._driver_dir = os.path.normpath(tempfile.mkdtemp())
            driver_path = os.path.join(self._driver_dir, "chromedriver")
            shutil.copyfile(c.CHROME_DRIVER_PATH, driver_path)
            logger.info(f"Duplicated at {driver_path}")
            driver_permission = os.stat(driver_path)
            os.chmod(driver_path, driver_permission.st_mode | stat.S_IEXEC)
            return driver_path

    def remove_duplicated_undetected_driver(self):
        if self._driver_dir:
            shutil.rmtree(self._driver_dir)
            logger.info("Deleted duplicated chrome driver")

    def save_screenshot(self, file_name):
        self.driver.save_screenshot(file_name)

    @property
    def driver(self) -> Optional[WebDriver]:
        return self._driver

    def wait_until_presence(
        self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP
    ) -> Optional[WebElement]:
        return WebDriverWait(self.driver, timeout).until(ec.presence_of_element_located((by, identifier)))

    def wait_until_visible(
        self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP
    ) -> Optional[WebElement]:
        return WebDriverWait(self.driver, timeout).until(ec.visibility_of_element_located((by, identifier)))

    def wait_until_exception(
            self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP
    ) -> Optional[WebElement]:
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        your_element = WebDriverWait(self.driver, timeout, ignored_exceptions=ignored_exceptions) \
            .until(ec.presence_of_element_located((by, identifier)))
        return your_element
    def wait_until_clickable(
        self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP
    ) -> Optional[WebElement]:
        return WebDriverWait(self.driver, timeout).until(ec.element_to_be_clickable((by, identifier)))

    def wait_until_all_visible(
        self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP
    ) -> List[WebElement]:
        return WebDriverWait(self.driver, timeout).until(ec.presence_of_all_elements_located((by, identifier)))

    def find_and_click_element(self, identifier: str, by: str = By.XPATH, from_element: Optional[WebElement] = None):
        if from_element:
            element = from_element.find_element(by=by, value=identifier)
        else:
            element = self.driver.find_element(by=by, value=identifier)
        self.scroll_and_click_element(element)

    def click_element(self, element: WebElement):
        self.driver.execute_script("arguments[0].click();", element)

    def scroll_to(self, element: WebElement):
        self.driver.execute_script("arguments[0].scrollIntoView(false);", element)

    def scroll_and_click_element(self, element: WebElement):
        self.driver.execute_script("arguments[0].scrollIntoView(false);", element)
        self.driver.execute_script("arguments[0].click();", element)

    def click_once_clickable(self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP):
        element = self.wait_until_clickable(identifier, by, timeout)
        self.scroll_and_click_element(element)

    def click_once_presence(self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP):
        element = self.wait_until_presence(identifier, by, timeout)
        self.click_element(element)

    def click_once_visible(self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP):
        element = self.wait_until_visible(identifier, by, timeout)
        self.click_element(element)

    # def click_mouse_action(self, identifier: str, by: str = By.XPATH, timeout: int = c.DEFAULT_SLEEP)
    #     element = driver.find_element_by_id('your-id') # or your another selector here
    #     action.move_to_element(element)
    #     action.perform()

    def find_elements(self, identifier: str, by: str = By.XPATH, from_element: Optional[WebElement] = None):
        if from_element:
            return from_element.find_elements(by, identifier)
        else:
            return self.driver.find_elements(by, identifier)

    def find_element(self, identifier: str, by: str = By.XPATH, from_element: Optional[WebElement] = None):
        if from_element:
            return from_element.find_element(by, identifier)
        else:
            return self.driver.find_element(by, identifier)

    def get_text_from_element(self, identifier: str, by: str = By.XPATH, from_element: Optional[WebElement] = None):
        if from_element:
            element = from_element.find_element(by, identifier)
        else:
            element = self.driver.find_element(by, identifier)
        return self.get_text(element)


    @staticmethod
    def get_text(element: Optional[WebElement] = None):
        try:
            if element:
                content = element.get_attribute("textContent")
                if content:
                    return re.sub(r"\s+", " ", content).strip()
        except Exception:
            traceback.print_exc()
        return ""


class RequestsBasedAirlineCrawler:
    NEED_VIRTUAL_DISPLAY = False
    RESPONSE_FORMAT = c.ResponseFormat.Buffered

    def __init__(self):
        pass

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: SmartCabinClassType = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        pass

    def run(
        self,
        origin: str,
        destination: str,
        departure_date: SmartDateType,
        cabin_class: SmartCabinClassType = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        if isinstance(cabin_class, str):
            cabin_class = c.CabinClass(cabin_class)

        if isinstance(departure_date, str):
            departure_date = datetime.date.fromisoformat(departure_date)

        for flight in self._run(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            cabin_class=cabin_class,
        ):
            yield flight


class SeleniumBasedAirlineCrawler(SeleniumBasedCrawler):
    AIRLINE: Optional[c.Airline] = None
    REQUIRED_LOGIN = False
    NEED_VIRTUAL_DISPLAY = True
    RESPONSE_FORMAT = c.ResponseFormat.Streaming

    DEPARTURE_IATA = ""
    DESTINATION_IATA = ""
    KEYVELD = ""

    def _select_oneway(self) -> None:
        raise NotImplementedError("`_choose_oneway` should be implemented")

    def select_oneway(self) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Selecting one way...")
            self._select_oneway()
        except Exception:
            raise OnewayNotSelectable(
                airline=self.AIRLINE,
            )

    def _ryanair(self, origin:str, destination:str, keyveld:str) -> None:
        raise NotImplementedError("`-Ryanair info` should be implemented")

    def ryanair(self, origin:str, destination:str, keyveld:str) -> None:

        self.DEPARTURE_IATA = origin
        self.DEPARTURE_IATA = destination
        self.KEYVELD = keyveld

        try:
            logger.info(f"{self.AIRLINE.value}: Ryanair ...")
            self._ryanair(origin, destination, keyveld)
        except Exception:
            raise

    def _vueling(self, origin:str, destination:str, keyveld:str) -> None:
        raise NotImplementedError("`-Ryanair info` should be implemented")

    def vueling(self, origin:str, destination:str, keyveld:str) -> None:

        self.DEPARTURE_IATA = origin
        self.DEPARTURE_IATA = destination
        self.KEYVELD = keyveld

        try:
            logger.info(f"{self.AIRLINE.value}: Vueling ...")
            self._vueling(origin, destination, keyveld)
        except Exception:
            raise

    def _price_info(self) -> None:
        raise NotImplementedError("`-price info` should be implemented")
    def price_info(self) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Selecting one way...")
            self._price_info()
        except Exception:
            raise OnewayNotSelectable(
                airline=self.AIRLINE,
            )

    def _transavia(self, origin:str, destination:str, keyveld:str) -> None:
        raise NotImplementedError("`-transavia info` should be implemented")

    def transavia(self, origin:str, destination:str, keyveld:str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._transavia(origin, destination, keyveld)
        except Exception:
            raise
    def _easyjet(self, origin:str, destination:str, keyveld:str) -> None:
        raise NotImplementedError("`-easyjet info` should be implemented")

    def easyjet(self, origin:str, destination:str, keyveld:str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: easyjet ...")
            self._easyjet(origin, destination, keyveld)
        except Exception:
            raise

    def _wizzair(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("wizzair info` should be implemented")

    def wizzair(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._wizzair(origin, destination, keyveld)
        except Exception:
            raise

    def _linkedin(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("wizzair info` should be implemented")

    def linkedin(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._linkedin(origin, destination, keyveld)
        except Exception:
            raise

    def _aliexpress(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("wizzair info` should be implemented")

    def aliexpress(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._aliexpress(origin, destination, keyveld)
        except Exception:
            raise
    
    def _ebay(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("wizzair info` should be implemented")

    def ebay(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._ebay(origin, destination, keyveld)
        except Exception:
            raise

    def _mexico(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("wizzair info` should be implemented")

    def mexico(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Transavia ...")
            self._mexico(origin, destination, keyveld)
        except Exception:
            raise

    def _googlevocie(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("GoogleVoice` should be implemented")

    def googlevoice(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: GoogleVoice ...")
            self._googlevocie(origin, destination, keyveld)
        except Exception:
            raise
    
    def _nurse(self, origin: str, destination: str, keyveld: str) -> None:
        # raise NotImplementedError("`-wizzair info` should be implemented")
        print("Nurse` should be implemented")

    def nurse(self, origin: str, destination: str, keyveld: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Nurse ...")
            self._nurse(origin, destination, keyveld)
        except Exception:
            raise

    def psprint(self) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: PsPrint ... ")
            self._psprint()
        except Exception:
            raise

    def _psprint(self) -> None:
        raise NotImplementedError("psprint info should be implemented")
    def _select_miles(self) -> None:
        raise NotImplementedError("`_choose_miles` should be implemented")

    def select_miles(self) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Selecting miles...")
            self._select_miles()
        except Exception:
            raise MileNotSelectable(airline=self.AIRLINE)

    def _select_origin(self, origin: str) -> None:
        raise NotImplementedError("`_choose_origin` should be implemented")

    def select_origin(self, origin: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Selecting origin airport({origin})...")
            self._select_origin(origin)
        except (AirportNotSupported, OriginNotSelectable) as e:
            raise e
        except Exception:
            raise OriginNotSelectable(airline=self.AIRLINE, airport=origin)

    def _select_destination(self, origin: str) -> None:
        raise NotImplementedError("`_choose_destination` should be implemented")

    def select_destination(self, destination: str) -> None:
        try:
            logger.info(f"{self.AIRLINE.value} Selecting destination airport({destination})...")
            self._select_destination(destination)
        except AirportNotSupported as e:
            raise e
        except Exception:
            raise DestinationNotSelectable(airline=self.AIRLINE, airport=destination)

    def _select_date(self, departure_date: datetime.date) -> None:
        raise NotImplementedError("`_choose_destination` should be implemented")

    def select_date(self, departure_date: datetime.date) -> None:
        try:
            logger.info(f"{self.AIRLINE.value}: Selecting departure date({departure_date})...")
            self._select_date(departure_date)
        except Exception:
            raise DepartureDateNotSelectable(
                airline=self.AIRLINE,
                departure_date=departure_date,
            )

    def accept_cookie(self):
        raise NotImplementedError("`accept_cookie` should be implemented")

    def _submit(self):
        raise NotImplementedError("`_submit` should be implemented")

    def submit(self):
        logger.info(f"{self.AIRLINE.value} Submitting...")
        self._submit()

    def _login(self):
        pass

    def login(self):
        logger.info(f"{self.AIRLINE.value}: Logging into...")
        self._login()

    def search(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: c.CabinClass = c.CabinClass.Economy,
    ) -> None:
        logger.info(f"{self.AIRLINE.value}: Searching...")
        # self.price_info()

        keyveld = cabin_class
        # self.transavia(origin, destination, keyveld)

        # self.ryanair(origin,destination, keyveld)
        # self.wizzair(origin, destination, keyveld)
        # self.psprint()
        # self.select_oneway()
        # self.select_origin(origin)
        # self.select_destination(destination)
        # self.select_date(departure_date)
        # self.select_miles()
        # self.accept_cookie()
        # self.submit()
        print("------Airline--------")
        print (self.AIRLINE.value)
        if "Vueling" in self.AIRLINE.value:
            print("@@@Vueling-Airline@@@")
            self.vueling(origin, destination, keyveld)
        elif "Transavia" in self.AIRLINE.value:
            print("@@@Transavia-Airline@@@")
            self.transavia(origin, destination, keyveld)
        elif "easyjet" in self.AIRLINE.value:
            print("@@@easyjet-Airline@@@")
            self.easyjet(origin, destination, keyveld)
        elif "Ryanair" in self.AIRLINE.value:
            print("@@@ryanair-Airline@@@")
            self.ryanair(origin, destination, keyveld)
        elif "Wizzair" in self.AIRLINE.value:
            print("@@@Wizzair-Airline@@@")
            self.wizzair(origin, destination, keyveld)
        elif "linkedin" in self.AIRLINE.value:
            print("@@@Linkedin@@@")
            self.linkedin(origin, destination, keyveld)
        elif "aliexpress" in self.AIRLINE.value:
            print("@@@aliexpress@@@")
            self.aliexpress(origin, destination, keyveld)
        elif "ebay" in self.AIRLINE.value:
            print("@@@ebay@@@")
            self.ebay(origin, destination, keyveld)
        elif "mexico" in self.AIRLINE.value:
            print("@@@mexico@@@")
            self.mexico(origin, destination, keyveld)
        elif "googlevoice" in self.AIRLINE.value:
            print("@@@googlevoice@@@")
            self.googlevoice(origin, destination, keyveld)
        
        elif "nurse" in self.AIRLINE.value:
            print("@@@  NURSE  @@@")
            self.nurse(origin, destination, keyveld)




    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: c.CabinClass = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        pass

    def check_ip_address(self):
        self.driver.get("http://utilserver.privateproxy.me")
        element = self.wait_until_visible(
            by=By.CSS_SELECTOR,
            identifier="pre",
            timeout=c.HIGH_SLEEP,
        )
        logger.info(element.text)

    def validate(
        self,
        origin: str,
        destination: str,
        departure_date: datetime.date,
        cabin_class: c.CabinClass = c.CabinClass.Economy,
    ):
        if len(origin) != 3 or len(destination) != 3:
            return False
        if departure_date < datetime.date.today():
            return False
        if self.AIRLINE == c.Airline.VirginAtlantic and cabin_class == c.CabinClass.First:
            return False
        if self.AIRLINE == c.Airline.HawaiianAirline and cabin_class not in [c.CabinClass.Economy, c.CabinClass.First]:
            return False
        return True

    @retry(CrawlerException, tries=c.RETRY_COUNT)
    def run(
        self,
        origin: str,
        destination: str,
        departure_date: SmartDateType,
        cabin_class: SmartCabinClassType = c.CabinClass.Economy,
    ) -> Iterator[Flight]:
        if isinstance(cabin_class, str):
            cabin_class = c.CabinClass(cabin_class)

        if isinstance(departure_date, str):
            departure_date = datetime.date.fromisoformat(departure_date)

        # is_validated = self.validate(origin, destination, departure_date, cabin_class)
        # if not is_validated:
        #     return []

        try:
            self.setup_driver()
            # self.check_ip_address()
            logger.info(f"{self.AIRLINE.value}: Go to {self.HOME_PAGE_URL}")
            self.driver.get(self.HOME_PAGE_URL)
            if self.REQUIRED_LOGIN:
                self.login()
            self.search(origin, destination, departure_date, cabin_class)
            self.quit_driver()
            print('@@@@@@@@@@@      END        @@@@@@@@@@@@@@@@')
            # for flight in self._run(origin, destination, departure_date, cabin_class):
            #     yield flight
        except (AirportNotSupported, NoSearchResult) as e:
            logger.error(f"{self.AIRLINE.value}: {e.message}")
            return []
        except Exception as e:
            logger.error(f"{self.AIRLINE.value}: {e}")
            raise e
        finally:
            self.quit_driver()
