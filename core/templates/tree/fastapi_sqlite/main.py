from fastapi import FastAPI
from sqlmodel import SQLModel, Session, create_engine
from models import User

app = FastAPI()
engine = create_engine("sqlite:///app.db")


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    with Session(engine) as session:
        return {"users": session.query(User).all()}
