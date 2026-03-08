# Senate Bot - PM Mudra Yojana Loan Application Chatbot

A full-stack chatbot application for collecting PM Mudra Yojana loan applications through conversational interface.

## Project Structure

```
senate-bot/
├── backend/          # Server-side code and API logic
│   ├── app.py       # FastAPI server with REST endpoints
│   ├── database.py  # SQLite database operations
│   ├── .env         # Environment configuration (not committed to Git)
│   └── requirements.txt
├── frontend/         # Client-side user interface
│   ├── src/         # React components and API client
│   └── package.json
└── README.md
```

## Directory Purposes

### Backend Directory (`backend/`)
Contains all server-side code including:
- FastAPI REST API server
- Chatbot conversation logic
- Groq API integration for LLM responses
- Input validation functions (Aadhaar, PAN, mobile, email, DOB)
- SQLite database operations for storing loan applications
- Environment configuration management

### Frontend Directory (`frontend/`)
Contains all client-side code including:
- React user interface components
- Chat interface for user interactions
- API client for backend communication
- State management for conversation flow
- Success display for completed applications

## Environment Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm (comes with Node.js)
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd senate-bot/backend
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure environment variables (see below)

6. Run the backend server:
   ```bash
   python app.py
   ```
   The server will start on http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd senate-bot/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The application will open on http://localhost:5173

## Required Environment Variables

The backend requires the following environment variables to be configured in the `.env` file located at `senate-bot/backend/.env`:

### GROQ_API_KEY
- **Description**: API key for accessing the Groq LLM service
- **Required**: Yes
- **Format**: String
- **Example**: `GROQ_API_KEY=gsk_your_actual_api_key_here`
- **How to obtain**: 
  1. Visit https://console.groq.com
  2. Sign up or log in to your account
  3. Navigate to API Keys section
  4. Generate a new API key
  5. Copy the key and paste it in your `.env` file

### Setting Up Environment Variables

1. Create a `.env` file in the `backend/` directory (if it doesn't exist):
   ```bash
   cd senate-bot/backend
   touch .env  # On Windows: type nul > .env
   ```

2. Open the `.env` file in a text editor and add your API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

3. Save the file

**Important**: Never commit the `.env` file to version control. It's already included in `.gitignore` to prevent accidental commits.

## Running the Complete Application

1. Start the backend server (in one terminal):
   ```bash
   cd senate-bot/backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   python app.py
   ```

2. Start the frontend server (in another terminal):
   ```bash
   cd senate-bot/frontend
   npm run dev
   ```

3. Open your browser to http://localhost:5173

4. Start chatting with the bot to complete a loan application

## Features

- Conversational loan application collection
- Real-time input validation (Aadhaar, PAN, mobile, email, DOB)
- Persistent storage of applications in SQLite database
- Unique application ID generation (format: MU-YYYYMMDD-XXXX)
- Chat history management
- Conversation reset functionality
- Modern React-based user interface

## API Endpoints

The backend exposes the following REST endpoints:

- `POST /chat` - Send a message and receive bot response
- `GET /status` - Check server health
- `POST /reset` - Clear conversation history and start fresh

## Database

Applications are stored in a SQLite database (`applications.db`) in the backend directory. Each application includes:
- Personal details (name, Aadhaar, PAN, contact info, etc.)
- Business details (business name, type, address, years in operation)
- Loan details (amount, purpose)
- Document references
- Unique application ID and submission timestamp

## Development

This project is structured for easy development and future enhancements:
- Clear separation between frontend and backend
- RESTful API design for scalability
- Modular code organization
- Comprehensive validation logic
- Database persistence for data integrity

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
