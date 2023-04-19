import os
from dotenv import load_dotenv
import openai

# Load environment variables from the .env file
load_dotenv()

# Set up the OpenAI API client
openai.api_key = os.getenv("GPT_KEY")

def generate_response(prompt, max_tokens=150, temperature=0.5):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=temperature,
    )

    return response.choices[0].text.strip()
