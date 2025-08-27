from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change-this-secret"

DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")

# Provide year to templates
@app.context_processor
def inject_now():
    return {'year': datetime.now().year}

# ---------------- Database Helpers ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            grade INTEGER NOT NULL CHECK(grade >= 0 AND grade <= 100),
            UNIQUE(student_id, subject),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# ---------------- Utility Functions ----------------
def get_student_by_roll(roll_number):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,))
    row = cur.fetchone()
    conn.close()
    return row

def list_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY roll_number")
    rows = cur.fetchall()
    conn.close()
    return rows

def list_subjects():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT subject FROM grades ORDER BY subject")
    subjects = [r['subject'] for r in cur.fetchall()]
    conn.close()
    return subjects

# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html', students=list_students(), subjects=list_subjects())

@app.route('/students')
def students():
    return render_template('students.html', students=list_students())

@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll_number', '').strip()
        if not name or not roll:
            flash('Name and roll number are required.', 'danger')
            return redirect(url_for('add_student'))
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO students (name, roll_number) VALUES (?, ?)', (name, roll))
            conn.commit()
            conn.close()
            flash(f'Student {name} added.', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Roll number already exists.', 'danger')
            return redirect(url_for('add_student'))
    return render_template('add_student.html')

@app.route('/grades/add', methods=['GET', 'POST'])
def add_grade():
    if request.method == 'POST':
        roll = request.form.get('roll_number', '').strip()
        subject = request.form.get('subject', '').strip()
        try:
            grade = int(request.form.get('grade', '0'))
        except ValueError:
            grade = -1
        if not roll or not subject:
            flash('Roll number and subject are required.', 'danger')
            return redirect(url_for('add_grade'))
        if grade < 0 or grade > 100:
            flash('Grade must be between 0 and 100.', 'danger')
            return redirect(url_for('add_grade'))
        student = get_student_by_roll(roll)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('add_grade'))
        conn = get_db()
        cur = conn.cursor()
        # Insert or update grade for this subject
        try:
            cur.execute("""
                INSERT INTO grades (student_id, subject, grade)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id, subject) DO UPDATE SET grade=excluded.grade
            """, (student['id'], subject, grade))
            conn.commit()
        except sqlite3.OperationalError:
            # ON CONFLICT may not be supported on some older SQLite installs; fallback:
            cur.execute('SELECT id FROM grades WHERE student_id = ? AND subject = ?', (student['id'], subject))
            existing = cur.fetchone()
            if existing:
                cur.execute('UPDATE grades SET grade = ? WHERE id = ?', (grade, existing['id']))
            else:
                cur.execute('INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)', (student['id'], subject, grade))
            conn.commit()
        conn.close()
        flash(f'Grade {grade} saved for {student["name"]} in {subject}.', 'success')
        return redirect(url_for('student_detail', roll_number=roll))
    return render_template('add_grade.html', students=list_students())

@app.route('/students/<roll_number>')
def student_detail(roll_number):
    student = get_student_by_roll(roll_number)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, subject, grade FROM grades WHERE student_id = ? ORDER BY subject', (student['id'],))
    grades = cur.fetchall()
    conn.close()
    avg = round(sum([g['grade'] for g in grades]) / len(grades), 2) if grades else 0.0
    return render_template('student_detail.html', student=student, grades=grades, average=avg)

@app.route('/reports/class-average', methods=['GET', 'POST'])
def class_average():
    avg = None
    selected_subject = None
    if request.method == 'POST':
        selected_subject = request.form.get('subject', '').strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT AVG(grade) AS avg_grade FROM grades WHERE subject = ?', (selected_subject,))
        row = cur.fetchone()
        conn.close()
        if row and row['avg_grade'] is not None:
            avg = round(row['avg_grade'], 2)
        else:
            avg = None
            flash(f"No grades found for subject '{selected_subject}'.", 'warning')
    return render_template('class_average.html', subjects=list_subjects(), avg=avg, selected_subject=selected_subject)

@app.route('/reports/subject-topper', methods=['GET', 'POST'])
def subject_topper():
    topper = None
    selected_subject = None
    if request.method == 'POST':
        selected_subject = request.form.get('subject', '').strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.name, s.roll_number, g.grade
            FROM grades g
            JOIN students s ON s.id = g.student_id
            WHERE g.subject = ?
            ORDER BY g.grade DESC, s.name ASC
            LIMIT 1
        """, (selected_subject,))
        topper = cur.fetchone()
        conn.close()
        if topper is None:
            flash(f"No grades found for subject '{selected_subject}'.", 'warning')
    return render_template('subject_topper.html', subjects=list_subjects(), topper=topper, selected_subject=selected_subject)

# ---------------- Delete routes (safe) ----------------
@app.route('/students/delete/<roll_number>', methods=['POST'])
def delete_student(roll_number):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM students WHERE roll_number = ?', (roll_number,))
    student = cur.fetchone()
    if not student:
        conn.close()
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))
    student_id = student['id']
    student_name = student['name']
    # Delete grades for this student
    cur.execute('DELETE FROM grades WHERE student_id = ?', (student_id,))
    # Delete the student
    cur.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    flash(f'Student {student_name} ({roll_number}) and their grades were deleted.', 'success')
    return redirect(url_for('students'))

@app.route('/grades/delete/<int:grade_id>', methods=['POST'])
def delete_grade(grade_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT student_id FROM grades WHERE id = ?', (grade_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash('Grade not found.', 'danger')
        return redirect(url_for('students'))
    student_id = row['student_id']
    # get student's roll number to redirect back
    cur.execute('SELECT roll_number FROM students WHERE id = ?', (student_id,))
    s = cur.fetchone()
    roll = s['roll_number'] if s else None
    cur.execute('DELETE FROM grades WHERE id = ?', (grade_id,))
    conn.commit()
    conn.close()
    flash('Grade deleted.', 'success')
    if roll:
        return redirect(url_for('student_detail', roll_number=roll))
    return redirect(url_for('students'))

if __name__ == '__main__':
    app.run(debug=True)
