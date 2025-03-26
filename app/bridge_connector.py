import base64
import json
import os

import requests
from dotenv import load_dotenv
from openai import AzureOpenAI


class AzureConnector:
    def __init__(self, client_id: str, client_secret: str, app_key: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.azure_endpoint = 'https://chat-ai.cisco.com'
        self.api_version = "2024-12-01-preview"
        self.app_key = app_key

        # Get initial token
        self.access_token = self._get_access_token()

        # Initialize Azure client with token
        self.client = self._create_client()

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
                user=user_param
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    load_dotenv()

    connector = AzureConnector(
        client_id=os.getenv('CISCO_CLIENT_ID'),
        client_secret=os.getenv('CISCO_CLIENT_SECRET'),
        app_key=os.getenv('CISCO_APP_KEY')
    )

    text = input("Enter your message: ")
    print("\nResponse:", connector.chat(text))


if __name__ == "__main__":
    main()
