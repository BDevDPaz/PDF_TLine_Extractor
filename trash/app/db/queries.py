from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, text
from app.db.database import get_db_session
from app.db.models import Call, Message, DataUsage
import logging

logger = logging.getLogger(__name__)

def has_data() -> bool:
    """Check if there's any data in the database"""
    session = get_db_session()
    try:
        call_count = session.query(Call).count()
        message_count = session.query(Message).count()
        data_usage_count = session.query(DataUsage).count()
        return (call_count + message_count + data_usage_count) > 0
    finally:
        session.close()

def get_all_data() -> dict:
    """Get all data for the original analyzer (legacy compatibility)"""
    session = get_db_session()
    try:
        calls = session.query(Call).all()
        messages = session.query(Message).all()
        data_usage = session.query(DataUsage).all()
        
        return {
            "calls": [
                {
                    "timestamp": call.timestamp.isoformat(),
                    "call_type": call.call_type,
                    "phone_number": call.phone_number,
                    "description": call.description,
                    "duration_minutes": call.duration_minutes,
                    "source_file": call.source_file
                }
                for call in calls
            ],
            "messages": [
                {
                    "timestamp": message.timestamp.isoformat(),
                    "message_type": message.message_type,
                    "contact": message.contact,
                    "destination": message.destination,
                    "format": message.format,
                    "source_file": message.source_file
                }
                for message in messages
            ],
            "data_usage": [
                {
                    "timestamp": usage.timestamp.isoformat(),
                    "data_type": usage.data_type,
                    "mb_used": usage.mb_used,
                    "source_file": usage.source_file
                }
                for usage in data_usage
            ]
        }
    finally:
        session.close()

def get_summary_data() -> dict:
    """Get summary statistics for dashboard"""
    session = get_db_session()
    try:
        call_count = session.query(Call).count()
        message_count = session.query(Message).count()
        data_usage_count = session.query(DataUsage).count()
        
        total_call_minutes = session.query(func.sum(Call.duration_minutes)).scalar() or 0
        total_mb_used = session.query(func.sum(DataUsage.mb_used)).scalar() or 0.0
        
        unique_files = set()
        for call in session.query(Call.source_file).distinct():
            unique_files.add(call.source_file)
        for message in session.query(Message.source_file).distinct():
            unique_files.add(message.source_file)
        for data in session.query(DataUsage.source_file).distinct():
            unique_files.add(data.source_file)
        
        return {
            "total_calls": call_count,
            "total_messages": message_count,
            "total_data_records": data_usage_count,
            "total_call_minutes": int(total_call_minutes),
            "total_mb_used": round(total_mb_used, 2),
            "unique_files": len(unique_files)
        }
    finally:
        session.close()

def get_chronological_data(page: int = 1, per_page: int = 25, file_filter: str = 'all') -> dict:
    """
    Get chronologically sorted data with pagination and file filtering
    
    Args:
        page: Page number (1-based)
        per_page: Number of items per page (25, 50, or 100)
        file_filter: 'all' for consolidated view or specific filename for individual file
        
    Returns:
        Dictionary with paginated chronological data and metadata
    """
    session = get_db_session()
    
    try:
        # Build unified query using UNION ALL
        calls_query = session.query(
            Call.timestamp,
            Call.source_file,
            text("'call' as event_type"),
            Call.call_type.label('type_detail'),
            Call.phone_number.label('contact_info'),
            Call.description,
            Call.duration_minutes.label('numeric_value'),
            text("NULL as format_info")
        )
        
        messages_query = session.query(
            Message.timestamp,
            Message.source_file,
            text("'message' as event_type"),
            Message.message_type.label('type_detail'),
            Message.contact.label('contact_info'),
            Message.destination.label('description'),
            text("NULL as numeric_value"),
            Message.format.label('format_info')
        )
        
        data_query = session.query(
            DataUsage.timestamp,
            DataUsage.source_file,
            text("'data_usage' as event_type"),
            DataUsage.data_type.label('type_detail'),
            text("'System' as contact_info"),
            text("'Mobile Internet Usage' as description"),
            DataUsage.mb_used.label('numeric_value'),
            text("'MB' as format_info")
        )
        
        # Apply file filter if specified
        if file_filter != 'all':
            calls_query = calls_query.filter(Call.source_file == file_filter)
            messages_query = messages_query.filter(Message.source_file == file_filter)
            data_query = data_query.filter(DataUsage.source_file == file_filter)
        
        # Combine all queries
        combined_query = calls_query.union_all(messages_query, data_query)
        
        # Order by timestamp descending (most recent first)
        combined_query = combined_query.order_by(text('timestamp DESC'))
        
        # Get total count for pagination
        count_query = combined_query.subquery()
        total_records = session.query(func.count()).select_from(count_query).scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        results = combined_query.offset(offset).limit(per_page).all()
        
        # Convert results to dictionaries
        events = []
        for result in results:
            event = {
                'timestamp': result.timestamp.isoformat(),
                'source_file': result.source_file,
                'event_type': result.event_type,
                'type_detail': result.type_detail,
                'contact_info': result.contact_info,
                'description': result.description,
                'numeric_value': result.numeric_value,
                'format_info': result.format_info
            }
            events.append(event)
        
        # Calculate pagination metadata
        total_pages = (total_records + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Calculate page blocks for navigation (groups of 5)
        current_block = ((page - 1) // 5) + 1
        total_blocks = ((total_pages - 1) // 5) + 1
        block_start = ((current_block - 1) * 5) + 1
        block_end = min(current_block * 5, total_pages)
        
        return {
            'events': events,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_records': total_records,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None,
                'current_block': current_block,
                'total_blocks': total_blocks,
                'block_start': block_start,
                'block_end': block_end,
                'has_prev_block': current_block > 1,
                'has_next_block': current_block < total_blocks
            },
            'filter': {
                'file_filter': file_filter,
                'is_filtered': file_filter != 'all'
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_chronological_data: {e}")
        raise e
    finally:
        session.close()

def get_available_files() -> list[str]:
    """Get list of all unique source files in the database"""
    session = get_db_session()
    try:
        files = set()
        
        # Get files from all tables
        for call in session.query(Call.source_file).distinct():
            files.add(call.source_file)
        for message in session.query(Message.source_file).distinct():
            files.add(message.source_file)
        for data in session.query(DataUsage.source_file).distinct():
            files.add(data.source_file)
        
        return sorted(list(files))
        
    finally:
        session.close()
