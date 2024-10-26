import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import dotenv
import os


dotenv.load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
print(GROQ_API_KEY)
# Initialize language model
llm = ChatGroq(
    model='llama-3.1-70b-versatile',
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Streamlit UI
st.title("CSV Upload and LLM Processing")

# Step 1: Upload CSV File
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("CSV Data Preview:")
    st.write(df)

# Step 2: Input URL for Web Scraping
url = st.text_input("Enter a URL to scrape job details")

if st.button("Process URL") and url:
    # Set up Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Load the webpage
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    try:
        job_description = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jd-info"))).text
        driver.quit()

        # Define prompt to extract structured job information
        prompt_extract = PromptTemplate.from_template(
            """
            ## SCRAPED TEXT FROM WEBSITE ##
            {page_content}

            ##INSTRUCTION## 
            The scraped text is from the career page of a website.
            Your job is to extract the job postings and return them in JSON format with these keys: 
            'role', 'experience', 'skills', and 'description'.
            only return the valid JSON.
            ## VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | llm
        extracted_job = chain_extract.invoke(input={'page_content': job_description}).content

        # Parse JSON
        json_parser = JsonOutputParser()
        job = json_parser.parse(extracted_job)
        st.write("Extracted Job Details:", job)

        # Convert CSV data to a string format for inclusion in the prompt
        csv_content = df.to_dict(orient="records")

        # Create cold email prompt
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}
            
            ### INSTRUCTION:
            You are Mohan, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. 
            Your job is to write a cold email to the client describing AtliQ's capability to fulfill their needs.
            Use the following portfolio information for relevant examples: {csv_content}
            Remember you are Mohan, BDE at AtliQ. 
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):
            """
        )

        chain_email = prompt_email | llm
        email_response = chain_email.invoke({
            "job_description": str(job),
            "csv_content": csv_content
        })
        st.write("Generated Email:", email_response.content)

    except Exception as e:
        st.write("Error fetching job description:", str(e))
