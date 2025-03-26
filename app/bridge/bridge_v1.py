
import base64
import json
import os
import time
from typing import List, Dict, Optional

import requests
import tiktoken
from dotenv import load_dotenv
import openai

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

    def load_context_from_file(self, file_path: str) -> None:
        """
        Load context from a file.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()

            token_count = self.count_tokens(content)
            if token_count > self.max_tokens - 1000:  # Reserve tokens for response
                print(f"Warning: File contains {token_count} tokens, truncating to {self.max_tokens - 1000} tokens")
                content = self.truncate_to_token_limit(content, self.max_tokens - 1000)
                token_count = self.max_tokens - 1000

            self.context = content
            print(f"Loaded {token_count} tokens from file")

        except Exception as e:
            raise ValueError(f"Failed to load context file: {str(e)}")

    def chat_with_history(self, messages: List[Dict[str, str]]) -> str:
        """
        Send a message with conversation history and get a response.
        """
        try:
            user = json.dumps({"appkey": self.app_key})
            response = openai.ChatCompletion.create(
                deployment_id="gpt-4o",
                messages=messages,
                user=user,
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error details: {str(e)}")
            return f"Error: {str(e)}"

    def process_fedramp_query(self, question: str) -> str:
        """
        Process FedRAMP query using loaded context.

        Args:
            question (str): User's question

        Returns:
            str: AI response
        """
        try:
            messages = []

            if self.context:
                messages.append({
                    "role": "system",
                    "content": f"Context: {self.context}\n\nYou are a FedRAMP certification expert. Base your answers on the provided security controls."
                })

            messages.append({
                "role": "user",
                "content": question
            })

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
    # Initialize connector
    connector = AzureConnector()

    # Test query
    try:
        question = "What does AC-1 require?"
        response = connector.process_fedramp_query(question)
        print(f"Question: {question}")
        print(f"Response: {response}")
        assert response is not None
        assert isinstance(response, str)
        print("Test passed!")

    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    test_process_fedramp_query()
