# Overview

This is an AI-powered PDF data extraction and analysis application built with Flask that uses Google's Gemini AI to intelligently process telecommunications billing PDFs. The system extracts call logs, message history, and data usage information using advanced AI with JSON Schema validation. It features a mobile-style interface with navigation tabs, interactive data visualization, and an AI chat assistant that can answer questions about extracted data. The application uses SQLite for data persistence and provides comprehensive analysis tools.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

The application uses a single-page mobile-style interface built with:
- **TailwindCSS** for modern, responsive UI design
- **Vanilla JavaScript** for client-side interactions and API calls
- **Chart.js** for data visualizations (bar charts and pie charts)
- **AG-Grid Community** for advanced data table functionality
- **Lucide Icons** for consistent iconography
- **PDF.js** for in-browser PDF preview and page selection

The frontend is organized into five tab-based sections:
- Upload tab for PDF file selection
- Process tab with visual PDF page selector and AI extraction
- Data tab with searchable/filterable grid view
- Charts tab with interactive visualizations
- Chat tab for AI-powered Q&A about extracted data

## Backend Architecture

### Web Framework
- **Flask** as the primary web framework with template rendering
- **Werkzeug** for secure file upload handling
- Session-based security with configurable secret keys

### Hybrid AI-Powered Data Processing Pipeline
The system implements a robust hybrid PDF processing workflow:

1. **File Upload Handler**: Secures uploaded PDFs in the `data` directory
2. **Hybrid Processor Module**: Uses Google Gemini AI with regex fallback for maximum reliability
3. **Intelligent Data Extraction**: 
   - Primary: AI analyzes PDF content in optimized chunks to avoid timeouts
   - Fallback: Advanced regex patterns for reliable extraction when AI fails
   - Extracts call records, message logs, and data usage with timestamps
4. **Chat Assistant**: AI-powered conversational interface for querying extracted data
5. **Data Integrity Management**: Transaction-based processing with automatic rollback on errors
6. **Timeout Protection**: Chunked processing and strict limits prevent worker crashes

### Database Design
Uses **SQLite** with SQLAlchemy ORM featuring a unified data model:
- `extracted_data` table: Unified storage for all event types with fields:
  - `phone_line`: The telephone line associated with the event
  - `event_type`: Type of event (Llamada/Mensaje/Datos)
  - `timestamp`: Date and time of the event
  - `direction`: IN/OUT for calls and messages
  - `contact`: Phone number or contact information
  - `description`: Additional details about the event
  - `value`: Numeric or text value (minutes, MB, format)

The database includes source file tracking for data lineage and supports complete record replacement per source file to maintain data consistency.

### API Structure
RESTful endpoints provide JSON data for the frontend:
- `/api/upload` - PDF file upload endpoint
- `/api/process` - AI-powered data extraction endpoint
- `/api/get-data` - Complete dataset retrieval
- `/api/export-csv` - CSV export functionality
- `/api/chat` - AI chat assistant endpoint for Q&A

## External Dependencies

### AI Integration
- **Google Generative AI (Gemini 1.5 Flash)** with multiple AI capabilities:
  - Intelligent PDF data extraction using JSON Schema validation
  - Context-aware chat assistant for data analysis
  - Structured data extraction with Pydantic models
- **google-generativeai SDK** with hybrid approach: AI + regex fallback for maximum reliability
- API key configured through environment variables (`GOOGLE_API_KEY`)
- Comprehensive error handling for API failures

### Python Libraries
- **pdfplumber**: Advanced PDF text extraction with support for complex layouts
- **SQLAlchemy**: Database ORM with declarative base for model definitions
- **pandas**: Data manipulation and cleaning with DataFrame operations
- **dateutil**: Flexible date parsing for various timestamp formats
- **google-generativeai**: Official Google Generative AI SDK for Gemini models
- **pydantic**: Data validation and JSON Schema generation for AI responses

### Frontend CDN Dependencies
- Bootstrap 5 with Replit's dark theme customizations
- Chart.js for interactive data visualizations
- AG-Grid Community for advanced table features
- Feather Icons for UI consistency

The system is designed for deployment on Replit with automatic dependency management through `pyproject.toml` and includes comprehensive error handling, logging, and data validation throughout the processing pipeline.