import os
import time
import pandas as pd
import json
import base64
import requests
import tiktoken
from typing import List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv


class CiscoAIConnector:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 app_key: Optional[str] = None):
        self.client_id = client_id or os.getenv('CISCO_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('CISCO_CLIENT_SECRET')
        self.app_key = app_key or os.getenv('CISCO_APP_KEY')
        self.azure_endpoint = 'https://chat-ai.cisco.com'
        self.api_version = "2024-12-01-preview"

        # Validate credentials
        if not all([self.client_id, self.client_secret, self.app_key]):
            raise ValueError("Missing credentials. Provide them as parameters or environment variables.")

        # Initialize
        self.access_token = self._get_access_token()
        self.client = self._create_client()

        # Settings
        self.context = ""
        self.max_tokens = 120000
        self.last_request_time = 0
        self.rate_limit_wait = 45

    def _get_access_token(self) -> str:
        """Get access token from Cisco auth endpoint"""
        url = "https://id.cisco.com/oauth2/default/v1/token"
        value = base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode('utf-8')
        ).decode('utf-8')

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {value}"
        }

        response = requests.post(url, headers=headers, data="grant_type=client_credentials")
        return response.json()["access_token"]

    def _create_client(self) -> AzureOpenAI:
        """Create Azure OpenAI client"""
        return AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.access_token,
            api_version=self.api_version
        )

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_wait:
            wait_time = self.rate_limit_wait - elapsed
            print(f"\nWaiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def truncate_to_token_limit(self, text: str, limit: int) -> str:
        """Truncate text to token limit"""
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return encoding.decode(tokens[:limit])

    def load_context_from_file(self, file_path: str) -> None:
        """Load context from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

            token_count = self.count_tokens(content)
            if token_count > self.max_tokens - 1000:
                print(f"Warning: File contains {token_count} tokens, truncating...")
                content = self.truncate_to_token_limit(content, self.max_tokens - 1000)
                token_count = self.max_tokens - 1000

            self.context = content
            print(f"Loaded {token_count} tokens from file")

        except Exception as e:
            raise ValueError(f"Failed to load context file: {str(e)}")

    def chat(self, message: str) -> str:
        """Send a message and get response"""
        try:
            # self._wait_for_rate_limit()

            messages = []
            if self.context:
                messages.append({
                    "role": "system",
                    "content": f"Context: {self.context}\n\nUse this context to answer the question."
                })

            messages.append({"role": "user", "content": message})

            # Format user parameter exactly as required
            user_param = '{' + f'"appkey" : "{self.app_key}"' + '}'

            print(f"Debug - Sending request with user param: {user_param}")

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                user=user_param,
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Debug - Error details: {str(e)}")
            return f"Error: {str(e)}"

    def chat_with_history(self, messages: List[dict]) -> str:
        """Chat with message history"""
        try:
            # self._wait_for_rate_limit()

            formatted_messages = []
            if self.context:
                formatted_messages.append({
                    "role": "system",
                    "content": f"Context: {self.context}"
                })

            formatted_messages.extend(messages)

            # Format user parameter exactly as required
            user_param = '{' + f'"appkey" : "{self.app_key}"' + '}'

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=formatted_messages,
                user=user_param,
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"


    def load_csv_context(self, file_path: str, columns: Optional[List[str]] = None) -> None:
        """Load context from a CSV file with focus on security controls"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)

            # Select specific columns or use defaults for security controls
            if columns:
                df = df[columns]
            else:
                # Default columns for security controls
                default_columns = ['Control ID', 'Control Name', 'Control Text']
                available_columns = [col for col in default_columns if col in df.columns]
                df = df[available_columns]

            # Format the DataFrame as a structured text
            formatted_rows = []
            for _, row in df.iterrows():
                row_text = "\n".join([f"{col}: {row[col]}" for col in df.columns])
                formatted_rows.append(row_text)
                formatted_rows.append("-" * 80)  # Separator

            content = "\n".join(formatted_rows)

            # Check token count and truncate if needed
            token_count = self.count_tokens(content)
            if token_count > self.max_tokens - 2000:  # Reserve 2000 tokens for response
                print(f"Warning: CSV content contains {token_count} tokens, truncating...")
                content = self.truncate_to_token_limit(content, self.max_tokens - 2000)
                token_count = self.count_tokens(content)

            self.context = content
            print(f"Loaded {token_count} tokens from CSV")
            print(f"CSV shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Columns loaded: {', '.join(df.columns)}")

        except Exception as e:
            raise ValueError(f"Failed to load CSV file: {str(e)}")

    def query_fedramp(self, question: str) -> str:
        """Specialized method for FedRAMP queries"""
        formatted_query = f"""You are a FedRAMP certification expert. Based on the FedRAMP security controls provided:

        Question: {question}
    
        Instructions:
        1. For general FedRAMP questions, provide clear explanations.
        2. For certification questions, list specific requirements and controls.
        3. For compliance questions, identify gaps and required actions.
        4. Always reference specific control IDs when applicable.
        5. Provide practical, actionable recommendations.
    
        Please answer the question in a structured format."""

        return self.chat(formatted_query)


def interactive_fedramp_session():
    """Interactive FedRAMP consultation session"""
    try:
        connector = CiscoAIConnector()

        # Load security controls CSV
        print("\nLoading FedRAMP security controls...")
        connector.load_csv_context('/Users/bvoloshy/PycharmProjects/RAG-model/FedRAMP_High_Security_Controls.csv')

        # Initialize conversation history
        conversation = [
            {
                "role": "system",
                "content": "You are a FedRAMP certification expert. Provide clear, specific answers based on the security controls provided."
            }
        ]

        print("\nFedRAMP Consultation Session")
        print("Type 'quit' to end the session")
        print("-" * 50)

        while True:
            # Get user input
            question = input("\nYour question: ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("\nEnding session. Goodbye!")
                break

            # Add user question to conversation
            conversation.append({
                "role": "user",
                "content": question
            })

            # Get response
            response = connector.chat_with_history(conversation)
            print(f"\nResponse:\n{response}")

            # Add assistant response to conversation
            conversation.append({
                "role": "assistant",
                "content": response
            })

            # Rate limiting
            print("\nWaiting for next question...")
            # time.sleep(45)

    except Exception as e:
        print(f"Error during session: {str(e)}")


if __name__ == "__main__":
    load_dotenv()
    interactive_fedramp_session()
