from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from time import sleep
import json

# Load settings from settings.json
def load_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

settings = load_settings()

TEST_MODE = settings.get("TEST_MODE")

def legacy_reschedule(driver) -> None:
    """
    Attempts to reschedule an appointment using a web automation script via Selenium.

    The script searches for the nearest available date and time slot, selects them,
    and submits the rescheduling request. Retries the process up to 3 times in case of failure.

    Parameters:
    - driver (webdriver): A Selenium WebDriver instance controlling the browser.

    Returns:
    - None. Prints success or failure messages depending on the outcome.

    Raises:
    - TimeoutException, NoSuchElementException, ElementClickInterceptedException: 
      If any issues occur during the process.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.refresh()
            
            # Wait for and click the date input field
            date_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_date"))
            )
            date_input.click()

            def next_month() -> None:
                """
                Clicks the next month button in the datepicker.
                """
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-next"))
                )
                next_button.click()

            def cur_month_ava() -> bool:
                """
                Checks if there are any available dates in the current month.

                Returns:
                - bool: True if available dates exist, False otherwise.
                """
                calendar = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "ui-datepicker-div"))
                )
                dates = calendar.find_elements(By.CSS_SELECTOR, "td:not(.ui-datepicker-unselectable)")
                return len(dates) > 0

            def nearest_ava() -> int:
                """
                Finds the nearest available month with at least one available date.

                Returns:
                - int: The number of months from the current month to the nearest available date.
                
                Raises:
                - Exception: If no available dates are found within 16 months.
                """
                ava_in = 0
                while not cur_month_ava():
                    next_month()
                    ava_in += 1
                    if ava_in > 16: 
                        raise Exception("No available dates found within 12 months")
                return ava_in

            available_in_months = nearest_ava()

            # Select the first available date
            available_date = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#ui-datepicker-div td:not(.ui-datepicker-unselectable) a"))
            )
            available_date.click()
            sleep(3)

            # Select the time
            time_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_time"))
            )
            select = Select(time_select)

            select.select_by_index(len(select.options) - 1)  # Select the last option
            #select.select_by_index(1) select the first option 

            # Click "Reschedule" button
            reschedule_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='Reschedule']"))
            )
            reschedule_button.click()

            # Confirm rescheduling if not in test mode
            if not TEST_MODE:
                confirm = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button.alert"))
                )
                confirm.click()

                # Wait for the confirmation dialog to close
                WebDriverWait(driver, 30).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "a.button.alert"))
                )
            # Locate the div with the specific class and ID
            message_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#flash_messages.learnMorePopUp"))
            )

            
            success_message = message_div.find_element(By.CSS_SELECTOR, "div.learn_more > p").text
            if "successfully" in success_message:
                print(f"Successfully rescheduled for {available_in_months} months from now!")
            else:
                print("Rescheduling failed. The date may have been taken by someone else.")
            return

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            print(f"Rescheduling attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Retrying...")
                sleep(5)
            else:
                print("Max retries reached. Rescheduling failed.")
                raise