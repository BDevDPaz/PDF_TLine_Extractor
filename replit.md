# Overview

This is an advanced AI-powered PDF data extraction and analysis application built with Flask that combines multiple extraction methods for optimal accuracy while maintaining complete user privacy. The system uses enhanced regex patterns (based on proven telecommunications bill processors) as the primary extraction method, with Google's Gemini AI as intelligent fallback. It processes telecommunications billing PDFs to extract call logs, message history, and data usage information with discrete processing that ensures user data privacy. The application features a mobile-style interface with privacy-focused design, advanced filtering system, anonymization options, discrete data visualization, AI chat assistant with direct PDF upload capability, and comprehensive privacy-safe analysis tools. Uses SQLite for data persistence with transaction-based integrity management and secure data handling.

# User Preferences

- **Preferred communication style**: Simple, everyday language
- **Privacy Priority**: Complete privacy protection - user data must be processed discretely without developer visibility
- **Quality over Sophistication**: Extraction accuracy more important than AI complexity
- **Workflow Requirements**: Complete redesign from start to finish with focus on efficiency and user discretion
- **Interface Requirements**: Discrete data access with advanced filtering and secure export options

# System Architecture

## Frontend Architecture

The application uses a mobile-style interface with privacy-first design built with:
- **TailwindCSS** for modern, responsive UI design with discrete styling
- **Vanilla JavaScript** for client-side interactions and secure API calls
- **Chart.js** for privacy-focused data visualizations showing aggregated patterns
- **AG-Grid Community** for advanced data table with filtering capabilities
- **Lucide Icons** for consistent iconography including privacy indicators
- **PDF.js** for in-browser PDF preview and page selection

The frontend is organized into five tab-based sections with privacy enhancements:
- **Upload tab**: Secure PDF file selection with session tracking
- **Process tab**: Visual PDF page selector with hybrid AI/regex extraction
- **Data tab**: Advanced filtering system with discrete data access and anonymization options
- **Charts tab**: Privacy-safe visualizations showing usage patterns without exposing personal data
- **Chat tab**: AI-powered Q&A with direct PDF upload and chat history export functionality

## Backend Architecture

### Web Framework
- **Flask** as the primary web framework with template rendering
- **Werkzeug** for secure file upload handling
- Session-based security with configurable secret keys

### Advanced Multi-Layer Data Processing Pipeline
The system implements a sophisticated PDF processing workflow with multiple extraction methods:

1. **File Upload Handler**: Secures uploaded PDFs in the `data` directory
2. **Enhanced Regex Processor**: Advanced pattern-based extractor using proven telecommunications bill parsing patterns
   - Specific regex patterns for T-Mobile bill formats
   - State-persistent processing tracking sections, lines, and dates
   - Handles TALK, TEXT, and DATA sections with precise field extraction
3. **Hybrid AI Processor**: AI-powered fallback when regex patterns are insufficient
   - Smart content optimization to avoid API timeouts
   - JSON schema validation for structured data extraction
4. **Intelligent Processing Strategy**: 
   - Primary: Enhanced regex processor for maximum accuracy and speed
   - Fallback: AI hybrid processor when regex yields insufficient results
   - Automatic selection of best results between both methods
5. **Direct Chat File Analysis**: Users can upload PDFs directly to chat for immediate AI analysis
6. **Chat History Export**: Full conversation history download functionality
7. **Data Integrity Management**: Transaction-based processing with automatic rollback on errors

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
Privacy-enhanced RESTful endpoints with advanced filtering:
- `/api/upload` - Secure PDF file upload with session tracking
- `/api/process` - Hybrid extraction with privacy mode processing
- `/api/get-data` - Filtered dataset retrieval with privacy controls
- `/api/export-csv` - Advanced CSV export with anonymization options
- `/api/chat` - AI chat assistant with context-aware responses
- `/api/chat-file` - Direct PDF upload and analysis with privacy protection
- `/api/export-chat` - Secure chat history export functionality

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