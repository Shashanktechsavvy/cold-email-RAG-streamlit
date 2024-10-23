# utils/persistent_store.py

import uuid
import chromadb

# Initialize persistent ChromaDB client
client = chromadb.PersistentClient(path="vectorstore")
collection = client.get_or_create_collection(name="portfolio")

def add_portfolio_to_collection(df):
    """Adds CSV data to the ChromaDB collection."""
    if not collection.count():
        for _, row in df.iterrows():
            collection.add(
                documents=row["Techstack"],
                metadatas={"links": row["Links"]},
                ids=[str(uuid.uuid4())]
            )

def query_portfolio(skills):
    """Queries the portfolio using the given skills."""
    return collection.query(query_texts=skills, n_results=2).get('metadatas', [])
