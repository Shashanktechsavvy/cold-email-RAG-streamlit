import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from chains import Chain
from portfolio import Portfolio
from utils import clean_text

def scrape_job_description(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        job_description = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return job_description.text
    finally:
        driver.quit()

def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Cold Mail Generator")
    url_input = st.text_input("Enter a URL:", value="https://careers.mastercard.com/us/en/job/R-230382/Senior-Software-Engineer")
    submit_button = st.button("Submit")

    if submit_button:
        try:
            with st.spinner("Scraping job description..."):
                data = scrape_job_description(url_input)
            data = clean_text(data)
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)
            for job in jobs:
                skills = job.get('skills', [])
                links = portfolio.query_links(skills)
                email = llm.write_mail(job, links)
                st.code(email, language='markdown')
        except Exception as e:
            st.error(f"An Error Occurred: {e}")

if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)