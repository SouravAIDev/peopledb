from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, Session, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# FastAPI app initialization
app = FastAPI()

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()

# Database Models
class PersonDB(Base):
    __tablename__ = "person"
    
    id = Column(Integer, primary_key=True, index=True)  # The id is auto-incremented
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    
    educations = relationship("EducationDB", back_populates="person")
    skills = relationship("SkillDB", back_populates="person")



class EducationDB(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, index=True)
    degree = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    institute = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey("person.id"))

    # Relationship
    person = relationship("PersonDB", back_populates="educations")


class SkillDB(Base):
    __tablename__ = "skill"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, nullable=False)
    proficiency = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey("person.id"))

    # Relationship
    person = relationship("PersonDB", back_populates="skills")


# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class Education(BaseModel):
    degree: str
    cgpa: float
    institute: str

    class Config:
        orm_mode = True


class Skill(BaseModel):
    skill_name: str
    proficiency: str

    class Config:
        orm_mode = True

from typing import Optional, List

class PersonCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    educations: List[Education] = []
    skills: List[Skill] = []

class PersonResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    educations: List[Education] = []
    skills: List[Skill] = []

    class Config:
        orm_mode = True

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.post("/persons/", response_model=PersonResponse)
def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    # Check if the email already exists
    db_person = db.query(PersonDB).filter(PersonDB.email == person.email).first()
    if db_person:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create a new Person
    new_person = PersonDB(
        name=person.name,
        email=person.email,
        phone_number=person.phone_number,
    )
    db.add(new_person)
    db.commit()
    db.refresh(new_person)  # This will refresh the object and populate the ID

    # Add educations
    for edu in person.educations:
        new_education = EducationDB(
            degree=edu.degree,
            cgpa=edu.cgpa,
            institute=edu.institute,
            person_id=new_person.id,
        )
        db.add(new_education)

    # Add skills
    for skill in person.skills:
        new_skill = SkillDB(
            skill_name=skill.skill_name,
            proficiency=skill.proficiency,
            person_id=new_person.id,
        )
        db.add(new_skill)

    db.commit()
    db.refresh(new_person)

    # Return the newly created person, which will include the ID
    return new_person

@app.get("/persons/{person_id}", response_model=PersonResponse)
def read_person(person_id: int, db: Session = Depends(get_db)):
    person = db.query(PersonDB).filter(PersonDB.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

