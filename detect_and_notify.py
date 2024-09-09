import requests
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from request_tracker import RequestTracker
from reschedule import get_chrome_driver, login
from settings import *

def get_dates_from_payment_page(driver: WebDriver) -> tuple[list, list]:
    """
    Navigate to the payment page and retrieve available appointment dates and locations.
    
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
    
    Returns:
        tuple: A tuple containing two lists:
               - loc_str_array: List of locations
               - date_str_array: List of corresponding appointment dates
    """
    
    timeout = TIMEOUT
    continue_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Continue"))
    )
    continue_button.click()
    current_url = driver.current_url
    url_id = re.search(r"/(\d+)", current_url).group(1)
    payment_url = PAYMENT_PAGE_URL.format(id=url_id)
    driver.get(payment_url)

    content_table = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "for-layout"))
    )
    text_elements = content_table.find_elements(By.TAG_NAME, "td")
    loc_str_array = [e.text for i, e in enumerate(text_elements) if i % 2 == 0]
    date_str_array = [e.text for i, e in enumerate(text_elements) if i % 2 == 1]
    return loc_str_array, date_str_array

def detect_and_notify(loc_str_array: list, date_str_array: list) -> bool:
    """
    Detect available appointment slots and notify if they fall within the acceptable date range.
    
    Args:
        loc_str_array (list): List of locations.
        date_str_array (list): List of corresponding appointment dates.
    
    Returns:
        bool: True if an acceptable slot is detected, False otherwise.
    """

    earliest_acceptable_date = datetime.strptime(EARLIEST_ACCEPTABLE_DATE, "%Y-%m-%d").date()
    latest_acceptable_date = datetime.strptime(LATEST_ACCEPTABLE_DATE, "%Y-%m-%d").date()

    detected = False
    for loc_str, date_str in zip(loc_str_array, date_str_array):
        if date_str == "No Appointments Available":
            continue
        date = datetime.strptime(date_str, "%d %B, %Y").date()
        
        if earliest_acceptable_date <= date <= latest_acceptable_date:
            print(f"{datetime.now().strftime('%H:%M:%S')} FOUND SLOT ON {date}, location: {loc_str}!!!, sending email...")
            detected = True
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')} Earliest available date is {date}, location: {loc_str}")
    return detected

def detect_with_new_session() -> bool:
    """
    Create a new browser session to detect appointment availability and notify.
    
    Returns:
        bool: True if an acceptable slot is detected, False otherwise.
    """
    driver = get_chrome_driver()
    session_failures = 0
    detected = False
    while session_failures < NEW_SESSION_AFTER_FAILURES:
        try:
            login(driver)
            loc_str_array, date_str_array = get_dates_from_payment_page(driver)
            detected = detect_and_notify(loc_str_array, date_str_array)
            break
        except Exception as e:
            print("Unable to get payment page: ", e)
            session_failures += 1
            sleep(FAIL_RETRY_DELAY)
    driver.quit()
    return detected

if __name__ == "__main__":
    session_count = 0
    
    while True:
        session_count += 1
        print(f"Attempting with new session #{session_count}")
        detected = detect_with_new_session()
        sleep(NEW_SESSION_DELAY)
        if detected:
            sleep(600)
            print("Yay!!!")