import base64
import json
import os
import time

import requests
import tiktoken
from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()

class AzureConnector:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None, app_key: str | None = None):
        self.client_id = client_id if client_id else os.getenv('CISCO_CLIENT_ID')
        self.client_secret = client_secret if client_secret else os.getenv('CISCO_CLIENT_SECRET')
        self.azure_endpoint = 'https://chat-ai.cisco.com'
        self.api_version = "2024-12-01-preview"
        self.app_key = app_key if app_key else os.getenv('CISCO_APP_KEY')

        # Validate credentials
        if not all([self.client_id, self.client_secret, self.app_key]):
            raise ValueError("Missing credentials. Provide them as parameters or environment variables.")

        # Get initial token
        self.access_token = self._get_access_token()

        # Initialize Azure client with token
        self.client = self._create_client()
        self.context = ""
        self.max_tokens = 120000

    def _get_access_token(self) -> str:
        url = "https://id.cisco.com/oauth2/default/v1/token"
        value = base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode('utf-8')
        ).decode('utf-8')

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {value}"
        }

        response = requests.post(
            url,
            headers=headers,
            data="grant_type=client_credentials"
        )
        return response.json()["access_token"]

    def _create_client(self):
        return AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.access_token,
            api_version=self.api_version
        )

    def chat(self, input_text: str) -> str:
        """Send a message and get response"""
        try:
            user_param = json.dumps({"appkey": self.app_key})
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": input_text}],
                user=user_param,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def truncate_to_token_limit(self, text: str, limit: int) -> str:
        """Truncate text to stay within token limit"""
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return encoding.decode(tokens[:limit])

    def load_context_from_file(self, file_path: str) -> None:
        """Load context from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

            token_count = self.count_tokens(content)
            if token_count > self.max_tokens - 1000:  # Reserve 1000 tokens for response
                print(f"Warning: File contains {token_count} tokens, truncating to {self.max_tokens - 1000} tokens")
                content = self.truncate_to_token_limit(content, self.max_tokens - 1000)
                token_count = self.max_tokens - 1000

            self.context = content
            print(f"Loaded {token_count} tokens from file")

        except Exception as e:
            raise ValueError(f"Failed to load context file: {str(e)}")

    def chat_with_history(self, messages: list) -> str:
        """Send a message with conversation history and get response"""
        try:
            # Create user parameter as a dictionary
            user = json.dumps({"appkey": self.app_key})

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                user=user,
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error details: {str(e)}")
            return f"Error: {str(e)}"


# def main():
#
#
#     connector = AzureConnector()
#
#     text = input("Enter your message: ")
#     print("\nResponse:", connector.chat(text))
#     text = input("Enter your message: ")
#     print("\nResponse:", connector.chat(text))




def main():
    connector = AzureConnector()
    conversation_history = []

    print("\n=== Cisco AI Conversation ===")
    print("Type 'quit' to exit")
    print("-" * 50)

    while True:
        text = input("\nYour message: ").strip()

        if text.lower() in ['quit', 'exit', 'q']:
            print("\nEnding conversation. Goodbye!")
            break

        # Add user message to history
        conversation_history.append({"role": "user", "content": text})

        # Get response
        response = connector.chat_with_history(conversation_history)
        print(f"\nResponse: {response}")

        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": response})

        # Add delay for rate limiting
        time.sleep(4)

if __name__ == "__main__":
    main()
