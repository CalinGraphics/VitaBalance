from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
from pathlib import Path

# Încarcă variabilele de mediu din .env (robust: mereu din folderul backend)
_backend_dir = Path(__file__).resolve().parent
_env_path = _backend_dir / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# Obține URL-ul bazei de date din variabilele de mediu
# Dacă nu există, folosește SQLite pentru development local
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL/Supabase - folosește URL-ul din variabila de mediu
    # Supabase oferă un URL de forma: postgresql://user:password@host:port/database
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Supabase recomandă NullPool pentru serverless
        echo=False  # Setează True pentru debug SQL queries
    )
else:
    # SQLite pentru development local (fallback)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./vitabalance.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Necesar pentru SQLite
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

