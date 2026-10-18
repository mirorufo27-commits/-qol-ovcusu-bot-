import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL','sqlite:///data/qolovcusu.db')

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

def init_db():
    # Run the SQL migration script if using sqlite file
    path = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'initial.sql')
    with engine.connect() as conn:
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
            conn.execute(sql)
            conn.commit()
