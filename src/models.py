from sqlalchemy import Column, Integer, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())