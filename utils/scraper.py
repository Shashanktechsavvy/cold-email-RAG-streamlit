# utils/scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import streamlit as st

class StreamlitWebScraper:
    def __init__(self):
        """Initialize the scraper with Streamlit-compatible configuration."""
        self.setup_chrome_options()

    def setup_chrome_options(self):
        """Configure Chrome options for Streamlit environment."""
        self.chrome_options = Options()
        
        # Essential options for running in Streamlit
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Additional options for stability
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Set window size to ensure consistent rendering
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Additional performance options
        self.chrome_options.add_argument("--disable-software-rasterizer")
        self.chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    @st.cache_resource
    def get_driver(_self):
        """
        Create and cache the WebDriver instance.
        Using Streamlit's cache to avoid creating multiple instances.
        """
        try:
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            driver = webdriver.Chrome(
                service=service,
                options=_self.chrome_options
            )
            return driver
        except Exception as e:
            st.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def scrape_job_description(self, url):
        """
        Scrape job description from the given URL.
        
        Args:
            url (str): The URL of the job posting
            
        Returns:
            str: The scraped job description
        """
        try:
            driver = self.get_driver()
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            # Load the page
            driver.get(url)
            
            # Common selectors for job descriptions
            selectors = [
                "div.jd-info",
                "div.job-description",
                "div[class*='description']",
                "div[class*='job']",
                "article",
                "main",
                "#job-details",
                "[data-testid='job-description']"
            ]
            
            # Try different selectors with wait
            wait = WebDriverWait(driver, 10)
            description_text = None
            
            for selector in selectors:
                try:
                    element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    description_text = element.text
                    if description_text and len(description_text) > 100:  # Ensure we got meaningful content
                        break
                except:
                    continue
            
            if not description_text:
                # Fallback to body text if no specific selector worked
                description_text = driver.find_element(By.TAG_NAME, "body").text
            
            return description_text.strip()
            
        except Exception as e:
            st.error(f"Error scraping job description: {str(e)}")
            raise
            
        finally:
            # Don't quit the driver as it's cached by Streamlit
            pass

# Create singleton instance
scraper = StreamlitWebScraper()

# Function for backward compatibility
def scrape_job_description(url):
    return scraper.scrape_job_description(url)