"""
Project manager - handles project creation, loading, and management.
"""
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import shutil

from src.config import PROJECTS_DIR, EXPORTS_DIR
from src.database.models import Project, SubtitleSegment, TimelineItem, LearningRecord, get_session


class ProjectManager:
    """Manage video editing projects."""

    def __init__(self, projects_dir: Path = None):
        self.projects_dir = projects_dir or PROJECTS_DIR
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.current_project: Optional[Project] = None

    def create_project(self, name: str, source_video_path: str = None) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            source_video_path: Optional path to source video

        Returns:
            Created Project object
        """
        session = get_session()

        # Check if project with same name exists
        existing = session.query(Project).filter(Project.name == name).first()
        if existing:
            session.close()
            raise ValueError(f"Project with name '{name}' already exists")

        # Create project record
        project = Project(
            name=name,
            source_video_path=source_video_path
        )
        session.add(project)
        session.commit()

        # Create project directory
        project_dir = self.projects_dir / name
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (project_dir / "segments").mkdir(exist_ok=True)
        (project_dir / "temp").mkdir(exist_ok=True)

        self.current_project = project
        session.close()

        return project

    def load_project(self, name: str) -> Optional[Project]:
        """
        Load project by name.

        Args:
            name: Project name

        Returns:
            Project object or None if not found
        """
        session = get_session()
        project = session.query(Project).filter(Project.name == name).first()
        session.close()

        if project:
            self.current_project = project

        return project

    def load_project_by_id(self, project_id: int) -> Optional[Project]:
        """Load project by ID."""
        session = get_session()
        project = session.query(Project).filter(Project.id == project_id).first()
        session.close()

        if project:
            self.current_project = project

        return project

    def save_subtitle_segments(self, segments: List[Dict]):
        """
        Save subtitle segments to database.

        Args:
            segments: List of segment dicts with start, end, text, error flags
        """
        if not self.current_project:
            return

        session = get_session()

        # Clear existing segments
        existing = session.query(SubtitleSegment).filter(
            SubtitleSegment.project_id == self.current_project.id
        ).all()
        for seg in existing:
            session.delete(seg)

        # Save new segments
        for seg in segments:
            segment = SubtitleSegment(
                project_id=self.current_project.id,
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                is_pause_error=seg.get("is_pause_error", False),
                is_repetition_error=seg.get("is_repetition_error", False),
                is_filler_error=seg.get("is_filler_error", False)
            )
            session.add(segment)

        session.commit()
        session.close()

    def get_subtitle_segments(self) -> List[Dict]:
        """Get subtitle segments for current project."""
        if not self.current_project:
            return []

        session = get_session()
        segments = session.query(SubtitleSegment).filter(
            SubtitleSegment.project_id == self.current_project.id
        ).order_by(SubtitleSegment.start_time).all()

        result = [
            {
                "start": seg.start_time,
                "end": seg.end_time,
                "text": seg.text,
                "is_pause_error": seg.is_pause_error,
                "is_repetition_error": seg.is_repetition_error,
                "is_filler_error": seg.is_filler_error
            }
            for seg in segments
        ]

        session.close()
        return result

    def save_timeline_items(self, items: List[Dict]):
        """
        Save timeline items to database.

        Args:
            items: List of timeline item dicts
        """
        if not self.current_project:
            return

        session = get_session()

        # Clear existing items
        existing = session.query(TimelineItem).filter(
            TimelineItem.project_id == self.current_project.id
        ).all()
        for item in existing:
            session.delete(item)

        # Save new items
        for item in items:
            timeline_item = TimelineItem(
                project_id=self.current_project.id,
                item_type=item["type"],
                start_time=item["start"],
                end_time=item["end"],
                source_path=item.get("source_path"),
                overlay_position_x=item.get("position", (0, 0))[0],
                overlay_position_y=item.get("position", (0, 0))[1],
                z_index=item.get("z_index", 0)
            )
            session.add(timeline_item)

        session.commit()
        session.close()

    def get_timeline_items(self) -> List[Dict]:
        """Get timeline items for current project."""
        if not self.current_project:
            return []

        session = get_session()
        items = session.query(TimelineItem).filter(
            TimelineItem.project_id == self.current_project.id
        ).order_by(TimelineItem.start_time).all()

        result = [
            {
                "type": item.item_type,
                "start": item.start_time,
                "end": item.end_time,
                "source_path": item.source_path,
                "position": (item.overlay_position_x or 0, item.overlay_position_y or 0),
                "z_index": item.z_index
            }
            for item in items
        ]

        session.close()
        return result

    def list_projects(self) -> List[Dict]:
        """List all projects."""
        session = get_session()
        projects = session.query(Project).order_by(Project.updated_at.desc()).all()

        result = [
            {
                "id": p.id,
                "name": p.name,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
                "source_video_path": p.source_video_path
            }
            for p in projects
        ]

        session.close()
        return result

    def delete_project(self, name: str):
        """Delete project by name."""
        session = get_session()
        project = session.query(Project).filter(Project.name == name).first()

        if project:
            # Delete project directory
            project_dir = self.projects_dir / name
            if project_dir.exists():
                shutil.rmtree(project_dir)

            # Delete from database
            session.delete(project)
            session.commit()

        session.close()

    def update_output_path(self, output_path: str):
        """Update the output video path for current project."""
        if not self.current_project:
            return

        session = get_session()
        project = session.query(Project).filter(
            Project.id == self.current_project.id
        ).first()

        if project:
            project.output_video_path = output_path
            project.updated_at = datetime.now()
            session.commit()

        session.close()
