from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import sys
from dotenv import load_dotenv
from src.utils.config_manager import get_env_path

env_path = get_env_path()
load_dotenv(dotenv_path=env_path)

Base = declarative_base()

def get_db_url():
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "jewelry_pos")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def get_engine():
    return create_engine(get_db_url(), echo=False)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()