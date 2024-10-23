# tils/persistent_store.py

# Import and configure pysqlite3 before any other imports
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    print("pysqlite3 not found, attempting to install it...")
    import subprocess
    subprocess.check_call(["pip", "install", "pysqlite3-binary"])
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import uuid
import chromadb

class PortfolioStore:
    def __init__(self, path="vectorstore"):
        """Initialize the persistent ChromaDB client."""
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name="portfolio")

    def add_portfolio_to_collection(self, df):
        """Adds CSV data to the ChromaDB collection."""
        if not self.collection.count():
            documents = []
            metadatas = []
            ids = []
            
            for _, row in df.iterrows():
                documents.append(row["Techstack"])
                metadatas.append({"links": row["Links"]})
                ids.append(str(uuid.uuid4()))
            
            # Batch add items to collection
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

    def query_portfolio(self, skills, n_results=2):
        """Queries the portfolio using the given skills."""
        try:
            results = self.collection.query(
                query_texts=skills,
                n_results=n_results
            )
            return results.get('metadatas', [])
        except Exception as e:
            print(f"Error querying portfolio: {str(e)}")
            return []

# Create a default instance
portfolio_store = PortfolioStore()

# Export the methods for backward compatibility
add_portfolio_to_collection = portfolio_store.add_portfolio_to_collection
query_portfolio = portfolio_store.query_portfolio