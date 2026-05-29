import time
import logging
from typing import Generator

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from openai import OpenAI

from src.database import engine, SessionLocal
from src.models import Base, Summary
from src.config import (
    OPENAI_API_KEY,
    MAX_INPUT_LENGTH,
    MAX_REQUESTS_PER_MINUTE,
    RETRY_LIMIT,
    AI_TIMEOUT_SECONDS,
    MAX_OUTPUT_TOKENS,
)

# --- setup ---
app = FastAPI(
    title="MindCache API",
    description="A FastAPI service that summarises text using AI and stores resuults in PostgreSQL.",
    version="0.1.0",
)

api_client = OpenAI(api_key=OPENAI_API_KEY)

Base.metadata.create_all(bind=engine)  # if tables don't exist, create them

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- in-memory rate limiter ---
request_log: dict[str, list[float]] = {}


class InputText(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_INPUT_LENGTH,
        description="Text to summarise",
    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()  # create a new database session
    try:
        yield db
    finally:
        db.close()  # close the database session


# --- endpoints ---
@app.get("/")
def root():
    return {"message": "MindCache API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/summarise")
def summarise(input_text: InputText, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"

    text = input_text.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Input text must not be empty.",
        )

    response = api_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You summarise text clearly and concisely."
                    "Return one short paragraph of no more than 100 words,"
                    "followed by 3 to 5 bullet points."
                ),
            },
            {"role": "user", "content": text},
        ],
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=AI_TIMEOUT_SECONDS,
    )

    summary_text = response.choices[0].message.content

    if not summary_text:
        raise HTTPException(
            status_code=502,
            detail="AI service returned an empty response.",
        )

    new_summary = Summary(input=text, output=summary_text)

    db.add(new_summary)  # add the new summary to the session
    db.commit()  # commit the session to save the summary to the database
    db.refresh(
        new_summary
    )  # refresh the instance to get the generated ID and timestamp

    logger.info(f"Summary created successfully from IP: {client_ip}")

    return {
        "id": new_summary.id,
        "summary": summary_text,
        "created_at": new_summary.created_at,
    }


@app.get("/history")
def history(db: Session = Depends(get_db)):
    summaries = db.query(Summary).order_by(Summary.created_at.desc()).all()

    return [
        {
            "id": summary.id,
            "input": summary.input,
            "output": summary.output,
            "created_at": summary.created_at,
        }
        for summary in summaries
    ]
