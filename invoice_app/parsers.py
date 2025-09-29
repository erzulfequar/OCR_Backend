import re
from decimal import Decimal
import dateutil.parser

# ---------------------- Helpers ---------------------- #
def parse_amount(text):
    """Extract the last number in text as amount"""
    matches = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b', text)
    return float(Decimal(matches[-1].replace(',', ''))) if matches else 0.0

def clean_text(text):
    """Remove unwanted chars and normalize spaces"""
    text = re.sub(r'[\|\{\}\[\]]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_date(text):
    try:
        dt = dateutil.parser.parse(text, fuzzy=True, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
    except:
        return None

# ---------------------- Main Parser ---------------------- #
def parse_bill(text: str):
    data = {
        "invoice_no": None,
        "date": None,
        "from": None,
        "to": None,
        "items": [],
        "taxes": {"cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst_total": 0.0},
        "total": 0.0,
    }

    # ---------------- Invoice Number ---------------- #
    invoice_synonyms = r"(Invoice|Bill|Est|Estimate|Quotation|Quote|Ref No|Receipt|Tax Invoice|estimate date)"
    inv = re.search(invoice_synonyms + r"[^\d]*(\d+)", text, re.IGNORECASE)
    if inv:
        data["invoice_no"] = inv.group(1)

    # ---------------- Date ---------------- #
    date_synonyms = r"(Date|Invoice Date|Billing Date|Date of Issue|Due Date)"
    date_matches = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\w{3,9}\s+\d{1,2},?\s+\d{2,4}\b", text)
    if date_matches:
        data["date"] = parse_date(date_matches[0])

    # ---------------- From / To ---------------- #
    company_match = re.search(r"(?:Ltd|Private|Pvt|LLP|Inc|Technologies).*", text, re.IGNORECASE)
    if company_match:
        gst = re.search(r"GSTIN[:\s]*([0-9A-Z]{15})", text, re.IGNORECASE)
        gst_text = f", GSTIN: {gst.group(1)}" if gst else ""
        data["from"] = company_match.group(0).strip() + gst_text

    bill_to_match = re.search(r"(Bill\s*To|Customer|Client)[:\-]?\s*(.*?)(?=(Ship\s*To|$))", text, re.DOTALL | re.IGNORECASE)
    if bill_to_match:
        data["to"] = clean_text(bill_to_match.group(2))

    # ---------------- Items ---------------- #
    items = []
    lines = text.splitlines()
    current_item = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        qty_match = re.search(r"\b\d+(?:\.\d+)?\b", line)
        amt_match = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?", line)

        if qty_match and amt_match:
            if current_item:
                items.append(current_item)

            amt = parse_amount(line)
            current_item = {
                "description": clean_text(line),
                "quantity": float(qty_match.group(0)),
                "rate": amt,
                "amount": amt,
            }
    if current_item:
        items.append(current_item)
    data["items"] = items

    # ---------------- Taxes ---------------- #
    tax_synonyms = {
        "cgst": r"(CGST|Central GST|Central Tax)",
        "sgst": r"(SGST|State GST|State Tax)",
        "igst": r"(IGST|Integrated GST|Integrated Tax)",
    }
    for key, pattern in tax_synonyms.items():
        match = re.search(pattern + r"[:\s]*([\d,]+\.\d{1,2}|\d+)", text, re.IGNORECASE)
        data["taxes"][key] = float(match.group(1).replace(',', '')) if match else 0.0
    data["taxes"]["gst_total"] = data["taxes"]["cgst"] + data["taxes"]["sgst"] + data["taxes"]["igst"]

    # ---------------- Total ---------------- #
    total_synonyms = r"(Total|Grand Total|Amount Payable|Net Amount)"
    total_match = re.search(total_synonyms + r"[:\s]*([\d,]+\.\d{1,2}|\d+)", text, re.IGNORECASE)
    if total_match:
        data["total"] = float(total_match.group(1).replace(',', ''))
    else:
        subtotal = sum(item["amount"] for item in items)
        data["total"] = subtotal + data["taxes"]["gst_total"]

    return data
