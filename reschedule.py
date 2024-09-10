import re
import json
import traceback
from datetime import datetime
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from legacy_rescheduler import legacy_reschedule
from request_tracker import RequestTracker
#from settings import *

# Load settings from settings.json
def load_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

settings = load_settings()

# Assign settings to variables
USER_EMAIL = settings.get("USER_EMAIL")
USER_PASSWORD = settings.get("USER_PASSWORD")
EARLIEST_ACCEPTABLE_DATE = settings.get("EARLIEST_ACCEPTABLE_DATE")
LATEST_ACCEPTABLE_DATE = settings.get("LATEST_ACCEPTABLE_DATE")
HEADLESS_MODE = settings.get("HEADLESS_MODE")
TEST_MODE = settings.get("TEST_MODE")
DETACH = settings.get("DETACH")
NEW_SESSION_AFTER_FAILURES = int(settings.get("NEW_SESSION_AFTER_FAILURES", 5))
NEW_SESSION_DELAY = int(settings.get("NEW_SESSION_DELAY", 120))
TIMEOUT = int(settings.get("TIMEOUT", 10))
FAIL_RETRY_DELAY = int(settings.get("FAIL_RETRY_DELAY", 30))
DATE_REQUEST_DELAY = int(settings.get("DATE_REQUEST_DELAY", 30))
DATE_REQUEST_MAX_RETRY = int(settings.get("DATE_REQUEST_MAX_RETRY", 60))
DATE_REQUEST_MAX_TIME = int(settings.get("DATE_REQUEST_MAX_TIME", 1800))
LOGIN_URL = settings.get("LOGIN_URL")
AVAILABLE_DATE_REQUEST_SUFFIX = settings.get("AVAILABLE_DATE_REQUEST_SUFFIX")
APPOINTMENT_PAGE_URL = settings.get("APPOINTMENT_PAGE_URL")
PAYMENT_PAGE_URL = settings.get("PAYMENT_PAGE_URL")
REQUEST_HEADERS = settings.get("REQUEST_HEADERS")


def get_chrome_driver() -> WebDriver:
    """
    Initializes and returns a Chrome WebDriver instance with specified options.

    Returns:
    - WebDriver: An instance of Chrome WebDriver configured with headless or visible GUI 
      based on the settings.
    """
    options = webdriver.ChromeOptions()
    if not HEADLESS_MODE:
        options.add_argument("headless")
        options.add_argument("window-size=1920x1080")
        options.add_argument("disable-gpu")
    options.add_experimental_option("detach", DETACH)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    return driver


def login(driver: WebDriver) -> None:
    """
    Logs in to the appointment website using the provided WebDriver instance.

    Parameters:
    - driver (WebDriver): A Selenium WebDriver instance controlling the browser.

    Returns:
    - None. Logs in to the website using pre-configured user credentials.
    """
    driver.get(LOGIN_URL)
    timeout = TIMEOUT
    sleep(10)
    email_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "user_email"))
    )
    email_input.send_keys(USER_EMAIL)

    password_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "user_password"))
    )
    password_input.send_keys(USER_PASSWORD)
    
    policy_checkbox = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "icheckbox"))
    )
    policy_checkbox.click()

    login_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.NAME, "commit"))
    )
    login_button.click()


def get_appointment_page(driver: WebDriver) -> None:
    """
    Navigates to the appointment page after logging in.

    Parameters:
    - driver (WebDriver): A Selenium WebDriver instance controlling the browser.

    Returns:
    - None. Navigates to the appointment page using the current URL.
    """
    timeout = TIMEOUT
    continue_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Continue"))
    )
    continue_button.click()
    current_url = driver.current_url
    url_id = re.search(r"/(\d+)", current_url).group(1)
    appointment_url = APPOINTMENT_PAGE_URL.format(id=url_id)
    driver.get(appointment_url)


def get_available_dates(driver: WebDriver, request_tracker: RequestTracker) -> list | None:
    """
    Retrieves a list of available appointment dates from the appointment page.

    Parameters:
    - driver (WebDriver): A Selenium WebDriver instance controlling the browser.
    - request_tracker (RequestTracker): Tracks retries and request timeouts.

    Returns:
    - list | None: A list of available dates if successful, None otherwise.
    """
    request_tracker.log_retry()
    request_tracker.retry()
    #print(request_tracker)
    current_url = driver.current_url
    #print(current_url)
    request_url = current_url + AVAILABLE_DATE_REQUEST_SUFFIX
    #print(request_url)
    request_header_cookie = "".join(
        [f"{cookie['name']}={cookie['value']};" for cookie in driver.get_cookies()]
    )
    request_headers = REQUEST_HEADERS.copy()
    request_headers["Cookie"] = request_header_cookie
    request_headers["User-Agent"] = driver.execute_script("return navigator.userAgent")
    try:
        response = requests.get(request_url, headers=request_headers)
        #print(response)
    except Exception as e:
        print("Get available dates request failed: ", e)
        return None
    if response.status_code != 200:
        print(f"Failed with status code {response.status_code}")
        return None
    try:
        dates_json = response.json()
    except:
        print("Failed to decode json")
        return None
    dates = [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in dates_json]
    print(dates)
    return dates


def reschedule(driver: WebDriver) -> bool:
    """
    Attempts to reschedule the appointment by selecting the earliest available date.

    Parameters:
    - driver (WebDriver): A Selenium WebDriver instance controlling the browser.

    Returns:
    - bool: True if the rescheduling was successful, False otherwise.
    """
    date_request_tracker = RequestTracker(DATE_REQUEST_MAX_RETRY, DATE_REQUEST_MAX_TIME)
    while date_request_tracker.should_retry():
        dates = get_available_dates(driver, date_request_tracker)
        if not dates:
            print("Error occured when requesting available dates")
            sleep(DATE_REQUEST_DELAY)
            continue
        earliest_available_date = dates[0]
        latest_acceptable_date = datetime.strptime(LATEST_ACCEPTABLE_DATE, "%Y-%m-%d").date()

        if earliest_available_date <= latest_acceptable_date:
            print(f"{datetime.now().strftime('%H:%M:%S')} FOUND SLOT ON {earliest_available_date}!!!")
            try:
                legacy_reschedule(driver)
                print("SUCCESSFULLY RESCHEDULED!!!")
                return True
            except Exception as e:
                print("Rescheduling failed: ", e)
                traceback.print_exc()
                continue
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')} Earliest available date is {earliest_available_date}")
        sleep(DATE_REQUEST_DELAY)
    return False


def reschedule_with_new_session() -> bool:
    """
    Attempts to reschedule by creating a new session, logging in, and trying to reschedule the appointment.

    Returns:
    - bool: True if the rescheduling was successful, False otherwise.
    """
    driver = get_chrome_driver()
    session_failures = 0
    while session_failures < NEW_SESSION_AFTER_FAILURES:
        try:
            login(driver)
            get_appointment_page(driver)
            break
        except Exception as e:
            print("Unable to get appointment page: ", e)
            session_failures += 1
            sleep(FAIL_RETRY_DELAY)
            continue
    rescheduled = reschedule(driver)
    if rescheduled:
        return True
    else:
        driver.quit()
        return False


if __name__ == "__main__":
    session_count = 0
    while True:
        session_count += 1
        print(f"Attempting with new session #{session_count}")
        rescheduled = reschedule_with_new_session()
        sleep(NEW_SESSION_DELAY)
        if rescheduled:
            break
