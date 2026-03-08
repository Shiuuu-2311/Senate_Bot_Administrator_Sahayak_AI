from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import uvicorn

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    form_complete: bool
    application_id: str = None

class StatusResponse(BaseModel):
    status: str

class ResetResponse(BaseModel):
    message: str


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Validation Functions
import re
from datetime import datetime

def validate_aadhaar(value):
    """Validate Aadhaar number (12 digits)"""
    value = value.strip().replace(" ", "")
    if not value.isdigit():
        return False, "Aadhaar must contain only numbers"
    if len(value) != 12:
        return False, f"Aadhaar must be exactly 12 digits, you entered {len(value)}"
    return True, "Valid"

def validate_pan(value):
    """Validate PAN number (ABCDE1234F format)"""
    value = value.strip().upper()
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pattern, value):
        return False, "PAN must be in format ABCDE1234F (5 letters, 4 numbers, 1 letter)"
    return True, "Valid"

def validate_mobile(value):
    """Validate mobile number (10 digits starting with 6, 7, 8, or 9)"""
    value = value.strip().replace(" ", "")
    if not value.isdigit():
        return False, "Mobile number must contain only digits"
    if len(value) != 10:
        return False, "Mobile number must be exactly 10 digits"
    if value[0] not in ['6', '7', '8', '9']:
        return False, "Mobile number must start with 6, 7, 8, or 9"
    return True, "Valid"

def validate_email(value):
    """Validate email address format"""
    value = value.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        return False, "Please enter a valid email address like example@gmail.com"
    return True, "Valid"

def validate_dob(value):
    """Validate date of birth (DD/MM/YYYY format, age >= 18)"""
    value = value.strip()
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %m %Y"]
    for fmt in formats:
        try:
            dob = datetime.strptime(value, fmt)
            age = (datetime.now() - dob).days // 365
            if age < 18:
                return False, f"You must be at least 18 years old to apply. Your age appears to be {age}"
            if age > 100:
                return False, "Please enter a valid date of birth"
            return True, "Valid"
        except ValueError:
            continue
    return False, "Please enter date in DD/MM/YYYY format"


# Conversation State Management
conversation_history = []

application_data = {
    # Personal Details
    "full_name": None,
    "aadhaar_number": None,
    "pan_number": None,
    "date_of_birth": None,
    "gender": None,
    "category": None,
    "mobile_number": None,
    "email": None,
    "residential_address": None,
    
    # Business Details
    "business_name": None,
    "business_type": None,
    "business_description": None,
    "business_address": None,
    "business_status": None,       # existing or new
    "years_in_operation": None,    # only if existing
    "number_of_employees": None,
    
    # Loan Details
    "loan_category": None,         # Shishu / Kishore / Tarun
    "loan_amount": None,
    "loan_purpose": None,
    "preferred_bank": None,
    
    # Documents
    "documents_provided": []
}

# System Prompt
static_system_prompt = """
ROLE
You are a Government Digital Assistant helping citizens apply for a PM Mudra Yojana loan.
Your job is to collect information step-by-step and complete a structured application form.

IMPORTANT PRINCIPLE
This is a structured form collection task, not a general conversation.
You must only ask for missing information and validate user input.

The current application state will be provided separately as:
APPLICATION_DATA (fields already collected and fields still missing)

Your task is to determine the next field needed and ask the user for it.


APPLICATION FORM STRUCTURE

SECTION 1 — PERSONAL DETAILS
1. full_name
2. aadhaar_number (12 digits)
3. pan_number (ABCDE1234F format)
4. date_of_birth (DD/MM/YYYY)
5. gender (Male/Female/Other)
6. category (General/SC/ST/OBC/Minority)
7. mobile_number (10 digits)
8. email
9. residential_address

SECTION 2 — BUSINESS DETAILS
10. business_name
11. business_type (Manufacturing/Trading/Services)
12. business_description
13. business_address
14. business_status (Existing/New)
15. years_in_operation (ONLY if Existing)
16. employee_count

SECTION 3 — LOAN DETAILS
17. loan_category (Shishu/Kishore/Tarun)
18. loan_amount
19. loan_purpose (equipment / working capital / expansion)
20. preferred_bank

SECTION 4 — DOCUMENT CONFIRMATION
21. confirm_documents_ready

DOCUMENTS REQUIRED

Mandatory:
- Aadhaar card
- PAN card
- Passport size photo
- Address proof of business
- Bank statement (last 6 months)

Conditional:
- Business proof (if business is existing)
- Caste certificate (if category is SC/ST/OBC/Minority)



STRICT VALIDATION RULES

AADHAAR
- Must be exactly 12 digits
- No spaces, letters, or symbols
If invalid say:
"That doesn't look like a valid Aadhaar number. It must contain exactly 12 digits. Please re-enter."

PAN
- Format: 5 uppercase letters + 4 digits + 1 uppercase letter
Example: ABCDE1234F
If invalid say:
"That doesn't look like a valid PAN number. It must follow the format ABCDE1234F. Please re-enter."

MOBILE
- Must be exactly 10 digits
- Must start with 6, 7, 8, or 9
If invalid ask user to re-enter.

NEVER:
- Guess missing numbers
- Correct the user's value
- Accept invalid values



CONVERSATION RULES

1. Ask ONE question at a time.
2. Always ask for the next missing field in the form.
3. If the user provides multiple answers in one message, extract all valid ones.
4. If business_status = New → skip years_in_operation.
5. If category = General → caste certificate not required.
6. If business address = residential address → reuse it.

Always acknowledge the user's answer briefly before asking the next question.

Example style:
"Thank you. I've recorded your mobile number. Now please tell me your email address."

Use clear and simple Language.
Detect the language the user is writing in and always respond in that same language throughout the conversation



APPLICATION COMPLETION

When all fields are collected:

1. Show a structured summary of the application.
2. Ask the user to review the details.
3. Ask:
"Do you want to SUBMIT the application or change anything?"

Only when the user explicitly says "Submit", output:

FORM_COMPLETE
<JSON application object>

Do NOT output FORM_COMPLETE unless the user explicitly confirms submission.



OUTPUT STYLE

Your responses should contain:
- Friendly acknowledgement
- Next question

Never mention internal field names like "aadhaar_number".
Instead ask naturally.

Example:
Incorrect:
"Provide aadhaar_number."

Correct:
"Please enter your 12-digit Aadhaar number."



IMPORTANT

Use ONLY the provided APPLICATION_DATA to determine what to ask next.
Do not restart the form if data already exists.
Do not ask questions that already have answers.
"""


# Helper Functions
import json

def get_fields_needed():
    """Get list of fields that still need to be collected"""
    needed = []
    for key, value in application_data.items():
        if value is None:
            needed.append(key)
    # Remove years_in_operation if business is new
    if application_data.get("business_status", "").lower() == "new":
        if "years_in_operation" in needed:
            needed.remove("years_in_operation")
    return needed

def build_dynamic_prompt():
    """Build dynamic prompt with current application state"""
    collected = {k: v for k, v in application_data.items() if v is not None}
    needed = get_fields_needed()
    
    return f"""
CURRENT APPLICATION STATE:
Fields collected so far: {json.dumps(collected, indent=2)}
Fields still needed: {json.dumps(needed, indent=2)}
"""

def extract_form_data(response_text):
    """Extract JSON data from FORM_COMPLETE response"""
    if "FORM_COMPLETE" not in response_text:
        return None
    
    try:
        # Find the JSON block after FORM_COMPLETE
        json_start = response_text.find("{", response_text.find("FORM_COMPLETE"))
        json_end = response_text.rfind("}") + 1
        json_str = response_text[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        print(f"Could not parse form data: {e}")
        return None

def update_application_data(extracted_data):
    """Update application_data with extracted data"""
    if not extracted_data:
        return
    for key in application_data:
        if key in extracted_data and extracted_data[key]:
            application_data[key] = extracted_data[key]


# API Endpoints

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Health check endpoint"""
    return StatusResponse(status="ok")

@app.post("/reset", response_model=ResetResponse)
async def reset_conversation():
    """Reset conversation history and application data"""
    global conversation_history, application_data
    
    # Clear conversation history
    conversation_history = []
    
    # Reset application data
    application_data = {
        "full_name": None,
        "aadhaar_number": None,
        "pan_number": None,
        "date_of_birth": None,
        "gender": None,
        "category": None,
        "mobile_number": None,
        "email": None,
        "residential_address": None,
        "business_name": None,
        "business_type": None,
        "business_description": None,
        "business_address": None,
        "business_status": None,
        "years_in_operation": None,
        "number_of_employees": None,
        "loan_category": None,
        "loan_amount": None,
        "loan_purpose": None,
        "preferred_bank": None,
        "documents_provided": []
    }
    
    return ResetResponse(message="Conversation reset successfully")

@app.post("/chat")
async def chat(request: ChatRequest):
    """Process user message and return bot response"""
    try:
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": request.message
        })
        
        # Call Groq API with static + dynamic prompt and last 3 messages only
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": static_system_prompt + build_dynamic_prompt()}
            ] + conversation_history[-3:],
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message.content
        
        # Add response to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Check if form is complete
        if "FORM_COMPLETE" in assistant_message:
            extracted = extract_form_data(assistant_message)
            update_application_data(extracted)
            clean_response = assistant_message.split("FORM_COMPLETE")[0].strip()
            
            # TODO: Save to database and get application_id (will be implemented in Task 7)
            return {
                "response": clean_response,
                "form_complete": True,
                "application_id": None  # Will be populated after database integration
            }
        
        return {
            "response": assistant_message,
            "form_complete": False,
            "application_id": None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
