from fastapi import FastAPI
from .models import Base
from .database import engine
from .routers import auth, todos, admin, users
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status

app2 = FastAPI()

Base.metadata.create_all(bind=engine)

app2.mount("/static", StaticFiles(directory="fastapi_demo/static"), name="static")


@app2.get('/')
async def root():
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

app2.include_router(auth.router)
app2.include_router(todos.router)
app2.include_router(admin.router)
app2.include_router(users.router)

