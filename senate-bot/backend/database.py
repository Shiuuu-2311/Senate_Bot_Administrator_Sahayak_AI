import sqlite3
from typing import Any, Dict, Optional
from datetime import datetime
import random

DB_FILE = "applications.db"


def _get_connection():
    """Get a SQLite database connection"""
    return sqlite3.connect(DB_FILE)


def init_db() -> None:
    """Initialize the SQLite database and applications table if they do not exist"""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id TEXT PRIMARY KEY,
                full_name TEXT,
                aadhaar_number TEXT,
                pan_number TEXT,
                date_of_birth TEXT,
                gender TEXT,
                category TEXT,
                mobile_number TEXT,
                email TEXT,
                residential_address TEXT,
                business_name TEXT,
                business_type TEXT,
                business_description TEXT,
                business_address TEXT,
                business_status TEXT,
                years_in_operation TEXT,
                number_of_employees TEXT,
                loan_category TEXT,
                loan_amount TEXT,
                loan_purpose TEXT,
                preferred_bank TEXT,
                status TEXT DEFAULT 'Pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Error creating applications table: {e}") from e


def generate_application_id() -> str:
    """Generate unique application ID in format MU-YYYYMMDD-XXXX"""
    max_retries = 10
    for _ in range(max_retries):
        # Get current date in YYYYMMDD format
        date_str = datetime.now().strftime("%Y%m%d")
        # Generate random 4-digit number
        random_num = random.randint(0, 9999)
        # Format as MU-YYYYMMDD-XXXX
        app_id = f"MU-{date_str}-{random_num:04d}"
        
        # Check if ID already exists
        if not application_id_exists(app_id):
            return app_id
    
    raise RuntimeError("Failed to generate unique application ID after maximum retries")


def application_id_exists(application_id: str) -> bool:
    """Check whether an application_id already exists in the database"""
    query = "SELECT 1 FROM applications WHERE application_id = ? LIMIT 1"
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (application_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except Exception as e:
        raise RuntimeError(f"Error checking application_id existence: {e}") from e


def save_application(application_data: Dict[str, Any], application_id: str, status: str = "Pending") -> None:
    """
    Save a completed application into the applications table.
    """
    query = """
        INSERT INTO applications (
            application_id,
            full_name,
            aadhaar_number,
            pan_number,
            date_of_birth,
            gender,
            category,
            mobile_number,
            email,
            residential_address,
            business_name,
            business_type,
            business_description,
            business_address,
            business_status,
            years_in_operation,
            number_of_employees,
            loan_category,
            loan_amount,
            loan_purpose,
            preferred_bank,
            status
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?
        )
    """

    values = (
        application_id,
        application_data.get("full_name"),
        application_data.get("aadhaar_number"),
        application_data.get("pan_number"),
        application_data.get("date_of_birth"),
        application_data.get("gender"),
        application_data.get("category"),
        application_data.get("mobile_number"),
        application_data.get("email"),
        application_data.get("residential_address"),
        application_data.get("business_name"),
        application_data.get("business_type"),
        application_data.get("business_description"),
        application_data.get("business_address"),
        application_data.get("business_status"),
        application_data.get("years_in_operation"),
        application_data.get("number_of_employees"),
        application_data.get("loan_category"),
        application_data.get("loan_amount"),
        application_data.get("loan_purpose"),
        application_data.get("preferred_bank"),
        status,
    )

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Error saving application: {e}") from e


def get_application_by_id(application_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single application by its application_id.
    """
    query = "SELECT * FROM applications WHERE application_id = ?"

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (application_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
            
        # Convert row to dictionary
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))
    except Exception as e:
        raise RuntimeError(f"Error fetching application by id: {e}") from e

