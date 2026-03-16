# Requirements Document

## Introduction

This document specifies the requirements for restructuring the existing Form Filling Bot (PM Mudra Yojana loan application chatbot) from a Jupyter notebook implementation into a properly organized full-stack project called "senate-bot". The restructuring will establish a clean separation between backend and frontend components, implement proper configuration management, and prepare the foundation for future enhancements.

## Glossary

- **Project_Root**: The top-level directory containing the entire senate-bot application
- **Backend_Directory**: The directory containing server-side code, API logic, and business logic (senate-bot/backend)
- **Frontend_Directory**: The directory containing client-side code and user interface components (senate-bot/frontend)
- **Environment_File**: The .env file containing sensitive configuration data like API keys
- **Gitignore_File**: The .gitignore file specifying which files and directories Git should ignore
- **Notebook_File**: The existing Jupyter notebook (Form_Filling_chatbot.ipynb) containing the current chatbot implementation
- **Configuration_Manager**: The system component responsible for loading and managing environment variables
- **FastAPI_Server**: The backend API server built with FastAPI framework
- **Chat_Endpoint**: The POST /chat endpoint that processes user messages and returns bot responses
- **Status_Endpoint**: The GET /status endpoint that returns server health information
- **Reset_Endpoint**: The POST /reset endpoint that clears conversation history
- **CORS_Middleware**: The Cross-Origin Resource Sharing middleware enabling frontend-backend communication
- **Database_Module**: The database.py module handling SQLite database operations
- **Applications_Table**: The database table storing loan application data
- **Application_ID**: A unique identifier in format MU-YYYYMMDD-XXXX for each loan application
- **React_App**: The frontend user interface built with React and Vite
- **Chat_Interface**: The React component displaying conversation messages
- **API_Client**: The frontend module making HTTP requests to the backend
- **FORM_COMPLETE**: A status indicator signaling that all required application data has been collected
- **Git_Repository**: The version control repository tracking project changes

## Requirements

### Requirement 1: Create Project Directory Structure

**User Story:** As a developer, I want a well-organized project structure with separate backend and frontend directories, so that I can maintain clear separation of concerns and scale the application effectively.

#### Acceptance Criteria

1. THE Project_Root SHALL be named "senate-bot"
2. THE Project_Root SHALL contain a subdirectory named "backend"
3. THE Project_Root SHALL contain a subdirectory named "frontend"
4. THE Backend_Directory SHALL be located at "senate-bot/backend"
5. THE Frontend_Directory SHALL be located at "senate-bot/frontend"

### Requirement 2: Migrate Environment Configuration

**User Story:** As a developer, I want the environment configuration file properly located in the backend directory, so that sensitive API keys are organized with the server-side code that uses them.

#### Acceptance Criteria

1. WHEN the .env file exists in the project, THE Configuration_Manager SHALL move it to the Backend_Directory
2. THE Environment_File SHALL be located at "senate-bot/backend/.env"
3. THE Environment_File SHALL contain the GROQ_API_KEY configuration
4. WHEN the Environment_File is moved, THE Configuration_Manager SHALL preserve all existing key-value pairs

### Requirement 3: Implement Git Ignore Configuration

**User Story:** As a developer, I want a .gitignore file that prevents sensitive files from being committed to version control, so that API keys and other secrets remain secure.

#### Acceptance Criteria

1. THE Gitignore_File SHALL be created at the Project_Root level
2. THE Gitignore_File SHALL include ".env" as an ignored pattern
3. THE Gitignore_File SHALL include "*.env" as an ignored pattern to catch all environment file variations
4. THE Gitignore_File SHALL include common Python patterns (\_\_pycache\_\_, *.pyc, *.pyo, *.pyd)
5. THE Gitignore_File SHALL include ".ipynb_checkpoints" to ignore Jupyter notebook checkpoints
6. THE Gitignore_File SHALL include "node_modules/" for future frontend dependencies
7. THE Gitignore_File SHALL include ".DS_Store" for macOS system files

### Requirement 4: Preserve Existing Chatbot Implementation

**User Story:** As a developer, I want the existing chatbot notebook preserved during restructuring, so that I don't lose the working implementation while reorganizing the project.

#### Acceptance Criteria

1. THE Notebook_File SHALL remain accessible after restructuring
2. WHEN restructuring is complete, THE Notebook_File SHALL contain all original validation functions
3. WHEN restructuring is complete, THE Notebook_File SHALL contain all original conversation logic
4. WHEN restructuring is complete, THE Notebook_File SHALL contain all original data collection functionality

### Requirement 5: Maintain Chatbot Functionality

**User Story:** As a developer, I want to ensure the chatbot's core functionality remains intact, so that the restructuring doesn't break the working loan application collection system.

#### Acceptance Criteria

1. THE Backend_Directory SHALL support loading the GROQ_API_KEY from the Environment_File
2. WHEN the Environment_File is in the Backend_Directory, THE Configuration_Manager SHALL successfully load environment variables
3. THE Project_Root SHALL maintain compatibility with the Groq API integration using llama-3.3-70b-versatile model
4. THE Project_Root SHALL preserve all validation functions for Aadhaar, PAN, mobile, email, and date of birth
5. THE Project_Root SHALL preserve the application data structure for personal details, business details, loan details, and documents

### Requirement 6: Document Project Structure

**User Story:** As a developer, I want clear documentation of the new project structure, so that I understand where different components should be placed as the project evolves.

#### Acceptance Criteria

1. WHEN restructuring is complete, THE Project_Root SHALL contain a README.md file
2. THE README.md SHALL document the purpose of the Backend_Directory
3. THE README.md SHALL document the purpose of the Frontend_Directory
4. THE README.md SHALL include instructions for setting up the Environment_File
5. THE README.md SHALL list the required environment variables (GROQ_API_KEY)

### Requirement 7: Implement FastAPI Backend Server

**User Story:** As a developer, I want a FastAPI backend server that exposes REST endpoints, so that the frontend can communicate with the chatbot logic through a standard API.

#### Acceptance Criteria

1. THE Backend_Directory SHALL contain an app.py file implementing the FastAPI_Server
2. THE FastAPI_Server SHALL expose a Chat_Endpoint at POST /chat
3. THE FastAPI_Server SHALL expose a Status_Endpoint at GET /status
4. THE FastAPI_Server SHALL expose a Reset_Endpoint at POST /reset
5. THE FastAPI_Server SHALL include CORS_Middleware configured to accept requests from the React_App
6. WHEN the FastAPI_Server starts, it SHALL listen on port 8000
7. THE app.py SHALL contain all validation functions from the Notebook_File
8. THE app.py SHALL contain the conversation_history management logic
9. THE app.py SHALL contain the application_data structure
10. THE app.py SHALL contain the system prompt for the chatbot

### Requirement 8: Implement Chat Endpoint

**User Story:** As a user, I want to send messages to the chatbot and receive responses, so that I can complete my loan application through conversation.

#### Acceptance Criteria

1. WHEN a POST request is sent to the Chat_Endpoint with a user message, THE FastAPI_Server SHALL process the message
2. WHEN processing a message, THE Chat_Endpoint SHALL append the user message to conversation_history
3. WHEN processing a message, THE Chat_Endpoint SHALL call the Groq API with the conversation context
4. WHEN the Groq API returns a response, THE Chat_Endpoint SHALL append the bot response to conversation_history
5. WHEN the Groq API returns a response, THE Chat_Endpoint SHALL return the bot message to the client
6. WHEN all required fields are collected, THE Chat_Endpoint SHALL detect FORM_COMPLETE status
7. IF an error occurs during API communication, THEN THE Chat_Endpoint SHALL return an error response with status code 500

### Requirement 9: Implement Status and Reset Endpoints

**User Story:** As a developer, I want status and reset endpoints, so that I can verify server health and clear conversation state during testing.

#### Acceptance Criteria

1. WHEN a GET request is sent to the Status_Endpoint, THE FastAPI_Server SHALL return a JSON response with status "ok"
2. WHEN a POST request is sent to the Reset_Endpoint, THE FastAPI_Server SHALL clear the conversation_history
3. WHEN a POST request is sent to the Reset_Endpoint, THE FastAPI_Server SHALL reset the application_data structure
4. WHEN the Reset_Endpoint completes, it SHALL return a success confirmation message

### Requirement 10: Create Backend Dependencies File

**User Story:** As a developer, I want a requirements.txt file listing all Python dependencies, so that I can easily install the backend environment.

#### Acceptance Criteria

1. THE Backend_Directory SHALL contain a requirements.txt file
2. THE requirements.txt SHALL include fastapi as a dependency
3. THE requirements.txt SHALL include uvicorn as a dependency
4. THE requirements.txt SHALL include groq as a dependency
5. THE requirements.txt SHALL include python-dotenv as a dependency
6. THE requirements.txt SHALL include python-multipart as a dependency for form data handling

### Requirement 11: Implement SQLite Database Module

**User Story:** As a developer, I want a SQLite database to persist loan applications, so that submitted applications are stored permanently without requiring external database setup.

#### Acceptance Criteria

1. THE Backend_Directory SHALL contain a database.py file implementing the Database_Module
2. THE Database_Module SHALL create a SQLite database file named applications.db
3. THE Database_Module SHALL define an Applications_Table with columns for all form fields
4. THE Applications_Table SHALL include an application_id column as the primary key
5. THE Applications_Table SHALL include a status column with default value "Pending"
6. THE Applications_Table SHALL include a submitted_at column storing the submission timestamp
7. THE Applications_Table SHALL include columns for personal details (name, father_name, date_of_birth, gender, category, aadhaar, pan, mobile, email, address)
8. THE Applications_Table SHALL include columns for business details (business_name, business_type, business_address, years_in_business)
9. THE Applications_Table SHALL include columns for loan details (loan_amount, loan_purpose)
10. THE Applications_Table SHALL include columns for documents (aadhaar_document, pan_document, business_proof, bank_statement)

### Requirement 12: Implement Application ID Generation

**User Story:** As a system administrator, I want unique application IDs in a readable format, so that I can easily identify and reference loan applications.

#### Acceptance Criteria

1. THE Database_Module SHALL generate Application_ID values in format MU-YYYYMMDD-XXXX
2. WHEN generating an Application_ID, THE Database_Module SHALL use the current date for YYYYMMDD
3. WHEN generating an Application_ID, THE Database_Module SHALL generate a random 4-digit number for XXXX
4. WHEN generating an Application_ID, THE Database_Module SHALL verify uniqueness before returning
5. IF an Application_ID collision occurs, THEN THE Database_Module SHALL regenerate a new ID

### Requirement 13: Implement Database Save Function

**User Story:** As a user, I want my completed loan application saved to the database, so that my information is permanently stored for processing.

#### Acceptance Criteria

1. THE Database_Module SHALL provide a save_application function
2. WHEN save_application is called with application data, THE Database_Module SHALL generate a unique Application_ID
3. WHEN save_application is called, THE Database_Module SHALL insert a new row into the Applications_Table
4. WHEN save_application completes successfully, it SHALL return the generated Application_ID
5. IF a database error occurs during save, THEN THE Database_Module SHALL raise an exception with error details

### Requirement 14: Implement Database Fetch Function

**User Story:** As a developer, I want to retrieve applications by ID, so that I can verify saved data and implement future lookup features.

#### Acceptance Criteria

1. THE Database_Module SHALL provide a fetch_application_by_id function
2. WHEN fetch_application_by_id is called with a valid Application_ID, THE Database_Module SHALL return the application data
3. WHEN fetch_application_by_id is called with an invalid Application_ID, THE Database_Module SHALL return None
4. THE returned application data SHALL include all fields from the Applications_Table

### Requirement 15: Integrate Database with Chat Endpoint

**User Story:** As a user, I want my application automatically saved when I complete the form, so that I receive a confirmation with my application ID.

#### Acceptance Criteria

1. WHEN the Chat_Endpoint detects FORM_COMPLETE status, it SHALL call the save_application function
2. WHEN save_application succeeds, THE Chat_Endpoint SHALL include the Application_ID in the response
3. WHEN save_application succeeds, THE Chat_Endpoint SHALL return a success message to the user
4. IF save_application fails, THEN THE Chat_Endpoint SHALL return an error message to the user

### Requirement 16: Create React Frontend Application

**User Story:** As a user, I want a modern web interface to interact with the chatbot, so that I can complete my loan application in a user-friendly environment.

#### Acceptance Criteria

1. THE Frontend_Directory SHALL contain a React application created with Vite
2. THE React_App SHALL include a package.json file with all frontend dependencies
3. THE React_App SHALL include react and react-dom as dependencies
4. THE React_App SHALL be configured to run on port 5173 during development
5. THE Frontend_Directory SHALL contain a src directory with component files

### Requirement 17: Implement Chat Interface Component

**User Story:** As a user, I want to see my conversation with the chatbot in a clear message layout, so that I can easily follow the application process.

#### Acceptance Criteria

1. THE React_App SHALL include a Chat_Interface component
2. THE Chat_Interface SHALL display messages in a scrollable container
3. WHEN displaying bot messages, THE Chat_Interface SHALL position them on the left side
4. WHEN displaying user messages, THE Chat_Interface SHALL position them on the right side
5. THE Chat_Interface SHALL include an input box for typing messages
6. THE Chat_Interface SHALL include a send button for submitting messages
7. WHEN a new message is added, THE Chat_Interface SHALL automatically scroll to show the latest message

### Requirement 18: Implement Success State Display

**User Story:** As a user, I want to see my application ID when I complete the form, so that I have confirmation my application was submitted successfully.

#### Acceptance Criteria

1. WHEN the Chat_Interface receives a FORM_COMPLETE response, it SHALL display the Application_ID prominently
2. WHEN the Chat_Interface receives a FORM_COMPLETE response, it SHALL display a success message
3. THE success message SHALL include the Application_ID in a readable format

### Requirement 19: Implement Chat Reset Functionality

**User Story:** As a user, I want to reset the chat and start a new application, so that I can begin fresh if needed.

#### Acceptance Criteria

1. THE Chat_Interface SHALL include a reset button
2. WHEN the reset button is clicked, THE React_App SHALL call the Reset_Endpoint
3. WHEN the Reset_Endpoint responds successfully, THE Chat_Interface SHALL clear all displayed messages
4. WHEN the Reset_Endpoint responds successfully, THE Chat_Interface SHALL display the initial greeting message

### Requirement 20: Implement API Client Module

**User Story:** As a developer, I want a centralized API client module, so that all backend communication is handled consistently.

#### Acceptance Criteria

1. THE React_App SHALL include an API_Client module for backend communication
2. THE API_Client SHALL be configured to send requests to http://localhost:8000
3. THE API_Client SHALL provide a function to call the Chat_Endpoint
4. THE API_Client SHALL provide a function to call the Reset_Endpoint
5. THE API_Client SHALL provide a function to call the Status_Endpoint
6. WHEN an API request fails, THE API_Client SHALL handle the error gracefully

### Requirement 21: Implement Message Flow

**User Story:** As a user, I want my messages sent to the backend and responses displayed in real-time, so that the conversation feels natural and responsive.

#### Acceptance Criteria

1. WHEN a user submits a message, THE Chat_Interface SHALL send it to the Chat_Endpoint via the API_Client
2. WHEN the Chat_Endpoint returns a response, THE Chat_Interface SHALL display the bot message
3. WHEN waiting for a response, THE Chat_Interface SHALL display a loading indicator
4. IF the API request fails, THEN THE Chat_Interface SHALL display an error message to the user

### Requirement 22: Test Backend Independently

**User Story:** As a developer, I want to verify the backend works correctly before connecting the frontend, so that I can isolate and fix backend issues early.

#### Acceptance Criteria

1. THE FastAPI_Server SHALL be testable using curl or Postman
2. WHEN testing the Status_Endpoint, it SHALL return a successful response
3. WHEN testing the Chat_Endpoint with a sample message, it SHALL return a bot response
4. WHEN testing the Reset_Endpoint, it SHALL confirm the reset operation
5. THE developer SHALL verify database saves by checking the applications.db file

### Requirement 23: Run Complete Application

**User Story:** As a developer, I want clear instructions for running both backend and frontend, so that I can start the complete application easily.

#### Acceptance Criteria

1. THE Backend_Directory SHALL include instructions to run the FastAPI_Server with "python app.py"
2. THE Frontend_Directory SHALL include instructions to run the React_App with "npm run dev"
3. WHEN both servers are running, THE React_App SHALL successfully communicate with the FastAPI_Server
4. WHEN both servers are running, users SHALL be able to complete the full loan application flow
5. THE README.md SHALL document the commands to start both backend and frontend

### Requirement 24: Initialize Git Repository

**User Story:** As a developer, I want version control for the project, so that I can track changes and collaborate effectively.

#### Acceptance Criteria

1. THE Project_Root SHALL be initialized as a Git_Repository
2. THE Git_Repository SHALL include the Gitignore_File before the first commit
3. THE developer SHALL make regular commits throughout development
4. WHEN committing changes, THE Git_Repository SHALL exclude files matching Gitignore_File patterns
5. THE Environment_File SHALL NOT be committed to the Git_Repository

### Requirement 25: Push to GitHub

**User Story:** As a developer, I want the project hosted on GitHub, so that it's backed up and accessible for collaboration.

#### Acceptance Criteria

1. THE Git_Repository SHALL be pushed to a GitHub remote repository
2. WHEN pushing to GitHub, THE Environment_File SHALL be excluded
3. WHEN pushing to GitHub, THE node_modules directory SHALL be excluded
4. WHEN pushing to GitHub, THE Python cache files SHALL be excluded
5. THE GitHub repository SHALL contain all source code and configuration files except those in Gitignore_File
