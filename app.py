from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from datetime import date

app = Flask(__name__)
app.secret_key = 'secret' 

def get_db():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists('attendance.db'):
        with sqlite3.connect('attendance.db') as conn:
            with open('schema.sql') as f:
                conn.executescript(f.read())
            conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', 'admin123'))

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        db = get_db()

        if role == 'admin':
            user = db.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['admin_id'] = user['id']
                return redirect('/admin/dashboard')
        elif role == 'teacher':
            user = db.execute("SELECT * FROM teachers WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['teacher_id'] = user['id']
                return redirect('/teacher/dashboard')

        return "Invalid credentials"
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    teachers = db.execute("SELECT * FROM teachers").fetchall()
    return render_template('admin_dashboard.html', students=students, teachers=teachers)

@app.route('/admin/add_student', methods=['POST'])
def add_student():
    if 'admin_id' not in session:
        return redirect('/login')
    db = get_db()
    db.execute("INSERT INTO students (name, roll_no, class) VALUES (?, ?, ?)",
               (request.form['name'], request.form['roll_no'], request.form['class']))
    db.commit()
    return redirect('/admin/dashboard')

@app.route('/admin/add_teacher', methods=['POST'])
def add_teacher():
    if 'admin_id' not in session:
        return redirect('/login')
    db = get_db()
    db.execute("INSERT INTO teachers (name, username, password, subject, class) VALUES (?, ?, ?, ?, ?)",
               (request.form['name'], request.form['username'], request.form['password'],
                request.form['subject'], request.form['class']))
    db.commit()
    return redirect('/admin/dashboard')
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect('/login')
    
    db = get_db()
    teacher = db.execute("SELECT * FROM teachers WHERE id=?", (session['teacher_id'],)).fetchone()
    students = db.execute("SELECT * FROM students WHERE class=?", (teacher['class'],)).fetchall()
    today = date.today().strftime("%d-%m-%Y")
    
    return render_template('teacher_dashboard.html', teacher=teacher, students=students, current_date=today)
@app.route('/teacher/mark', methods=['POST'])
def mark_attendance():
    db = get_db()
    teacher = db.execute("SELECT * FROM teachers WHERE id=?", (session['teacher_id'],)).fetchone()
    for student_id in request.form:
        status = request.form[student_id]
        db.execute("INSERT INTO attendance (student_id, teacher_id, subject, class, date, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (student_id, teacher['id'], teacher['subject'], teacher['class'], str(date.today()), status))
    db.commit()
    return render_template('confirmation.html', message="✅ Attendance submitted successfully!")

@app.route('/student/view', methods=['GET', 'POST'])
def student_lookup():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        db = get_db()
        student = db.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
        if not student:
            return "❌ Roll number not found"
        records = db.execute("""
            SELECT subject, date, status
            FROM attendance
            WHERE student_id = ?
            ORDER BY date DESC
        """, (student['id'],)).fetchall()
        return render_template('student_report.html', student=student, records=records)
    return render_template('student_lookup.html')

@app.route('/admin/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return redirect('/admin/dashboard')

@app.route('/admin/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        class_name = request.form['class']
        db.execute("""
            UPDATE students SET name = ?, roll_no = ?, class = ? WHERE id = ?
        """, (name, roll_no, class_name, student_id))
        db.commit()
        return redirect('/admin/dashboard')
    return render_template('edit_student.html', student=student)

@app.route('/admin/delete-teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    db.commit()
    return redirect('/admin/dashboard')

@app.route('/admin/edit-teacher/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    db = get_db()
    teacher = db.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        db.execute("""
            UPDATE teachers SET name = ?, email = ?, subject = ? WHERE id = ?
        """, (name, email, subject, teacher_id))
        db.commit()
        return redirect('/admin/dashboard')
    return render_template('edit_teacher.html', teacher=teacher)

if __name__ == '__main__':
    app.run(debug=True) 
    hello