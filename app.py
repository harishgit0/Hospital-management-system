from flask import Flask
from flask import render_template, flash
from flask import request
from flask import redirect
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import date

# Ensure database folder exists
if not os.path.exists('database'):
    os.makedirs('database')

# Initializing setup
app = Flask(__name__)
app.secret_key = "secretkey123"

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'hospital.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)   # Increased length for hashed passwords
    role = db.Column(db.String(100), nullable=False, default='patient')
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient_profile = db.relationship('Patients', backref='user', lazy=True, uselist=False)
    doctor_profile = db.relationship('Doctors', backref='user', lazy=True, uselist=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Patients(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    emergency_contact = db.Column(db.String(15), nullable=False)
    medical_history = db.Column(db.String(500), nullable=False)
    # Relationships
    # appointments = db.relationship('Appointment', backref='patient', cascade="all, delete-orphan")

    medical_history_entries = db.relationship('MedicalHistory', backref='patient', lazy=True)


class MedicalHistory(db.Model):
    history_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    condition_name = db.Column(db.String(100), nullable=False)
    diagnosis_date = db.Column(db.Date, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(500))


class Departments(db.Model):
    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(300))
    # Relationships
    doctors = db.relationship('Doctors', backref='department', lazy=True)


class Doctors(db.Model):
    doctor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    consultation_fee = db.Column(db.Float, nullable=False)
    bio = db.Column(db.String(500))


class Appointments(db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id', ondelete='CASCADE'), nullable=False)
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    reason_for_visit = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    treatments = db.relationship(
        "Treatments",
        backref="appointment",
        cascade="all, delete-orphan"
    )
    patient = db.relationship('Patients', backref='appointments', lazy=True)
    doctor = db.relationship('Doctors', backref='appointments', lazy=True)


class Treatments(db.Model):
    treatment_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id',ondelete='CASCADE'), nullable=False)
    diagnosis = db.Column(db.String(100), nullable=False)
    prescription = db.Column(db.String(500), nullable=False)
    doctor_notes = db.Column(db.String(500), nullable=False)
    treatment_date = db.Column(db.DateTime, nullable=False)
    follow_up_required = db.Column(db.Boolean, nullable=False)
    follow_up_date = db.Column(db.DateTime)


class DoctorAvailability(db.Model):
    availability_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    doctor = db.relationship('Doctors', backref='availabilities', lazy=True)


class AppointmentSlots(db.Model):
    slot_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False, nullable=False)
    doctor = db.relationship('Doctors', backref='slots', lazy=True)


@app.route('/')
def index():
    return render_template('index.html')



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()

        if not user:
            flash("Invalid username!", "danger")
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash("Incorrect password!", "danger")
            return redirect(url_for('login'))

        # Store basic session info
        session['user_id'] = user.user_id
        session['role'] = user.role

        # LOGIN AS ADMIN
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))

        # LOGIN AS DOCTOR
        elif user.role == 'doctor':
            doctor = Doctors.query.filter_by(user_id=user.user_id).first()

            if doctor:
                session['doctor_id'] = doctor.doctor_id      # <── FIXED (important)
            else:
                flash("Doctor profile missing! Contact admin.", "danger")
                return redirect(url_for('login'))

            return redirect(url_for('doctor_dashboard'))

        # LOGIN AS PATIENT
        elif user.role == 'patient':
            patient = Patients.query.filter_by(user_id=user.user_id).first()

            if patient:
                session['patient_id'] = patient.patient_id
            else:
                flash("Patient profile missing! Contact admin.", "danger")
                return redirect(url_for('login'))

            return redirect(url_for('patient_dashboard'))

        else:
            flash("Unknown user role!", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")



# ✅ FIXED REGISTER ROUTE — Hash password
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        flash("All fields are required!", "danger")
        return redirect(url_for('register'))

    user = Users.query.filter_by(email=email).first()
    if user:
        flash("User already exists!", "danger")
        return redirect(url_for('register'))

    new_user = Users(username=username, email=email, role="patient")
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.flush()   # get user_id

    # CREATE PATIENT PROFILE
    new_patient = Patients(
        user_id=new_user.user_id,
        date_of_birth=datetime.utcnow(),
        gender="Not set",
        blood_group="NA",
        emergency_contact="NA",
        medical_history="None"
    )
    db.session.add(new_patient)

    db.session.commit()

    flash("User registered successfully!", "success")
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/patient/dashboard')
def patient_dashboard():
    patient_id = session.get('patient_id')
    

    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    patient = Patients.query.get(patient_id)

    if not patient:
        flash("Patient profile missing! Contact admin.", "danger")
        return redirect(url_for('login'))
    
    appointment=patient.appointments
    department=Departments.query.all()

    return render_template('patient_dashboard.html', patient=patient,appointments=appointment,departments=department)
@app.route("/patient/appointment")
def patient_appointment():
    patient_id = session.get('patient_id')
    
    patient = Patients.query.get(patient_id)

    appointment=patient.appointments
    department=Departments.query.all()
    return render_template("patient_appointment.html",patient=patient,appointments=appointment,departments=department)
@app.route("/patient/department")
def patient_department():
    department=Departments.query.all()
    return render_template("patient_department.html",departments=department)

@app.route("/patient/history")
def patient_history():
    patient_id = session.get('patient_id')
    
    patient = Patients.query.get(patient_id)

    appointment=patient.appointments
    department=Departments.query.all()
    treatment=Treatments.query.get(patient_id)
    return render_template("patient_history.html",patient=patient,appointments=appointment,departments=department,treatment=treatment)

@app.route("/patient/appointment/add", methods=["GET", "POST"])
def patient_fix_appointment():
    patient_id = session.get('patient_id')
    patient = Patients.query.get(patient_id)

    # Get all departments and doctors
    departments = Departments.query.all()
    doctors = Doctors.query.all()

    if request.method == "POST":
        doctor_id = request.form.get("doctor")
        slot_id = request.form.get("slot")  # selected slot id
        reason = request.form.get("reason")

        if not doctor_id or not slot_id or not reason:
            flash("All fields are required!", "danger")
            return redirect(request.url)

        slot = AppointmentSlots.query.get(slot_id)

        if not slot or slot.is_booked:
            flash("Selected slot is no longer available.", "danger")
            return redirect(request.url)

        # Create appointment
        new_appointment = Appointments(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=datetime.combine(slot.slot_date, slot.slot_time),
            reason_for_visit=reason,
            status="pending"
        )
        db.session.add(new_appointment)

        # Mark slot as booked
        slot.is_booked = True
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for("patient_appointment"))

    return render_template(
        "patient_fix_appointment.html",
        patient=patient,
        departments=departments,
        doctors=doctors)
@app.route("/patient/appointment/free_slots")
def patient_free_slots():
    doctor_id = request.args.get("doctor_id")
    slot_date = request.args.get("date")  # YYYY-MM-DD

    if not doctor_id or not slot_date:
        return {"error": "Doctor and date required"}, 400

    slots = AppointmentSlots.query.filter_by(
        doctor_id=doctor_id,
        slot_date=datetime.strptime(slot_date, "%Y-%m-%d").date(),
        is_booked=False
    ).all()

    slots_list = [{"id": slot.slot_id, "time": slot.slot_time.strftime("%I:%M %p")} for slot in slots]
    return {"slots": slots_list}

@app.route("/patient/appointment/delete/<int:appointment_id>", methods=["GET","POST"])
def delete_appointment(appointment_id):
    # if request.method == "POST":
    appointment = Appointments.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash("Appointment deleted successfully!", "success")
    return redirect(url_for("patient_appointment"))

@app.route("/patient/edit",methods=["GET","POST"])
def patient_edit():
    patient_id = session.get('patient_id')
    treatment=Treatments.query.get(patient_id)
    
    patient = Patients.query.get(patient_id)
    return render_template("patient_edit.html",patient=patient,treatment=treatment)


@app.route("/patient/appointment/reschedule/<int:appointment_id>", methods=["GET", "POST"])
def patient_reschedule(appointment_id):
    appointment = Appointments.query.get_or_404(appointment_id)

    if request.method == "POST":
        new_date = request.form.get("new_date")
        new_time = request.form.get("new_time")

        if not new_date or not new_time:
            flash("Both date and time are required!", "danger")
            return redirect(request.url)

        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        appointment.appointment_datetime = new_datetime
        db.session.commit()
        flash("Appointment rescheduled successfully!", "success")
        return redirect(url_for("patient_appointment"))

    return render_template("patient_reschedule.html", appointment=appointment)


@app.route('/admin/dashboard')
def admin_dashboard():
    total_patients = Patients.query.count()
    total_doctors = Doctors.query.count()
    total_appointments = Appointments.query.count()
    doctors=Doctors.query.all()
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html', total_patients=total_patients, total_doctors=total_doctors, total_appointments=total_appointments,doctors=doctors)
    return redirect(url_for('login'))

@app.route("/admin/patients")
def admin_patient():
    patient=Patients.query.all()
    return render_template("admin_patient.html",patients=patient)
@app.route("/admin/doctors")
def admin_doctor():
    doctor=Doctors.query.all()
    return render_template("admin_doctor.html",doctors=doctor)

@app.route("/admin/doctor/add", methods=["GET", "POST"])
def admin_add_doctor():
    departments = Departments.query.all()  # always fetch for GET and form

    if request.method == "POST":
        # Form data
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")
        address = request.form.get("address")
        email = request.form.get("email")
        department_id = request.form.get("department_id")  # must match form input name
        qualification = request.form.get("qualification")
        experience_years = request.form.get("experience_years")
        consultation_fee = request.form.get("consultation_fee")
        bio = request.form.get("bio")

        # Validate required fields
        if not all([fname, lname, username, password, phone, email, department_id, qualification, experience_years, consultation_fee]):
            flash("Please fill in all required fields!", "danger")
            return redirect(url_for("admin_add_doctor"))

        try:
            experience_years = int(experience_years)
            consultation_fee = float(consultation_fee)
        except ValueError:
            flash("Invalid number for experience or consultation fee!", "danger")
            return redirect(url_for("admin_add_doctor"))

        # Create User
        new_user = Users(
            username=username,
            email=email,
            role="doctor",
            fname=fname,
            lname=lname,
            phone=phone,
            address=address
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # get user_id before committing

        # Use selected department
        department = Departments.query.get(department_id)
        if not department:
            flash("Selected department not found!", "danger")
            return redirect(url_for("admin_add_doctor"))

        # Create Doctor
        new_doctor = Doctors(
            user_id=new_user.user_id,
            department_id=department.department_id,
            qualification=qualification,
            experience_years=experience_years,
            consultation_fee=consultation_fee,
            bio=bio
        )
        db.session.add(new_doctor)
        db.session.commit()

        flash("Doctor added successfully", "success")
        return redirect(url_for("admin_doctor"))

    return render_template("admin_add_doctor.html", departments=departments)
@app.route("/admin/patient/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    patient = Patients.query.get_or_404(patient_id)
    user = patient.user  # linked user account

    db.session.delete(patient)
    if user:
        db.session.delete(user)  # optionally delete user account
    db.session.commit()

    flash("Patient deleted successfully!", "success")
    return redirect(url_for("admin_patient"))
@app.route("/admin/doctor/delete/<int:doctor_id>", methods=["POST"])
def delete_doctor(doctor_id):
    doctor=Doctors.query.get_or_404(doctor_id)
    user = doctor.user  # linked user account

    db.session.delete(doctor)
    if user:
        db.session.delete(user)  # optionally delete user account
    db.session.commit()

    flash("Doctor deleted successfully!", "success")
    return redirect(url_for("admin_doctor"))
@app.route("/admin/patient/view/<int:patient_id>")
def view_patient(patient_id):
    patient = Patients.query.get_or_404(patient_id)
    # patient = Patients.query.get_or_404(patient_id)
    return render_template("admin_view_patient.html", patient=patient)

@app.route("/admin/appointment")
def admin_appointment():
    appointment=Appointments.query.all()
    return render_template("admin_appointment.html",appointments=appointment)



@app.route("/doctor/dashboard")
def doctor_dashboard():
    doctor_id = session.get('doctor_id')

    if not doctor_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    doctor = Doctors.query.get(doctor_id)

    if not doctor:
        flash("Doctor profile missing! Contact admin.", "danger")
        return redirect(url_for('login'))

    # Get doctor's appointments
    appointments = doctor.appointments

    # Get all departments
    departments = Departments.query.all()

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        appointments=appointments,
        departments=departments
    )

@app.route("/doctor/appointment")
def doctor_appointment():
    doctor_id=session.get('doctor_id')
    doctor=Doctors.query.get(doctor_id)
    appointment=doctor.appointments
    department=Departments.query.all()
    return render_template("doctor_appointment.html",appointments=appointment,doctor=doctor,departments=department)

@app.route("/doctor/patient")
def doctor_patient():
    doctor_id = session.get('doctor_id')

    if not doctor_id:
        flash("Session expired! Please login again.", "warning")
        return redirect(url_for('login'))

    doctor = Doctors.query.get(doctor_id)

    if not doctor:
        flash("Doctor profile missing! Contact admin.", "danger")
        return redirect(url_for('login'))

    # Fetch unique patients from doctor appointments
    patients = list({appt.patient for appt in doctor.appointments})

    return render_template("doctor_patient.html", doctor=doctor, patients=patients)



@app.route("/doctor/profile")
def doctor_profile():
    doctor_id = session.get('doctor_id')

    if not doctor_id:
        flash("Session expired! Please login again.", "warning")
        return redirect(url_for('login'))

    doctor = Doctors.query.get(doctor_id)

    if not doctor:
        flash("Doctor profile missing! Contact admin.", "danger")
        return redirect(url_for('login'))

    return render_template("doctor_profile.html", doctor=doctor)

@app.route('/doctor/<int:doctor_id>/slots')
def doctor_slots(doctor_id):
    doctor = Doctors.query.get_or_404(doctor_id)

    # Get today's date
    today = date.today()

    # Fetch all slots for this doctor for today
    slots_today = AppointmentSlots.query.filter_by(doctor_id=doctor_id, slot_date=today).all()

    # Filter out booked slots
    free_slots = [slot for slot in slots_today if not slot.is_booked]

    return render_template('doctor_slots.html', doctor=doctor, free_slots=free_slots)

# ✅ Admin auto-creation with hashed password
with app.app_context():
    db.create_all()

    admin_email = "admin@hospital.com"
    admin_user = Users.query.filter_by(email=admin_email).first()

    if not admin_user:
        admin = Users(
            username="admin",
            email=admin_email,
            role="admin",
            fname="System",
            lname="Admin",
            phone="0000000000",
            address="Hospital HQ"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin created with secure hashed password.")
    else:
        print("Admin already exists.")

if __name__ == '__main__':
    app.run(debug=True)
