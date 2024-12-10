import os
import time
import re
import json
import boto3
import pandas as pd
import logging
import gspread
import sys
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from oauth2client.service_account import ServiceAccountCredentials

""" Functions for Operating Selenium """
def get_chrome_options(download_dir):
    """ Sets the chrome drive options """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--disable-popup-blocking")
    prefs = {
        "download.default_directory": download_dir,
        # "download.prompt_for_download": False, # added for testing remove if problems
        # "download.directory_upgrade": True, # added for testing remove if problems
        "w3c": True,
        # "safebrowsing.enabled": True
        }
    chrome_options.add_experimental_option('prefs', prefs)
    return chrome_options

def enable_download_headless(browser,download_dir):
    # """ Enable and define how files ar downloaded """
     browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
     params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
     browser.execute("send_command", params)

def enable_download_headless1(browser, download_dir):
    # Enable and define how files are downloaded with file name time stamped
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # Get current timestamp
    filename = f"{timestamp}_extract.html"  # Construct filename with timestamp
    download_path = os.path.join(download_dir, filename)  # Combine download directory with filename
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)
    print(f"Downloads enabled. Files will be saved to: {download_path}")
    return filename

def enable_download_headless2(browser, download_dir):
    # Enable and define how files are downloaded
    # browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {
        'behavior': 'allow',
        'downloadPath': download_dir
    }
    browser.execute_cdp_cmd("Page.setDownloadBehavior", params)

def setup_chromedriver(download_dir):
    chrome_options = get_chrome_options(download_dir)
    driver = webdriver.Chrome(options=chrome_options)
    enable_download_headless(driver, download_dir)
    return driver

""" Functions for Logging to Google Sheets and log file """
# Configure logging
logging.basicConfig(
    filename='/home/KIPPNashvilleData/powerschool/powerschool_ada_adm.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Set up Google Sheets credentials and client
def setup_google_sheets(spreadsheet_name, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/KIPPNashvilleData/creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name).worksheet(sheet_name)
    return sheet

# Log to Google Sheets and log file
def log_message(sheet, message):
    # Log to Google Sheets
    sheet.append_row([time.strftime("%Y-%m-%d %H:%M:%S"), message])

    # Log to the local log file
    logging.info(message)


""" Function for Moving Files to AWS S3 Bucket """

def upload_to_s3(source_file, bucket_name, destination_path, access_key_id, access_secret_key):
    """ Function to move files to AWS S3 Bucket """
    s3 = boto3.resource('s3', aws_access_key_id=access_key_id, aws_secret_access_key=access_secret_key)
    s3.meta.client.upload_file(source_file, bucket_name, destination_path)

""" Functions for Data Cleaning  """
def clean_header_base(header):
    """ Clean all headers to conform to database conventions """
    clean_header = header.lower().replace(' ', '_')
    clean_header = re.sub(r'[^\w_]', '_', clean_header)
    return clean_header

def clean_header_ps(header):
    """ Clean headers for PowerSchool to remove table names and conform to database conventions """
    split_header = header.rsplit('.', 1)
    if len(split_header) > 1:
        clean_header = split_header[1]
    else:
        clean_header = split_header[0]
    clean_header = clean_header.lower().replace(' ', '_')
    return clean_header

def process_headers(headers, method):
    """ Process headers based on the cleaning method """
    if method == "none":
        return headers  # Return the original headers without cleaning
    cleaned_headers = []
    for header in headers:
        if method == "base":
            cleaned_header = clean_header_base(header)
        elif method == "ps":
            cleaned_header = clean_header_ps(header)
        cleaned_headers.append(cleaned_header)
    return cleaned_headers

def process_csv_file(config_path, csv_file, source_directory, aws_folder, cleaning_method, sheet):
    """ Process CSV files based on cleaning method """
    with open(config_path) as config_file:
        config = json.load(config_file)
        aws_config = config["awss3"]
    csv_file_path = os.path.join(source_directory, csv_file)
    access_key_id = aws_config["access_key_id"]
    access_secret_key = aws_config["access_secret_key"]
    s3_bucket_name = aws_config["bucket_name"]

    # Check if the file was updated in the last 12 hours
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(csv_file_path))
    if datetime.now() - file_mod_time > timedelta(hours=12):
        message = f"{csv_file} was not updated in the last 12 hours. Skipping."
        logging.info(message)
        log_message(sheet, f"WARNING: {message}")
        print(message)
        return

    # Read headers from CSV file with the specified encoding
    try:
        df = pd.read_csv(csv_file_path, low_memory=False, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file_path, low_memory=False, encoding='latin-1')

    # Process headers only if cleaning method is not "none"
    if cleaning_method != "none":
        df.columns = process_headers(df.columns, cleaning_method)

    # Upload the CSV file to AWS S3
    aws_path = aws_folder + '/' + csv_file
    df.to_csv(csv_file_path, index=False)  # Write cleaned headers back to the CSV file (or original if "none")
    upload_to_s3(csv_file_path, s3_bucket_name, aws_path, access_key_id, access_secret_key)
    message = f"{csv_file} moved to S3: {aws_folder}"
    logging.info(message)
    log_message(sheet, f"INFO: {message}")
    print(message)

"""Functions for Navigating Infinite Campus"""
# Maintaining the functions needed navigate Infinite Campus
"""
 - If the any IC report scraping file encounters errors on the iframe functions, the frame names may have changed in Infinite Campus.
 - At which time iframe_names will need to be updated in both iframe functions.
 - To determine the location of th iframe for each function:
    - run a report from the DataView in Infinite Campus
    - use the inspect tool to find the target frame for the report list and the settings
    - run the script called [TODO: ADD name of script with function:]
 - TODO finish instructions for running the iframe FILE * FUNCTIONS and getting frame name
 - insert new frame names into list for variable "iframe_names"
"""

def go_to_reports(driver):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_name}")
        except:
            print(f"Timeout: {iframe_name} iframe not found")

def go_to_reports_id(driver):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_ids = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_id in iframe_ids:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_id)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_id}")
        except:
            print(f"Timeout: {iframe_id} iframe not found")


def go_to_settings(driver):
    """ Move the browser to the iframe with the report settings. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe: {iframe_name}")
        except TimeoutException:
            print(f"Timeout: {iframe_name} iframe not found")


def traverse_iframes_by_index(driver):
    """ Use to find the names of the iframes in the infinite campus site page """
    def print_iframe_details(index, iframe_name):
        print(f"Switched to iframe with index {index}: {iframe_name}")

    def traverse_iframes_recursive(driver, iframes, index=0):
        if index < len(iframes):
            iframe_element = iframes[index]
            driver.switch_to.frame(iframe_element)
            iframe_name = driver.execute_script("return window.name;")
            print_iframe_details(index, iframe_name)
            nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            traverse_iframes_recursive(driver, nested_iframes)
            driver.switch_to.parent_frame()
            traverse_iframes_recursive(driver, iframes, index+1)

if __name__ == "__main__":
    print("This code is being run directly.")