# utils/scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_job_description(url):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    # Set up the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Load the page
        driver.get(url)
        # Wait for the job description to load
        wait = WebDriverWait(driver, 10)
        job_description = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jd-info")))
        return job_description.text
    finally:
        driver.quit()
