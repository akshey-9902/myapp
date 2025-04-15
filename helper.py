#!/usr/bin/env python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os, random

# Load environment variables from .env if available.
load_dotenv()

# Use the DB_URI from the .env file or default to SQLite.
DATABASE_URL = os.getenv("DB_URI", "sqlite:///dummy.db")

# Create the database engine.
engine = create_engine(DATABASE_URL, echo=True)

# Declarative base (SQLAlchemy 2.0 style)
Base = declarative_base()

# ---------------------------
# Dummy Models Definitions
# ---------------------------

class EmployeeMaster(Base):
    __tablename__ = "employee_master"
    pk = Column(Integer, primary_key=True)
    pf_number = Column(String(50))
    first_name = Column(String(255))
    name_hindi = Column(String(255))
    identifier_master_pk = Column(Integer)

class ProgrammeMaster(Base):
    __tablename__ = "programme_master"
    pk = Column(Integer, primary_key=True)
    programme_name = Column(String(255))

class StudentMasterProgrammeDetails(Base):
    __tablename__ = "student_master_programme_details"
    pk = Column(Integer, primary_key=True)
    employee_master_pk = Column(Integer, ForeignKey('employee_master.pk'))
    acad_programme_master_pk = Column(Integer, ForeignKey('programme_master.pk'))
    acad_branch_master_pk = Column(Integer)
    batch = Column(String(10))
    specialization_master_pk = Column(Integer)
    pg_status = Column(Integer)

class AcadDegreeNamePrint(Base):
    __tablename__ = "acad_degree_name_print"
    pk = Column(Integer, primary_key=True)
    acad_branch_master_pk = Column(Integer)
    programme_pk = Column(Integer, ForeignKey('programme_master.pk'))
    batch = Column(String(10))
    specialization_pk = Column(Integer)
    english_prog_name = Column(String(255))
    engish_spec_name = Column(String(255))
    hindi_prog_name = Column(String(255))
    hindi_spec_name = Column(String(255))  # Correct spelling

class AcadCourseGradeCPI(Base):
    __tablename__ = "acad_course_grade_cpi"
    pk = Column(Integer, primary_key=True)
    student_pk = Column(Integer)
    flag = Column(Integer)
    cpi = Column(String(50))

class DGPA(Base):
    __tablename__ = "dgpa"
    pk = Column(Integer, primary_key=True)
    employee_master_pk = Column(Integer)
    flag = Column(Integer)
    dgpa = Column(String(50))

class AcadStudentWarningAP(Base):
    __tablename__ = "acad_student_warning_ap"
    pk = Column(Integer, primary_key=True)
    employee_master_pk = Column(Integer)
    flag = Column(Integer)
    wap = Column(Integer)
    acad_session_master_pk = Column(Integer)
    acad_semester_pk = Column(Integer)

# New dummy model: AcadSessionMaster.
class AcadSessionMaster(Base):
    __tablename__ = "acad_session_master"
    pk = Column(Integer, primary_key=True)
    given_year = Column(String(10))
    given_month = Column(String(50))
    given_day = Column(String(10))
    convo_year = Column(String(10))
    convo_day = Column(String(10))
    completion_year = Column(String(10))
    convo_month_hindi = Column(String(50))
    # Optionally, you could add more columns like session_name, etc.

# ---------------------------
# Function to Reset Database and Insert Dummy Data
# ---------------------------
def reset_database():
    # Drop all tables and recreate them to avoid duplicates.
    print("Resetting the database (dropping and recreating tables)...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database reset complete.")

def insert_dummy_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Number of dummy employee records to create:
    n = 100

    # Insert one AcadSessionMaster record (dummy session details).
    session_master = AcadSessionMaster(
        pk=1,
        given_year="2020",
        given_month="October",
        given_day="15",
        convo_year="2020",
        convo_day="16",
        completion_year="2020",
        convo_month_hindi="अक्टूबर"
    )
    session.add(session_master)
    
    # Insert ProgrammeMaster records.
    programme1 = ProgrammeMaster(pk=1, programme_name="Bachelor of Technology")
    programme2 = ProgrammeMaster(pk=2, programme_name="Master of Science")
    session.add_all([programme1, programme2])
    session.commit()
    
    # For each employee, create unique records and associated related records.
    for i in range(1, n + 1):
        # Create an employee.
        employee = EmployeeMaster(
            pk=i,
            pf_number=f"E{str(i).zfill(3)}",   # e.g., E001, E002, ...
            first_name=f"John{i}",
            name_hindi=f"जॉन{i}",
            identifier_master_pk=2  # For query filtering.
        )
        session.add(employee)
        session.flush()
        
        # Randomly assign a programme (1 or 2) and other attributes.
        prog_pk = random.choice([1, 2])
        branch = random.randint(101, 105)
        batch = "2020" if prog_pk == 1 else "2021"
        specialization = random.randint(200, 205)
        
        # Create StudentMasterProgrammeDetails record.
        student = StudentMasterProgrammeDetails(
            pk=i,  # Use same pk as employee.
            employee_master_pk=employee.pk,
            acad_programme_master_pk=prog_pk,
            acad_branch_master_pk=branch,
            batch=batch,
            specialization_master_pk=specialization,
            pg_status=1
        )
        session.add(student)
        
        # Create AcadDegreeNamePrint record.
        degree_print = AcadDegreeNamePrint(
            pk=i,
            acad_branch_master_pk=branch,
            programme_pk=prog_pk,
            batch=batch,
            specialization_pk=specialization,
            english_prog_name="B.Tech" if prog_pk == 1 else "M.Sc",
            engish_spec_name="Computer Science" if prog_pk == 1 else "Physics",
            hindi_prog_name="बी.टेक" if prog_pk == 1 else "एम.एससी",
            hindi_spec_name="कंप्यूटर विज्ञान" if prog_pk == 1 else "भौतिकी"
        )
        session.add(degree_print)
        
        # Create AcadCourseGradeCPI record with a random CPI.
        cpi_val = f"{random.uniform(6.0, 10.0):.2f}"
        course_grade = AcadCourseGradeCPI(
            pk=i,
            student_pk=employee.pk,
            flag=1,
            cpi=cpi_val
        )
        session.add(course_grade)
        
        # Create DGPA record with a random DGPA.
        dgpa_val = f"{random.uniform(6.0, 10.0):.2f}"
        dgpa_record = DGPA(
            pk=i,
            employee_master_pk=employee.pk,
            flag=1,
            dgpa=dgpa_val
        )
        session.add(dgpa_record)
        
        # Create AcadStudentWarningAP record.
        warning = AcadStudentWarningAP(
            pk=i,
            employee_master_pk=employee.pk,
            flag=1,
            wap=6,
            acad_session_master_pk=1,  # Linking to the dummy session record.
            acad_semester_pk=random.choice([1, 2])
        )
        session.add(warning)
    
    session.commit()
    print(f"Inserted dummy data for {n} employees and associated records.")

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == '__main__':
    reset_database()
    insert_dummy_data()
