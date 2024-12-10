import time
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials



""" Functions for Logging to Google Sheets and log file """
# Configure logging
def setup_logging(filename):
    logging.basicConfig(
        filename=filename,
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

if __name__ == "__main__":
    print("This code is being run directly.")