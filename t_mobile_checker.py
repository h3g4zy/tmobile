import json
import asyncio
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TMobileChecker:
    def __init__(self):
        # Set up Chrome options to disable notifications, geolocation, and enable headless mode
        # T-Mobile asks for location permissions, so we must disable it!
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-geolocation")
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--log-level=3")

        # Make it undetectable! :)
        self.chrome_options.add_argument("--disable-blink-features")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Initialize cache dictionary
        self.cache = {}

    @staticmethod
    def load_cookies(driver, cookies):
        """
        Load a list of cookies into a Selenium WebDriver instance.

        :param driver: Selenium WebDriver instance.
        :param cookies: List of dictionaries representing cookies.
        """
        valid_same_site_values = ["Strict", "Lax", "None"]

        for cookie in cookies:
            # Convert expirationDate from timestamp to datetime if necessary
            if 'expirationDate' in cookie:
                cookie['expiry'] = int(cookie.pop('expirationDate'))
            
            # Handle the sameSite attribute
            if 'sameSite' in cookie and cookie['sameSite'] not in valid_same_site_values:
                print(f"Invalid sameSite value: {cookie['sameSite']} in cookie {cookie['name']}. Removing sameSite attribute.")
                cookie.pop('sameSite')
            
            driver.add_cookie(cookie)

    async def create_driver_and_run(self, imei):
        # Check if result is already in cache
        if imei in self.cache:
            return self.cache[imei]

        driver = webdriver.Chrome(options=self.chrome_options)

        # driver.wait = WebDriverWait(driver, 10)
        
        try:
            driver.get('https://prepaid.t-mobile.com/bring-your-own-device?brand=TMOPrepaid')

            zip_code_field = self.wait_for_element_by_xpath(driver, "//input[@placeholder='ZIP code']", timeout=4)
            if zip_code_field:
                zip_code_field.send_keys("33129")
                await asyncio.sleep(1)
                driver.find_element(By.XPATH, "//button[@id='entry-modal-continue-cta']").click()
                
            # Wait for the IMEI input field
            input_field = self.wait_for_element_by_xpath(driver, "//input[@placeholder='IMEI*']")
            if input_field is None:
                return json.dumps({"error": "Timeout error: IMEI input field not found"})

            # Enter the IMEI
            input_field.send_keys(imei)

            # Click the compatibility check button
            button = self.wait_for_element_by_xpath(driver, "//button[@id='checkCompatibility']")
            if button is None:
                return json.dumps({"error": "Timeout error: Compatibility check button not found"})
            button.click()

            await asyncio.sleep(0.5)

            # Check for incompatibility
            result = self.check_for_incompatibility(driver, imei)
            if result is not None:
                self.cache[imei] = result
                return result


            
            # Wait for the results to load..
            results_div = self.wait_for_element_by_xpath(driver, "//div[@class='byod-device-sim-block row']", timeout=5)
            if results_div is None:
                # Check for errors
                error_xpath = "//p[@id='errorMessage0']"
                error_elem = self.is_element_found(driver, By.XPATH, error_xpath)
                if error_elem:
                    error_txt = error_elem.text.strip()
                    return json.dumps({"imei": imei, "error_message": error_txt})
                return json.dumps({"error": "Timeout error: Results not found"})

            if self.is_element_found(driver, By.XPATH, "//span[@class='error-red-text']"):
                error_message = driver.find_element(By.XPATH, "//span[@class='error-red-text']").text
                return json.dumps({"imei": imei, "compatible": False ,"compatibility_message": error_message})
            
            # Extract device information
            device_name = self.wait_for_element_by_xpath(driver, "//div[@class='device-name']").text
            compatibility_message = self.wait_for_element_by_xpath(driver, "//span[@class='compatibility-message full-compatible-message']").text
            device_infos = driver.find_elements(By.XPATH, "//span[contains(@class, 'device-info')]/..")
            device_info_dict = {}
            for d in device_infos:
                key, value = d.text.strip().split(":")
                device_info_dict[key.strip()] = value


            result = json.dumps({
                "imei": imei,
                "compatible": True,
                "device_name": device_name,
                "device_info": device_info_dict,
                "compatibility_message": compatibility_message
            })

            # Store result in cache
            self.cache[imei] = result

            return result
        finally:
            driver.quit()

    def is_valid_imei(self, imei):
        """
        Check if the given IMEI is valid.

        Args:
            imei (str): The IMEI to validate.

        Returns:
            bool: True if the IMEI is valid, False otherwise.
        """
        # IMEI must be a 15-digit number
        if not re.match(r'^\d{15}$', imei):
            return False
        
        # IMEI must pass the Luhn algorithm
        imei_digits = [int(digit) for digit in imei]
        checksum = sum(imei_digits[::-2]) + sum(sum(divmod(d * 2, 10)) for d in imei_digits[-2::-2])
        return checksum % 10 == 0

    async def main(self, imei):
        if not self.is_valid_imei(imei):
            return json.dumps({"error": "Invalid IMEI format"})
        
        return await self.create_driver_and_run(imei)

    def wait_for_element_by_xpath(self, driver, xpath, timeout=10):
        """
        Wait for an element to be located by XPath.

        Args:
            driver (WebDriver): The WebDriver instance.
            xpath (str): The XPath of the element to wait for.
            timeout (int): The maximum time to wait, in seconds. Default is 10 seconds.

        Returns:
            WebElement or None: The located element, or None if not found within the specified timeout.
        """
        try:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            return element
        except TimeoutException:
            return None

    def is_element_found(self, driver, by, value, timeout=10):
        """
        Check if an element is found on the page by the specified locator strategy.

        Args:
            driver (WebDriver): The WebDriver instance.
            by: The locator strategy (e.g., By.ID, By.XPATH).
            value (str): The value of the locator (e.g., ID value, XPath expression).
            timeout (int): The maximum time to wait for the element, in seconds. Default is 10 seconds.

        Returns:
            bool: True if the element is found, False otherwise.
        """
        try:
            element = driver.find_element(by, value)
            return element
        except NoSuchElementException:
            return False

    def check_for_incompatibility(self, driver, imei):
        dialog_XPATH = "//div[contains(@class, 'ui-dialog') and contains(@style, 'display: block')]"
        not_compatible_dialog_XPATH = "//h3[contains(@id, 'pdialog-headertext') and contains(text(), 'Not Compatible')]"
        if self.is_element_found(driver, By.XPATH, dialog_XPATH):
            message = self.is_element_found(driver, By.XPATH, f'{dialog_XPATH}//*[@id="pdialog-bodytext"]/div[1]/p')
            if message:
                message = message.text
                header_msg = self.is_element_found(driver, By.XPATH, not_compatible_dialog_XPATH).text
                return json.dumps({"imei": imei, "compatible": False ,"compatibility_message": message, "header_message": header_msg})
        return None

if __name__ == '__main__':
    imei = "350360630683393"
    checker = TMobileChecker()
    result = asyncio.run(checker.main(imei))
    print(result)
