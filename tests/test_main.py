import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db, Base, PersonCreate, PersonResponse

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_person():
    person_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone_number": "1234567890",
        "educations": [],
        "skills": []
    }
    response = client.post("/persons/", json=person_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == person_data["name"]
    assert data["email"] == person_data["email"]
    assert data["phone_number"] == person_data["phone_number"]
    assert "id" in data
    assert data["educations"] == person_data["educations"]
    assert data["skills"] == person_data["skills"]

def test_read_person():
    # First, create a person
    person_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone_number": "9876543210",
        "educations": [],
        "skills": []
    }
    create_response = client.post("/persons/", json=person_data)
    create_data = create_response.json()
    person_id = create_data["id"]

    # Now, read the person
    response = client.get(f"/persons/{person_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == person_data["name"]
    assert data["email"] == person_data["email"]
    assert data["phone_number"] == person_data["phone_number"]
    assert data["id"] == person_id
    assert data["educations"] == person_data["educations"]
    assert data["skills"] == person_data["skills"]

def test_create_person_invalid_data():
    invalid_person_data = {
        "name": "Invalid Person",
        "email": "invalid-email",
        "phone_number": "123",
        "educations": [],
        "skills": []
    }
    response = client.post("/persons/", json=invalid_person_data)
    assert response.status_code == 422  # Unprocessable Entity

def test_read_person_not_found():
    response = client.get("/persons/9999")  # Assuming 9999 is an ID that doesn't exist
    assert response.status_code == 404

def test_create_person_with_education_and_skills():
    person_data = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone_number": "5551234567",
        "educations": [
            {"degree": "Bachelor's", "cgpa": 3.5, "institute": "Example University"}
        ],
        "skills": [
            {"skill_name": "Python", "proficiency": "Advanced"}
        ]
    }
    response = client.post("/persons/", json=person_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == person_data["name"]
    assert data["email"] == person_data["email"]
    assert data["phone_number"] == person_data["phone_number"]
    assert len(data["educations"]) == len(person_data["educations"])
    assert len(data["skills"]) == len(person_data["skills"])
    assert "id" in data

def test_create_person_duplicate_email():
    # First, create a person
    person_data = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone_number": "1231231234",
        "educations": [],
        "skills": []
    }
    client.post("/persons/", json=person_data)

    # Try to create another person with the same email
    duplicate_person_data = {
        "name": "Another Bob",
        "email": "bob@example.com",
        "phone_number": "4564564567",
        "educations": [],
        "skills": []
    }
    response = client.post("/persons/", json=duplicate_person_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

# Add more test cases as needed