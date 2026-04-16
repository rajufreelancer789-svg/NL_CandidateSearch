# SQLAlchemy models for resume candidates
# Single table: candidates

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    category = Column(String(100), nullable=False)  # Resume category (IT, Finance, HR, etc)
    file_path = Column(String(500), nullable=False)  # Path to PDF file
    doc_id = Column(String(255))  # PageIndex document ID
    tree_json = Column(Text)  # Full PageIndex tree (JSON string)
    tree_compressed = Column(Text)  # Compressed tree for search (JSON string - node_id, title, summary only)
    uploaded_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', category='{self.category}')>"
