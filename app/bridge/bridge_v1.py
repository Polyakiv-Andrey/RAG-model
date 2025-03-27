
import base64
import json
import os
import time
from typing import List, Dict, Optional

import requests
import tiktoken
from dotenv import load_dotenv
import openai
import faiss
import pickle
from sentence_transformers import SentenceTransformer

load_dotenv()


class AzureConnector:
    """
    Connector for Azure OpenAI integration.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        app_key: Optional[str] = None,
    ) -> None:
        self.client_id = client_id if client_id else os.getenv("CISCO_CLIENT_ID")
        self.client_secret = client_secret if client_secret else os.getenv("CISCO_CLIENT_SECRET")
        self.azure_endpoint = "https://chat-ai.cisco.com"
        self.api_version = "2024-12-01-preview"
        self.app_key = app_key if app_key else os.getenv("CISCO_APP_KEY")

        if not all([self.client_id, self.client_secret, self.app_key]):
            raise ValueError("Missing credentials. Provide them as parameters or environment variables.")

        self.access_token = self._get_access_token()
        self._configure_openai_client()
        self.context = ""
        self.max_tokens = 120000

    def _get_access_token(self) -> str:
        """
        Retrieve the access token using client credentials.
        """
        url = "https://id.cisco.com/oauth2/default/v1/token"
        value = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {value}",
        }
        response = requests.post(url, headers=headers, data="grant_type=client_credentials")
        return response.json()["access_token"]

    def _configure_openai_client(self) -> None:
        """
        Configure the global OpenAI settings for Azure OpenAI.
        """
        openai.api_type = "azure"
        openai.api_base = self.azure_endpoint
        openai.api_version = self.api_version
        openai.api_key = self.access_token

    def chat(self, input_text: str) -> str:
        """
        Send a message and get a response.
        """
        try:
            user_param = json.dumps({"appkey": self.app_key})
            response = openai.ChatCompletion.create(
                deployment_id="gpt-4o",
                messages=[{"role": "user", "content": input_text}],
                user=user_param,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in the text using tiktoken.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def truncate_to_token_limit(self, text: str, limit: int) -> str:
        """
        Truncate text to stay within the token limit.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return encoding.decode(tokens[:limit])

    def load_local_embeddings(
            self, index_path: str, content_path: str, model_name: str = "all-MiniLM-L6-v2"
    ) -> None:
        """
        Load local embeddings and FAISS index.
        """
        self.index = faiss.read_index(index_path)
        with open(content_path, "rb") as f:
            self.embedded_contents = pickle.load(f)
        self.embedding_model = SentenceTransformer(model_name)

    def retrieve_local_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant context from local embeddings.

        Args:
            query (str): User query for context retrieval.
            top_k (int): Number of top embeddings to retrieve.

        Returns:
            str: Retrieved context chunks concatenated.
        """
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True).reshape(1, -1)
        _, indices = self.index.search(query_embedding, top_k)
        relevant_chunks = [self.embedded_contents[i] for i in indices[0]]
        return "\n\n".join(relevant_chunks)

    def process_fedramp_query(self, question: str, prompt: str, top_k: int = 5) -> str:

        try:
            # Load embeddings only if not already loaded
            if not hasattr(self, 'index') or not hasattr(self, 'embedded_contents'):
                self.load_local_embeddings(
                    index_path="/app/bridge/local_fedramp.index",
                    content_path="/app/bridge/local_fedramp_contents.pkl"
                )
            relevant_context = self.retrieve_local_context(question, top_k=top_k)
            # print(f"Retrieved context: {relevant_context}")
            messages = [
                {
                    "role": "system",
                    "content": f"{prompt}. Here is your context:\n\n{relevant_context}"
                },
                {
                    "role": "user",
                    "content": question
                }
            ]

            user_param = json.dumps({"appkey": self.app_key})
            response = openai.ChatCompletion.create(
                deployment_id="gpt-4o",
                messages=messages,
                user=user_param,
                temperature=0.7,
                max_tokens=2000,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise ValueError(f"Failed to process query: {str(e)}")

def test_process_fedramp_query():
    connector = AzureConnector()



    question = "Do you have context?"
    response = connector.process_fedramp_query(question)

    print(f"Question: {question}")
    print(f"Response: {response}")


if __name__ == "__main__":
    test_process_fedramp_query()
