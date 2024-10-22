import sys
import pysqlite3 as sqlite3

import pandas as pd
import pysqlite3
__import__('pysqlite3')
#www

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import traceback  # <-- Import traceback for error logging

from chains import Chain
from portfolio import Portfolio
from utils import clean_text

def scrape_job_description(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

     # Set the binary location for Chromium (on Linux servers this is the typical location)
    chrome_options.binary_location = "/usr/bin/google-chrome"

    # Initialize the driver using the ChromeDriver for Chromium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        job_description = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return job_description.text
    finally:
        driver.quit()

def create_streamlit_app(llm, clean_text):
    st.title("📧 Cold Mail Generator")

    # Step 1: File uploader for CSV
    uploaded_file = st.file_uploader("Upload a portfolio CSV file", type=["csv"])
    if uploaded_file is not None:
        # Step 2: Load the CSV file into a DataFrame and initialize Portfolio
        if "portfolio" not in st.session_state:
            data = pd.read_csv(uploaded_file)
            st.session_state["portfolio"] = Portfolio(data)  # Initialize portfolio once

        portfolio = st.session_state["portfolio"]
        st.success("Portfolio loaded successfully!")

        # Step 3: Allow multiple URL inputs once the file is uploaded
        url_input = st.text_input("Enter a URL to scrape job description:")
        submit_button = st.button("Submit")

        if submit_button and url_input:
            try:
                with st.spinner("Scraping job description..."):
                    data = scrape_job_description(url_input)
                data = clean_text(data)

                # Ensure previous results are cleared
                if "jobs" in st.session_state:
                    del st.session_state["jobs"]

                # Load the portfolio and extract jobs
                portfolio.load_portfolio()
                jobs = llm.extract_jobs(data)
                st.session_state["jobs"] = jobs  # Save the jobs to session state

                for job in jobs:
                    skills = job.get('skills', [])
                    links = portfolio.query_links(skills)
                    email = llm.write_mail(job, links)
                    st.code(email, language='markdown')

            except Exception as e:
                # Log the full stack trace to the terminal
                traceback.print_exc()  # <-- Add this line to log full error to the terminal
                st.error(f"An error occurred: {e}")
    else:
        st.info("Please upload a CSV file to proceed.")

if __name__ == "__main__":
    chain = Chain()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, clean_text)
