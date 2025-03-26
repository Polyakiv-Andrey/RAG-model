import openai


def chat_with_gpt(user_input):
    # Replace your actual OpenAI API key
    openai.api_key = "sk------------------------------p"
    # Generating a response using GPT-3.5 Turbo
    response = openai.Completion.create(
        engine="text-davinci-002",  # Use the appropriate engine
        prompt=user_input,
        max_tokens=150
    )
    # Extracting and returning the assistant's response
    assistant_response = response['choices'][0]['text']
    return assistant_response





def __main__(args):
    # Example usage
    user_input = input("How may I help you? ")
    Ask_chatgpt = chat_with_gpt(user_input)
    print(f"Assistant: {Ask_chatgpt}")
