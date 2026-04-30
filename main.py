from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class InputText(BaseModel):
    text: str

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/summarise")
def summarise(input_text: InputText):
    response = api_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarise text into short paragraph and bullet points."},
            {"role": "user", "content": input_text.text}
        ]
    )
    return {"summary": response}

@app.get("/health")
def health():
    return {"status": "healthy"}
