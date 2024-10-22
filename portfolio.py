import chromadb
import uuid
import sys

import pandas as pd
import pysqlite3
__import__('pysqlite3')
#www

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
class Portfolio:
    def __init__(self, data):
        self.data = data  # Expecting a DataFrame from the uploaded CSV
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def load_portfolio(self):
        if not self.collection.count():
            for _, row in self.data.iterrows():
                self.collection.add(documents=row["Techstack"],
                                    metadatas={"links": row["Links"]},
                                    ids=[str(uuid.uuid4())])

    def query_links(self, skills):
        return self.collection.query(query_texts=skills, n_results=2).get('metadatas', [])
