import re
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from app.services.attachment_service import extract_tabular_items_from_text

ORDER_KEYWORDS = [
    "order", "booking", "purchase order", "po#", "po-", "p.o.", "requisition",
    "elastic booking", "thread booking", "fabric booking", "accessories booking",
    "delivery", "proforma", "pi#", "buyer"
]

def is_order_email(subject: str, body: str = "") -> bool:
    """Heuristic check whether an email is likely a customer order/booking email."""
    text = f"{subject or ''} {body or ''}".lower()
    return any(keyword in text for keyword in ORDER_KEYWORDS)

def clean_extracted_value(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    val = val.strip().strip(" :;,-&_#./\"'")
    return val if val else None

def extract_subject_details(subject: str) -> Dict[str, Optional[str]]:
    """
    Intelligently extracts:
    - order_type (e.g. 'Elastic Booking')
    - booking_number (e.g. 'CCKL-01734/26')
    - po_number (e.g. 'PO-2100011291')
    - buyer_name (e.g. 'VDE')
    
    Specifically tuned for patterns like:
    "Elastic booking for CCKL-01734/26& PO-2100011291 of VDE buyer"
    as well as numerous industry variants.
    """
    if not subject:
        return {
            "order_type": None,
            "booking_number": None,
            "po_number": None,
            "buyer_name": None
        }

    sub_clean = subject.strip()
    
    order_type = None
    booking_number = None
    po_number = None
    buyer_name = None

    # 1. Order Type Extraction
    type_match = re.search(
        r'\b(Elastic\s+booking|Sewing\s+thread\s+booking|Thread\s+booking|Fabric\s+booking|'
        r'Zipper\s+booking|Label\s+booking|Carton\s+booking|Accessories\s+booking|'
        r'Garment\s+order|Purchase\s+order|Work\s+order|Sample\s+order|Requisition\s+order|'
        r'Booking\s+sheet|Booking|Purchase\s+Order|PO)\b',
        sub_clean,
        re.IGNORECASE
    )
    if type_match:
        order_type = type_match.group(1).strip().title()
        if order_type.upper() == "PO":
            order_type = "Purchase Order"
    else:
        order_type = "Purchase Order"

    # 2. Buyer Extraction
    # Pattern A: "... of <BUYER> buyer" (e.g. "of VDE buyer")
    buyer_match_1 = re.search(r'\bof\s+([A-Za-z0-9\s&.\-]+?)\s+(?:buyer|customer)\b', sub_clean, re.IGNORECASE)
    # Pattern B: "... buyer: <BUYER>" or "Buyer - <BUYER>"
    buyer_match_2 = re.search(r'\b(?:buyer|customer|client)\s*[:\-]\s*([A-Za-z0-9\s&.\-]+?)(?:\s+(?:order|booking|po|\&|\/|$)|$)', sub_clean, re.IGNORECASE)
    # Pattern C: "for <BUYER> buyer"
    buyer_match_3 = re.search(r'\bfor\s+([A-Za-z0-9\s&.\-]+?)\s+(?:buyer|customer)\b', sub_clean, re.IGNORECASE)
    # Pattern D: "... of <BUYER>" at end of subject
    buyer_match_4 = re.search(r'\bof\s+([A-Za-z0-9\s&.\-]+)$', sub_clean, re.IGNORECASE)

    if buyer_match_1:
        buyer_name = clean_extracted_value(buyer_match_1.group(1))
    elif buyer_match_2:
        buyer_name = clean_extracted_value(buyer_match_2.group(1))
    elif buyer_match_3:
        buyer_name = clean_extracted_value(buyer_match_3.group(1))
    elif buyer_match_4 and len(buyer_match_4.group(1).split()) <= 4:
        buyer_name = clean_extracted_value(buyer_match_4.group(1))

    # 3. Booking Number Extraction
    # Handles: CCKL-01734/26, BK-2026-9901, CCKL/01734/26, Booking# 12345
    booking_patterns = [
        r'\b([A-Z]{2,6}-\d{3,8}/\d{2,4})\b',                        # e.g. CCKL-01734/26
        r'\b(?:booking|bk)[\s#:\-]*([A-Za-z0-9\-_/]+)\b',          # e.g. booking for CCKL-01734/26
        r'\b([A-Z]{2,5}\s*/\s*\d{3,8}/\d{2,4})\b',                 # e.g. CCKL/01734/26
        r'\b(BK[-_][A-Za-z0-9\-_]+)\b'                             # e.g. BK-2026-9901
    ]
    for pat in booking_patterns:
        m = re.search(pat, sub_clean, re.IGNORECASE)
        if m:
            val = clean_extracted_value(m.group(1))
            # avoid capturing words like "for", "of", "and"
            if val and not val.lower() in ["for", "of", "the", "and", "buyer", "booking"]:
                booking_number = val
                break

    # 4. Purchase Order (PO) Number Extraction
    # Handles: PO-2100011291, PO# 2100011291, PO - 450012, PO2100011291
    po_patterns = [
        r'\b(?:PO|P\.O\.|Purchase\s*Order)[\s#:\-_]*([A-Za-z0-9\-_]{4,25})\b',
        r'\b(PO-[A-Za-z0-9\-_]+)\b',
        r'\b([0-9]{8,12})\b' # Fallback standard 8-12 digit SAP/ERP PO numbers
    ]
    for pat in po_patterns:
        m = re.search(pat, sub_clean, re.IGNORECASE)
        if m:
            val = clean_extracted_value(m.group(1))
            if val and val != booking_number:
                # Format standard prefix if purely numeric
                po_number = f"PO-{val}" if (val.isdigit() and not val.startswith("PO-")) else val
                break

    return {
        "order_type": order_type,
        "booking_number": booking_number,
        "po_number": po_number,
        "buyer_name": buyer_name
    }

def extract_dates(text: str) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """Extract order date and delivery/shipment date from body text."""
    order_date = None
    delivery_date = None

    delivery_patterns = [
        r'\b(?:delivery\s*date|shipment\s*date|del\s*date|handover\s*date|ex-factory\s*date)[\s:=]+([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',
        r'\b(?:delivery|shipment)[\s:=]+([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4})'
    ]
    for pat in delivery_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            delivery_date = parse_date_string(m.group(1))
            if delivery_date:
                break

    order_date_patterns = [
        r'\b(?:order\s*date|booking\s*date|po\s*date|issue\s*date)[\s:=]+([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',
    ]
    for pat in order_date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            order_date = parse_date_string(m.group(1))
            if order_date:
                break

    return order_date, delivery_date

def parse_date_string(date_str: str) -> Optional[datetime.datetime]:
    from dateutil import parser
    try:
        return parser.parse(date_str, fuzzy=True)
    except Exception:
        return None

def extract_currency_and_totals(text: str) -> Tuple[str, float, float, str]:
    """Extract currency, total quantity, total amount, and unit."""
    currency = "USD"
    total_qty = 0.0
    total_amount = 0.0
    unit = "PCS"

    # Currency
    curr_match = re.search(r'\b(USD|EUR|GBP|BDT|CAD|AUD)\b|\$|€|£|৳', text, re.IGNORECASE)
    if curr_match:
        c = curr_match.group(0).upper()
        if c == "$": currency = "USD"
        elif c == "€": currency = "EUR"
        elif c == "£": currency = "GBP"
        elif c == "৳": currency = "BDT"
        else: currency = c

    # Unit
    unit_match = re.search(r'\b(PCS|YDS|MTR|DZ|SETS|KGS|LBS)\b', text, re.IGNORECASE)
    if unit_match:
        unit = unit_match.group(1).upper()

    # Total Qty
    qty_patterns = [
        r'\b(?:total\s*quantity|total\s*qty|order\s*qty|booking\s*qty)[\s:=]+([\d,]+(?:\.\d+)?)\b',
        r'\b(?:qty|quantity)[\s:=]+([\d,]+(?:\.\d+)?)\s*(?:pcs|yds|mtr|dz)?\b'
    ]
    for pat in qty_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                total_qty = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                pass

    # Total Amount
    amt_patterns = [
        r'\b(?:total\s*amount|grand\s*total|net\s*amount|total\s*price|total\s*value)[\s:=]+\$?\s*([\d,]+(?:\.\d+)?)\b',
        r'\b(?:amount|total)[\s:=]+\$?\s*([\d,]+(?:\.\d+)?)\b'
    ]
    for pat in amt_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                total_amount = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                pass

    return currency, total_qty, total_amount, unit

def parse_html_table_items(html_content: str) -> List[Dict[str, Any]]:
    """Extract line items from HTML tables inside email body."""
    items = []
    if not html_content:
        return items

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(["th", "td"])]
            if not any(k in " ".join(headers) for k in ["item", "qty", "quantity", "description", "style", "price"]):
                continue

            for row in rows[1:]:
                cells = [td.get_text().strip() for td in row.find_all(["td", "th"])]
                if not any(cells):
                    continue

                item = {}
                for idx, cell_val in enumerate(cells):
                    if idx < len(headers):
                        h = headers[idx]
                        if any(k in h for k in ["item", "code", "style", "ref"]):
                            item["item_code"] = cell_val
                        elif any(k in h for k in ["desc", "detail", "particular"]):
                            item["description"] = cell_val
                        elif any(k in h for k in ["color", "colour"]):
                            item["color"] = cell_val
                        elif any(k in h for k in ["size"]):
                            item["size"] = cell_val
                        elif any(k in h for k in ["qty", "quantity"]):
                            try:
                                item["quantity"] = float(cell_val.replace(",", ""))
                            except ValueError:
                                item["quantity"] = 0.0
                        elif any(k in h for k in ["price", "rate", "cost"]):
                            try:
                                item["unit_price"] = float(cell_val.replace("$", "").replace(",", ""))
                            except ValueError:
                                item["unit_price"] = 0.0

                if item.get("quantity", 0) > 0 or item.get("description") or item.get("item_code"):
                    item["unit"] = "PCS"
                    item["total_price"] = round(item.get("quantity", 0) * item.get("unit_price", 0.0), 2)
                    items.append(item)
    except Exception:
        pass

    return items

def compute_order_fingerprint(po: Optional[str], booking: Optional[str], buyer: Optional[str]) -> str:
    """Compute SHA-256 fingerprint for duplicate detection."""
    components = [
        (po or "").strip().lower(),
        (booking or "").strip().lower(),
        (buyer or "").strip().lower()
    ]
    raw_str = "|".join(components)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def extract_full_order(
    subject: str,
    body_plain: str = "",
    body_html: str = "",
    attachment_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Unified extraction pipeline:
    Analyzes Subject + Plain Body + HTML Content + Attachments.
    Cross-validates, calculates confidence score, and structures order & line items.
    """
    subject_info = extract_subject_details(subject)

    combined_text = f"{subject or ''}\n\n{body_plain or ''}"
    attachment_items = []
    
    if attachment_data:
        for att in attachment_data:
            att_text = att.get("text", "")
            if att_text:
                combined_text += f"\n\n--- Attachment: {att.get('file_name', '')} ---\n{att_text}"
            if att.get("items"):
                attachment_items.extend(att.get("items"))

    # Extract dates, currency, totals
    order_date, delivery_date = extract_dates(combined_text)
    currency, total_qty, total_amount, unit = extract_currency_and_totals(combined_text)

    # Line items from HTML table or plain text / attachments
    items = parse_html_table_items(body_html)
    if not items and attachment_items:
        items = attachment_items
    if not items:
        items = extract_tabular_items_from_text(combined_text)

    # If line items exist and total_qty was 0, aggregate from items
    if items:
        sum_qty = sum(item.get("quantity", 0.0) for item in items)
        sum_amt = sum(item.get("total_price", 0.0) for item in items)
        if total_qty == 0.0 and sum_qty > 0.0:
            total_qty = sum_qty
        if total_amount == 0.0 and sum_amt > 0.0:
            total_amount = sum_amt

    # Check for body-level PO / Booking if not in subject
    po_number = subject_info.get("po_number")
    booking_number = subject_info.get("booking_number")
    buyer_name = subject_info.get("buyer_name")
    order_type = subject_info.get("order_type") or "Purchase Order"

    if not po_number:
        body_po = re.search(r'\b(?:PO|P\.O\.|Purchase\s*Order)[\s#:\-_]*([A-Za-z0-9\-_]{4,25})\b', combined_text, re.IGNORECASE)
        if body_po:
            po_number = clean_extracted_value(body_po.group(1))

    if not booking_number:
        body_bk = re.search(r'\b(?:Booking|BK)[\s#:\-_]*([A-Za-z0-9\-_/]{4,25})\b', combined_text, re.IGNORECASE)
        if body_bk:
            booking_number = clean_extracted_value(body_bk.group(1))

    if not buyer_name:
        body_buyer = re.search(r'\b(?:Buyer|Customer)[\s:=]+([A-Za-z0-9\s&.\-]+?)(?:\r|\n|$)', combined_text, re.IGNORECASE)
        if body_buyer:
            buyer_name = clean_extracted_value(body_buyer.group(1))

    # Calculate Confidence Score (0.0 to 1.0)
    score = 0.0
    if po_number: score += 0.35
    if booking_number: score += 0.25
    if buyer_name: score += 0.20
    if total_qty > 0: score += 0.10
    if items: score += 0.10

    score = min(round(score, 2), 1.0)

    # Status Determination
    status = "CONFIRMED"
    if score < 0.60 or not po_number:
        status = "REVIEW_NEEDED"

    fingerprint = compute_order_fingerprint(po_number, booking_number, buyer_name)

    return {
        "po_number": po_number,
        "booking_number": booking_number,
        "buyer_name": buyer_name,
        "order_type": order_type,
        "order_date": order_date,
        "delivery_date": delivery_date,
        "total_quantity": total_qty,
        "quantity_unit": unit,
        "currency": currency,
        "total_amount": total_amount,
        "confidence_score": score,
        "status": status,
        "fingerprint": fingerprint,
        "items": items
    }
