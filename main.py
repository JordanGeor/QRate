from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.db import Base, engine
from app.routers.public import router as public_router
from app.routers.admin import router as admin_router

app = FastAPI(title="QRate")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return RedirectResponse(url="/admin/login")

app.include_router(public_router)
app.include_router(admin_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
