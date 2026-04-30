from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class InputText(BaseModel):
    text: str

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/summarise")
def summarise(input_text: InputText):
    return {"summary": "placeholder"}

@app.get("/health")
def health():
    return {"status": "healthy"}
