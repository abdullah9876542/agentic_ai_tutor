"""
ocr/extractor.py — Marksheet extraction using GPT-4o Vision

Accepts an image (JPG, PNG) or PDF page.
Sends it to GPT-4o with a structured prompt.
Returns a list of { subject, score, max_score, grade } dicts.
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """
You are an academic result extraction assistant.
Your job is to read a student's marksheet or result card image and extract every subject with its score.

Return ONLY a valid JSON object — no explanation, no markdown, no code fences.

The JSON must follow this exact structure:
{
  "student_name": "string or null if not found",
  "student_id": "string or null if not found",
  "semester": "string or null if not found",
  "grades": [
    {
      "subject": "Subject Name",
      "score": 85.0,
      "max_score": 100.0,
      "grade": "A"
    }
  ],
  "raw_summary": "One sentence summary of what you found in the document"
}

Rules:
- "score" must be a number (float). If not available, use null.
- "max_score" should be the maximum marks for that subject. Default to 100.0 if not shown.
- "grade" is the letter grade if shown (A, B+, etc). Use null if not shown.
- Include every subject you can find. Do not skip any.
- If you cannot read the image at all, return: {"error": "Could not read the document"}
"""


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _image_to_base64(file_path: str) -> tuple[str, str]:
    """
    Read an image file and return (base64_string, media_type).
    Supports: .jpg, .jpeg, .png, .webp
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    media_type_map = {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
    }

    media_type = media_type_map.get(ext, "image/jpeg")

    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return data, media_type


def _pdf_first_page_to_image(file_path: str) -> str:
    """
    Convert the first page of a PDF to a PNG image.
    Saves it next to the original file and returns the new path.
    Requires: pdf2image + poppler installed.
    """
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
        if not images:
            raise ValueError("PDF has no pages.")
        output_path = file_path.replace(".pdf", "_page1.png")
        images[0].save(output_path, "PNG")
        return output_path
    except ImportError:
        raise RuntimeError(
            "pdf2image is not installed or poppler is missing. "
            "Please upload a JPG or PNG image instead of a PDF."
        )


# ─────────────────────────────────────────────────────────────────
# Main extraction function
# ─────────────────────────────────────────────────────────────────

def extract_grades_from_image(file_path: str) -> Dict[str, Any]:
    """
    Send a marksheet image to GPT-4o Vision and extract grades.

    Args:
        file_path: Path to the uploaded file (image or PDF)

    Returns:
        A dict with keys: student_name, student_id, semester, grades, raw_summary
        On failure: {"error": "human readable message"}
    """
    try:
        # Handle PDF — convert first page to image
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            try:
                file_path = _pdf_first_page_to_image(file_path)
            except RuntimeError as e:
                return {"error": str(e)}

        # Validate file exists
        if not Path(file_path).exists():
            return {"error": "Uploaded file not found on server."}

        # Convert to base64
        b64_data, media_type = _image_to_base64(file_path)

        # Call GPT-4o Vision
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64_data}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        raw_output = response.choices[0].message.content.strip()

        # Strip markdown code fences if model wraps in them anyway
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            # Remove first and last lines (```json ... ```)
            lines = [l for l in lines if not l.startswith("```")]
            raw_output = "\n".join(lines).strip()

        # Parse JSON
        result = json.loads(raw_output)

        # Check if GPT reported it couldn't read the document
        if "error" in result:
            return {"error": result["error"]}

        # Normalize grades list
        grades = []
        for item in result.get("grades", []):
            grades.append({
                "subject":   str(item.get("subject", "Unknown")).strip(),
                "score":     float(item["score"]) if item.get("score") is not None else None,
                "max_score": float(item.get("max_score") or 100.0),
                "grade":     item.get("grade"),
            })

        return {
            "student_name": result.get("student_name"),
            "student_id":   result.get("student_id"),
            "semester":     result.get("semester"),
            "grades":       grades,
            "raw_summary":  result.get("raw_summary", ""),
        }

    except json.JSONDecodeError as e:
        logger.error(f"[extractor] JSON parse error: {e}. Raw output: {raw_output}")
        return {"error": "GPT returned an unexpected format. Please try uploading a clearer image."}

    except Exception as e:
        logger.error(f"[extractor] Unexpected error: {e}", exc_info=True)
        return {"error": f"Extraction failed: {str(e)}"}
