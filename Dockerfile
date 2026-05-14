FROM python:3.14

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn openai psycopg2-binary sqlalchemy python-dotenv

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]