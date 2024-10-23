# utils/email_generator.py

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
GROQ_API_KEY = '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'
llm = ChatGroq(
    model='llama-3.1-70b-versatile',
    api_key=GROQ_API_KEY,  # Pass the API key here
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

email_template = PromptTemplate.from_template("""
    ### JOB DESCRIPTION:
    {job_description}
    
    ### INSTRUCTION:
    You are Mohan, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company.
    Your job is to write a cold email regarding the job mentioned above.
    Also, add the most relevant ones from the following links to showcase AtliQ's portfolio: {link_list}
    
    ### EMAIL (NO PREAMBLE):
""")

def generate_email(job, links):
    chain = email_template | llm
    res = chain.invoke({"job_description": job, "link_list": links})
    return res.content
