from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

class FileMetadata(Base):
    """Model representing metadata for a file in the system."""
    __tablename__ = 'files_metadata'

    file_id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    source = Column(String)  # e.g., network drive name
    file_type = Column(String)  # Derived from file extension (PDF, DWG, etc.)
    issue_status = Column(String)
    revision = Column(String)
    department = Column(String)
    drawing_type = Column(String)
    plant_area = Column(String)
    equipment_included = Column(String)
    notes = Column(String)
    todos = Column(String)
    last_modified = Column(DateTime)
    created_date = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<FileMetadata(file_id={self.file_id}, file_name='{self.file_name}')>"

    @property
    def is_fully_tagged(self) -> bool:
        """Check if all essential metadata fields are populated."""
        essential_fields = [
            self.department,
            self.revision,
            self.drawing_type
        ]
        return all(field is not None and field.strip() != '' for field in essential_fields)

class RecentProject(Base):
    """Model for tracking recently accessed project folders."""
    __tablename__ = 'recent_projects'

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    job_folder_path = Column(String, nullable=False, unique=True)
    last_accessed = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RecentProject(project_id={self.project_id}, path='{self.job_folder_path}')>"

class UserInputHistory(Base):
    """Model for tracking user input history for autocomplete suggestions."""
    __tablename__ = 'user_input_history'

    input_id = Column(Integer, primary_key=True, autoincrement=True)
    field_name = Column(String, nullable=False)  # e.g., drawing_type, plant_area
    field_value = Column(String, nullable=False)
    usage_count = Column(Integer, default=1)  # For ranking autocomplete suggestions

    def __repr__(self):
        return f"<UserInputHistory(field='{self.field_name}', value='{self.field_value}')>"

    @classmethod
    def increment_usage(cls, session, field_name: str, field_value: str) -> None:
        """Increment usage count for a field value, creating new record if needed."""
        record = session.query(cls).filter_by(
            field_name=field_name,
            field_value=field_value
        ).first()

        if record:
            record.usage_count += 1
        else:
            new_record = cls(
                field_name=field_name,
                field_value=field_value,
                usage_count=1
            )
            session.add(new_record)

def init_db(db_path: str = "fms.db") -> None:
    """Initialize the database and create all tables."""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)

# Example usage:
if __name__ == "__main__":
    # Initialize database
    init_db()