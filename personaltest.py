from openai import OpenAI
from dotenv import load_dotenv
from memoriai import Memori, create_memory_search_tool
import os

# Load environment variables from .env file
load_dotenv()

client = OpenAI()

personal = Memori(
    database_connect="sqlite:///personal.db",
    template="basic",
    mem_prompt="Focus on personal life and events",
    conscious_ingest=True,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

personal.enable()

response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": "You are a personal assistant."},
        {
            "role": "user",
            "content": "Hii, my name is Harshal MORE",
        },
    ],
)

print(response)