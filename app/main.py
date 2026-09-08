from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import engine, Base
from .routers.public import router as public_router
from .routers.admin import router as admin_router

# Create DB tables (including any new models such as ContactRequest)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="QRate")


@app.get("/")
def home():
    return RedirectResponse(url="/admin/login")


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(public_router)
app.include_router(admin_router)
