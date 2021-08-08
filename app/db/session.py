from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if 'sqlite' in settings.SQLALCHEMY_DATABASE_URI else {},
    echo=settings.SQLALCHEMY_ECHO
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

