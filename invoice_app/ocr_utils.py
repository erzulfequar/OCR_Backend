import os
from .gemini_helper import extract_invoice_with_gemini
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

# --------------------------
# Tesseract & Poppler Config
# --------------------------
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
POPPLER_PATH = r"C:\poppler\poppler-25.07.0\Library\bin"



# --------------------------
# OCR fallback functions
# --------------------------
def ocr_image(image_path, lang="eng"):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang=lang).strip()
    except Exception as e:
        return f"❌ OCR Error: {e}"


def ocr_pdf(pdf_path, lang="eng"):
    text = ""
    try:
        # Try PyMuPDF text extraction first
        doc = fitz.open(pdf_path)
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"

        # Fallback to OCR if no text found
        if not text.strip():
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH, dpi=300)
            for img in images:
                text += pytesseract.image_to_string(img, lang=lang) + "\n"
    except Exception as e:
        return f"❌ OCR PDF Error: {e}"

    return text.strip() or "❌ No text found via OCR"


# --------------------------
# Universal extractor
# --------------------------
def extract_text(file_path, lang="eng"):
    """
    Universal extractor for PDFs and images.
    1. Uses Gemini first.
    2. Falls back to OCR if Gemini fails.
    Returns structured JSON ready for table display.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        return {"error": "❌ Unsupported file format. Please upload JPG, PNG, or PDF."}

    try:
        # First, try Gemini
        data = extract_invoice_with_gemini(file_path)

        # Check if Gemini returned valid items
        if not data.get("items") or len(data["items"]) == 0:
            # Fallback to OCR
            if ext == ".pdf":
                raw_text = ocr_pdf(file_path, lang=lang)
            else:
                raw_text = ocr_image(file_path, lang=lang)

            # Return OCR result as a single item for table
            data = {
                "items": [{"description": raw_text}],
                "invoice_no": None,
                "date": None,
                "bill_to": None,
                "ship_to": None,
                "subtotal": None,
                "cgst": None,
                "sgst": None,
                "total": None
            }

        return data

    except Exception as e:
        return {"error": f"Extractor failed: {e}"}
