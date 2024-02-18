import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException, TimeoutException, StaleElementReferenceException
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import pygame

# Start a timer
start_time = time.time()

# Initialize BrightData scraping browser & launch session
SBR_WEBDRIVER = 'USER:PASS@brd.superproxy.io:9515'  

def main():
    print('Connecting to Scraping Browser...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating to site...')
        driver.get('https://www.therealestatesitetoscrape.com/')
        print('Navigated!')

if __name__ == '__main__':
    main()

def check_and_handle_captcha(driver):
    # Checks for the presence of a captcha and alerts user to intervene manually.
    # Returns True if the page is clear of captcha or if it's successfully handled.
    # Keeps trying indefinitely until captcha is no longer detected.

    while True:
        try:
            captcha_present = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#px-captcha'))
            )
            print("Captcha detected. Please intervene...")

            pygame.init()
            pygame.mixer.init()
            suffer = pygame.mixer.Sound("you_suffer.wav") # it's the track you're thinking of.
            suffer.play()
            time.sleep(suffer.get_length())
            pygame.quit()

            time.sleep(20)

            # Recheck if captcha is still present after handling attempt
            if not driver.find_elements(By.CSS_SELECTOR, '#px-captcha'):
                print("Captcha handled successfully.")
                return True
        
        except ElementNotVisibleException:
            print("Encountered an element non-visible reference, retrying...")
            return True
        except TimeoutException:
            print("Encountered a timeout reference, retrying...")
            return True
        except StaleElementReferenceException:
            print("Encountered a stale element reference, retrying...")
            return True

def scrape_agent_data(driver, agentData):
# Scrapes agent data from the page and appends it to the dataframe  

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    agents = soup.find_all('tr')

    for agent in agents[:10]:
        name_tag = agent.select_one('a.dcAMHg') # your selectors here
        number_tag = agent.select_one('.bwCmyj') # your selector here
        brokerage_tag = agent.select_one('.hlQXKE') # your selector here
        
        name = name_tag.get_text(strip=True) if name_tag else 'N/A'
        number = number_tag.get_text(strip=True) if number_tag else 'N/A'
        brokerage = brokerage_tag.get_text(strip=True) if brokerage_tag else 'N/A'
        
        # Create a DataFrame from the new row data
        new_row = pd.DataFrame([{'Name': name, 'Number': number, 'Brokerage': brokerage}])
        
        # Use pandas.concat to add the new row to agentData
        agentData = pd.concat([agentData, new_row], ignore_index=True)
    
    return agentData


# Initialize WebDriver with undetected_chromedriver & unnecessary web features for faster non-headless page loading
options = uc.ChromeOptions()
options.headless = False
options.add_argument("--window-size=800,600")
options.add_argument("--disable-gpu")
options.add_argument("--disable-images") 
options.add_argument("--blink-settings=imagesEnabled=false") 
options.add_argument("--autoplay-policy=no-user-gesture-required") 
options.add_argument("--disable-extensions")
driver = uc.Chrome(options=options)

# DataFrame to store scraped data & read zips.csv file & define csv file lookup
agentData = pd.DataFrame(columns=['Name', 'Number', 'Brokerage'])
columns = ['Name', 'Number', 'Brokerage']
zips = pd.read_csv('zips.csv', dtype={'zips': str})
file_exists = os.path.isfile('agentData.csv')

# Main scraping loop
for index, row in zips.iterrows():
    z = str(row['zips'])
    page_number = 1
    while True:
        if page_number == 26:  # Check if page_number has reached max pages (25) & break
            print("Reached page limit for zip code: ", z)
            break 
        
        driver.get(f'https://www.therealestatesitetoscrape.com/{z}/page={page_number}')
        time.sleep(2)

        if check_and_handle_captcha(driver):
            try:
                agentData = scrape_agent_data(driver, agentData)
                page_number += 1
            except (NoSuchElementException, TimeoutException):
                print(f"Finished scraping data for zip code {z}.")
                break 

    # Append data to CSV file after completing scraping for each zip code
    if not agentData.empty:
        if not file_exists:  # Write header only if file doesn't exist
            agentData.to_csv('agentData.csv', mode='a', index=False, header=True)
            file_exists = True  # Ensure header is not written again
        else:
            agentData.to_csv('agentData.csv', mode='a', index=False, header=False)

        # Clear DataFrame to free up memory
        agentData = pd.DataFrame(columns=columns)

# End timer
end_time = time.time()
print(f"Scraping completed in {end_time - start_time} seconds.")

driver.execute_script("window.localStorage.clear();")
driver.execute_script("window.sessionStorage.clear();")
driver.quit()
