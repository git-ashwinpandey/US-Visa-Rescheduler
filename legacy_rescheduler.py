from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from time import sleep
from settings import TEST_MODE

def legacy_reschedule(driver):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.refresh()
            
            # Wait for and click the date input field
            date_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_date"))
            )
            date_input.click()

            # Function to move to next month in the datepicker
            def next_month():
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-next"))
                )
                next_button.click()

            # Check if available date in current month
            def cur_month_ava():
                calendar = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "ui-datepicker-div"))
                )
                dates = calendar.find_elements(By.CSS_SELECTOR, "td:not(.ui-datepicker-unselectable)")
                return len(dates) > 0

            # Find nearest available month
            def nearest_ava():
                ava_in = 0
                while not cur_month_ava():
                    next_month()
                    ava_in += 1
                    if ava_in > 16:  # Limit to prevent infinite loop
                        raise Exception("No available dates found within 12 months")
                return ava_in

            available_in_months = nearest_ava()

            # Select the first available date
            available_date = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#ui-datepicker-div td:not(.ui-datepicker-unselectable) a"))
            )
            available_date.click()
            sleep(3)
            # Wait for and select the time
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

            # Extract the text from the first <p> tag inside this div
            success_message = message_div.find_element(By.CSS_SELECTOR, "div.learn_more > p").text
            print(success_message)
            # Check if "successfully" is in the message
            if "successfully" in success_message:
                #print("success")
                print(f"Successfully rescheduled for {available_in_months} months from now!")
            return

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            print(f"Rescheduling attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Retrying...")
                sleep(5)  # Wait before retrying
            else:
                print("Max retries reached. Rescheduling failed.")
                raise