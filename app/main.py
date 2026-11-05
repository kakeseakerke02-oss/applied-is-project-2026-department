from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.db import init_db
from app.routers.assessment_tools import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Кафедраның бағалау құралдары қоры", version="0.4.0",
    description="Бағалау құралдарын алу, қосу, өзгерту, жою және сүзу API-ы.",
    lifespan=lifespan,
)
app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok", "project": "department-assessment-fund", "labs": [1, 2, 3, 4]}
