from fastapi import FastAPI
from sqlmodel import SQLModel, Session, create_engine
from models import User

app = FastAPI()
engine = create_engine("sqlite:///app.db")


@app.on_event("startup")
def on_startup():
    """
    Create database tables for all SQLModel models on application startup.
    
    This function calls SQLModel.metadata.create_all(engine) to ensure the SQLite database
    (schema at the configured `engine`) contains tables for all declared SQLModel models.
    It is intended to be registered with FastAPI's "startup" event so tables are created
    when the application starts.
    """
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    """
    Return all User records from the database.
    
    Queries the database for all User rows and returns them in a dictionary under the "users" key. The returned User objects are SQLModel/Pydantic models and will be serialized by FastAPI for the HTTP response.
    
    Returns:
        dict: {"users": List[User]} — list of all User instances from the database.
    """
    with Session(engine) as session:
        return {"users": session.query(User).all()}
