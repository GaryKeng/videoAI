"""
Learning engine - self-evolution through user feedback.
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib
import json
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from src.config import CHROMA_DB_PATH, LEARNING_SIMILARITY_TOP_K, LEARNING_MIN_FREQUENCY
from src.database.models import LearningRecord, GlobalLearningRecord, get_session


class PatternStorage:
    """Store and retrieve patterns using file-based storage (or ChromaDB if available)."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or CHROMA_DB_PATH
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.client = None
        self.collection = None

    def _initialize(self):
        """Initialize storage (ChromaDB if available, otherwise file-based)."""
        if CHROMADB_AVAILABLE:
            if self.client is None:
                self.client = chromadb.Client(Settings(
                    persist_directory=str(self.db_path),
                    anonymized_telemetry=False
                ))
                self.collection = self.client.get_collection("subtitle_image_patterns")
        else:
            # File-based fallback
            self.patterns_file = self.db_path / "patterns.json"
            if not self.patterns_file.exists():
                self._save_patterns({})

    def _save_patterns(self, patterns: Dict):
        """Save patterns to file."""
        with open(self.patterns_file, "w", encoding="utf-8") as f:
            json.dump(patterns, f, ensure_ascii=False)

    def _load_patterns(self) -> Dict:
        """Load patterns from file."""
        if self.patterns_file.exists():
            with open(self.patterns_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def add_pattern(
        self,
        subtitle_text: str,
        ocr_text: str,
        image_path: str,
        match_result: bool,
        adjustment_type: str = None
    ):
        """
        Add a learning pattern.

        Args:
            subtitle_text: Subtitle text
            ocr_text: OCR text from image
            image_path: Path to matched image
            match_result: Whether it was a successful match
            adjustment_type: Type of adjustment (added, removed, modified)
        """
        self._initialize()

        # Create hash for deduplication
        text_hash = hashlib.md5(f"{subtitle_text}:{ocr_text}".encode()).hexdigest()

        if CHROMADB_AVAILABLE and self.client:
            # Generate simple embedding (in production, use proper embeddings)
            embedding = self._simple_embedding(subtitle_text + " " + ocr_text)

            self.collection.add(
                ids=[text_hash],
                embeddings=[embedding],
                metadatas=[{
                    "subtitle_text": subtitle_text,
                    "ocr_text": ocr_text,
                    "image_path": image_path,
                    "match_result": match_result,
                    "adjustment_type": adjustment_type,
                    "timestamp": datetime.now().isoformat()
                }],
                documents=[f"{subtitle_text} || {ocr_text}"]
            )
        else:
            # File-based fallback
            patterns = self._load_patterns()
            patterns[text_hash] = {
                "subtitle_text": subtitle_text,
                "ocr_text": ocr_text,
                "image_path": image_path,
                "match_result": match_result,
                "adjustment_type": adjustment_type,
                "timestamp": datetime.now().isoformat()
            }
            self._save_patterns(patterns)

    def find_similar_patterns(
        self,
        subtitle_text: str,
        ocr_text: str = None,
        top_k: int = LEARNING_SIMILARITY_TOP_K
    ) -> List[Dict]:
        """
        Find similar patterns.

        Args:
            subtitle_text: Subtitle text to search
            ocr_text: Optional OCR text
            top_k: Number of results to return

        Returns:
            List of similar pattern dicts
        """
        self._initialize()

        query_text = subtitle_text
        if ocr_text:
            query_text = f"{subtitle_text} {ocr_text}"

        if CHROMADB_AVAILABLE and self.client:
            embedding = self._simple_embedding(query_text)

            try:
                results = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=top_k
                )

                patterns = []
                for i in range(len(results["ids"][0])):
                    patterns.append({
                        "subtitle_text": results["metadatas"][0][i].get("subtitle_text", ""),
                        "ocr_text": results["metadatas"][0][i].get("ocr_text", ""),
                        "image_path": results["metadatas"][0][i].get("image_path", ""),
                        "match_result": results["metadatas"][0][i].get("match_result", False),
                        "adjustment_type": results["metadatas"][0][i].get("adjustment_type"),
                        "distance": results["distances"][0][i] if "distances" in results else 0
                    })

                return patterns
            except Exception:
                return []
        else:
            # File-based fallback: return all patterns (simplified)
            patterns = self._load_patterns()
            return list(patterns.values())[:top_k]

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple embedding using text hash."""
        import numpy as np
        hash_value = hashlib.md5(text.encode()).hexdigest()
        # Convert hash to fixed-size embedding
        embedding = np.array([
            int(hash_value[i:i+8], 16) / (2**32 - 1)
            for i in range(0, 32, 8)
        ]).astype(np.float32).tolist()
        return embedding

    def clear_all(self):
        """Clear all patterns."""
        self._initialize()
        if CHROMADB_AVAILABLE and self.client:
            self.client.delete_collection("subtitle_image_patterns")
        else:
            self._save_patterns({})


class LearningEngine:
    """Main learning engine for self-evolution."""

    def __init__(self):
        self.pattern_storage = PatternStorage()

    def record_adjustment(
        self,
        project_id: int,
        subtitle_text: str,
        ocr_text: str,
        original_match_path: str,
        final_match_path: str,
        adjustment_type: str
    ):
        """
        Record a user adjustment.

        Args:
            project_id: Project ID
            subtitle_text: Subtitle text
            ocr_text: OCR text from image
            original_match_path: Original AI match path
            final_match_path: Final user-selected path
            adjustment_type: Type of adjustment (added, removed, modified)
        """
        # Store in ChromaDB
        match_result = (original_match_path == final_match_path)
        self.pattern_storage.add_pattern(
            subtitle_text=subtitle_text,
            ocr_text=ocr_text,
            image_path=final_match_path,
            match_result=match_result,
            adjustment_type=adjustment_type
        )

        # Store in SQLite for frequency tracking
        session = get_session()

        # Check if record exists
        existing = session.query(LearningRecord).filter(
            LearningRecord.subtitle_text == subtitle_text,
            LearningRecord.ocr_text == ocr_text
        ).first()

        if existing:
            existing.frequency += 1
            existing.adjustment_type = adjustment_type
            existing.final_image_path = final_match_path
            existing.last_updated = datetime.now()
        else:
            record = LearningRecord(
                project_id=project_id,
                subtitle_text=subtitle_text,
                ocr_text=ocr_text,
                original_match=False,
                user_adjusted_match=True,
                adjustment_type=adjustment_type,
                final_image_path=final_match_path,
                frequency=1
            )
            session.add(record)

        session.commit()
        session.close()

    def get_learned_patterns(
        self,
        subtitle_text: str,
        ocr_text: str = None
    ) -> List[Dict]:
        """
        Get learned patterns for a subtitle.

        Args:
            subtitle_text: Subtitle text
            ocr_text: Optional OCR text

        Returns:
            List of learned pattern dicts with frequency weighting
        """
        patterns = self.pattern_storage.find_similar_patterns(
            subtitle_text, ocr_text
        )

        # Filter by minimum frequency and boost by frequency
        boosted_patterns = []
        session = get_session()

        for pattern in patterns:
            # Query frequency from SQLite
            db_record = session.query(LearningRecord).filter(
                LearningRecord.subtitle_text == pattern.get("subtitle_text", ""),
                LearningRecord.ocr_text == pattern.get("ocr_text", "")
            ).first()

            if db_record and db_record.frequency >= LEARNING_MIN_FREQUENCY:
                pattern["frequency"] = db_record.frequency
                boosted_patterns.append(pattern)

        session.close()
        return boosted_patterns

    def process_completed_video(
        self,
        project_id: int,
        ai_matches: List[Dict],
        final_matches: List[Dict]
    ):
        """
        Process completed video to learn from user adjustments.

        Args:
            project_id: Project ID
            ai_matches: AI initial matches (list of dicts with subtitle_text, ocr_text, image_path)
            final_matches: Final user matches
        """
        for ai_match, final_match in zip(ai_matches, final_matches):
            if ai_match.get("image_path") != final_match.get("image_path"):
                # User adjusted the match
                self.record_adjustment(
                    project_id=project_id,
                    subtitle_text=ai_match.get("subtitle_text", ""),
                    ocr_text=ai_match.get("ocr_text", ""),
                    original_match_path=ai_match.get("image_path", ""),
                    final_match_path=final_match.get("image_path", ""),
                    adjustment_type="modified"
                )
            elif ai_match.get("image_path") and not final_match.get("image_path"):
                # User removed the match
                self.record_adjustment(
                    project_id=project_id,
                    subtitle_text=ai_match.get("subtitle_text", ""),
                    ocr_text=ai_match.get("ocr_text", ""),
                    original_match_path=ai_match.get("image_path", ""),
                    final_match_path="",
                    adjustment_type="removed"
                )

    def get_statistics(self) -> Dict:
        """Get learning statistics."""
        session = get_session()

        total_records = session.query(LearningRecord).count()
        adjusted_records = session.query(LearningRecord).filter(
            LearningRecord.user_adjusted_match == True
        ).count()

        high_frequency = session.query(LearningRecord).filter(
            LearningRecord.frequency >= LEARNING_MIN_FREQUENCY
        ).count()

        session.close()

        return {
            "total_records": total_records,
            "adjusted_records": adjusted_records,
            "high_frequency_records": high_frequency
        }
