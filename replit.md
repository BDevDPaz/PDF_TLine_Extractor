# Overview

This is a PDF data extraction and analysis application built with Flask that processes telecommunications billing PDFs to extract call logs, message history, and data usage information. The system provides a comprehensive dashboard with multiple tools for uploading, analyzing, visualizing, and note-taking on extracted data. It integrates with Google's Gemini AI for intelligent content generation and uses a SQLite database for data persistence.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

The application uses a multi-page web interface built with:
- **Bootstrap 5 with dark theme** for responsive UI components
- **Vanilla JavaScript** for client-side interactions and API calls
- **Chart.js** for data visualizations and charts
- **AG-Grid Community** for advanced data table functionality
- **Feather Icons** for consistent iconography

The frontend is organized into four main sections:
- Welcome page serving as a dashboard hub
- Upload interface for PDF file processing
- Data analyzer with interactive charts and tables
- Notes application with AI integration
- PDF viewer for document inspection

## Backend Architecture

### Web Framework
- **Flask** as the primary web framework with template rendering
- **Werkzeug** for secure file upload handling
- Session-based security with configurable secret keys

### Data Processing Pipeline
The system implements a sophisticated PDF processing workflow:

1. **File Upload Handler**: Secures uploaded PDFs in the `data/raw` directory
2. **Main Extractor**: Orchestrates the entire extraction process using `pdfplumber` for PDF text extraction
3. **Specialized Extractors**: Three dedicated regex-based extractors for different data types:
   - Call extractor for phone call records
   - Message extractor for SMS/text message logs
   - Data usage extractor for mobile internet consumption
4. **Data Integrity Management**: Implements transaction-based processing with automatic rollback on errors

### Database Design
Uses **SQLite** with SQLAlchemy ORM featuring three main entities:
- `calls` table: Phone call records with timestamps, types, numbers, descriptions, and durations
- `messages` table: Message logs with contact information, message types, and formats
- `data_usage` table: Mobile internet usage records with consumption metrics

The database includes source file tracking for data lineage and supports complete record replacement per source file to maintain data consistency.

### API Structure
RESTful endpoints provide JSON data for the frontend:
- `/api/data` - Complete dataset retrieval
- `/api/summary` - Aggregated statistics and metrics
- `/api/chronological` - Paginated timeline data with filtering
- `/upload` - File processing endpoint

## External Dependencies

### AI Integration
- **Google Generative AI (Gemini 1.5 Flash)** for intelligent content generation in the notes application
- API key configured through environment variables (`GOOGLE_API_KEY`)
- Error handling for API failures and missing configuration

### Python Libraries
- **pdfplumber**: Advanced PDF text extraction with support for complex layouts
- **SQLAlchemy**: Database ORM with declarative base for model definitions
- **pandas**: Data manipulation and cleaning with DataFrame operations
- **dateutil**: Flexible date parsing for various timestamp formats
- **tqdm**: Progress indication during batch PDF processing

### Frontend CDN Dependencies
- Bootstrap 5 with Replit's dark theme customizations
- Chart.js for interactive data visualizations
- AG-Grid Community for advanced table features
- Feather Icons for UI consistency

The system is designed for deployment on Replit with automatic dependency management through `pyproject.toml` and includes comprehensive error handling, logging, and data validation throughout the processing pipeline.