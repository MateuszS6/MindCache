import time
import logging
from typing import Generator

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from openai import OpenAI

from src.database import engine, SessionLocal
from src.models import Base, Summary
from src.config import (
    APP_API_KEY,
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
    description="A FastAPI service that summarises text using AI and stores results in PostgreSQL.",
    version="0.1.0",
)

api_client = OpenAI(api_key=OPENAI_API_KEY)

Base.metadata.create_all(bind=engine)  # if tables don't exist, create them

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputText(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_INPUT_LENGTH,  # cap input length for cost effectiveness
        description="Text to summarise",
    )


def verify_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key != APP_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key."
        )


def get_db() -> Generator[Session, None, None]:
    # FastAPI manages the DB session for the request
    db = SessionLocal()  # create a new database session
    try:
        yield db  # return the current database session to the caller
    finally:
        db.close()  # close the database session


# --- in-memory rate limiter ---
request_log: dict[str, list[float]] = {}


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_seconds = 60

    if ip not in request_log:
        request_log[ip] = []  # add client ip if not found in request log

    request_log[ip] = [
        request_time  # repopulate with request times
        for request_time in request_log[ip]  # fetch request times for this client...
        if now - request_time < window_seconds  # ...that are within the last minute
    ]

    # check if the amount of requests in the last minute is over the limit
    if len(request_log[ip]) >= MAX_REQUESTS_PER_MINUTE:
        return True

    request_log[ip].append(now)  # rate is not limited so append current time
    return False


# --- endpoints ---
@app.get("/")
def root():
    return {"message": "MindCache API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/summarise")
def summarise(input_text: InputText, request: Request, db: Session = Depends(get_db), _: None = Depends(verify_api_key)):
    client_ip = request.client.host if request.client else "unknown"

    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429, detail="Too many recent requests. Please try again later."
        )

    text = input_text.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Input text must not be empty.",
        )

    for attempt in range(RETRY_LIMIT):  # give the system a number of summarise attempts
        try:
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
                max_tokens=MAX_OUTPUT_TOKENS,  # cap AI response for cost effectiveness
                timeout=AI_TIMEOUT_SECONDS,  # prevent hanging if the AI service is slow
            )

            summary_text = response.choices[0].message.content

            if not summary_text:
                raise HTTPException(
                    status_code=502,
                    detail="AI service returned an empty response.",
                )

            new_summary = Summary(input=text, output=summary_text)

            db.add(new_summary)  # add the new summary to the session
            db.commit()  # commit the session to save the summary to the DB
            db.refresh(
                new_summary
            )  # refresh the instance to get the generated ID and timestamp

            logger.info(f"Summary created successfully from IP: {client_ip}")

            return {
                "id": new_summary.id,
                "summary": summary_text,
                "created_at": new_summary.created_at,
            }

        except HTTPException:
            raise  # catch any unspecified HTTPExceptions

        except Exception as error:
            logger.warning(
                f"Summarise attempt {attempt + 1}/{RETRY_LIMIT} failed: {str(error)}"
            )  # log all other Exceptions with error details

            if attempt == RETRY_LIMIT - 1:
                db.rollback()  # undo database change right after retry limit is reached
                raise HTTPException(
                    status_code=500,
                    detail="Something went wrong when trying to generate summary. Please try again later.",
                )


@app.get("/history")
def history(limit: int = 20, db: Session = Depends(get_db), _: None = Depends(verify_api_key)):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100.",
        )

    summaries = (
        db.query(Summary)
        .order_by(Summary.created_at.desc())  # in descending order of creation date
        .limit(limit)  # bounded
        .all()  # return this result
    )

    return [
        {
            "id": summary.id,
            "input": summary.input,
            "output": summary.output,
            "created_at": summary.created_at,
        }
        for summary in summaries
    ]  # return selected summaries in JSON format and according to Summary model
