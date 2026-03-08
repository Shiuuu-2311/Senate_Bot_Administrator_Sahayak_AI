import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error


load_dotenv()


DB_NAME = os.getenv("MYSQL_DATABASE", "senate_bot")

BASE_DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
}

FULL_DB_CONFIG = {
    **BASE_DB_CONFIG,
    "database": DB_NAME,
}


def _get_connection(include_database: bool = True):
    """
    Get a new MySQL connection.
    If include_database is False, connect without specifying the database (used for CREATE DATABASE).
    """
    config = FULL_DB_CONFIG if include_database else BASE_DB_CONFIG
    return mysql.connector.connect(**config)


def init_db() -> None:
    """
    Initialize the MySQL database and applications table if they do not exist.
    """
    # Create database if it doesn't exist
    try:
        with _get_connection(include_database=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
    except Error as e:
        # Let the caller surface this as a startup error if needed
        raise RuntimeError(f"Error creating database {DB_NAME}: {e}") from e

    # Create applications table if it doesn't exist
    try:
        with _get_connection(include_database=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS applications (
                        application_id VARCHAR(32) PRIMARY KEY,
                        full_name VARCHAR(255),
                        aadhaar_number VARCHAR(20),
                        pan_number VARCHAR(20),
                        date_of_birth VARCHAR(20),
                        gender VARCHAR(20),
                        category VARCHAR(50),
                        mobile_number VARCHAR(20),
                        email VARCHAR(255),
                        residential_address TEXT,
                        business_name VARCHAR(255),
                        business_type VARCHAR(100),
                        business_description TEXT,
                        business_address TEXT,
                        business_status VARCHAR(50),
                        years_in_operation VARCHAR(20),
                        number_of_employees VARCHAR(20),
                        loan_category VARCHAR(50),
                        loan_amount VARCHAR(50),
                        loan_purpose TEXT,
                        preferred_bank VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'Pending',
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                    """
                )
            conn.commit()
    except Error as e:
        raise RuntimeError(f"Error creating applications table: {e}") from e


def application_id_exists(application_id: str) -> bool:
    """
    Check whether an application_id already exists in the database.
    """
    query = "SELECT 1 FROM applications WHERE application_id = %s LIMIT 1"
    try:
        with _get_connection(include_database=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (application_id,))
                return cursor.fetchone() is not None
    except Error as e:
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
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
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
        with _get_connection(include_database=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
            conn.commit()
    except Error as e:
        raise RuntimeError(f"Error saving application: {e}") from e


def get_application_by_id(application_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single application by its application_id.
    """
    query = "SELECT * FROM applications WHERE application_id = %s"

    try:
        with _get_connection(include_database=True) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (application_id,))
                row = cursor.fetchone()
                return row if row is not None else None
    except Error as e:
        raise RuntimeError(f"Error fetching application by id: {e}") from e

