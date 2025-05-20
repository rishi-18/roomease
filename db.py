import psycopg2
import pandas as pd

def get_connection():
    return psycopg2.connect(
        dbname="tiet_hostel",
        user="postgres",
        password="rishi_._18",
        host="localhost",
        port="5432"
    )

# Students
def get_students(search=""):
    conn = get_connection()
    query = f"""
        SELECT * FROM students 
        WHERE roll ILIKE %s OR name ILIKE %s
        ORDER BY roll;
    """
    df = pd.read_sql(query, conn, params=(f"%{search}%", f"%{search}%"))
    conn.close()
    return df

def add_student(roll, name, age, branch, room_no):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO students (roll, name, age, branch, room_no) VALUES (%s, %s, %s, %s, %s)",
                (roll, name, age, branch, room_no))
    conn.commit()
    conn.close()

def update_student(roll, name, age, branch, room_no):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE students SET name=%s, age=%s, branch=%s, room_no=%s WHERE roll=%s",
                (name, age, branch, room_no, roll))
    conn.commit()
    conn.close()

def delete_student(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE roll=%s", (roll,))
    conn.commit()
    conn.close()

def get_student_distribution():
    conn = get_connection()
    df = pd.read_sql("SELECT room_no, COUNT(*) as count FROM students GROUP BY room_no", conn)
    conn.close()
    return df

# Rooms
def get_rooms(search=""):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rooms WHERE room_no ILIKE %s ORDER BY room_no", conn, params=(f"%{search}%",))
    conn.close()
    return df

def add_room(room_no, capacity, availability):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO rooms (room_no, capacity, availability) VALUES (%s, %s, %s)",
                (room_no, capacity, availability))
    conn.commit()
    conn.close()

def update_room(room_no, capacity, availability):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rooms SET capacity=%s, availability=%s WHERE room_no=%s",
                (capacity, availability, room_no))
    conn.commit()
    conn.close()

def delete_room(room_no):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM rooms WHERE room_no=%s", (room_no,))
    conn.commit()
    conn.close()

# Fees
def get_fees(search=""):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM fees WHERE roll ILIKE %s ORDER BY date DESC", conn, params=(f"%{search}%",))
    conn.close()
    return df

def add_fee(roll, amount, date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO fees (roll, amount, date) VALUES (%s, %s, %s)",
                (roll, amount, date))
    conn.commit()
    conn.close()

# Staff
def get_staff(search=""):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM staff WHERE name ILIKE %s ORDER BY id", conn, params=(f"%{search}%",))
    conn.close()
    return df

def add_staff(name, role, contact):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO staff (name, role, contact) VALUES (%s, %s, %s)",
                (name, role, contact))
    conn.commit()
    conn.close()

# Complaints
def get_complaints(search=""):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM complaints WHERE roll ILIKE %s ORDER BY date DESC", conn, params=(f"%{search}%",))
    conn.close()
    return df

def add_complaint(roll, complaint, date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO complaints (roll, complaint, date) VALUES (%s, %s, %s)",
                (roll, complaint, date))
    conn.commit()
    conn.close()

# Visitors
def get_visitors(search=""):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM visitors WHERE roll ILIKE %s ORDER BY date DESC", conn, params=(f"%{search}%",))
    conn.close()
    return df

def add_visitor(roll, name, relation, date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visitors (roll, name, relation, date) VALUES (%s, %s, %s, %s)",
                (roll, name, relation, date))
    conn.commit()
    conn.close()
