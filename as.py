import streamlit as st
import pandas as pd
import uuid
import chromadb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler('app.log')  # Save to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables...")
dotenv.load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if GROQ_API_KEY:
    logger.info("GROQ API key loaded successfully")
else:
    logger.error("Failed to load GROQ API key")

# Initialize LLM
logger.info("Initializing LLM...")
llm = ChatGroq(
    model='llama-3.1-70b-versatile',
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def scrape_job_website(url):
    logger.info(f"Starting web scraping for URL: {url}")
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")

        logger.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        logger.info("Successfully loaded webpage")

        # Function to scroll and load content
        def scroll_to_load_all_content():
            logger.info("Starting page scroll to load dynamic content...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                scroll_count += 1
                logger.debug(f"Scroll iteration {scroll_count}")
                if new_height == last_height:
                    break
                last_height = new_height
            logger.info(f"Completed scrolling after {scroll_count} iterations")

        scroll_to_load_all_content()
        page_text = driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"Successfully extracted page text ({len(page_text)} characters)")
        driver.quit()
        return page_text
    except Exception as e:
        logger.error(f"Error during web scraping: {str(e)}")
        raise

def analyze_job_content(page_content):
    logger.info("Starting job content analysis...")
    try:
        prompt_extract = PromptTemplate.from_template(
            """
            ## SCRAPED TEXT FROM WEBSITE ##
            {page_content}

            ##INSTRUCTION## 
            The scraped text is from the career page of a website
            Your job is to extract the job postings and return them in JSON format also based on the posting sagrigate it this 
            following keys : 'role', 'experience', 'skills' and 'description'
            only return the valid JSON.
            ## VALID JSON (NO PREAMBLE):
            """
        )
        
        logger.info("Sending content to LLM for analysis...")
        chain = prompt_extract | llm
        res = chain.invoke(input={'page_content': page_content})
        logger.info("Successfully received LLM response")
        
        logger.info("Parsing JSON response...")
        json_parser = JsonOutputParser()
        parsed_result = json_parser.parse(res.content)
        if isinstance(parsed_result, list) and len(parsed_result) > 0:
            logger.info("Extracted first job from list response")
            parsed_result = parsed_result[0]
        elif isinstance(parsed_result, dict) and "jobs" in parsed_result:
            logger.info("Extracted first job from jobs array")
            parsed_result = parsed_result["jobs"][0]
            
        logger.info("Successfully parsed JSON response")
        return parsed_result
   
    except Exception as e:
        logger.error(f"Error during job content analysis: {str(e)}")
        raise

def generate_email(job_data, portfolio_links, user_info):
    logger.info("Starting email generation...")
    try:
        prompt_email = PromptTemplate.from_template(
            """
            ### USER INFO:
            Name: {name}
            Company: {company}
            Email: {email}
            Phone: {phone}

            ### JOB DESCRIPTION:
            {job_description}
            
            ### INSTRUCTION:
            You are {name}, a business development executive at {company}. {company} is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. 
            Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
            process optimization, cost reduction, and heightened overall efficiency. 
            Your job is to write a cold email to the client regarding the job mentioned above describing the capability of {company} 
            in fulfilling their needs.
            Also add the most relevant ones from the following links to showcase {company}'s portfolio: {link_list}
            Remember you are {name} at {company}. 
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):
            """
        )
        
        logger.info("Sending data to LLM for email generation...")
        chain_email = prompt_email | llm
        res = chain_email.invoke({
            "name": user_info["name"],
            "company": user_info["company"],
            "email": user_info["email"],
            "phone": user_info["phone"],
            "job_description": str(job_data),
            "link_list": portfolio_links
        })
        logger.info("Successfully generated email")
        return res.content
    except Exception as e:
        logger.error(f"Error during email generation: {str(e)}")
        raise

def main():
    logger.info("Starting Streamlit application...")
    st.title("Job Application Email Generator")
    
    # User Information Section
    st.header("User Information")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
        email = st.text_input("Email")
    with col2:
        company = st.text_input("Company Name")
        phone = st.text_input("Phone Number")
    
    # Portfolio Upload Section
    st.header("Portfolio Upload")
    uploaded_file = st.file_uploader("Upload your portfolio CSV", type="csv")
    if uploaded_file:
        logger.info("Processing uploaded portfolio CSV...")
        try:
            df = pd.read_csv(uploaded_file)
            st.success("Portfolio CSV uploaded successfully!")
            logger.info(f"Successfully loaded portfolio CSV with {len(df)} rows")
            
            # Initialize ChromaDB
            logger.info("Initializing ChromaDB...")
            client = chromadb.PersistentClient('vectorstore')
            collection = client.get_or_create_collection(name="portfolio")
            
            # Add portfolio items to ChromaDB
            if not collection.count():
                logger.info("Adding portfolio items to ChromaDB...")
                for _, row in df.iterrows():
                    collection.add(
                        documents=row["Techstack"],
                        metadatas={"links": row["Links"]},
                        ids=[str(uuid.uuid4())]
                    )
                logger.info("Successfully added portfolio items to ChromaDB")
        except Exception as e:
            logger.error(f"Error processing portfolio CSV: {str(e)}")
            st.error("Error processing portfolio CSV")
    
    # Job URL Section
    st.header("Job Details")
    job_url = st.text_input("Enter Job Website URL")
    
    if st.button("Generate Email") and job_url and uploaded_file:
        logger.info("Starting email generation process...")
        with st.spinner("Analyzing job posting..."):
            try:
                # Scrape and analyze job content
                page_content = scrape_job_website(job_url)
                job_data = analyze_job_content(page_content)
                print(job_data)
                # Query portfolio links
                logger.info("Querying portfolio links...")
                portfolio_links = collection.query(
                    query_texts=job_data['skills'],
                    n_results=2
                ).get('metadatas', [])
                logger.info(f"Found {len(portfolio_links)} matching portfolio links")
                
                # Generate email
                user_info = {
                    "name": name,
                    "company": company,
                    "email": email,
                    "phone": phone
                }
                
                email_content = generate_email(job_data, portfolio_links, user_info)
                
                # Display results
                st.subheader("Job Analysis")
                st.json(job_data)
                
                st.subheader("Generated Email")
                st.write(email_content)
                
                # Add copy button for email
                if st.button("Copy Email to Clipboard"):
                    st.write("Email copied to clipboard!")
                
                logger.info("Successfully completed email generation process")
                
            except Exception as e:
                logger.error(f"Error in email generation process: {str(e)}")
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()