import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


""" Functions for Operating Selenium & Downloading Files from Websites"""

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


if __name__ == "__main__":
    print("This code is being run directly.")