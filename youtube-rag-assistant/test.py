import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the .env file
load_dotenv()

# Get the Groq API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "Missing API key. Check your .env file and GROQ_API_KEY variable."
    )

# Initialize the Groq client
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

# Send a request
response = client.responses.create(
    model="openai/gpt-oss-20b",
    input="Hi",
)

# Print the response
print(response.output_text)