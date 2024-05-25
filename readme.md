T-Mobile Compatibility Checker API
This project provides an API endpoint for checking the compatibility of a device with T-Mobile's network. It utilizes Selenium to automate the process of entering an IMEI (International Mobile Equipment Identity) number and retrieving compatibility information from T-Mobile's website.

Prerequisites
Before running the API, make sure you have the following dependencies installed:

Python 3.x
Selenium
Quart
You can install the dependencies via pip:
pip install selenium quart

Additionally, you need to have Google Chrome installed on your system as the Selenium WebDriver uses ChromeDriver.

Usage
Running the API
Clone or download this repository to your local machine.
Navigate to the project directory.
Run the following command to start the API server:

python app.py

By default, the API will run on http://127.0.0.1:5000/.

Checking Compatibility
To check the compatibility of a device, send a GET request to the /check endpoint with the IMEI number as a query parameter.

Example:

GET /check?imei=356460908981117
Replace 356460908981117 with the IMEI number of the device you want to check.

Response Format
The API returns JSON responses with the following format:

{
  "imei": "356460908981117",
  "compatible": true,
  "device_name": "Samsung Galaxy S20",
  "compatibility_message": "Your device is compatible with T-Mobile's network."
}

If the provided IMEI is invalid or missing, an error message is returned:

{
  "error": "Invalid IMEI format"
}

Notes:
This API utilizes headless Chrome for web scraping. Ensure that you have Chrome installed on your system.
The API endpoint may take some time to respond, as it involves web scraping operations.
IMEI validation is performed to ensure the provided IMEI is in the correct format before making the compatibility check.

Feel free to explore and customize the code according to your requirements!