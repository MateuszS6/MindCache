import os
import time
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from src.database import engine
from src.database import SessionLocal
from src.models import Base
from src.models import Summary

load_dotenv()


# --- config ---
MAX_INPUT_LENGTH = 1000
MAX_REQUESTS_PER_MINUTE = 5
RETRY_LIMIT = 2


# --- setup ---
app = FastAPI()
api_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
Base.metadata.create_all(bind=engine)  # if tables don't exist, create them

# logging.basicConfig(level=logging.INFO)


class InputText(BaseModel):
    text: str


@app.get("/")
def root():
    return {"message": "API is running"}


@app.post("/summarise")
def summarise(input_text: InputText):
    if len(input_text.text) > MAX_INPUT_LENGTH:
        return {
            "error": f"Input text is too long. Please limit to {MAX_INPUT_LENGTH} characters."
        }

    response = api_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Summarise text into short paragraph and bullet points.",
            },
            {"role": "user", "content": input_text.text},
        ],
    )

    summary_text = response.choices[0].message.content

    db = SessionLocal()  # create a new database session

    new_summary = Summary(input=input_text.text, output=summary_text)

    db.add(new_summary)  # add the new summary to the session
    db.commit()  # commit the session to save the summary to the database
    db.close()  # close the database session

    return {"summary": summary_text}


@app.get("/history")
def history():
    db = SessionLocal()

    summaries = db.query(Summary).all()

    results = []

    for summary in summaries:
        results.append(
            {
                "id": summary.id,
                "input": summary.input,
                "output": summary.output,
                "created_at": summary.created_at,
            }
        )

    db.close()

    return results


@app.get("/health")
def health():
    return {"status": "healthy"}
