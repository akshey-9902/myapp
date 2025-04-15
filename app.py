import eventlet
eventlet.monkey_patch()
import os
import io
import zipfile
import subprocess
import sys
import tempfile
import threading
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from docxtpl import DocxTemplate
from dotenv import load_dotenv
from sqlalchemy import or_, text, inspect

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['TEMPLATE_PATH'] = os.getenv('TEMPLATE', 'AIB Degree - Copy.docx')
app.config['OUTPUT_DIR'] = os.getenv('OUTPUT_DIR', 'output')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

# ------------------------------
# Models (for reference)
# ------------------------------

class Degree(db.Model):
    __tablename__ = 'degrees'
    entryno = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    name_hindi = db.Column(db.String)
    spec_name = db.Column(db.String)
    spec_name_hindi = db.Column(db.String)
    degree_name = db.Column(db.String)
    degree_name_hindi = db.Column(db.String)
    completion_year = db.Column(db.String)
    convo_day = db.Column(db.String)
    convo_month_hindi = db.Column(db.String)
    convo_year = db.Column(db.String)
    degree_gpa = db.Column(db.String)
    given_day = db.Column(db.String)
    given_month = db.Column(db.String)
    given_year = db.Column(db.String)

# In this approach, we do not create a temporary "GeneratedDegree" table;
# instead, we fetch query results directly and pass them on.

# ------------------------------
# User authentication model
# ------------------------------

class User(UserMixin):
    id = 1
    username = os.getenv('ADMIN_USER', 'admin')
    password = os.getenv('ADMIN_PASS', 'admin123')

@login_manager.user_loader
def load_user(user_id):
    return User() if str(user_id) == '1' else None

# ------------------------------
# Helper functions for template data
# ------------------------------

def convert_record_to_context(record: dict) -> dict:
    mapping = {
        'entryno': 'entryNumber',
        'name': 'name',
        'name_hindi': 'name_hindi',
        'spec_name': 'spec_name',
        'spec_name_hindi': 'spec_name_hindi',
        'degree_name': 'degree_name',
        'degree_name_hindi': 'degree_name_hindi',
        'completion_year': 'completionYear',
        'convo_day': 'convo_day',
        'convo_month_hindi': 'convo_month_hindi',
        'convo_year': 'convo_year',
        'degree_gpa': 'degreeGPA',
        'given_day': 'givenDay',
        'given_month': 'givenMonth',
        'given_year': 'givenYear'
    }
    return {new_key: record.get(old_key, '') for old_key, new_key in mapping.items()}

def render_docx(context: dict) -> io.BytesIO:
    tpl = DocxTemplate(app.config['TEMPLATE_PATH'])
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)
    return buf

def convert_worker(docx_path, max_retries=100):
    pdf_path = os.path.join(
        os.path.dirname(docx_path),
        os.path.basename(docx_path).replace('.docx', '.pdf')
    )
    libreoffice_cmd = os.getenv('LIBREOFFICE_PATH', 'libreoffice')
    attempt = 0
    while attempt < max_retries:
        try:
            time.sleep(1)
            subprocess.run([libreoffice_cmd, '--headless', '--convert-to', 'pdf', docx_path,
                            '--outdir', os.path.dirname(docx_path)], check=True)
            break
        except subprocess.CalledProcessError as e:
            attempt += 1
            app.logger.error(f"Attempt {attempt}/{max_retries} failed for {docx_path}: {e}")
            time.sleep(2)
    else:
        app.logger.error(f"Failed converting {docx_path} after {max_retries} attempts.")
    return pdf_path

# Dummy helper functions for dropdown data.

def get_sessions():
    return [
        {'pk': 1, 'session_name': "2017-2018", 'session_short_name': "2017-18"},
        {'pk': 2, 'session_name': "2016-2017", 'session_short_name': "2016-17"},
        {'pk': 3, 'session_name': "2015-2016", 'session_short_name': "2015-16"},
        {'pk': 4, 'session_name': "2014-2015", 'session_short_name': "2014-15"},
        {'pk': 5, 'session_name': "2013-2014", 'session_short_name': "2013-14"},
        {'pk': 6, 'session_name': "2012-2013", 'session_short_name': "2012-13"},
        {'pk': 7, 'session_name': "2011-2012", 'session_short_name': "2011-12"},
        {'pk': 8, 'session_name': "2010-2011", 'session_short_name': "2010-11"},
        {'pk': 9, 'session_name': "2009-2010", 'session_short_name': "2009-10"},
        {'pk': 10, 'session_name': "2018-2019", 'session_short_name': "2018-19"},
        {'pk': 11, 'session_name': "2007-2008", 'session_short_name': "2007-08"},
        {'pk': 12, 'session_name': "2008-2009", 'session_short_name': "2008-09"},
        {'pk': 13, 'session_name': "2006-2007", 'session_short_name': "2006-07"},
        {'pk': 14, 'session_name': "2019-2020", 'session_short_name': "2019-20"},
        {'pk': 16, 'session_name': "2020-2021", 'session_short_name': "2020-21"},
        {'pk': 17, 'session_name': "2021-2022", 'session_short_name': "2021-22"},
        {'pk': 18, 'session_name': "2022-2023", 'session_short_name': "2022-23"},
        {'pk': 19, 'session_name': "2023-2024", 'session_short_name': "2023-24"},
        {'pk': 20, 'session_name': "2024-2025", 'session_short_name': "2024-25"},
        {'pk': 21, 'session_name': "2025-2026", 'session_short_name': "2025-26"},
    ]

def get_programmes():
    return [
        {'pk': 1, 'programme_name': "BACHELOR OF TECHNOLOGY"},
        {'pk': 3, 'programme_name': "MASTER OF SCIENCE"},
        {'pk': 4, 'programme_name': "MASTER OF TECHNOLOGY (MTECH)"},
        {'pk': 5, 'programme_name': "DOCTOR OF PHILOSOPHY (PHD)"},
        {'pk': 7, 'programme_name': "B.TECH-M.TECH (DUAL)"},
        {'pk': 8, 'programme_name': "M.SC-PH.D (DUAL DEGREE)"},
        {'pk': 9, 'programme_name': "M.B.A."},
        {'pk': 10, 'programme_name': "MS-RESEARCH"},
        {'pk': 11, 'programme_name': "MASTER IN PUBLIC POLICY"},
        {'pk': 12, 'programme_name': "ADVANCE DEGREE"},
        {'pk': 13, 'programme_name': "BACHELOR OF DESIGN"},
        {'pk': 23, 'programme_name': "MDES"},
        {'pk': 24, 'programme_name': "INTERDISCIPLINARY M.TECH"},
        {'pk': 25, 'programme_name': "PGDIP"},
        {'pk': 26, 'programme_name': "PGDIIT"},
        {'pk': 27, 'programme_name': "INTEGRATED M.TECH"},
        {'pk': 28, 'programme_name': "UG-VST"},
        {'pk': 29, 'programme_name': "PG-VST"},
        {'pk': 30, 'programme_name': "M. TECH HVA - HIGH VALUE ASSISTANTSHIP (3 YEARS)"},
        {'pk': 31, 'programme_name': "DIPLOMA"},
        {'pk': 32, 'programme_name': "ABU DHABI"},
        {'pk': 33, 'programme_name': "MA"},
        {'pk': 34, 'programme_name': "EXECUTIVE MBA"},
    ]

def get_semesters():
    return [
        {'pk': 1, 'semester': "Odd"},
        {'pk': 2, 'semester': "Even"},
        {'pk': 3, 'semester': "Summer"},
    ]


# ------------------------------
# Routes
# ------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == User.username and request.form['password'] == User.password:
            login_user(User())
            return redirect(url_for('select_details'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Step 1: User selects session, programme, and semester.
@app.route('/select_details', methods=['GET', 'POST'])
@login_required
def select_details():
    if request.method == 'POST':
        # Fetch parameters from the form.
        session_pk = request.form.get('session_pk')
        programme_pk = request.form.get('programme_pk')
        semester_pk = request.form.get('semester_pk')
        # Store these in session for later re-use.
        session['session_pk'] = session_pk
        session['programme_pk'] = programme_pk
        session['semester_pk'] = semester_pk
        return redirect(url_for('dashboard'))
    
    sessions = get_sessions()
    programmes = get_programmes()
    semesters = get_semesters()
    return render_template('select_details.html', sessions=sessions, programmes=programmes, semesters=semesters)

# Dashboard: Re-run the query using stored parameters and display results.
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    session_pk = session.get('session_pk')
    programme_pk = session.get('programme_pk')
    semester_pk = session.get('semester_pk')
    
    if not (session_pk and programme_pk and semester_pk):
        flash("Please select session details", "warning")
        return redirect(url_for('select_details'))
    
    sql = text("""
        SELECT DISTINCT
            employee_master.pf_number AS entryno,
            employee_master.first_name AS name,
            employee_master.name_hindi,
            IFNULL(dgpa.dgpa, acad_course_grade_cpi.cpi) AS degree_gpa,
            acad_degree_name_print.english_prog_name AS degree_name,
            acad_degree_name_print.engish_spec_name AS spec_name,
            acad_degree_name_print.hindi_prog_name AS degree_name_hindi,
            acad_degree_name_print.hindi_spec_name AS spec_name_hindi,
            acad_session_master.given_year,
            acad_session_master.given_month,
            acad_session_master.given_day,
            acad_session_master.convo_year,
            acad_session_master.convo_day,
            acad_session_master.completion_year,
            acad_session_master.convo_month_hindi
        FROM
            employee_master
            INNER JOIN student_master_programme_details 
                ON student_master_programme_details.employee_master_pk = employee_master.pk
            INNER JOIN programme_master 
                ON programme_master.pk = student_master_programme_details.acad_programme_master_pk
            INNER JOIN acad_degree_name_print 
                ON acad_degree_name_print.acad_branch_master_pk = student_master_programme_details.acad_branch_master_pk
                AND acad_degree_name_print.programme_pk = student_master_programme_details.acad_programme_master_pk
                AND acad_degree_name_print.batch = student_master_programme_details.batch
                AND acad_degree_name_print.specialization_pk = student_master_programme_details.specialization_master_pk
            INNER JOIN acad_course_grade_cpi 
                ON acad_course_grade_cpi.student_pk = student_master_programme_details.employee_master_pk
               AND acad_course_grade_cpi.flag = 1
            LEFT JOIN dgpa 
                ON dgpa.employee_master_pk = student_master_programme_details.employee_master_pk
               AND dgpa.flag = student_master_programme_details.pg_status
            INNER JOIN acad_student_warning_ap 
                ON acad_student_warning_ap.employee_master_pk = student_master_programme_details.employee_master_pk
               AND acad_student_warning_ap.flag = 1
            INNER JOIN acad_session_master
                ON acad_student_warning_ap.acad_session_master_pk = acad_session_master.pk
        WHERE
            acad_student_warning_ap.wap IN (6)
            AND acad_session_master.pk = :session_pk
            AND acad_student_warning_ap.acad_semester_pk = :semester_pk
            AND programme_master.pk = :programme_pk
            AND acad_student_warning_ap.flag = 1
            AND acad_course_grade_cpi.flag = 1
            AND employee_master.identifier_master_pk = 2
    """)
    
    results = db.session.execute(sql, {
        'session_pk': session_pk,
        'semester_pk': semester_pk,
        'programme_pk': programme_pk
    }).fetchall()
    
    # Convert SQLAlchemy Row objects into dictionaries for passing to the template.
    records = [dict(r._mapping) for r in results]
    return render_template('dashboard.html', records=records)

# Generation Route: Re-fetch records for each selected entry for document generation.
@app.route('/generate', methods=['POST'])
@login_required
def generate():
    selected = request.form.getlist('entries')
    if not selected:
        flash("Select at least one record to generate degrees.", "warning")
        return redirect(url_for('dashboard'))
    
    session_pk = session.get('session_pk')
    programme_pk = session.get('programme_pk')
    semester_pk = session.get('semester_pk')
    
    # Fetch full details for each selected entry.
    records = []
    for entry in selected:
        sql = text("""
            SELECT DISTINCT
                employee_master.pf_number AS entryno,
                employee_master.first_name AS name,
                employee_master.name_hindi,
                IFNULL(dgpa.dgpa, acad_course_grade_cpi.cpi) AS degree_gpa,
                acad_degree_name_print.english_prog_name AS degree_name,
                acad_degree_name_print.engish_spec_name AS spec_name,
                acad_degree_name_print.hindi_prog_name AS degree_name_hindi,
                acad_degree_name_print.hindi_spec_name AS spec_name_hindi,
                acad_session_master.given_year,
                acad_session_master.given_month,
                acad_session_master.given_day,
                acad_session_master.convo_year,
                acad_session_master.convo_day,
                acad_session_master.completion_year,
                acad_session_master.convo_month_hindi
            FROM
                employee_master
                INNER JOIN student_master_programme_details 
                    ON student_master_programme_details.employee_master_pk = employee_master.pk
                INNER JOIN programme_master 
                    ON programme_master.pk = student_master_programme_details.acad_programme_master_pk
                INNER JOIN acad_degree_name_print 
                    ON acad_degree_name_print.acad_branch_master_pk = student_master_programme_details.acad_branch_master_pk
                    AND acad_degree_name_print.programme_pk = student_master_programme_details.acad_programme_master_pk
                    AND acad_degree_name_print.batch = student_master_programme_details.batch
                    AND acad_degree_name_print.specialization_pk = student_master_programme_details.specialization_master_pk
                INNER JOIN acad_course_grade_cpi 
                    ON acad_course_grade_cpi.student_pk = student_master_programme_details.employee_master_pk
                   AND acad_course_grade_cpi.flag = 1
                LEFT JOIN dgpa 
                    ON dgpa.employee_master_pk = student_master_programme_details.employee_master_pk
                   AND dgpa.flag = student_master_programme_details.pg_status
                INNER JOIN acad_student_warning_ap 
                    ON acad_student_warning_ap.employee_master_pk = student_master_programme_details.employee_master_pk
                   AND acad_student_warning_ap.flag = 1
                INNER JOIN acad_session_master
                    ON acad_student_warning_ap.acad_session_master_pk = acad_session_master.pk
            WHERE
                acad_student_warning_ap.wap IN (6)
                AND acad_session_master.pk = :session_pk
                AND acad_student_warning_ap.acad_semester_pk = :semester_pk
                AND programme_master.pk = :programme_pk
                AND employee_master.pf_number = :entryno
                AND acad_student_warning_ap.flag = 1
                AND acad_course_grade_cpi.flag = 1
                AND employee_master.identifier_master_pk = 2
        """)
        result = db.session.execute(sql, {
            'session_pk': session_pk,
            'semester_pk': semester_pk,
            'programme_pk': programme_pk,
            'entryno': entry
        }).fetchone()
        if result:
            records.append(dict(result._mapping))
    
    # At this point, records is a list of dictionaries containing the data for each selected entry.
    # Proceed to generate documents (e.g. DOCX/PDF) using these records.
    task_id = uuid.uuid4().hex
    thread = threading.Thread(target=generate_task, args=(records, task_id, request.form.get('output_format', 'pdf')))
    thread.start()
    return render_template('progress.html', task_id=task_id)

def generate_task(records, task_id, output_format):
    with app.app_context():
        total = len(records)
        with tempfile.TemporaryDirectory() as tmpdirname:
            docx_paths = []
            # Stage 1: Generate DOCX files.
            for i, record in enumerate(records):
                context = convert_record_to_context(record)
                docx_buf = render_docx(context)
                entry = record.get('entryno', f"doc_{i}")
                docx_path = os.path.join(tmpdirname, f'{entry}.docx')
                with open(docx_path, 'wb') as f:
                    f.write(docx_buf.read())
                docx_paths.append(docx_path)
                progress = int((i + 1) / total * 30)
                socketio.emit('progress_update', {'task_id': task_id, 'progress': progress})
            
            if output_format == 'pdf':
                pdf_paths = []
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_to_docx = {executor.submit(convert_worker, docx): docx for docx in docx_paths}
                    for i, future in enumerate(as_completed(future_to_docx)):
                        try:
                            pdf_path = future.result()
                            pdf_paths.append(pdf_path)
                        except Exception as e:
                            app.logger.error(f"Conversion failed for {future_to_docx[future]}: {e}")
                        progress = 30 + int((i + 1) / total * 50)
                        socketio.emit('progress_update', {'task_id': task_id, 'progress': progress})
                output_paths = pdf_paths
            else:
                output_paths = docx_paths
                socketio.emit('progress_update', {'task_id': task_id, 'progress': 80})
            
            # Stage 3: Zip the output files.
            tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            zip_path = tmp_zip.name
            tmp_zip.close()
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in output_paths:
                    if os.path.exists(file_path):
                        zf.write(file_path, arcname=os.path.basename(file_path))
                    else:
                        app.logger.warning(f"File {file_path} not found. Skipping.")
            socketio.emit('progress_update', {'task_id': task_id, 'progress': 100})
            socketio.emit('generation_complete', {'task_id': task_id, 'zip_path': zip_path})

@app.route('/download')
@login_required
def download():
    zip_path = request.args.get('zip')
    if not zip_path or not os.path.exists(zip_path):
        flash('File not found', 'danger')
        return redirect(url_for('dashboard'))
    response = send_file(zip_path, as_attachment=True, download_name='degrees.zip')
    
    @response.call_on_close
    def cleanup_tempfile():
        try:
            os.remove(zip_path)
        except Exception as e:
            app.logger.error(f"Error deleting temp file: {e}")
    
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
