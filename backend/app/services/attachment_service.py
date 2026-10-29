import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# PDF Parser using fitz (PyMuPDF) or pypdf
def parse_pdf(file_path: str) -> Dict[str, Any]:
    text_content = []
    extracted_items = []
    
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text_content.append(text)
        doc.close()
    except Exception:
        # Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        except Exception as e:
            text_content.append(f"Error reading PDF: {str(e)}")

    full_text = "\n".join(text_content)
    return {
        "text": full_text,
        "items": extract_tabular_items_from_text(full_text)
    }

# Excel Parser (.xlsx, .xls)
def parse_excel(file_path: str) -> Dict[str, Any]:
    text_content = []
    extracted_items = []
    
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            text_content.append(f"--- Sheet: {sheet_name} ---")
            
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue

            # Look for header row
            header_idx = -1
            headers = []
            for idx, row in enumerate(rows[:15]):
                row_str = [str(c or "").lower() for c in row]
                if any(k in row_str for k in ["item", "description", "qty", "quantity", "po", "booking"]):
                    header_idx = idx
                    headers = [str(c or "").strip() for c in row]
                    break
            
            if header_idx != -1 and header_idx + 1 < len(rows):
                for row in rows[header_idx + 1:]:
                    if not any(row):
                        continue
                    item = {}
                    for col_idx, val in enumerate(row):
                        if col_idx < len(headers) and headers[col_idx]:
                            h = headers[col_idx].lower()
                            v = val if val is not None else ""
                            if any(k in h for k in ["item", "code", "style", "ref"]):
                                item["item_code"] = str(v)
                            elif any(k in h for k in ["desc", "detail", "particular"]):
                                item["description"] = str(v)
                            elif any(k in h for k in ["color", "colour", "shade"]):
                                item["color"] = str(v)
                            elif any(k in h for k in ["size", "dimension"]):
                                item["size"] = str(v)
                            elif any(k in h for k in ["qty", "quantity"]):
                                try:
                                    item["quantity"] = float(str(v).replace(",", ""))
                                except ValueError:
                                    item["quantity"] = 0.0
                            elif any(k in h for k in ["rate", "price", "unit price"]):
                                try:
                                    item["unit_price"] = float(str(v).replace("$", "").replace(",", ""))
                                except ValueError:
                                    item["unit_price"] = 0.0
                    
                    if item.get("quantity", 0) > 0 or item.get("description") or item.get("item_code"):
                        item["total_price"] = round(item.get("quantity", 0) * item.get("unit_price", 0.0), 2)
                        extracted_items.append(item)

            # Dump as readable text lines
            for r in rows:
                row_vals = [str(v) for v in r if v is not None]
                if row_vals:
                    text_content.append(" | ".join(row_vals))

    except Exception as e:
        text_content.append(f"Error parsing Excel: {str(e)}")

    return {
        "text": "\n".join(text_content),
        "items": extracted_items
    }

# Word Parser (.docx)
def parse_docx(file_path: str) -> Dict[str, Any]:
    text_content = []
    extracted_items = []
    
    try:
        import docx
        doc = docx.Document(file_path)
        for p in doc.paragraphs:
            if p.text.strip():
                text_content.append(p.text.strip())
        
        for table in doc.tables:
            for row in table.rows:
                row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_vals:
                    text_content.append(" | ".join(row_vals))
    except Exception as e:
        text_content.append(f"Error parsing DOCX: {str(e)}")

    full_text = "\n".join(text_content)
    return {
        "text": full_text,
        "items": extract_tabular_items_from_text(full_text)
    }

# CSV Parser
def parse_csv(file_path: str) -> Dict[str, Any]:
    import csv
    text_content = []
    extracted_items = []
    
    try:
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if any(row):
                    text_content.append(" | ".join(row))
    except Exception as e:
        text_content.append(f"Error parsing CSV: {str(e)}")

    full_text = "\n".join(text_content)
    return {
        "text": full_text,
        "items": extract_tabular_items_from_text(full_text)
    }

# Universal line items extractor from text blocks
def extract_tabular_items_from_text(text: str) -> List[Dict[str, Any]]:
    items = []
    # Match patterns like: "Item / Style: XYZ-123 Qty: 500 Price: 1.25"
    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        qty_match = re.search(r'\b(?:qty|quantity)\s*[:=\-]?\s*([\d,]+(?:\.\d+)?)\b', line_clean, re.IGNORECASE)
        price_match = re.search(r'\b(?:price|rate|cost)\s*[:=\-]?\s*\$?([\d,]+(?:\.\d+)?)\b', line_clean, re.IGNORECASE)
        
        if qty_match:
            try:
                qty = float(qty_match.group(1).replace(",", ""))
                unit_price = float(price_match.group(1).replace(",", "")) if price_match else 0.0
                
                # Check for item code / description in line
                item_code = ""
                code_match = re.search(r'\b(?:item|code|style|ref)\s*[:=\-#]?\s*([A-Za-z0-9\-_]+)', line_clean, re.IGNORECASE)
                if code_match:
                    item_code = code_match.group(1)
                
                items.append({
                    "item_code": item_code or "ITEM-1",
                    "description": line_clean[:120],
                    "quantity": qty,
                    "unit": "PCS",
                    "unit_price": unit_price,
                    "total_price": round(qty * unit_price, 2)
                })
            except Exception:
                pass
    return items

def process_attachment(file_path: str) -> Dict[str, Any]:
    """Inspect file extension and extract text and items."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".xlsx", ".xls"]:
        return parse_excel(file_path)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_path)
    elif ext in [".csv", ".tsv"]:
        return parse_csv(file_path)
    else:
        return {"text": "", "items": []}
