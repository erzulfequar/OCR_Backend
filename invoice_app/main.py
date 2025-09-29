from fastapi import FastAPI, UploadFile, File, HTTPException
import os, shutil
from invoice_app.ocr_utils import extract_text
from invoice_app.gemini_helper import extract_invoice_with_gemini
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# ✅ FastAPI init
app = FastAPI(title="Invoice OCR + Gemini API")

# ✅ Gemini key manually (abhi env ka jhanjhat nahi)
genai.configure(api_key="AIzaSyAjHk30Lt_CNEYQN9150Jjmg4fYztmtG38")

# ✅ CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- API: Upload Invoice & Get JSON ----------
@app.post("/process-invoice/")
async def process_invoice(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Step 1: OCR extract
        text = extract_text(file_path)

        # Step 2: Gemini JSON extract
        structured_data = extract_invoice_with_gemini(text)

        if not structured_data or "error" in structured_data:
            raise Exception(structured_data.get("error", "Failed to extract JSON"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR/Gemini Error: {e}")

    return structured_data
