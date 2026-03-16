# Implementation Plan: Senate Bot Project Structure

## Overview

This plan restructures the Form Filling Bot from a Jupyter notebook into a production-ready full-stack application with FastAPI backend and React frontend. The implementation follows 7 phases: project structure setup, backend API development, database integration, frontend development, frontend-backend connection, testing, and version control setup.

## Tasks

- [ ] 1. Set up project structure and configuration
  - Create senate-bot directory with backend and frontend subdirectories
  - Move .env file to backend directory preserving all key-value pairs
  - Create .gitignore file at project root with patterns for .env, Python cache, node_modules, and system files
  - Create README.md documenting directory purposes, environment setup, and required variables
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2. Implement FastAPI backend server
  - [ ] 2.1 Create app.py with FastAPI server setup
    - Initialize FastAPI application
    - Configure CORS middleware to allow requests from http://localhost:5173
    - Set up uvicorn server to run on port 8000
    - Load GROQ_API_KEY from .env using python-dotenv
    - _Requirements: 7.1, 7.5, 7.6, 5.1, 5.2_
  
  - [ ] 2.2 Migrate validation functions from notebook to app.py
    - Implement validate_aadhaar function (12-digit validation)
    - Implement validate_pan function (10-character format validation)
    - Implement validate_mobile function (10-digit validation)
    - Implement validate_email function (email format validation)
    - Implement validate_dob function (DD/MM/YYYY format validation)
    - _Requirements: 5.4, 7.7_
  
  - [ ]* 2.3 Write unit tests for validation functions
    - Test valid inputs return True for each validator
    - Test invalid inputs return False for each validator
    - Test edge cases (empty strings, special characters, wrong lengths)
    - _Requirements: 5.4_
  
  - [ ] 2.4 Implement conversation state management
    - Create conversation_history list structure
    - Create application_data dictionary with personal_details, business_details, loan_details, and documents sections
    - Implement system prompt initialization
    - _Requirements: 7.8, 7.9, 7.10, 5.5_

- [ ] 3. Implement API endpoints
  - [ ] 3.1 Implement POST /chat endpoint
    - Accept JSON request with message field
    - Append user message to conversation_history
    - Call Groq API with conversation context using llama-3.3-70b-versatile model
    - Append bot response to conversation_history
    - Return JSON response with bot message and form_complete flag
    - Implement error handling for API failures (return 500 status)
    - _Requirements: 7.2, 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 5.3_
  
  - [ ]* 3.2 Write property test for message persistence
    - **Property 1: Message Persistence in Conversation History**
    - **Validates: Requirements 8.2, 8.4**
    - Generate random user messages and verify they appear in conversation_history
    - _Requirements: 8.2, 8.4_
  
  - [ ]* 3.3 Write property test for chat response format
    - **Property 2: Chat Response Contains Bot Message**
    - **Validates: Requirements 8.5**
    - Generate random messages and verify responses contain non-empty bot message field
    - _Requirements: 8.5_
  
  - [ ] 3.4 Implement form completion detection logic
    - Check if all required fields in application_data are populated
    - Set form_complete flag to true when all fields are valid
    - _Requirements: 8.6_
  
  - [ ]* 3.5 Write property test for form completion detection
    - **Property 3: Form Completion Detection**
    - **Validates: Requirements 8.6**
    - Generate complete application_data structures and verify FORM_COMPLETE detection
    - _Requirements: 8.6_
  
  - [ ] 3.6 Implement GET /status endpoint
    - Return JSON response with status "ok"
    - _Requirements: 7.3, 9.1_
  
  - [ ] 3.7 Implement POST /reset endpoint
    - Clear conversation_history (keep only system prompt)
    - Reset application_data to empty structure
    - Return success confirmation message
    - _Requirements: 7.4, 9.2, 9.3, 9.4_
  
  - [ ]* 3.8 Write property test for reset functionality
    - **Property 4: Reset Clears Application State**
    - **Validates: Requirements 9.2, 9.3**
    - Set conversation state and verify reset endpoint clears both structures
    - _Requirements: 9.2, 9.3_

- [ ] 4. Create backend dependencies file
  - Create requirements.txt with fastapi, uvicorn, groq, python-dotenv, and python-multipart
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 5. Checkpoint - Test backend independently
  - Ensure backend server starts successfully on port 8000
  - Test GET /status endpoint returns {"status": "ok"}
  - Test POST /chat endpoint with sample message returns bot response
  - Test POST /reset endpoint confirms reset operation
  - Ask the user if questions arise
  - _Requirements: 22.1, 22.2, 22.3, 22.4_

- [ ] 6. Implement SQLite database module
  - [ ] 6.1 Create database.py with database initialization
    - Implement init_db function to create applications.db file
    - Define Applications_Table schema with all required columns
    - Create table with application_id as primary key
    - Add status column with default "Pending"
    - Add submitted_at column with CURRENT_TIMESTAMP default
    - Add columns for personal details (name, father_name, date_of_birth, gender, category, aadhaar, pan, mobile, email, address)
    - Add columns for business details (business_name, business_type, business_address, years_in_business)
    - Add columns for loan details (loan_amount, loan_purpose)
    - Add columns for documents (aadhaar_document, pan_document, business_proof, bank_statement)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10_
  
  - [ ] 6.2 Implement application ID generation function
    - Create generate_application_id function
    - Use format MU-YYYYMMDD-XXXX with current date
    - Generate random 4-digit number (0000-9999)
    - Check database for ID uniqueness
    - Regenerate if collision detected (max 10 retries)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 6.3 Write property test for application ID format
    - **Property 5: Application ID Format Compliance**
    - **Validates: Requirements 12.1, 12.2, 12.3**
    - Generate multiple IDs and verify format MU-YYYYMMDD-XXXX with current date
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ]* 6.4 Write property test for application ID uniqueness
    - **Property 6: Application ID Uniqueness**
    - **Validates: Requirements 12.4**
    - Generate multiple IDs and verify all are unique
    - _Requirements: 12.4_
  
  - [ ] 6.5 Implement save_application function
    - Accept application data dictionary as parameter
    - Generate unique Application_ID
    - Insert new row into Applications_Table with all fields
    - Return generated Application_ID on success
    - Raise exception with error details on database errors
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ]* 6.6 Write property test for save operation
    - **Property 7: Save Operation Returns Unique ID**
    - **Validates: Requirements 13.2, 13.4**
    - Generate random application data and verify save returns valid ID
    - _Requirements: 13.2, 13.4_
  
  - [ ] 6.7 Implement fetch_application_by_id function
    - Accept Application_ID as parameter
    - Query Applications_Table for matching ID
    - Return application data dictionary if found
    - Return None if ID not found
    - Include all fields from Applications_Table in returned data
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  
  - [ ]* 6.8 Write property test for database round-trip
    - **Property 8: Database Round-Trip Preservation**
    - **Validates: Requirements 13.3, 14.2**
    - Save random application data and verify fetching returns equivalent data
    - _Requirements: 13.3, 14.2_
  
  - [ ]* 6.9 Write property test for invalid ID handling
    - **Property 9: Invalid ID Returns None**
    - **Validates: Requirements 14.3**
    - Generate invalid IDs and verify fetch returns None
    - _Requirements: 14.3_
  
  - [ ]* 6.10 Write property test for fetched data completeness
    - **Property 10: Fetched Data Completeness**
    - **Validates: Requirements 14.4**
    - Save application and verify fetched data includes all schema fields
    - _Requirements: 14.4_

- [ ] 7. Integrate database with chat endpoint
  - [ ] 7.1 Add database save on form completion
    - Import save_application function in app.py
    - Call save_application when form_complete is detected
    - Include Application_ID in chat response when save succeeds
    - Return success message with Application_ID to user
    - Return error message if save_application fails
    - _Requirements: 15.1, 15.2, 15.3, 15.4_
  
  - [ ]* 7.2 Write property test for completed form response
    - **Property 11: Completed Form Response Includes Application ID**
    - **Validates: Requirements 15.2, 15.3**
    - Simulate form completion and verify response includes form_complete=true and application_id
    - _Requirements: 15.2, 15.3_
  
  - [ ] 7.3 Test database integration manually
    - Complete a full form submission through chat endpoint
    - Verify applications.db file is created
    - Query database to confirm application was saved with correct data
    - _Requirements: 22.5_

- [ ] 8. Checkpoint - Verify backend with database
  - Ensure all backend tests pass
  - Verify database saves applications correctly
  - Test form completion flow end-to-end
  - Ask the user if questions arise

- [ ] 9. Create React frontend application
  - [ ] 9.1 Initialize React app with Vite
    - Run npm create vite@latest in frontend directory
    - Select React template
    - Install dependencies (react, react-dom)
    - Configure Vite to run on port 5173
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_
  
  - [ ] 9.2 Set up project structure
    - Create src directory with component files
    - Set up basic App component structure
    - _Requirements: 16.5_

- [ ] 10. Implement API client module
  - [ ] 10.1 Create API client module
    - Create api.js file in src directory
    - Configure API_BASE_URL as http://localhost:8000
    - Implement sendMessage function to call POST /chat
    - Implement resetConversation function to call POST /reset
    - Implement checkStatus function to call GET /status
    - Add error handling for failed requests
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_
  
  - [ ]* 10.2 Write unit tests for API client
    - Test sendMessage calls correct endpoint with proper payload
    - Test resetConversation calls correct endpoint
    - Test checkStatus calls correct endpoint
    - Test error handling for network failures
    - _Requirements: 20.6_

- [ ] 11. Implement chat interface component
  - [ ] 11.1 Create ChatInterface component
    - Create ChatInterface.jsx file
    - Set up component state for messages, inputValue, isLoading, formComplete, and applicationId
    - Implement message display container with scrollable area
    - Style bot messages on left side
    - Style user messages on right side
    - Implement auto-scroll to latest message on new message
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.7_
  
  - [ ] 11.2 Add input controls
    - Create input box for typing messages
    - Create send button for submitting messages
    - Create reset button for clearing conversation
    - _Requirements: 17.5, 17.6, 19.1_
  
  - [ ] 11.3 Implement success state display
    - Display Application_ID prominently when formComplete is true
    - Show success message with Application_ID in readable format
    - _Requirements: 18.1, 18.2, 18.3_

- [ ] 12. Implement message flow
  - [ ] 12.1 Connect chat interface to API client
    - Implement handleSendMessage function
    - Call sendMessage from API client when user submits message
    - Display loading indicator while waiting for response
    - Update messages state with bot response
    - Handle form_complete flag and application_id in response
    - Display error message if API request fails
    - _Requirements: 21.1, 21.2, 21.3, 21.4_
  
  - [ ] 12.2 Implement reset functionality
    - Implement handleReset function
    - Call resetConversation from API client when reset button clicked
    - Clear all displayed messages on successful reset
    - Display initial greeting message after reset
    - _Requirements: 19.2, 19.3, 19.4_
  
  - [ ]* 12.3 Write integration tests for chat interface
    - Test message rendering with mock data
    - Test input handling and send button functionality
    - Test reset button clears messages
    - Test success state displays application ID
    - Use Mock Service Worker (MSW) for API mocking
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 18.1, 19.1_

- [ ] 13. Checkpoint - Test complete application
  - Start backend server with python app.py
  - Start frontend server with npm run dev
  - Verify frontend successfully communicates with backend
  - Complete full loan application flow from start to finish
  - Verify success state displays application ID
  - Test reset functionality
  - Ensure all tests pass
  - Ask the user if questions arise
  - _Requirements: 23.1, 23.2, 23.3, 23.4_

- [ ] 14. Write comprehensive tests
  - [ ]* 14.1 Run backend unit tests
    - Execute pytest for validation functions
    - Execute pytest for API endpoints
    - Execute pytest for database operations
    - Verify all unit tests pass
  
  - [ ]* 14.2 Run backend property-based tests
    - Execute pytest for all 11 property tests
    - Run with --hypothesis-show-statistics flag
    - Verify all properties hold across generated inputs
  
  - [ ]* 14.3 Run frontend tests
    - Execute npm run test for API client tests
    - Execute npm run test for component integration tests
    - Verify all frontend tests pass

- [ ] 15. Initialize Git repository and push to GitHub
  - [ ] 15.1 Initialize Git repository
    - Run git init in project root
    - Verify .gitignore is in place before first commit
    - Make initial commit with project structure
    - _Requirements: 24.1, 24.2, 24.3_
  
  - [ ] 15.2 Verify gitignore patterns
    - Confirm .env file is not tracked by Git
    - Confirm node_modules directory is not tracked
    - Confirm Python cache files are not tracked
    - Confirm .DS_Store is not tracked
    - _Requirements: 24.4, 24.5_
  
  - [ ] 15.3 Create GitHub repository and push
    - Create new repository on GitHub
    - Add GitHub remote to local repository
    - Push all commits to GitHub main branch
    - Verify .env is excluded from GitHub
    - Verify node_modules is excluded from GitHub
    - Verify Python cache files are excluded from GitHub
    - Verify all source code and configuration files are present
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

- [ ] 16. Final checkpoint - Complete verification
  - Verify README.md documents startup commands for both backend and frontend
  - Verify all acceptance criteria are met
  - Verify chatbot functionality is preserved from original notebook
  - Ensure all tests pass
  - Ask the user if questions arise
  - _Requirements: 23.5, 4.1, 4.2, 4.3, 4.4, 5.3, 5.4, 5.5_

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples, edge cases, and integration points
- Backend uses Python with FastAPI, frontend uses JavaScript/React
- Database uses SQLite for simplicity (no external database setup required)
- CORS is configured to allow frontend (localhost:5173) to communicate with backend (localhost:8000)
- All sensitive files (.env, credentials) are excluded from version control via .gitignore
