#Implementation of Selenium WebDriver with Python using PyTest
import pytest
from selenium import webdriver
import sys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
def test_lambdatest_google():
    chrome_driver = webdriver.Chrome()
    chrome_driver.get('https://www.google.com')
    chrome_driver.maximize_window()
    if not "Google" in chrome_driver.title:
        raise Exception("Could not load page")
    element = chrome_driver.find_element_by_name("q")
    element.send_keys("LambdaTest")
    element.submit()
    # Check if the LambdaTest Home Page is open
    title = "Most Powerful Cross Browser Testing Tool Online | LambdaTest"
    lt_link = chrome_driver.find_element_by_xpath("//h3[.='LambdaTest: Most Powerful Cross Browser Testing Tool Online']")
    lt_link.click()
    sleep(5)
    assert title == chrome_driver.title
    sleep(2)
    chrome_driver.quit()