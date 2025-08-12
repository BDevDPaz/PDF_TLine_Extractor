import re
from dateutil.parser import parse
import os
import logging

logger = logging.getLogger(__name__)

def extract_message_data(text: str, filepath: str) -> list[dict]:
    """
    Extract message data from PDF text using regex patterns
    
    Args:
        text: Full text extracted from PDF
        filepath: Path to the source PDF file
        
    Returns:
        List of message record dictionaries
    """
    pattern = re.compile(
        r"(Jul|Aug|Jun)\s+(\d{1,2})\s+"
        r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s+"
        r"(IN|OUT)\s+((?:\(\d{3}\)\s)?\d{3,})\s+"
        r"(.+?)\s+"
        r"(TXT|PIC)\n",
        re.MULTILINE
    )
    
    matches = pattern.finditer(text)
    messages = []
    current_year = "2024"
    
    for match in matches:
        month, day, time, msg_type, who, destination, msg_format = match.groups()
        try:
            date_str = f"{month} {day}, {current_year} {time}"
            full_date = parse(date_str)
            
            messages.append({
                "timestamp": full_date,
                "message_type": "Recibido" if msg_type == "IN" else "Enviado",
                "contact": who.strip(),
                "destination": destination.strip(),
                "format": msg_format,
                "source_file": os.path.basename(filepath)
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse message record: {match.group(0)} - {e}")
            continue
    
    logger.info(f"Extracted {len(messages)} message records from {os.path.basename(filepath)}")
    return messages
