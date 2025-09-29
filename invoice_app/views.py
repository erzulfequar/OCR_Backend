from django.shortcuts import render
from .forms import DocumentForm
from .ocr_utils import extract_text
from .gemini_helper import extract_invoice_with_gemini

import os
from django.conf import settings


# ------------------------------
# Existing HTML upload view
# ------------------------------
def upload_document(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            file_path = document.file.path
            structured_data = None
            try:
                text = extract_text(file_path)
                structured_data = extract_invoice_with_gemini(text)
            except Exception as e:
                print("OCR/Gemini Error:", e)
            return render(request, "result.html", {"structured_data": structured_data})
    else:
        form = DocumentForm()

    return render(request, "upload.html", {"form": form})
