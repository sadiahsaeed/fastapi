from sqlalchemy import create_engine, Column, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import os
from sqlalchemy import Column, String, BigInteger, Sequence

Base = declarative_base()

class Collections(Base): 
    __tablename__ = 'collection'

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # Auto-incrementing BIGINT primary key
    collection = Column(String, nullable=False)           # Collection name or data
    chatbot_id = Column(String, nullable=False)


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # Auto-incrementing BIGINT primary key
    collection_name = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)


# Database connection setup
# DATABASE_URL = f"postgresql://{os.getenv('PG_USER_NAME')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_NAME')}"
DATABASE_URL = f"postgresql://{os.getenv('PG_USER_NAME')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)