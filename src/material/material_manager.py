"""
Material manager - manages material library, file watching, and OCR processing.
"""
import hashlib
from pathlib import Path
from typing import Union, List, Dict, Optional
import json

from src.config import MATERIALS_FOLDER, EXPORTS_DIR
from src.database.models import MaterialImage, Project, get_session


class OCRProcessor:
    """OCR processor for images."""

    def __init__(self, backend: str = "easyocr"):
        """
        Initialize OCR processor.

        Args:
            backend: "easyocr" or "paddleocr"
        """
        self.backend = backend
        self.reader = None

    def load_model(self):
        """Load OCR model."""
        if self.reader is None:
            if self.backend == "easyocr":
                import easyocr
                self.reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
            elif self.backend == "paddleocr":
                from paddleocr import PaddleOCR
                self.reader = PaddleOCR(use_angle_cls=True, lang="ch")
            print(f"OCR model ({self.backend}) loaded")

    def process_image(self, image_path: Union[str, Path]) -> str:
        """
        Process image and extract text.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text string
        """
        if self.reader is None:
            self.load_model()

        image_path = Path(image_path)

        if self.backend == "easyocr":
            result = self.reader.readtext(str(image_path))
            text_parts = []
            for detection in result:
                _, text, _ = detection
                if text:
                    text_parts.append(text)
            return " ".join(text_parts)

        elif self.backend == "paddleocr":
            result = self.reader.ocr(str(image_path), cls=True)
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        text_parts.append(text)
            return " ".join(text_parts)

        return ""

    def process_batch(self, image_paths: List[Path]) -> List[Dict]:
        """
        Process multiple images.

        Args:
            image_paths: List of image paths

        Returns:
            List of dicts with image_path and ocr_text
        """
        results = []
        for img_path in image_paths:
            ocr_text = self.process_image(img_path)
            results.append({
                "image_path": str(img_path),
                "ocr_text": ocr_text
            })
        return results


class MaterialManager:
    """Manages material library."""

    def __init__(self, materials_folder: Path = None):
        self.materials_folder = materials_folder or MATERIALS_FOLDER
        self.ocr_processor = OCRProcessor(backend="easyocr")
        self.materials: List[MaterialImage] = []
        self._ensure_materials_folder()

    def _ensure_materials_folder(self):
        """Ensure materials folder exists."""
        self.materials_folder.mkdir(parents=True, exist_ok=True)

    def import_materials(self, project_id: Optional[int] = None) -> List[Dict]:
        """
        Import materials from the materials folder.

        Args:
            project_id: Optional project ID for database association

        Returns:
            List of dicts with material info
        """
        imported = []

        # Find PNG and JPG images
        image_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
        image_files = [
            f for f in self.materials_folder.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        print(f"Found {len(image_files)} image files in materials folder")

        for img_path in image_files:
            # Check if already imported
            session = get_session()
            existing = session.query(MaterialImage).filter(
                MaterialImage.file_path == str(img_path)
            ).first()

            if existing:
                # Update existing
                ocr_text = existing.ocr_text
            else:
                # Process new image
                ocr_text = self.ocr_processor.process_image(img_path)

                # Save to database
                material = MaterialImage(
                    project_id=project_id,
                    file_path=str(img_path),
                    ocr_text=ocr_text
                )
                session.add(material)
                session.commit()

            imported.append({
                "image_path": str(img_path),
                "ocr_text": ocr_text
            })

            session.close()

        return imported

    def get_all_materials(self, project_id: Optional[int] = None) -> List[Dict]:
        """
        Get all materials, optionally filtered by project.

        Args:
            project_id: Optional project ID

        Returns:
            List of material dicts
        """
        session = get_session()
        query = session.query(MaterialImage)
        if project_id:
            query = query.filter(MaterialImage.project_id == project_id)

        materials = query.all()
        result = []

        for mat in materials:
            result.append({
                "id": mat.id,
                "image_path": mat.file_path,
                "ocr_text": mat.ocr_text
            })

        session.close()
        return result

    def refresh_materials(self) -> List[Dict]:
        """
        Refresh materials from folder.

        Returns:
            Updated list of materials
        """
        return self.import_materials()
