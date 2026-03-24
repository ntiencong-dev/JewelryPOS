from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import sys
from dotenv import load_dotenv

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

env_path = os.path.join(get_base_dir(), 'config', '.env')
load_dotenv(dotenv_path=env_path)

Base = declarative_base()

def get_db_url():
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    db_name = os.getenv("DB_NAME", "jewelry_pos")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def get_engine():
    return create_engine(get_db_url(), echo=False)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()