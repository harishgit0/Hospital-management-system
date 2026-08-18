# Hospital Management System

A role-based hospital management web application for administrators, doctors, and patients, focused on appointment scheduling, medical records, doctor availability, and treatment workflows.

## Overview

The Hospital Management System provides separate workflows for **Admin**, **Doctor**, and **Patient** users. It supports patient registration, doctor and department management, appointment booking and rescheduling, treatment records, and doctor availability through a relational database-backed web application.

## Key Features

### Authentication & Roles
- User registration and login
- Password hashing with Werkzeug
- Session-based authentication
- Role-based dashboards for Admin, Doctor, and Patient users

### Patient
- View personal dashboard and profile
- Browse departments and doctors
- Book appointments using available appointment slots
- Cancel appointments and release the associated slot
- Reschedule appointments to another available slot
- View appointment and treatment history
- Update patient profile and medical information

### Admin
- Dashboard with patient, doctor, and appointment counts
- View and manage patients
- Add and manage doctors
- View all appointments
- Manage doctor and patient records

### Clinical Data
- Patient medical-history records
- Doctor departments and professional details
- Appointment lifecycle management
- Treatment records with diagnosis, prescription, notes, and follow-up information
- Doctor availability and appointment-slot management

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | Jinja2, HTML, CSS, Bootstrap |
| Database | SQLite |
| ORM | Flask-SQLAlchemy / SQLAlchemy |
| Authentication | Flask sessions, Werkzeug password hashing |

## Data Model

The application uses relational models including:

- **Users** — common authentication and role information
- **Patients** — patient-specific profile and medical data
- **MedicalHistory** — historical patient conditions and notes
- **Departments** — hospital departments
- **Doctors** — doctor profile, department, qualification, experience, and consultation details
- **Appointments** — patient-doctor appointments and status
- **Treatments** — diagnosis, prescription, notes, and follow-up details
- **DoctorAvailability** — doctor availability periods
- **AppointmentSlots** — individual bookable time slots

Relationships and cascade rules are used to keep related appointment and treatment data consistent when records are removed.

## Project Structure

```text
Hospital-management-system/
├── app.py
├── requirements.txt
├── database/
├── static/
├── templates/
├── .gitignore
└── README.md
```

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/harishgit0/Hospital-management-system.git
cd Hospital-management-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it, then install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

Open the local Flask development URL shown in the terminal.

## What This Project Demonstrates

- Relational database modelling
- Multi-role application design
- Authentication and authorization workflows
- Appointment scheduling and slot management
- CRUD operations with business rules
- Cascading relationships between appointments and treatments
- Server-rendered Flask application development

## Author

**Harish Chauhan**  
BS Data Science & Applications, IIT Madras
