from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import timedelta

def scrape_weather_data_from_page(base_url, date):
    # Initialize the web driver (make sure to have the appropriate driver installed, e.g., chromedriver)
    driver = webdriver.Chrome()
    
    # Open the base URL
    driver.get(base_url)
    
    # Convert date to the format expected by the dropdown
    day = date.strftime('%d').lstrip('0')  # Remove leading zero
    month = date.strftime('%B')
    year = date.strftime('%Y')
    
    # Select the specific day from the dropdown
    try:
        day_dropdown = Select(driver.find_element(By.ID, 'wt-his-select'))
        day_dropdown.select_by_visible_text(f"{day} {month} {year}")
    except Exception as e:
        print(f"Error selecting date from dropdown: {e}")
        driver.quit()
        return
    
    # Wait for the page to load the new data
    time.sleep(3)
    
    # Fetch the HTML content of the page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the table by its ID
    table = soup.find('table', {'id': 'wt-his'})

    if not table:
        print(f"No data found for the specified date: {date.strftime('%d-%m-%Y')}")
        driver.quit()
        return

    # Initialize a list to store the data
    data = []

    # Iterate over each row in the table body (skipping the header)
    for i, row in enumerate(table.find('tbody').find_all('tr')):
        # Extract data from each column
        time_ = row.find('th').text.strip()
        
        # Reformat time to 'HH:MM' and remove day and date
        time_ = time_.split(' ')[0]  # Split by space and take the first part, which is 'HH:MM'
        
        # Ensure the first time entry is '00:00'
        if i == 0:
            time_ = '00:00'
        
        temp = row.find_all('td')[1].text.strip()
        humidity = row.find_all('td')[5].text.strip()  # Corrected column for humidity
        
        # Append the data as a tuple to the list
        data.append((time_, temp, humidity))

    # Create a DataFrame
    df = pd.DataFrame(data, columns=['Time', 'Temperature', 'Humidity'])

    # Convert date to DDMMYYYY format for the filename
    date_ddmmyyyy = date.strftime('%d%m%Y')
    filename = f'hourly_weather_data_{date_ddmmyyyy}.csv'
    
    # Save the DataFrame to a CSV file
    df.to_csv(filename, index=False)

    print(f"Scraping completed and data saved to '{filename}'.")

    # Quit the driver
    driver.quit()

# Base URL of the manually set page
base_url = 'https://www.timeanddate.com/weather/singapore/singapore/historic?month=4&year=2023'

# Prompt the user to enter the starting and ending dates manually in DDMMYYYY format
start_date_input = input("Enter the start date (DDMMYYYY): ")
end_date_input = input("Enter the end date (DDMMYYYY): ")

# Convert the input dates to a proper format
try:
    start_date = pd.to_datetime(start_date_input, format='%d%m%Y')
    end_date = pd.to_datetime(end_date_input, format='%d%m%Y')
except ValueError:
    print("Invalid date format. Please enter the dates in DDMMYYYY format.")
    exit()

# Loop through the date range and scrape data for each day
current_date = start_date
while current_date <= end_date:
    scrape_weather_data_from_page(base_url, current_date)
    current_date += timedelta(days=1)
