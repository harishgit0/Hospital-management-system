# app.py (cleaned & corrected)
from flask import Flask, render_template, flash, request, redirect, url_for, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

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


# -----------------------------
# Models
# -----------------------------
class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='patient')
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

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
    status = db.Column(db.String(20), nullable=False, default="pending")
    reason_for_visit = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    treatments = db.relationship(
        "Treatments",
        backref="appointment",
        cascade="all, delete-orphan"
    )
    patient = db.relationship('Patients', backref='appointments', lazy=True)
    doctor = db.relationship('Doctors', backref='appointments', lazy=True)


class Treatments(db.Model):
    treatment_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id', ondelete='CASCADE'), nullable=False)
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

# Register models AFTER they are defined
app.jinja_env.globals['AppointmentSlots'] = AppointmentSlots


# -----------------------------
# Helpers
# -----------------------------
def ensure_logged_in(role=None):
    """Return True if session is valid; otherwise redirect/abort in caller."""
    if 'user_id' not in session:
        return False
    if role and session.get('role') != role:
        return False
    return True


# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        print("New message received:", name, email, message)

        # You can later save to DB or send email here

        flash("Message sent successfully!", "success")
        return redirect(url_for('contact_us'))

    return render_template('contact_us.html')


# -----------------------------
# Auth
# -----------------------------
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()

        if not user:
            flash("Invalid username!", "danger")
            return redirect(url_for('login'))

        if not user.check_password(password):
            flash("Incorrect password!", "danger")
            return redirect(url_for('login'))

        session['user_id'] = user.user_id
        session['role'] = user.role

        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'doctor':
            doctor = Doctors.query.filter_by(user_id=user.user_id).first()
            if doctor:
                session['doctor_id'] = doctor.doctor_id
            else:
                flash("Doctor profile missing! Contact admin.", "danger")
                return redirect(url_for('login'))
            return redirect(url_for('doctor_dashboard'))
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

    existing = Users.query.filter_by(email=email).first()
    if existing:
        flash("User already exists!", "danger")
        return redirect(url_for('register'))

    new_user = Users(username=username, email=email, role="patient")
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.flush()

    # Create patient profile (use date only)
    new_patient = Patients(
        user_id=new_user.user_id,
        date_of_birth=datetime.utcnow().date(),
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
    session.pop('role', None)
    session.pop('doctor_id', None)
    session.pop('patient_id', None)
    flash("Logged out.", "info")
    return redirect(url_for('index'))


# -----------------------------
# Patient area
# -----------------------------
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

    appointments = patient.appointments
    departments = Departments.query.all()

    return render_template('patient_dashboard.html', patient=patient, appointments=appointments, departments=departments)


@app.route("/patient/appointment")
def patient_appointment():
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    patient = Patients.query.get(patient_id)
    appointments = patient.appointments
    departments = Departments.query.all()
    return render_template("patient_appointment.html", patient=patient, appointments=appointments, departments=departments)


@app.route("/patient/department")
def patient_department():
    departments = Departments.query.all()
    return render_template("patient_department.html", departments=departments)


@app.route("/patient/history")
def patient_history():
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    patient = Patients.query.get(patient_id)
    appointments = patient.appointments
    departments = Departments.query.all()

    treatments = (
        Treatments.query
        .join(Appointments, Treatments.appointment_id == Appointments.appointment_id)
        .filter(Appointments.patient_id == patient_id)
        .all()
    )

    return render_template("patient_history.html", patient=patient, appointments=appointments, departments=departments, treatment=treatments)


@app.route("/patient/appointment/add", methods=["GET", "POST"])
def patient_fix_appointment():
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    patient = Patients.query.get(patient_id)

    departments = Departments.query.all()
    doctors = Doctors.query.all()

    if request.method == "POST":
        doctor_id = request.form.get("doctor")
        slot_id = request.form.get("slot")
        reason = request.form.get("reason")

        if not doctor_id or not slot_id or not reason:
            flash("All fields are required!", "danger")
            return redirect(request.url)

        slot = AppointmentSlots.query.get(slot_id)
        if not slot or slot.is_booked:
            flash("Selected slot is no longer available.", "danger")
            return redirect(request.url)

        new_appointment = Appointments(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=datetime.combine(slot.slot_date, slot.slot_time),
            reason_for_visit=reason,
            status="pending"
        )
        slot.is_booked = True
        db.session.add(new_appointment)
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for("patient_appointment"))

    return render_template("patient_fix_appointment.html", patient=patient, departments=departments, doctors=doctors)


@app.route("/patient/appointment/free_slots")
def patient_free_slots():
    doctor_id = request.args.get("doctor_id")
    slot_date = request.args.get("date")  # YYYY-MM-DD

    if not doctor_id or not slot_date:
        return {"error": "Doctor and date required"}, 400

    try:
        slot_date_obj = datetime.strptime(slot_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format"}, 400

    slots = AppointmentSlots.query.filter_by(
        doctor_id=doctor_id,
        slot_date=slot_date_obj,
        is_booked=False
    ).all()

    slots_list = [{"id": slot.slot_id, "time": slot.slot_time.strftime("%I:%M %p")} for slot in slots]
    return {"slots": slots_list}


@app.route("/patient/appointment/delete/<int:appointment_id>", methods=["GET", "POST"])
def delete_appointment(appointment_id):
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    appointment = Appointments.query.get_or_404(appointment_id)

    # Security: ensure the patient owns this appointment (or admin)
    if appointment.patient_id != patient_id and session.get('role') != 'admin':
        abort(403)

    # Find linked slot and free it
    slot = AppointmentSlots.query.filter_by(
        doctor_id=appointment.doctor_id,
        slot_date=appointment.appointment_datetime.date(),
        slot_time=appointment.appointment_datetime.time()
    ).first()

    if slot:
        slot.is_booked = False

    db.session.delete(appointment)
    db.session.commit()
    flash("Appointment deleted successfully!", "success")
    return redirect(url_for("patient_appointment"))


@app.route("/patient/edit", methods=["GET", "POST"])
def patient_edit():
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    patient = Patients.query.get(patient_id)

    if request.method == "POST":
        # Update some editable patient fields (example)
        patient.gender = request.form.get("gender", patient.gender)
        dob = request.form.get("date_of_birth")
        if dob:
            try:
                patient.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format for date of birth.", "danger")
                return redirect(request.url)
        patient.blood_group = request.form.get("blood_group", patient.blood_group)
        patient.emergency_contact = request.form.get("emergency_contact", patient.emergency_contact)
        patient.medical_history = request.form.get("medical_history", patient.medical_history)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("patient_dashboard"))

    # GET
    treatments = Treatments.query.join(Appointments).filter(Appointments.patient_id == patient_id).all()
    return render_template("patient_edit.html", patient=patient, treatment=treatments)


@app.route("/patient/appointment/reschedule/<int:appointment_id>", methods=["GET", "POST"])
def patient_reschedule(appointment_id):
    patient_id = session.get('patient_id')
    if not patient_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    appointment = Appointments.query.get_or_404(appointment_id)

    # Security: ensure the patient owns this appointment (or admin)
    if appointment.patient_id != patient_id and session.get('role') != 'admin':
        abort(403)

    if request.method == "POST":
        new_date = request.form.get("new_date")
        new_time = request.form.get("new_time")
        if not new_date or not new_time:
            flash("Both date and time are required!", "danger")
            return redirect(request.url)

        try:
            new_dt = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date/time format.", "danger")
            return redirect(request.url)

        # Check if corresponding slot exists and is free
        slot = AppointmentSlots.query.filter_by(
            doctor_id=appointment.doctor_id,
            slot_date=new_dt.date(),
            slot_time=new_dt.time()
        ).first()

        if not slot:
            flash("Selected slot does not exist.", "danger")
            return redirect(request.url)

        if slot.is_booked:
            flash("Selected slot is already booked.", "danger")
            return redirect(request.url)

        # Free old slot if exists
        old_slot = AppointmentSlots.query.filter_by(
            doctor_id=appointment.doctor_id,
            slot_date=appointment.appointment_datetime.date(),
            slot_time=appointment.appointment_datetime.time()
        ).first()
        if old_slot:
            old_slot.is_booked = False

        # Book new slot & update appointment
        slot.is_booked = True
        appointment.appointment_datetime = new_dt
        db.session.commit()
        flash("Appointment rescheduled successfully!", "success")
        return redirect(url_for("patient_appointment"))

    return render_template("patient_reschedule.html", appointment=appointment)


# -----------------------------
# Admin area
# -----------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    total_patients = Patients.query.count()
    total_doctors = Doctors.query.count()
    total_appointments = Appointments.query.count()
    doctors = Doctors.query.all()
    return render_template('admin_dashboard.html', total_patients=total_patients, total_doctors=total_doctors, total_appointments=total_appointments, doctors=doctors)


@app.route("/admin/patients")
def admin_patient():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    patients = Patients.query.all()
    return render_template("admin_patient.html", patients=patients)


@app.route("/admin/doctors")
def admin_doctor():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    doctors = Doctors.query.all()
    return render_template("admin_doctor.html", doctors=doctors)


@app.route("/admin/doctor/add", methods=["GET", "POST"])
def admin_add_doctor():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    departments = Departments.query.all()
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        username = request.form.get("username")
        password = request.form.get("password")
        phone = request.form.get("phone")
        address = request.form.get("address")
        email = request.form.get("email")
        department_id = request.form.get("department_id")
        qualification = request.form.get("qualification")
        experience_years = request.form.get("experience_years")
        consultation_fee = request.form.get("consultation_fee")
        bio = request.form.get("bio")

        if not all([fname, lname, username, password, phone, email, department_id, qualification, experience_years, consultation_fee]):
            flash("Please fill in all required fields!", "danger")
            return redirect(url_for("admin_add_doctor"))

        try:
            experience_years = int(experience_years)
            consultation_fee = float(consultation_fee)
        except ValueError:
            flash("Invalid number for experience or consultation fee!", "danger")
            return redirect(url_for("admin_add_doctor"))

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
        db.session.flush()

        department = Departments.query.get(department_id)
        if not department:
            flash("Selected department not found!", "danger")
            return redirect(url_for("admin_add_doctor"))

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
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    patient = Patients.query.get_or_404(patient_id)
    user = patient.user

    db.session.delete(patient)
    if user:
        db.session.delete(user)
    db.session.commit()

    flash("Patient deleted successfully!", "success")
    return redirect(url_for("admin_patient"))


@app.route("/admin/doctor/delete/<int:doctor_id>", methods=["POST"])
def delete_doctor(doctor_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    doctor = Doctors.query.get_or_404(doctor_id)
    user = doctor.user

    db.session.delete(doctor)
    if user:
        db.session.delete(user)
    db.session.commit()

    flash("Doctor deleted successfully!", "success")
    return redirect(url_for("admin_doctor"))


@app.route("/admin/patient/view/<int:patient_id>")
def view_patient(patient_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    patient = Patients.query.get_or_404(patient_id)
    return render_template("admin_view_patient.html", patient=patient)


@app.route("/admin/appointment")
def admin_appointment():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    appointment = Appointments.query.all()
    return render_template("admin_appointment.html", appointments=appointment)


# -----------------------------
# Doctor area
# -----------------------------
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

    appointments = doctor.appointments
    departments = Departments.query.all()
    patients = list({appt.patient for appt in doctor.appointments})
    return render_template("doctor_dashboard.html", doctor=doctor, appointments=appointments, departments=departments, patients=patients)


@app.route("/doctor/appointment")
def doctor_appointment():
    doctor_id = session.get('doctor_id')
    if not doctor_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('login'))

    doctor = Doctors.query.get(doctor_id)
    appointment = doctor.appointments
    departments = Departments.query.all()
    return render_template("doctor_appointment.html", appointments=appointment, doctor=doctor, departments=departments)


@app.route("/doctor/booked-dates")
def doctor_booked_dates():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        return jsonify([])

    booked = Appointments.query.filter_by(doctor_id=doctor_id).all()
    booked_set = {
        appt.appointment_datetime.date().strftime("%Y-%m-%d")
        for appt in booked
    }

    return jsonify(sorted(list(booked_set)))


@app.route("/doctor/add-appointment", methods=["GET", "POST"])
def doctor_add_appointment():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Session expired! Please login again.", "warning")
        return redirect(url_for('login'))

    slots = []
    selected_date = None

    if request.method == "POST":
        # Get date from form
        selected_date = request.form.get("date")
        patient_id = request.form.get("patient")
        slot_id = request.form.get("slot")
        reason = request.form.get("reason")

        if not selected_date or not patient_id or not slot_id or not reason:
            flash("All fields are required!", "danger")
            return redirect(request.url)

        try:
            sel_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date selected!", "danger")
            return redirect(request.url)

        slot = AppointmentSlots.query.get(slot_id)
        if not slot or slot.is_booked:
            flash("Invalid or already booked slot selected!", "danger")
            return redirect(request.url)

        # Create appointment
        new_appointment = Appointments(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_datetime=datetime.combine(slot.slot_date, slot.slot_time),
            reason_for_visit=reason,
            status="approved"
        )
        slot.is_booked = True
        db.session.add(new_appointment)
        db.session.commit()
        flash("Appointment added successfully!", "success")
        return redirect(url_for("doctor_appointment"))

    # If GET request or after POST validation error, load available slots
    # Check if date is provided via GET parameters (optional)
    if request.method == "GET":
        selected_date = request.args.get("date")

    if selected_date:
        try:
            sel_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            slots = AppointmentSlots.query.filter_by(doctor_id=doctor_id, slot_date=sel_date).all()
        except ValueError:
            slots = []

    # Get patients of the doctor (from previous appointments)
    patients = list({appt.patient for appt in Doctors.query.get(doctor_id).appointments})

    return render_template(
        "doctor_add_appointment.html",
        selected_date=selected_date,
        patients=patients,
        slots=slots
    )

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
    # By default show today's slots; you can expand to a range or accept a date query param
    today = date.today()
    slots_today = AppointmentSlots.query.filter_by(doctor_id=doctor_id, slot_date=today).all()
    free_slots = [slot for slot in slots_today if not slot.is_booked]
    return render_template('doctor_slots.html', doctor=doctor, free_slots=free_slots)


# -----------------------------
# DB init & default admin
# -----------------------------
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