# Design Document: Senate Bot Project Structure

## Overview

This design document specifies the technical architecture for restructuring the Form Filling Bot (PM Mudra Yojana loan application chatbot) from a Jupyter notebook implementation into a production-ready full-stack application called "senate-bot". The system will maintain all existing chatbot functionality while establishing a clean separation between backend and frontend components.

The architecture follows a client-server model with a FastAPI backend serving REST endpoints and a React frontend providing the user interface. The backend consolidates all notebook logic (validation functions, conversation management, Groq API integration) into a single app.py file, uses SQLite for data persistence, and exposes three primary endpoints: /chat for message processing, /status for health checks, and /reset for conversation clearing. The frontend implements a chat interface component that communicates with the backend via HTTP requests.

Key design goals include:
- Preserving all existing chatbot functionality during restructuring
- Establishing clear separation of concerns between client and server
- Implementing persistent storage for loan applications
- Enabling cross-origin communication through CORS configuration
- Providing a foundation for future enhancements

## Architecture

### System Components

The system consists of three primary layers:

**1. Frontend Layer (React + Vite)**
- Chat Interface Component: Displays conversation messages with left-aligned bot messages and right-aligned user messages
- API Client Module: Handles all HTTP communication with the backend
- State Management: Manages conversation history, loading states, and form completion status
- Success Display: Shows application ID upon form completion

**2. Backend Layer (FastAPI)**
- app.py: Main application file containing all notebook logic plus REST endpoints
- Validation Functions: Aadhaar, PAN, mobile, email, and date of birth validators
- Conversation Manager: Maintains conversation_history and application_data structures
- Groq API Integration: Interfaces with llama-3.3-70b-versatile model
- CORS Middleware: Enables cross-origin requests from the React frontend

**3. Data Layer (SQLite)**
- database.py: Database operations module
- applications.db: SQLite database file
- Applications Table: Stores all loan application data with generated application IDs

### Communication Flow

```
User Input → Chat Interface → API Client → POST /chat → FastAPI Server
                                                           ↓
                                                    Groq API Call
                                                           ↓
                                                    Response Processing
                                                           ↓
                                                    Form Complete Check
                                                           ↓
                                                    Database Save (if complete)
                                                           ↓
Bot Response ← Chat Interface ← API Client ← JSON Response ← FastAPI Server
```

### Deployment Architecture

Development environment:
- Backend: localhost:8000 (FastAPI with uvicorn)
- Frontend: localhost:5173 (Vite dev server)
- Database: Local SQLite file (applications.db)

The backend and frontend run as separate processes that communicate via HTTP. CORS middleware on the backend allows requests from the frontend origin.

## Components and Interfaces

### Backend Components

#### 1. FastAPI Server (app.py)

**Responsibilities:**
- Expose REST API endpoints
- Manage conversation state
- Validate user inputs
- Integrate with Groq API
- Trigger database saves on form completion

**Key Functions:**
```python
# Validation functions (migrated from notebook)
validate_aadhaar(aadhaar: str) -> bool
validate_pan(pan: str) -> bool
validate_mobile(mobile: str) -> bool
validate_email(email: str) -> bool
validate_dob(dob: str) -> bool

# Conversation management
process_message(user_message: str) -> dict
check_form_complete() -> bool
```

**API Endpoints:**

1. **POST /chat**
   - Request: `{"message": "user message text"}`
   - Response: `{"response": "bot message", "form_complete": false}`
   - Response (complete): `{"response": "bot message", "form_complete": true, "application_id": "MU-20240115-1234"}`
   - Error: `{"error": "error message"}` (status 500)

2. **GET /status**
   - Response: `{"status": "ok"}`

3. **POST /reset**
   - Response: `{"message": "Conversation reset successfully"}`

**State Management:**
```python
conversation_history = []  # List of message dicts
application_data = {
    "personal_details": {},
    "business_details": {},
    "loan_details": {},
    "documents": {}
}
```

#### 2. Database Module (database.py)

**Responsibilities:**
- Initialize SQLite database and schema
- Generate unique application IDs
- Save completed applications
- Retrieve applications by ID

**Key Functions:**
```python
init_db() -> None
generate_application_id() -> str
save_application(data: dict) -> str
fetch_application_by_id(app_id: str) -> dict | None
```

**Application ID Algorithm:**
- Format: MU-YYYYMMDD-XXXX
- YYYYMMDD: Current date (e.g., 20240115)
- XXXX: Random 4-digit number (0000-9999)
- Uniqueness: Check database for collisions, regenerate if needed
- Implementation: Use datetime.now() for date, random.randint(0, 9999) for number

### Frontend Components

#### 1. Chat Interface Component

**Responsibilities:**
- Display conversation messages
- Handle user input
- Show loading states
- Display success state with application ID
- Trigger conversation reset

**Props/State:**
```javascript
// State
messages: Array<{role: 'user' | 'bot', content: string}>
inputValue: string
isLoading: boolean
formComplete: boolean
applicationId: string | null

// Methods
handleSendMessage()
handleReset()
scrollToBottom()
```

**UI Elements:**
- Message container (scrollable)
- Message bubbles (styled by role)
- Input box
- Send button
- Reset button
- Success display (conditional)
- Loading indicator

#### 2. API Client Module

**Responsibilities:**
- Centralize backend communication
- Handle request/response formatting
- Manage error handling

**Functions:**
```javascript
sendMessage(message: string): Promise<ChatResponse>
resetConversation(): Promise<ResetResponse>
checkStatus(): Promise<StatusResponse>
```

**Configuration:**
```javascript
const API_BASE_URL = 'http://localhost:8000'
```

### Interface Contracts

#### Chat Request/Response
```typescript
// Request
interface ChatRequest {
  message: string
}

// Response
interface ChatResponse {
  response: string
  form_complete: boolean
  application_id?: string
  error?: string
}
```

#### Reset Request/Response
```typescript
// Response
interface ResetResponse {
  message: string
}
```

#### Status Request/Response
```typescript
// Response
interface StatusResponse {
  status: string
}
```

## Data Models

### Application Data Structure (In-Memory)

```python
application_data = {
    "personal_details": {
        "name": str,
        "father_name": str,
        "date_of_birth": str,  # Format: DD/MM/YYYY
        "gender": str,
        "category": str,
        "aadhaar": str,  # 12 digits
        "pan": str,  # 10 characters
        "mobile": str,  # 10 digits
        "email": str,
        "address": str
    },
    "business_details": {
        "business_name": str,
        "business_type": str,
        "business_address": str,
        "years_in_business": int
    },
    "loan_details": {
        "loan_amount": float,
        "loan_purpose": str
    },
    "documents": {
        "aadhaar_document": str,
        "pan_document": str,
        "business_proof": str,
        "bank_statement": str
    }
}
```

### Database Schema (SQLite)

**Table: applications**

```sql
CREATE TABLE applications (
    application_id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'Pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Personal Details
    name TEXT,
    father_name TEXT,
    date_of_birth TEXT,
    gender TEXT,
    category TEXT,
    aadhaar TEXT,
    pan TEXT,
    mobile TEXT,
    email TEXT,
    address TEXT,
    
    -- Business Details
    business_name TEXT,
    business_type TEXT,
    business_address TEXT,
    years_in_business INTEGER,
    
    -- Loan Details
    loan_amount REAL,
    loan_purpose TEXT,
    
    -- Documents
    aadhaar_document TEXT,
    pan_document TEXT,
    business_proof TEXT,
    bank_statement TEXT
)
```

**Indexes:**
- Primary key on application_id (automatic)
- Index on submitted_at for chronological queries (future enhancement)

### Conversation History Structure

```python
conversation_history = [
    {
        "role": "system",
        "content": "System prompt text..."
    },
    {
        "role": "user",
        "content": "User message text"
    },
    {
        "role": "assistant",
        "content": "Bot response text"
    }
]
```

### Configuration Data (.env)

```
GROQ_API_KEY=your_api_key_here
```

This file is located at `senate-bot/backend/.env` and loaded using python-dotenv.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following testable properties. During reflection, I eliminated redundancies:

- Criteria 1.4 and 1.5 are redundant with 1.2 and 1.3 (directory existence)
- Criteria 5.2 is redundant with 5.1 (environment loading)
- Criteria 22.2 and 22.4 are redundant with 9.1 and 9.4 (endpoint testing)
- Criteria 25.2 is redundant with 24.5 (gitignore for .env)
- Conversation history properties (8.2, 8.4) can be combined into a single property about message persistence
- Reset properties (9.2, 9.3) can be combined into a single property about state clearing
- Database schema checks (11.3-11.10) can be combined into a single property about schema completeness
- Application ID format checks (12.1-12.3) can be combined into a single comprehensive property

### Property 1: Message Persistence in Conversation History

*For any* user message or bot response processed by the chat endpoint, that message should be appended to and retrievable from the conversation_history.

**Validates: Requirements 8.2, 8.4**

### Property 2: Chat Response Contains Bot Message

*For any* valid chat request, the response should contain a bot message field with non-empty content.

**Validates: Requirements 8.5**

### Property 3: Form Completion Detection

*For any* application_data structure where all required fields (personal details, business details, loan details, documents) are populated with valid values, the system should detect FORM_COMPLETE status.

**Validates: Requirements 8.6**

### Property 4: Reset Clears Application State

*For any* conversation state (conversation_history and application_data), calling the reset endpoint should return both structures to their initial empty state (or system prompt only for history).

**Validates: Requirements 9.2, 9.3**

### Property 5: Application ID Format Compliance

*For any* generated application ID, it should match the format MU-YYYYMMDD-XXXX where YYYYMMDD is the current date and XXXX is a 4-digit number.

**Validates: Requirements 12.1, 12.2, 12.3**

### Property 6: Application ID Uniqueness

*For any* newly generated application ID, it should not already exist in the applications database table.

**Validates: Requirements 12.4**

### Property 7: Save Operation Returns Unique ID

*For any* application data passed to save_application, the function should return a unique application ID string.

**Validates: Requirements 13.2, 13.4**

### Property 8: Database Round-Trip Preservation

*For any* application data saved to the database, fetching it by the returned application ID should retrieve data equivalent to what was saved.

**Validates: Requirements 13.3, 14.2**

### Property 9: Invalid ID Returns None

*For any* application ID that does not exist in the database, fetch_application_by_id should return None.

**Validates: Requirements 14.3**

### Property 10: Fetched Data Completeness

*For any* application fetched from the database, the returned data should include all fields defined in the Applications_Table schema (application_id, status, submitted_at, personal details, business details, loan details, documents).

**Validates: Requirements 14.4**

### Property 11: Completed Form Response Includes Application ID

*For any* chat request that results in form completion, the response should include both form_complete=true and a valid application_id field.

**Validates: Requirements 15.2, 15.3**

## Error Handling

### Backend Error Handling

**API Communication Errors (8.7, 15.4):**
- When Groq API calls fail, catch exceptions and return HTTP 500 with error details
- Log error messages for debugging
- Return user-friendly error message in response JSON

**Database Errors (13.5):**
- Wrap database operations in try-except blocks
- Catch SQLite exceptions during save operations
- Raise custom exceptions with descriptive error messages
- Return HTTP 500 to client when database operations fail

**Application ID Collision (12.5):**
- Implement retry logic with maximum attempts (e.g., 10 retries)
- If collision detected, regenerate new random number
- If max retries exceeded, raise exception
- Log collision events for monitoring

**Validation Errors:**
- Validate input data before processing
- Return HTTP 400 for malformed requests
- Include specific validation error messages in response

### Frontend Error Handling

**API Request Failures (20.6, 21.4):**
- Catch network errors in API client
- Display user-friendly error messages in chat interface
- Provide retry option for failed requests
- Handle timeout scenarios gracefully

**State Management Errors:**
- Validate response structure before updating state
- Handle missing or malformed response fields
- Maintain UI consistency during error states

### Error Response Formats

**Backend Error Response:**
```json
{
  "error": "Descriptive error message",
  "details": "Technical details (optional)"
}
```

**Frontend Error Display:**
- Show error message as a system message in chat
- Use distinct styling for error messages
- Provide actionable guidance when possible

## Testing Strategy

### Dual Testing Approach

This project requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of valid inputs and expected outputs
- Edge cases (empty inputs, boundary values, special characters)
- Error conditions and exception handling
- Integration points between components
- API endpoint responses with specific payloads

**Property-Based Tests** focus on:
- Universal properties that hold across all valid inputs
- Comprehensive input coverage through randomization
- Invariants that must be maintained
- Round-trip properties (save/fetch, serialize/deserialize)

Both approaches are complementary and necessary: unit tests catch concrete bugs with specific scenarios, while property tests verify general correctness across a wide input space.

### Backend Testing

**Testing Framework:** pytest for unit tests, Hypothesis for property-based tests

**Unit Test Coverage:**
- Validation functions (validate_aadhaar, validate_pan, validate_mobile, validate_email, validate_dob)
  - Test valid inputs return True
  - Test invalid inputs return False
  - Test edge cases (empty strings, special characters, wrong lengths)
- API endpoints
  - Test POST /chat with sample messages
  - Test GET /status returns {"status": "ok"}
  - Test POST /reset clears state
  - Test CORS headers are present
- Database operations
  - Test init_db creates tables
  - Test save_application with complete data
  - Test fetch_application_by_id with valid and invalid IDs
- Error handling
  - Test API errors return 500
  - Test database errors raise exceptions
  - Test validation errors return appropriate responses

**Property-Based Test Configuration:**
- Library: Hypothesis (Python)
- Minimum iterations: 100 per test
- Tag format: `# Feature: senate-bot-project-structure, Property {number}: {property_text}`

**Property-Based Tests:**

1. **Property 1: Message Persistence**
   ```python
   # Feature: senate-bot-project-structure, Property 1: Message Persistence in Conversation History
   @given(st.text(min_size=1))
   def test_message_persistence(message):
       # Send message to chat endpoint
       # Verify message appears in conversation_history
   ```

2. **Property 2: Chat Response Contains Bot Message**
   ```python
   # Feature: senate-bot-project-structure, Property 2: Chat Response Contains Bot Message
   @given(st.text(min_size=1))
   def test_chat_response_format(message):
       # Send message to chat endpoint
       # Verify response contains non-empty bot message
   ```

3. **Property 3: Form Completion Detection**
   ```python
   # Feature: senate-bot-project-structure, Property 3: Form Completion Detection
   @given(complete_application_data())
   def test_form_completion_detection(app_data):
       # Set application_data to complete state
       # Verify form_complete flag is True
   ```

4. **Property 4: Reset Clears Application State**
   ```python
   # Feature: senate-bot-project-structure, Property 4: Reset Clears Application State
   @given(st.lists(st.text()), st.dictionaries(st.text(), st.text()))
   def test_reset_clears_state(history, data):
       # Set conversation_history and application_data
       # Call reset endpoint
       # Verify both are cleared
   ```

5. **Property 5: Application ID Format Compliance**
   ```python
   # Feature: senate-bot-project-structure, Property 5: Application ID Format Compliance
   @given(st.integers(min_value=1, max_value=100))
   def test_application_id_format(n):
       # Generate n application IDs
       # Verify each matches MU-YYYYMMDD-XXXX format
       # Verify date portion matches current date
   ```

6. **Property 6: Application ID Uniqueness**
   ```python
   # Feature: senate-bot-project-structure, Property 6: Application ID Uniqueness
   @given(st.integers(min_value=10, max_value=100))
   def test_application_id_uniqueness(n):
       # Generate n application IDs
       # Verify all are unique
   ```

7. **Property 7: Save Operation Returns Unique ID**
   ```python
   # Feature: senate-bot-project-structure, Property 7: Save Operation Returns Unique ID
   @given(application_data_strategy())
   def test_save_returns_id(app_data):
       # Call save_application with data
       # Verify return value is non-empty string
       # Verify return value matches ID format
   ```

8. **Property 8: Database Round-Trip Preservation**
   ```python
   # Feature: senate-bot-project-structure, Property 8: Database Round-Trip Preservation
   @given(application_data_strategy())
   def test_database_round_trip(app_data):
       # Save application data
       # Fetch by returned ID
       # Verify fetched data equals saved data
   ```

9. **Property 9: Invalid ID Returns None**
   ```python
   # Feature: senate-bot-project-structure, Property 9: Invalid ID Returns None
   @given(st.text().filter(lambda x: not x.startswith("MU-")))
   def test_invalid_id_returns_none(invalid_id):
       # Call fetch_application_by_id with invalid ID
       # Verify return value is None
   ```

10. **Property 10: Fetched Data Completeness**
    ```python
    # Feature: senate-bot-project-structure, Property 10: Fetched Data Completeness
    @given(application_data_strategy())
    def test_fetched_data_completeness(app_data):
        # Save application
        # Fetch by ID
        # Verify all required fields are present
    ```

11. **Property 11: Completed Form Response Includes Application ID**
    ```python
    # Feature: senate-bot-project-structure, Property 11: Completed Form Response Includes Application ID
    @given(complete_application_data())
    def test_completed_form_response(app_data):
        # Set application_data to complete state
        # Send message triggering completion
        # Verify response includes form_complete=True and application_id
    ```

### Frontend Testing

**Testing Framework:** Vitest for unit tests, React Testing Library for component tests

**Unit Test Coverage:**
- API Client module
  - Test sendMessage calls correct endpoint
  - Test resetConversation calls correct endpoint
  - Test checkStatus calls correct endpoint
  - Test error handling for failed requests
- Chat Interface component (integration tests)
  - Test message rendering
  - Test input handling
  - Test send button functionality
  - Test reset button functionality
  - Test success state display

**Note:** Frontend property-based testing is less applicable for UI components. Focus on unit tests and integration tests for frontend code.

### Integration Testing

**End-to-End Test Scenarios:**
1. Complete loan application flow from start to finish
2. Reset conversation mid-flow and restart
3. Error recovery (API failures, network issues)
4. CORS verification (frontend-backend communication)
5. Database persistence verification

**Testing Tools:**
- Backend: pytest with requests library
- Frontend: Vitest with MSW (Mock Service Worker) for API mocking
- E2E: Playwright or Cypress (future enhancement)

### Test Execution

**Backend:**
```bash
cd backend
pytest tests/ -v
pytest tests/test_properties.py -v --hypothesis-show-statistics
```

**Frontend:**
```bash
cd frontend
npm run test
```

**Coverage Goals:**
- Backend: >80% code coverage
- Frontend: >70% code coverage
- All correctness properties: 100% implementation

### Continuous Integration

Future enhancement: Set up GitHub Actions to run tests on every commit and pull request.

## CORS Configuration

### Purpose

CORS (Cross-Origin Resource Sharing) middleware is required because the frontend (localhost:5173) and backend (localhost:8000) run on different ports, which browsers treat as different origins. Without CORS configuration, browsers block API requests from the frontend to the backend.

### Implementation

**Backend (FastAPI):**
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
```

### Configuration Details

**allow_origins:** List of allowed origins
- Development: `["http://localhost:5173"]`
- Production: Update to actual frontend domain

**allow_credentials:** Enable cookies and authentication headers
- Set to `True` for session-based auth (future enhancement)

**allow_methods:** HTTP methods allowed
- `["*"]` allows GET, POST, PUT, DELETE, etc.
- Can restrict to `["GET", "POST"]` for tighter security

**allow_headers:** HTTP headers allowed
- `["*"]` allows all headers including Content-Type, Authorization
- Can restrict to specific headers if needed

### Security Considerations

**Development vs Production:**
- Development: Allow localhost origins
- Production: Replace with actual frontend domain
- Never use `["*"]` for allow_origins in production

**Preflight Requests:**
- Browsers send OPTIONS requests before actual requests
- CORS middleware handles these automatically
- Ensure OPTIONS method is allowed

### Testing CORS

**Verification Steps:**
1. Start backend server (localhost:8000)
2. Start frontend server (localhost:5173)
3. Open browser developer tools → Network tab
4. Send a message in chat interface
5. Check response headers for:
   - `Access-Control-Allow-Origin: http://localhost:5173`
   - `Access-Control-Allow-Credentials: true`

**Common Issues:**
- Missing CORS headers → Add middleware
- Wrong origin → Update allow_origins list
- Preflight failures → Ensure OPTIONS method allowed

## Deployment Procedures

### Development Environment Setup

**Prerequisites:**
- Python 3.8+ installed
- Node.js 16+ and npm installed
- Git installed

**Backend Setup:**
```bash
# Navigate to project root
cd senate-bot

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Initialize database
python -c "from database import init_db; init_db()"

# Run backend server
python app.py
# Server runs on http://localhost:8000
```

**Frontend Setup:**
```bash
# Navigate to frontend directory
cd senate-bot/frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Server runs on http://localhost:5173
```

### Running the Application

**Start Backend:**
```bash
cd senate-bot/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

**Start Frontend (in separate terminal):**
```bash
cd senate-bot/frontend
npm run dev
```

**Access Application:**
- Open browser to http://localhost:5173
- Chat interface should load and connect to backend
- Test by sending a message

### Testing Procedures

**Backend Testing:**
```bash
cd senate-bot/backend
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run property-based tests with statistics
pytest tests/test_properties.py -v --hypothesis-show-statistics

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Frontend Testing:**
```bash
cd senate-bot/frontend

# Run tests
npm run test

# Run tests with coverage
npm run test -- --coverage
```

**Manual API Testing:**
```bash
# Test status endpoint
curl http://localhost:8000/status

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Test reset endpoint
curl -X POST http://localhost:8000/reset
```

### Database Management

**View Database Contents:**
```bash
cd senate-bot/backend
sqlite3 applications.db

# SQL commands
.tables                          # List tables
.schema applications             # View schema
SELECT * FROM applications;      # View all records
SELECT * FROM applications WHERE application_id = 'MU-20240115-1234';
.quit                           # Exit
```

**Reset Database:**
```bash
cd senate-bot/backend
rm applications.db
python -c "from database import init_db; init_db()"
```

### Production Deployment (Future)

**Backend Deployment:**
- Use production WSGI server (gunicorn)
- Set environment variables securely (not .env file)
- Update CORS origins to production frontend domain
- Use production database (PostgreSQL recommended)
- Enable HTTPS

**Frontend Deployment:**
- Build production bundle: `npm run build`
- Serve static files via CDN or web server
- Update API_BASE_URL to production backend
- Enable HTTPS

**Infrastructure:**
- Backend: Deploy to cloud platform (AWS, GCP, Azure, Heroku)
- Frontend: Deploy to static hosting (Vercel, Netlify, S3)
- Database: Use managed database service
- Monitoring: Set up logging and error tracking

### Version Control

**Git Workflow:**
```bash
# Initialize repository
cd senate-bot
git init
git add .
git commit -m "Initial commit: Project structure"

# Create GitHub repository and push
git remote add origin https://github.com/username/senate-bot.git
git branch -M main
git push -u origin main
```

**Gitignore Verification:**
```bash
# Verify .env is not tracked
git status
# Should not show .env file

# Verify node_modules is not tracked
cd frontend
npm install
cd ..
git status
# Should not show node_modules/
```

### Troubleshooting

**Backend Issues:**
- Port 8000 already in use → Kill process or use different port
- GROQ_API_KEY not found → Check .env file exists and is in backend directory
- Database errors → Delete applications.db and reinitialize
- Import errors → Verify virtual environment is activated and dependencies installed

**Frontend Issues:**
- Port 5173 already in use → Kill process or Vite will auto-select different port
- API connection failed → Verify backend is running on localhost:8000
- CORS errors → Check CORS middleware configuration in backend
- Module not found → Run `npm install`

**Integration Issues:**
- Frontend can't reach backend → Check both servers are running
- CORS errors → Verify allow_origins includes frontend URL
- No response from chat → Check backend logs for errors
- Database not saving → Verify applications.db exists and has write permissions

