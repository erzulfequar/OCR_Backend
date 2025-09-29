import os
import json
import google.generativeai as genai

# ------------------------------
# Step 0: Configure Gemini AI
# ------------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ------------------------------
# Step 1: Standard keys for normalization
# ------------------------------
STANDARD_KEYS = {
    "InvoiceNumber": ["Invoice No.", "Doc No.", "Ref. No.", "Estimate No."],
    "InvoiceDate": ["Date", "Dated", "Estimate Date", "Bill Date"],
    "BuyerName": ["To", "Buyer (Bill to)", "Customer"],
    "BuyerAddress": ["Ship To", "Bill To Address"],
    "SellerName": ["From", "Vendor", "Supplier"],
    "SellerAddress": ["Dispatch From", "From Address"],
    "TotalAmount": ["Total InvAmt", "Grand Total", "Net Payable"],
    "Items": ["Items", "Line Items", "Products"],
    "Taxes": ["IGST", "CGST", "SGST", "VAT", "Tax"]
}

# ------------------------------
# Step 2: Extract invoice dynamically using Gemini AI
# ------------------------------
def extract_invoice_with_gemini(text: str):
    prompt = f"""
    You are a professional invoice parsing AI.
    Extract all fields from this invoice text dynamically.
    Include line item taxes, HSN/SAC, and totals.
    Return only valid JSON.
    Text to process:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "", 1).strip()
        data = json.loads(raw_text)
        return data
    except Exception as e:
        return {"error": str(e)}

# ------------------------------
# Step 3: Normalize JSON and preserve invoice fields
# ------------------------------
def normalize_invoice(raw_json, standard_keys):
    normalized = {}

    # Map top-level fields
    for std_key, synonyms in standard_keys.items():
        for syn in synonyms:
            if syn in raw_json:
                normalized[std_key] = raw_json[syn]
                break
        else:
            normalized[std_key] = None

    # Extract GSTINs if available
    normalized["SellerGSTIN"] = raw_json.get("GSTIN") or raw_json.get("GSTIN/UIN") or None
    normalized["BuyerGSTIN"] = raw_json.get("GSTIN/UIN >") or raw_json.get("GSTIN/UIN") or None

    # Process Items
    items = normalized.get("Items", [])
    normalized_items = []

    for item in items:
        # Preserve exact Rate and Quantity from invoice
        qty = item.get("quantity") or item.get("Quantity") or None
        rate = item.get("rate") or item.get("Rate") or item.get("Price") or None
        amt = item.get("taxable_amount") or item.get("Amount") or None

        # Convert to float if possible
        try:
            qty = float(str(qty).replace(",", "")) if qty else None
        except:
            qty = None
        try:
            amt = float(str(amt).replace(",", "")) if amt else None
        except:
            amt = None
        try:
            rate = float(str(rate).replace(",", "")) if rate else None
        except:
            rate = None

        # Line taxes dynamically (preserve GST if present)
        line_taxes = []
        tax_rate = item.get("tax_rate") or 0
        try:
            tax_rate = float(str(tax_rate).replace(",", ""))
        except:
            tax_rate = 0.0

        tax_amount = amt * (tax_rate / 100) if amt else None
        if tax_amount:
            line_taxes.append({"TaxName": "GST", "TaxRate": tax_rate, "TaxAmount": tax_amount})

        line_total = (amt or 0.0) + (tax_amount or 0.0)

        normalized_items.append({
            "Description": item.get("description"),
            "HSN/SAC": item.get("hsn_sac"),
            "Quantity": qty,
            "Rate": rate,
            "LineSubtotal": amt,
            "LineTaxes": line_taxes,
            "LineTotal": line_total
        })

    normalized["Items"] = normalized_items

    # Document-level taxes dynamically
    taxes = {}
    for key, value in raw_json.items():
        if key.upper() in ["CGST", "SGST", "IGST", "VAT", "TAX"]:
            try:
                taxes[key.upper()] = float(str(value).replace(",", ""))
            except:
                taxes[key.upper()] = 0.0
    normalized["Taxes"] = taxes

    return normalized

# ------------------------------
# Step 4: Example usage
# ------------------------------
if __name__ == "__main__":
    invoice_text = "<PASTE YOUR INVOICE TEXT HERE>"

    # Extract dynamic JSON
    dynamic_json = extract_invoice_with_gemini(invoice_text)
    print("Dynamic JSON:\n", json.dumps(dynamic_json, indent=2))

    # Normalize JSON for ERP
    normalized_json = normalize_invoice(dynamic_json, STANDARD_KEYS)
    print("\nNormalized JSON (ERP-ready):\n", json.dumps(normalized_json, indent=2))
