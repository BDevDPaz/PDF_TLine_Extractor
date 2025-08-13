import pdfplumber
import pandas as pd
from tqdm import tqdm
import os
import logging
from app.db.database import get_db_session
from app.db.models import Call, Message, DataUsage
from .call_extractor import extract_call_data
from .message_extractor import extract_message_data
from .data_usage_extractor import extract_data_usage_data

logger = logging.getLogger(__name__)

def process_pdf_files(filepaths: list[str]) -> dict:
    """
    Process multiple PDF files and extract data with data integrity management
    
    Args:
        filepaths: List of file paths to process
        
    Returns:
        Dictionary with counts of extracted records by type
    """
    all_calls, all_messages, all_data_usage = [], [], []
    source_filenames = [os.path.basename(fp) for fp in filepaths]
    
    logger.info(f"Processing {len(filepaths)} PDF files: {source_filenames}")

    # Extract data from all PDFs
    for filepath in tqdm(filepaths, desc="Extrayendo datos de PDFs"):
        try:
            with pdfplumber.open(filepath) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text
                
                if not full_text:
                    logger.warning(f"No text extracted from {os.path.basename(filepath)}")
                    continue
                
                # Extract different types of data
                all_calls.extend(extract_call_data(full_text, filepath))
                all_messages.extend(extract_message_data(full_text, filepath))
                all_data_usage.extend(extract_data_usage_data(full_text, filepath))
                
        except Exception as e:
            logger.error(f"Error reading {os.path.basename(filepath)}: {e}")
            raise

    # Convert to DataFrames and remove duplicates
    calls_df = pd.DataFrame(all_calls).drop_duplicates().reset_index(drop=True)
    messages_df = pd.DataFrame(all_messages).drop_duplicates().reset_index(drop=True)
    data_usage_df = pd.DataFrame(all_data_usage).drop_duplicates().reset_index(drop=True)

    logger.info(f"Extracted: {len(calls_df)} calls, {len(messages_df)} messages, {len(data_usage_df)} data usage records")

    # Database transaction with integrity management
    session = get_db_session()
    try:
        # Delete existing records for the files being processed
        if source_filenames:
            deleted_calls = session.query(Call).filter(Call.source_file.in_(source_filenames)).delete(synchronize_session=False)
            deleted_messages = session.query(Message).filter(Message.source_file.in_(source_filenames)).delete(synchronize_session=False)
            deleted_data = session.query(DataUsage).filter(DataUsage.source_file.in_(source_filenames)).delete(synchronize_session=False)
            
            logger.info(f"Deleted existing records: {deleted_calls} calls, {deleted_messages} messages, {deleted_data} data usage")

        # Insert new records
        if not calls_df.empty:
            session.bulk_insert_mappings(Call, calls_df.to_dict(orient='records'))
        if not messages_df.empty:
            session.bulk_insert_mappings(Message, messages_df.to_dict(orient='records'))
        if not data_usage_df.empty:
            session.bulk_insert_mappings(DataUsage, data_usage_df.to_dict(orient='records'))
        
        session.commit()
        logger.info("Successfully committed all changes to database")
        
        return {
            "calls": len(calls_df),
            "messages": len(messages_df),
            "data_usage": len(data_usage_df)
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed, rolled back: {e}")
        raise e
    finally:
        session.close()
