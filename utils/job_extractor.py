import json
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import re

GROQ_API_KEY = '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'

def create_llm():
    """Create and configure the LLM instance."""
    return ChatGroq(
        model='llama-3.1-70b-versatile',
        api_key=GROQ_API_KEY,
        temperature=1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

def clean_json_response(response):
    """Clean the LLM response to extract valid JSON."""
    # Remove code block markers if present
    response = re.sub(r'```(?:json)?\n?(.*?)```', r'\1', response, flags=re.DOTALL)
    
    # Remove any leading/trailing whitespace
    response = response.strip()
    
    # Try to find JSON-like content within the response
    json_match = re.search(r'(\{.*\})', response, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    return response

def validate_job_details(job_details):
    """Validate that the job details contain required fields."""
    required_fields = ['role', 'experience', 'skills', 'description']
    missing_fields = [field for field in required_fields if field not in job_details]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return job_details

prompt_extract = PromptTemplate.from_template("""
    ## SCRAPED TEXT FROM WEBSITE ##
    {page_content}

    ## INSTRUCTION ##
    The scraped text is from the career page of a website.
    Your job is to extract the job posting details and return them in JSON format with the following keys:
    'role', 'experience', 'skills', and 'description'.
    
    The response must be a valid JSON object with these exact keys.
    Do not include any additional text, markdown formatting, or code block markers.
    
    ## JSON OUTPUT:
""")

def extract_job_details(scraped_text):
    """
    Extracts job details using the LLM and returns the JSON data.
    
    Args:
        scraped_text (str): The scraped text from the job posting
        
    Returns:
        dict: Extracted job details
        
    Raises:
        ValueError: If the LLM response is invalid or missing required fields
    """
    try:
        # Create LLM chain
        llm = create_llm()
        chain = prompt_extract | llm
        
        # Get LLM response
        result = chain.invoke(input={"page_content": scraped_text})
        response = result.content
        
        # Log the raw response for debugging
        print(f"Raw LLM Response:\n{response}")
        
        # Check for empty response
        if not response:
            raise ValueError("LLM returned an empty response")
        
        # Clean and parse the response
        cleaned_response = clean_json_response(response)
        print(f"Cleaned Response:\n{cleaned_response}")
        
        # Parse JSON
        job_details = json.loads(cleaned_response)
        
        # Validate the job details
        validated_details = validate_job_details(job_details)
        
        return validated_details
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}\nResponse: {response}")
    except Exception as e:
        raise ValueError(f"Error extracting job details: {str(e)}")