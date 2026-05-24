import io
from pathlib import Path

from PIL import Image


class OCRService:
    """OCR service for extracting text from images using pytesseract."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from an image file using Tesseract OCR.

        Args:
            file_path: Path to the image file (PNG, JPG, etc.)

        Returns:
            Extracted text string.
        """
        try:
            import pytesseract
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            return text.strip()
        except ImportError:
            raise ImportError(
                "pytesseract is required for OCR. Install it with: pip install pytesseract"
            )
        except Exception as e:
            raise Exception(f"OCR failed for {file_path}: {str(e)}")

    @staticmethod
    def extract_text_from_bytes(data: bytes, filename: str) -> str:
        """Extract text from image bytes."""
        import pytesseract
        img = Image.open(io.BytesIO(data))
        text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        return text.strip()
