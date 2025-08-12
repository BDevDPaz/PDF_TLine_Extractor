import re
from dateutil.parser import parse
import os
import logging

logger = logging.getLogger(__name__)

def extract_data_usage_data(text: str, filepath: str) -> list[dict]:
    """
    Extract data usage records from PDF text using regex patterns
    
    Args:
        text: Full text extracted from PDF
        filepath: Path to the source PDF file
        
    Returns:
        List of data usage record dictionaries
    """
    pattern = re.compile(
        r"(Jul|Aug|Jun)\s+(\d{1,2})\s+"
        r"Mobile Internet\s+"
        r"([\d,]+\.\d+)\n",
        re.MULTILINE
    )
    
    matches = pattern.finditer(text)
    data_usage = []
    current_year = "2024"
    
    for match in matches:
        month, day, mb_used = match.groups()
        try:
            date_str = f"{month} {day}, {current_year}"
            full_date = parse(date_str)
            
            # Remove commas and convert to float
            mb_used_clean = float(mb_used.replace(',', ''))
            
            data_usage.append({
                "timestamp": full_date,
                "data_type": "Mobile Internet",
                "mb_used": mb_used_clean,
                "source_file": os.path.basename(filepath)
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse data usage record: {match.group(0)} - {e}")
            continue
    
    logger.info(f"Extracted {len(data_usage)} data usage records from {os.path.basename(filepath)}")
    return data_usage
