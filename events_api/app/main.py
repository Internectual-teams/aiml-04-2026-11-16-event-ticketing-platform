from fastapi import FastAPI

app = FastAPI(title="Events API", version="0.1.0")


@app.get("/")
def root():
    return {"message": "Events API is running"}