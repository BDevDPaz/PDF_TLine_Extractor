import re
from dateutil.parser import parse
import os
import logging

logger = logging.getLogger(__name__)

def extract_call_data(text: str, filepath: str) -> list[dict]:
    """
    Extract call data from PDF text using regex patterns
    
    Args:
        text: Full text extracted from PDF
        filepath: Path to the source PDF file
        
    Returns:
        List of call record dictionaries
    """
    pattern = re.compile(
        r"(Jul|Aug|Jun)\s+(\d{1,2})\s+"
        r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s+"
        r"(IN|OUT)\s+\((.+?)\)\s+"
        r"(.+?)\s+"
        r"([A-Z])?\s+"
        r"(\d+)\n",
        re.MULTILINE
    )
    
    matches = pattern.finditer(text)
    calls = []
    current_year = "2024"
    
    for match in matches:
        month, day, time, call_type, phone, desc, type_code, minutes = match.groups()
        try:
            date_str = f"{month} {day}, {current_year} {time}"
            full_date = parse(date_str)
            
            calls.append({
                "timestamp": full_date,
                "call_type": "Recibida" if call_type == "IN" else "Realizada",
                "phone_number": phone,
                "description": desc.strip(),
                "duration_minutes": int(minutes),
                "source_file": os.path.basename(filepath)
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse call record: {match.group(0)} - {e}")
            continue
    
    logger.info(f"Extracted {len(calls)} call records from {os.path.basename(filepath)}")
    return calls
