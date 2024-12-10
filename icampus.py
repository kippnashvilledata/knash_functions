import os
import glob
import time
import pandas as pd
# import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException
from kipp import log_message
""" These functions will work only while connected to the Infinite Campus website in conjuction with the webnav.py Selenium functions."""

"""Functions for Navigating Infinite Campus"""
def login_to_icampus(driver, username, password, sheet):
    """
    Log in to Infinite Campus using the provided credentials.
    """
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
        time.sleep(10)
        driver.find_element(By.ID, "signinbtn").click()
        time.sleep(15)

        if driver.title != "Infinite Campus":
            raise Exception("ERROR: Login failed - Site title does not match 'Infinite Campus'")
            log_message(sheet, "ERROR: Login failed - Site title does not match 'Infinite Campus'")
        return True
    except Exception as e:
        log_message(sheet, f"ERROR: Unable to log in to IC: {e}")
        return False

def go_to_reports(driver, sheet):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            log_message(sheet, f"INFO: Switched to iframe: {iframe_name}")
        except:
            log_message(sheet, f"ERROR: Timeout: {iframe_name} iframe not found")  

def go_to_reports_id(driver, sheet):
    """ Move to the browser to the reports iframe. """
    driver.switch_to.default_content()
    iframe_ids = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"] #"frameWorkspace", 
    #iframe_names = ["frameWorkspaceWrapper", "frameWorkspaceDetail", "reportList"]
    for iframe_id in iframe_ids:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_id)))
            driver.switch_to.frame(iframe)
            # print(f"Switched to iframe: {iframe_id}")
            log_message(sheet, f"INFO: Switched to iframe: {iframe_id}")
        except:
            print(f"Timeout: {iframe_id} iframe not found")
            log_message(sheet, f"ERROR: Timeout - {iframe_id} iframe not found")
            
            
def go_to_settings(driver, sheet):
    """ Move the browser to the iframe with the report settings. """
    driver.switch_to.default_content()
    iframe_names = ["frameWorkspace", "frameWorkspaceWrapper", "frameWorkspaceDetail"]
    for iframe_name in iframe_names:
        try:
            # Wait for the iframe to be present before switching to it
            iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, iframe_name)))
            driver.switch_to.frame(iframe)
            log_message(sheet, f"INFO: Switched to iframe: {iframe_name}") 
        except TimeoutException:
            log_message(sheet, f"ERROR: Timeout: {iframe_name} iframe not found")

# Function to process downloaded report
def process_download(download_dir, base_file_name, sheet):
    try:
        html_files = glob.glob(os.path.join(download_dir, 'extract.html'))
        if html_files:
            most_recent_html = html_files[0]
            with open(most_recent_html, 'r') as file:
                html_content = file.read()
                num_records = html_content.count('<tr>')
                if num_records > 2:  # Check if there are more than 2 records
                    os.rename(most_recent_html, os.path.join(download_dir, f"{base_file_name}.html"))
                    log_message(sheet, f"INFO: Renamed extract.html to '{base_file_name}.html'")
                    df = pd.read_html(os.path.join(download_dir, f"{base_file_name}.html"), header=1)[0]
                    df = df[df.iloc[:, 0] != "All Records"]
                    cleaned_csv_path = os.path.join(download_dir, f"{base_file_name}.csv")
                    df.to_csv(cleaned_csv_path, index=False)
                    log_message(sheet, f"INFO: Updated file saved to '{cleaned_csv_path}'")
                    return True
                else:
                    os.remove(most_recent_html)
                    log_message(sheet, f"INFO: Deleted '{most_recent_html}' as it has 2 or fewer records.")
                    return False
        else:
            log_message(sheet, "WARNING: No 'extract.html' file found in the directory.")
            return False
    except Exception as e:
        log_message(sheet, f"ERROR: Unable to process a download for {base_file_name}: {e}")
        return False

def generate_report(driver, report_xpath, download_dir, base_file_name, sheet):
    try:
        report = driver.find_element(By.XPATH, report_xpath)
        report.click()
        log_message(sheet, f"INFO: Report clicked for {base_file_name}")

        # Set report options
        go_to_settings(driver, sheet)
        format_drop = driver.find_element(By.ID, "mode")
        htmlop = Select(format_drop)
        htmlop.select_by_value("html")
        school_list = driver.find_element(By.ID, "calendarID")
        select = Select(school_list)
        school_options = ["4163", "4164", "4165", "4166", "4166"]
        for value in school_options:
            select.select_by_value(value)
        log_message(sheet, f"INFO: Options set for {base_file_name}")

        # Generate report
        generate_button = driver.find_element(By.ID, "next")
        generate_button.click()
        log_message(sheet, f"INFO: Generate report button clicked for {base_file_name}.")

        # Wait for report to download
        time.sleep(60)
        return process_download(download_dir, base_file_name, sheet)

    except Exception as e:
        log_message(sheet, f"ERROR: Unable to generate report for {base_file_name}: {e}")
        return False

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

def traverse_iframes_by_index(driver):
    """ Use to find the names of the iframes in the infinite campus site page """
    def print_iframe_details(index, iframe_name):
        print(f"INFO: Switched to iframe: {iframe_name}")

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
    # log_message(sheet, "INFO: Running the script directly.")