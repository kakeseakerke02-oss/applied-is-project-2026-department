from fastapi import FastAPI

app = FastAPI(title="Кафедраның бағалау құралдары қоры")

@app.get("/")
def root():
    return {"status": "ok", "project": "department-assessment-fund", "lab": 1}
