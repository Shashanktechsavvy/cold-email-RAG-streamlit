# app.py

import streamlit as st
import pandas as pd

from utils.scraper import scrape_job_description
from utils.job_extractor import extract_job_details
from utils.persistent_store import add_portfolio_to_collection, query_portfolio
from utils.email_generator import generate_email

st.title("Job Scraper & Cold Email Generator")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("Upload CSV for portfolio", type=["csv"])

# Step 2: Input URL for job posting
job_url = st.text_input("Enter the job posting URL")

if uploaded_file and job_url:
    # Step 3: Read and display the uploaded CSV
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded CSV data:")
    st.dataframe(df)

    # Step 4: Scrape job description from the provided URL
    if st.button("Process URL and Generate Email"):
        with st.spinner('Scraping job description...'):
            scraped_text = scrape_job_description(job_url)
            st.write("Scraped Job Description:")
            st.text(scraped_text)

            # Step 5: Extract job details using LLM
            try:
                with st.spinner('Extracting job details...'):
                    job_details = extract_job_details(scraped_text)
                    st.write("Extracted Job Details (JSON):")
                    st.json(job_details)  # Display extracted JSON

                    # Step 6: Add portfolio to ChromaDB and query based on job skills
                    add_portfolio_to_collection(df)
                    job_skills = job_details['skills']  # Extract skills from job details
                    links = query_portfolio(job_skills)

                    # Step 7: Generate email based on job description and portfolio links
                    with st.spinner('Generating email...'):
                        email = generate_email(job_details, links)
                        st.write("Generated Cold Email:")
                        st.code(email)
            except ValueError as e:
                st.error(f"Error extracting job details: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
