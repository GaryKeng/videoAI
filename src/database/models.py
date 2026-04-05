"""
SQLAlchemy models for VideoAI database.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from src.config import DB_PATH

Base = declarative_base()


class Project(Base):
    """Video editing project."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    source_video_path = Column(String(512), nullable=True)
    output_video_path = Column(String(512), nullable=True)

    # Relationships
    subtitle_segments = relationship("SubtitleSegment", back_populates="project", cascade="all, delete-orphan")
    material_images = relationship("MaterialImage", back_populates="project", cascade="all, delete-orphan")
    timeline_items = relationship("TimelineItem", back_populates="project", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="project", cascade="all, delete-orphan")


class SubtitleSegment(Base):
    """Subtitle segment with timestamp."""
    __tablename__ = "subtitle_segments"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    # Error markers
    is_pause_error = Column(Boolean, default=False)
    is_repetition_error = Column(Boolean, default=False)
    is_filler_error = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="subtitle_segments")


class MaterialImage(Base):
    """Material image with OCR text."""
    __tablename__ = "material_images"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    file_path = Column(String(512), nullable=False)
    ocr_text = Column(Text, nullable=True)
    embedding_vector = Column(Text, nullable=True)  # JSON serialized

    # Relationships
    project = relationship("Project", back_populates="material_images")


class TimelineItem(Base):
    """Timeline item (video segment or image overlay)."""
    __tablename__ = "timeline_items"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    item_type = Column(String(50), nullable=False)  # "video" or "image_overlay"
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    source_path = Column(String(512), nullable=True)
    overlay_position_x = Column(Integer, nullable=True)
    overlay_position_y = Column(Integer, nullable=True)
    z_index = Column(Integer, default=0)

    # Relationships
    project = relationship("Project", back_populates="timeline_items")


class LearningRecord(Base):
    """Learning record for self-evolution."""
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    subtitle_text = Column(Text, nullable=False)
    ocr_text = Column(Text, nullable=False)

    # Match results
    original_match = Column(Boolean, nullable=False)
    user_adjusted_match = Column(Boolean, nullable=False)
    adjustment_type = Column(String(50), nullable=True)  # "added", "removed", "modified"
    final_image_path = Column(String(512), nullable=True)

    # Frequency tracking
    frequency = Column(Integer, default=1)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    project = relationship("Project", back_populates="learning_records")


class GlobalLearningRecord(Base):
    """Global learning record across all projects."""
    __tablename__ = "global_learning_records"

    id = Column(Integer, primary_key=True)
    subtitle_text_hash = Column(String(64), nullable=False, index=True)
    ocr_text_hash = Column(String(64), nullable=False, index=True)
    matched_image_path = Column(String(512), nullable=True)
    rejected_image_path = Column(String(512), nullable=True)

    # Frequency tracking
    match_count = Column(Integer, default=0)
    reject_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DatabaseManager:
    """Database manager singleton."""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
        self._session_factory = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)

    def get_session(self):
        return self._session_factory()

    def close(self):
        if self._engine:
            self._engine.dispose()


# Global database instance
db_manager = DatabaseManager()


def get_session():
    return db_manager.get_session()
