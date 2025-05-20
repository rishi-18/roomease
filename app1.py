import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import re
from datetime import datetime
from sqlalchemy.sql import text

# -------------------------
# Database connections
engine = create_engine('postgresql+psycopg2://postgres:rishi_._18@localhost/tiet_hostel')

def get_conn():
    return psycopg2.connect(
        host="localhost",
        database="tiet_hostel",
        user="postgres",
        password="rishi_._18"
    )

# -------------------------
# Validation functions

def validate_roll_no(roll_no):
    if not roll_no or not re.match(r'^[A-Za-z0-9]+$', roll_no):
        return "Roll Number must be alphanumeric and not empty."
    return None

def validate_contact_no(contact_no):
    if contact_no and not re.match(r'^\d{10}$', contact_no):
        return "Contact Number must be exactly 10 digits."
    return None

def validate_year(year):
    if year not in ["1st", "2nd", "3rd", "4th"]:
        return "Invalid Year selected."
    return None

def validate_room_exists_and_vacant(room_no, engine):
    try:
        room_df = pd.read_sql("SELECT room_no, status FROM rooms WHERE room_no = %s", engine, params=(room_no,))
        if room_df.empty:
            return f"Room '{room_no}' does not exist."
        elif room_df.iloc[0]['status'] != 'Vacant':
            return f"Room '{room_no}' is not vacant."
    except Exception as e:
        return f"Error validating room: {e}"
    return None

def validate_room_number_format(room_no):
    if not room_no or not re.match(r'^[A-Za-z0-9]+$', room_no):
        return "Room Number must be alphanumeric and not empty."
    return None

def confirm_delete(entity_name, entity_id):
    st.warning(f"Are you sure you want to delete {entity_name} '{entity_id}'? This action cannot be undone.")
    return st.button(f"Confirm Delete {entity_name}")

# -------------------------
# Streamlit page setup
st.set_page_config(page_title="ROOMEASE", layout="wide")
st.sidebar.title("🏠 ROOMEASE")
menu = st.sidebar.radio("Go to", ["Dashboard", "Students", "Rooms", "Fees", "Staff", "Complaints", "Visitors"])

# -------------------------
if menu == "Dashboard":
    st.title("📊 Dashboard")
    
    try:
        student_df = pd.read_sql("SELECT * FROM students", engine)
        room_df = pd.read_sql("SELECT * FROM rooms", engine)
        fees_df = pd.read_sql("SELECT * FROM fees", engine)
        complaints_df = pd.read_sql("SELECT * FROM complaints", engine)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Students", student_df.shape[0])
        with col2:
            occupied = room_df[room_df['status'] == 'Occupied'].shape[0] if 'status' in room_df.columns else 0
            st.metric("Occupied Rooms", occupied)
        with col3:
            paid_fees = fees_df[fees_df['status'] == 'Paid'].shape[0] if 'status' in fees_df.columns else 0
            st.metric("Paid Fees", paid_fees)
        with col4:
            pending_complaints = complaints_df[complaints_df['status'] == 'Pending'].shape[0] if 'status' in complaints_df.columns else 0
            st.metric("Pending Complaints", pending_complaints)

        st.subheader("Department-wise Distribution")
        if "department" in student_df.columns:
            dept_counts = student_df["department"].value_counts().reset_index()
            dept_counts.columns = ["Department", "Count"]
            st.bar_chart(dept_counts.set_index("Department"))

        st.subheader("Room Status")
        if "status" in room_df.columns:
            room_status = room_df["status"].value_counts().reset_index()
            room_status.columns = ["Status", "Count"]
            st.bar_chart(room_status.set_index("Status"))
            
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")

# -------------------------
elif menu == "Students":
    tab1, tab2, tab3 = st.tabs(["📋 View Students", "➕ Add Student", "✏️ Edit / Delete Student"])

    # View Students
    with tab1:
        st.subheader("All Students")
        try:
            df = pd.read_sql("SELECT * FROM students", engine)
            
            if not df.empty:
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    dept_filter = st.multiselect("Filter by Department", options=df["department"].dropna().unique())
                with col2:
                    year_filter = st.multiselect("Filter by Year", options=df["year"].dropna().unique())
                with col3:
                    room_filter = st.multiselect("Filter by Room", options=df["room_no"].dropna().unique())

                if dept_filter:
                    df = df[df["department"].isin(dept_filter)]
                if year_filter:
                    df = df[df["year"].isin(year_filter)]
                if room_filter:
                    df = df[df["room_no"].isin(room_filter)]

                st.dataframe(df, use_container_width=True)
            else:
                st.info("No students found in the database.")
        except Exception as e:
            st.error(f"Error loading students: {e}")

    # Add Student
    with tab2:
        st.subheader("Add New Student")
        with st.form("add_student", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                roll_no = st.text_input("Roll Number*", help="Alphanumeric, e.g., 102303xxx")
                name = st.text_input("Name*")
                department = st.selectbox("Department*", ["CSE", "ECE", "EE", "ME", "CE", "BT"])
            with col2:
                room_no = st.text_input("Room Number*", help="Must be an existing vacant room")
                year = st.selectbox("Year*", ["1st", "2nd", "3rd", "4th"])
                contact_no = st.text_input("Contact Number", help="10 digit number only")

            submitted = st.form_submit_button("Add Student")

            if submitted:
                errors = []
                err = validate_roll_no(roll_no)
                if err:
                    errors.append(err)
                if not name:
                    errors.append("Name is required.")
                err = validate_contact_no(contact_no)
                if err:
                    errors.append(err)
                err = validate_year(year)
                if err:
                    errors.append(err)
                err = validate_room_exists_and_vacant(room_no, engine)
                if err:
                    errors.append(err)

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with st.spinner("Adding student and updating room status..."):
                            conn = get_conn()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO students (roll_no, name, department, room_no, year, contact_no) VALUES (%s, %s, %s, %s, %s, %s)",
                                (roll_no, name, department, room_no, year, contact_no)
                            )
                            cursor.execute("UPDATE rooms SET status='Occupied' WHERE room_no=%s", (room_no,))
                            conn.commit()
                            st.success(f"Student '{name}' added successfully, and room '{room_no}' marked as Occupied.")
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding student: {e}")
                    finally:
                        if 'conn' in locals():
                            cursor.close()
                            conn.close()

    # Edit/Delete Student
    with tab3:
        st.subheader("Edit or Delete Student")
        try:
            df = pd.read_sql("SELECT * FROM students", engine)
            if df.empty:
                st.info("No students found to edit or delete.")
            else:
                student_rolls = df["roll_no"].astype(str).tolist()
                selected_roll = st.selectbox("Select Student Roll Number", options=student_rolls)
                if selected_roll:
                    selected_student = df[df["roll_no"].astype(str) == selected_roll].iloc[0]

                    with st.form("edit_student"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Name", value=selected_student["name"])
                            department = st.selectbox("Department", ["CSE", "ECE", "EE", "ME", "CE", "BT"], index=["CSE", "ECE", "EE", "ME", "CE", "BT"].index(selected_student.get("department", "CSE")))
                            room_no = st.text_input("Room Number", value=selected_student["room_no"], help="Must be an existing vacant room or the current room")
                        with col2:
                            year_list = ["1st", "2nd", "3rd", "4th"]
                            year_val = str(selected_student["year"])
                            year = st.selectbox("Year", year_list, index=year_list.index(year_val) if year_val in year_list else 0)
                            contact_no = st.text_input("Contact Number", value=selected_student["contact_no"])

                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Student")
                        with col2:
                            delete_button = st.form_submit_button("Delete Student")

                    if update_button:
                        errors = []
                        err = validate_contact_no(contact_no)
                        if err:
                            errors.append(err)
                        err = validate_year(year)
                        if err:
                            errors.append(err)
                        # Validate room: either same as current or vacant
                        if room_no != selected_student["room_no"]:
                            err = validate_room_exists_and_vacant(room_no, engine)
                            if err:
                                errors.append(err)

                        if errors:
                            for e in errors:
                                st.error(e)
                        else:
                            try:
                                with st.spinner("Updating student info..."):
                                    conn = get_conn()
                                    cursor = conn.cursor()

                                    # If room changed: set old room vacant, new room occupied
                                    if room_no != selected_student["room_no"]:
                                        cursor.execute("UPDATE rooms SET status='Vacant' WHERE room_no=%s", (selected_student["room_no"],))
                                        cursor.execute("UPDATE rooms SET status='Occupied' WHERE room_no=%s", (room_no,))

                                    cursor.execute("""
                                        UPDATE students SET name=%s, department=%s, room_no=%s, year=%s, contact_no=%s WHERE roll_no=%s
                                    """, (name, department, room_no, year, contact_no, selected_roll))
                                    conn.commit()
                                    st.success(f"Student '{selected_roll}' updated successfully.")
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating student: {e}")
                            finally:
                                if 'conn' in locals():
                                    cursor.close()
                                    conn.close()

                    if delete_button:
                        if confirm_delete("Student", selected_roll):
                            try:
                                with st.spinner("Deleting student and updating room status..."):
                                    conn = get_conn()
                                    cursor = conn.cursor()
                                    # Get room_no before delete
                                    cursor.execute("SELECT room_no FROM students WHERE roll_no=%s", (selected_roll,))
                                    room = cursor.fetchone()
                                    cursor.execute("DELETE FROM students WHERE roll_no=%s", (selected_roll,))
                                    if room and room[0]:
                                        cursor.execute("UPDATE rooms SET status='Vacant' WHERE room_no=%s", (room[0],))
                                    conn.commit()
                                    st.success(f"Student '{selected_roll}' deleted and room '{room[0]}' marked as Vacant.")
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting student: {e}")
                            finally:
                                if 'conn' in locals():
                                    cursor.close()
                                    conn.close()
        except Exception as e:
            st.error(f"Error loading student data: {e}")

# -------------------------
elif menu == "Rooms":
    tab1, tab2, tab3 = st.tabs(["📋 View Rooms", "➕ Add Room", "✏️ Edit / Delete Room"])

    # View Rooms
    with tab1:
        st.subheader("All Rooms")
        try:
            df = pd.read_sql("SELECT * FROM rooms", engine)
            
            if not df.empty:
                status_filter = st.multiselect("Filter by Status", options=df["status"].dropna().unique())
                if status_filter:
                    df = df[df["status"].isin(status_filter)]
                
                st.dataframe(df, use_container_width=True)
                
                # Show students in selected room
                selected_room = st.selectbox("View occupants for room:", [""] + df["room_no"].tolist())
                if selected_room:
                    students_df = pd.read_sql("SELECT roll_no, name FROM students WHERE room_no = %s", engine, params=(selected_room,))
                    if not students_df.empty:
                        st.write(f"Students in room {selected_room}:")
                        st.dataframe(students_df)
                    else:
                        st.info(f"No students in room {selected_room}")
            else:
                st.info("No rooms found in the database.")
        except Exception as e:
            st.error(f"Error loading rooms: {e}")

    # Add Room
    with tab2:
        st.subheader("Add New Room")
        with st.form("add_room", clear_on_submit=True):
            room_no = st.text_input("Room Number*")
            capacity = st.number_input("Capacity*", min_value=1, max_value=4, value=2)
            status = st.selectbox("Status*", ["Vacant", "Occupied", "Maintenance"])
            submitted = st.form_submit_button("Add Room")

            if submitted:
                errors = []
                err = validate_room_number_format(room_no)
                if err:
                    errors.append(err)

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with st.spinner("Adding room..."):
                            conn = get_conn()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO rooms (room_no, capacity, status) VALUES (%s, %s, %s)", (room_no, capacity, status))
                            conn.commit()
                            st.success(f"Room '{room_no}' added successfully.")
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding room: {e}")
                    finally:
                        if 'conn' in locals():
                            cursor.close()
                            conn.close()

    # Edit/Delete Room
    with tab3:
        st.subheader("Edit or Delete Room")
        try:
            df = pd.read_sql("SELECT * FROM rooms", engine)
            if df.empty:
                st.info("No rooms found to edit or delete.")
            else:
                room_nos = df["room_no"].astype(str).tolist()
                selected_room = st.selectbox("Select Room Number", options=room_nos)
                if selected_room:
                    selected_room_row = df[df["room_no"].astype(str) == selected_room].iloc[0]
                    with st.form("edit_room"):
                        room_no = st.text_input("Room Number*", value=selected_room_row["room_no"])
                        capacity = st.number_input("Capacity*", min_value=1, max_value=4, value=int(selected_room_row.get("capacity", 2)))
                        status = st.selectbox("Status*", ["Vacant", "Occupied", "Maintenance"], index=["Vacant", "Occupied", "Maintenance"].index(selected_room_row["status"]))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Room")
                        with col2:
                            delete_button = st.form_submit_button("Delete Room")

                    if update_button:
                        errors = []
                        err = validate_room_number_format(room_no)
                        if err:
                            errors.append(err)

                        if errors:
                            for e in errors:
                                st.error(e)
                        else:
                            try:
                                with st.spinner("Updating room..."):
                                    conn = get_conn()
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE rooms SET room_no=%s, capacity=%s, status=%s WHERE room_no=%s
                                    """, (room_no, capacity, status, selected_room))
                                    conn.commit()
                                    st.success(f"Room '{selected_room}' updated successfully.")
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating room: {e}")
                            finally:
                                if 'conn' in locals():
                                    cursor.close()
                                    conn.close()

                    if delete_button:
                        if confirm_delete("Room", selected_room):
                            try:
                                with st.spinner("Deleting room..."):
                                    conn = get_conn()
                                    cursor = conn.cursor()

                                    # Check if room is occupied before delete
                                    cursor.execute("SELECT COUNT(*) FROM students WHERE room_no=%s", (selected_room,))
                                    count = cursor.fetchone()[0]
                                    if count > 0:
                                        st.error("Cannot delete room as it is currently occupied by students.")
                                    else:
                                        cursor.execute("DELETE FROM rooms WHERE room_no=%s", (selected_room,))
                                        conn.commit()
                                        st.success(f"Room '{selected_room}' deleted successfully.")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting room: {e}")
                            finally:
                                if 'conn' in locals():
                                    cursor.close()
                                    conn.close()
        except Exception as e:
            st.error(f"Error loading room data: {e}")

# -------------------------
elif menu == "Visitors":
    st.title("🛋️ Visitors Management")
    tab1, tab2, tab3 = st.tabs(["📋 View Visitors", "➕ Add Visitor", "✏️ Edit/Delete Records"])

    with tab1:
        try:
            df = pd.read_sql("""
                SELECT v.*, s.name as student_name 
                FROM visitors v
                LEFT JOIN students s ON v.roll_no = s.roll_no
                ORDER BY v.visit_date DESC
            """, engine)
            
            if not df.empty:
                # Convert visit_date to datetime.date for comparison
                df['visit_date'] = pd.to_datetime(df['visit_date']).dt.date
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    date_range = st.date_input("Filter by Date Range", 
                                             [df["visit_date"].min(), df["visit_date"].max()])
                with col2:
                    student_filter = st.multiselect("Filter by Student", options=df["student_name"].dropna().unique())
                
                if len(date_range) == 2:
                    df = df[(df['visit_date'] >= date_range[0]) & 
                           (df['visit_date'] <= date_range[1])]
                if student_filter:
                    df = df[df["student_name"].isin(student_filter)]

                st.dataframe(df, use_container_width=True)
            else:
                st.info("No visitor records found.")
        except Exception as e:
            st.error(f"Error loading visitors: {str(e)}")

    with tab2:
        with st.form("add_visitor", clear_on_submit=True):
            # Get list of students
            students = pd.read_sql("SELECT roll_no, name FROM students ORDER BY name", engine)
            
            col1, col2 = st.columns(2)
            with col1:
                roll_no = st.selectbox("Student Roll Number*", options=students["roll_no"], 
                                     format_func=lambda x: f"{x} - {students[students['roll_no']==x]['name'].values[0]}")
                visitor_name = st.text_input("Visitor Name*")
            with col2:
                relation = st.selectbox("Relation*", ["Parent", "Sibling", "Friend", "Relative", "Other"])
                visit_date = st.date_input("Visit Date*", value=datetime.today())
            
            purpose = st.text_area("Purpose of Visit")
            
            submitted = st.form_submit_button("Add Visitor")

            if submitted:
                errors = []
                if not visitor_name:
                    errors.append("Visitor name is required.")
                if not roll_no:
                    errors.append("Student roll number is required.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with get_conn() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    INSERT INTO visitors 
                                    (roll_no, visitor_name, relation, visit_date, purpose) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (roll_no, visitor_name, relation, visit_date, purpose))
                                conn.commit()
                                st.success("Visitor record added successfully!")
                                st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding visitor: {str(e)}")

    with tab3:
        try:
            df = pd.read_sql("""
                SELECT v.*, s.name as student_name 
                FROM visitors v
                LEFT JOIN students s ON v.roll_no = s.roll_no
                ORDER BY v.visit_date DESC
            """, engine)
            
            if not df.empty:
                visitor_ids = df["visitor_id"].tolist()
                selected_id = st.selectbox("Select Visitor Record", visitor_ids, 
                                         format_func=lambda x: f"{df[df['visitor_id']==x]['visitor_name'].values[0]} visiting {df[df['visitor_id']==x]['student_name'].values[0]}")
                
                if selected_id:
                    selected_visitor = df[df["visitor_id"] == selected_id].iloc[0]
                    
                    with st.form("edit_visitor"):
                        col1, col2 = st.columns(2)
                        with col1:
                            visitor_name = st.text_input("Visitor Name", value=selected_visitor["visitor_name"])
                            relation = st.selectbox("Relation", ["Parent", "Sibling", "Friend", "Relative", "Other"],
                                                 index=["Parent", "Sibling", "Friend", "Relative", "Other"].index(selected_visitor["relation"]))
                        with col2:
                            visit_date = st.date_input("Visit Date", value=selected_visitor["visit_date"])
                            purpose = st.text_area("Purpose", value=selected_visitor.get("purpose", ""))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Record")
                        with col2:
                            delete_button = st.form_submit_button("Delete Record")

                    if update_button:
                        try:
                            with get_conn() as conn:
                                with conn.cursor() as cursor:
                                    cursor.execute("""
                                        UPDATE visitors 
                                        SET visitor_name=%s, relation=%s, visit_date=%s, purpose=%s
                                        WHERE visitor_id=%s
                                    """, (visitor_name, relation, visit_date, purpose, selected_id))
                                    conn.commit()
                                    st.success("Visitor record updated successfully!")
                                    st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating visitor: {str(e)}")

                    if delete_button:
                        if confirm_delete("Visitor Record", selected_visitor["visitor_name"]):
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM visitors WHERE visitor_id=%s", (selected_id,))
                                        conn.commit()
                                        st.success("Visitor record deleted successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting visitor: {str(e)}")
            else:
                st.info("No visitor records found to edit or delete.")
        except Exception as e:
            st.error(f"Error loading visitors: {str(e)}")

# -------------------------
elif menu == "Staff":
    st.title("👨‍🏫 Hostel Staff")
    tab1, tab2, tab3 = st.tabs(["📋 View Staff", "➕ Add Staff", "✏️ Edit / Delete Staff"])

    with tab1:
        try:
            df = pd.read_sql("SELECT * FROM staff ORDER BY name", engine)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading staff data: {e}")

    with tab2:
        with st.form("add_staff", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name*")
                position = st.selectbox("Position*", ["Warden", "Caretaker", "Cleaner", "Cook", "Security", "Other"])
            with col2:
                contact_no = st.text_input("Contact Number*")
                salary = st.number_input("Monthly Salary", min_value=0, value=15000)
                join_date = st.date_input("Join Date", value=datetime.today())
            
            submitted = st.form_submit_button("Add Staff")

            if submitted:
                errors = []
                if not name:
                    errors.append("Name is required.")
                err = validate_contact_no(contact_no)
                if err:
                    errors.append(err)
                if not position:
                    errors.append("Position is required.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with get_conn() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    INSERT INTO staff (name, position, contact_no, salary, join_date) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (name, position, contact_no, salary, join_date))
                                conn.commit()
                                st.success("Staff member added successfully!")
                                st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding staff: {e}")

    with tab3:
        try:
            df = pd.read_sql("SELECT * FROM staff ORDER BY name", engine)
            if not df.empty:
                staff_ids = df["staff_id"].tolist()
                selected_id = st.selectbox("Select Staff Member", staff_ids, 
                                         format_func=lambda x: f"{df[df['staff_id']==x]['name'].values[0]} - {df[df['staff_id']==x]['position'].values[0]}")
                
                if selected_id:
                    selected_staff = df[df["staff_id"] == selected_id].iloc[0]
                    
                    with st.form("edit_staff"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Full Name", value=selected_staff["name"])
                            position = st.selectbox("Position", ["Warden", "Caretaker", "Cleaner", "Cook", "Security", "Other"],
                                                  index=["Warden", "Caretaker", "Cleaner", "Cook", "Security", "Other"].index(selected_staff["position"]))
                        with col2:
                            contact_no = st.text_input("Contact Number", value=selected_staff["contact_no"])
                            salary = st.number_input("Monthly Salary", min_value=0, value=int(selected_staff["salary"]))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Staff")
                        with col2:
                            delete_button = st.form_submit_button("Delete Staff")

                    if update_button:
                        errors = []
                        if not name:
                            errors.append("Name is required.")
                        err = validate_contact_no(contact_no)
                        if err:
                            errors.append(err)
                        if not position:
                            errors.append("Position is required.")

                        if errors:
                            for e in errors:
                                st.error(e)
                        else:
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("""
                                            UPDATE staff 
                                            SET name=%s, position=%s, contact_no=%s, salary=%s 
                                            WHERE staff_id=%s
                                        """, (name, position, contact_no, salary, selected_id))
                                        conn.commit()
                                        st.success("Staff member updated successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating staff: {e}")

                    if delete_button:
                        if confirm_delete("Staff Member", selected_staff["name"]):
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM staff WHERE staff_id=%s", (selected_id,))
                                        conn.commit()
                                        st.success("Staff member deleted successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting staff: {e}")
            else:
                st.info("No staff members found to edit or delete.")
        except Exception as e:
            st.error(f"Error loading staff data: {e}")

# -------------------------
elif menu == "Complaints":
    st.title("🚫 Complaints Management")
    tab1, tab2, tab3 = st.tabs(["📋 View Complaints", "➕ Lodge Complaint", "✏️ Update Complaints"])

    with tab1:
        try:
            df = pd.read_sql("""
                SELECT c.*, s.name as student_name 
                FROM complaints c
                LEFT JOIN students s ON c.roll_no = s.roll_no
                ORDER BY c.date_logged DESC
            """, engine)
            
            if not df.empty:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect("Filter by Status", options=df["status"].dropna().unique())
                with col2:
                    severity_filter = st.multiselect("Filter by Severity", options=df["severity"].dropna().unique()) if 'severity' in df.columns else None
                
                if status_filter:
                    df = df[df["status"].isin(status_filter)]
                if severity_filter and 'severity' in df.columns:
                    df = df[df["severity"].isin(severity_filter)]

                st.dataframe(df, use_container_width=True)
            else:
                st.info("No complaints found.")
        except Exception as e:
            st.error(f"Error loading complaints: {e}")

    with tab2:
        with st.form("add_complaint", clear_on_submit=True):
            # Get list of students
            students = pd.read_sql("SELECT roll_no, name FROM students ORDER BY name", engine)
            
            col1, col2 = st.columns(2)
            with col1:
                roll_no = st.selectbox("Student Roll Number*", options=students["roll_no"], 
                                     format_func=lambda x: f"{x} - {students[students['roll_no']==x]['name'].values[0]}")
                complaint_type = st.selectbox("Complaint Type*", ["Maintenance", "Cleanliness", "Noise", "Roommate", "Other"])
            with col2:
                severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"])
                status = st.selectbox("Status*", ["Pending", "In Progress", "Resolved"])
            
            complaint_text = st.text_area("Complaint Details*", height=150)
            
            submitted = st.form_submit_button("Lodge Complaint")

            if submitted:
                errors = []
                if not complaint_text:
                    errors.append("Complaint details are required.")
                if not roll_no:
                    errors.append("Student roll number is required.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with get_conn() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    INSERT INTO complaints (roll_no, complaint, type, severity, status, date_logged) 
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (roll_no, complaint_text, complaint_type, severity, status, datetime.today()))
                                conn.commit()
                                st.success("Complaint lodged successfully!")
                                st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error lodging complaint: {e}")

    with tab3:
        try:
            df = pd.read_sql("""
                SELECT c.*, s.name as student_name 
                FROM complaints c
                LEFT JOIN students s ON c.roll_no = s.roll_no
                ORDER BY c.date_logged DESC
            """, engine)
            
            if not df.empty:
                complaint_ids = df["complaint_id"].tolist()
                selected_id = st.selectbox("Select Complaint to Update", complaint_ids, 
                                         format_func=lambda x: f"ID: {x} - {df[df['complaint_id']==x]['student_name'].values[0]}")
                
                if selected_id:
                    selected_complaint = df[df["complaint_id"] == selected_id].iloc[0]
                    
                    with st.form("edit_complaint"):
                        col1, col2 = st.columns(2)
                        with col1:
                            status = st.selectbox("Status", ["Pending", "In Progress", "Resolved"], 
                                                 index=["Pending", "In Progress", "Resolved"].index(selected_complaint["status"]))
                            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], 
                                                  index=["Low", "Medium", "High", "Critical"].index(selected_complaint["severity"]))
                        with col2:
                            complaint_type = st.selectbox("Type", ["Maintenance", "Cleanliness", "Noise", "Roommate", "Other"], 
                                                        index=["Maintenance", "Cleanliness", "Noise", "Roommate", "Other"].index(selected_complaint.get("type", "Other")))
                            resolution_date = st.date_input("Resolution Date", 
                                                          value=selected_complaint["date_resolved"] if selected_complaint["date_resolved"] else datetime.today(),
                                                          disabled=status != "Resolved")
                        
                        complaint_text = st.text_area("Complaint Details", value=selected_complaint["complaint"], height=150)
                        resolution_notes = st.text_area("Resolution Notes", value=selected_complaint.get("resolution_notes", ""), height=100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Complaint")
                        with col2:
                            delete_button = st.form_submit_button("Delete Complaint")

                    if update_button:
                        try:
                            with get_conn() as conn:
                                with conn.cursor() as cursor:
                                    cursor.execute("""
                                        UPDATE complaints 
                                        SET complaint=%s, type=%s, severity=%s, status=%s, 
                                            resolution_notes=%s, date_resolved=%s
                                        WHERE complaint_id=%s
                                    """, (
                                        complaint_text,
                                        complaint_type,
                                        severity,
                                        status,
                                        resolution_notes,
                                        resolution_date if status == "Resolved" else None,
                                        selected_id
                                    ))
                                    conn.commit()
                                    st.success("Complaint updated successfully!")
                                    st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating complaint: {e}")

                    if delete_button:
                        if confirm_delete("Complaint", selected_id):
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM complaints WHERE complaint_id=%s", (selected_id,))
                                        conn.commit()
                                        st.success("Complaint deleted successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting complaint: {e}")
            else:
                st.info("No complaints found to update.")
        except Exception as e:
            st.error(f"Error loading complaints: {e}")
            
            
elif menu == "Fees":
    st.title("💳 Manage Fees")
    tab1, tab2, tab3 = st.tabs(["📋 View Fees", "➕ Add Fee Record", "✏️ Edit/Delete Records"])

    # First check what columns exist in the fees table (PostgreSQL version)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fees'
        """))
        fee_columns = [row[0] for row in result]

    with tab1:
        try:
            # Build the query based on available columns
            select_columns = ["f.*"]
            join_clause = ""
            if 'roll_no' in fee_columns:
                select_columns.append("s.name as student_name")
                join_clause = "LEFT JOIN students s ON f.roll_no = s.roll_no"
            
            query = text(f"""
                SELECT {', '.join(select_columns)} 
                FROM fees f
                {join_clause}
                ORDER BY f.fee_id DESC
            """)
            
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                # Convert dates to datetime.date for comparison if they exist
                if 'due_date' in fee_columns:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.date
                
                # Only show status filter if status column exists
                if 'status' in fee_columns:
                    status_filter = st.multiselect("Filter by Status", options=df["status"].dropna().unique())
                    if status_filter:
                        df = df[df["status"].isin(status_filter)]
                
                # Only show date filter if date columns exist
                if 'due_date' in fee_columns:
                    min_date = df['due_date'].min()
                    max_date = df['due_date'].max()
                    date_range = st.date_input("Filter by Due Date Range", [min_date, max_date])
                    if len(date_range) == 2:
                        df = df[(df['due_date'] >= date_range[0]) & 
                               (df['due_date'] <= date_range[1])]

                st.dataframe(df, use_container_width=True)
            else:
                st.info("No fee records found.")
        except Exception as e:
            st.error(f"Error loading fee records: {str(e)}")

    with tab2:
        with st.form("add_fee", clear_on_submit=True):
            # Get list of students
            students = pd.read_sql("SELECT roll_no, name FROM students ORDER BY name", engine)
            
            col1, col2 = st.columns(2)
            with col1:
                roll_no = st.selectbox("Student Roll Number*", options=students["roll_no"], 
                                     format_func=lambda x: f"{x} - {students[students['roll_no']==x]['name'].values[0]}")
                amount = st.number_input("Amount*", min_value=0, value=5000)
            with col2:
                due_date = st.date_input("Due Date*", min_value=datetime.today())
                if 'status' in fee_columns:
                    status = st.selectbox("Status*", ["Paid", "Unpaid", "Partial"])
                else:
                    status = None
            
            submitted = st.form_submit_button("Add Fee Record")

            if submitted:
                try:
                    with get_conn() as conn:
                        with conn.cursor() as cursor:
                            if 'status' in fee_columns:
                                cursor.execute("""
                                    INSERT INTO fees (roll_no, amount, due_date, status, payment_date) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (
                                    roll_no, 
                                    amount, 
                                    due_date, 
                                    status, 
                                    datetime.today() if status == "Paid" else None
                                ))
                            else:
                                cursor.execute("""
                                    INSERT INTO fees (roll_no, amount, due_date) 
                                    VALUES (%s, %s, %s)
                                """, (roll_no, amount, due_date))
                            conn.commit()
                            st.success("Fee record added successfully!")
                            st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error adding fee record: {str(e)}")

    with tab3:
        try:
            # Build query based on available columns
            select_columns = ["*"]
            query = text(f"SELECT {', '.join(select_columns)} FROM fees ORDER BY fee_id DESC")
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                # Convert dates to datetime.date for display if they exist
                if 'due_date' in fee_columns:
                    df['due_date'] = pd.to_datetime(df['due_date']).dt.date
                if 'payment_date' in fee_columns:
                    df['payment_date'] = pd.to_datetime(df['payment_date']).dt.date
                
                fee_ids = df["fee_id"].tolist()
                selected_id = st.selectbox("Select Fee Record to Edit/Delete", fee_ids)
                
                if selected_id:
                    selected_fee = df[df["fee_id"] == selected_id].iloc[0]
                    
                    with st.form("edit_fee"):
                        col1, col2 = st.columns(2)
                        with col1:
                            amount = st.number_input("Amount", min_value=0, value=int(selected_fee["amount"]))
                            if 'due_date' in fee_columns:
                                due_date = st.date_input("Due Date", value=selected_fee["due_date"])
                            else:
                                due_date = None
                        with col2:
                            if 'status' in fee_columns:
                                status = st.selectbox("Status", ["Paid", "Unpaid", "Partial"], 
                                                    index=["Paid", "Unpaid", "Partial"].index(selected_fee["status"]))
                                payment_date = st.date_input("Payment Date", 
                                                           value=selected_fee.get("payment_date", datetime.today()),
                                                           disabled=status != "Paid")
                            else:
                                status = None
                                payment_date = None
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Record")
                        with col2:
                            delete_button = st.form_submit_button("Delete Record")

                    if update_button:
                        try:
                            with get_conn() as conn:
                                with conn.cursor() as cursor:
                                    if 'status' in fee_columns:
                                        cursor.execute("""
                                            UPDATE fees 
                                            SET amount=%s, due_date=%s, status=%s, payment_date=%s 
                                            WHERE fee_id=%s
                                        """, (
                                            amount,
                                            due_date,
                                            status,
                                            payment_date if status == "Paid" else None,
                                            selected_id
                                        ))
                                    else:
                                        cursor.execute("""
                                            UPDATE fees 
                                            SET amount=%s, due_date=%s
                                            WHERE fee_id=%s
                                        """, (amount, due_date, selected_id))
                                    conn.commit()
                                    st.success("Fee record updated successfully!")
                                    st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating fee record: {str(e)}")

                    if delete_button:
                        if confirm_delete("Fee Record", selected_id):
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM fees WHERE fee_id=%s", (selected_id,))
                                        conn.commit()
                                        st.success("Fee record deleted successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting fee record: {str(e)}")
            else:
                st.info("No fee records found to edit or delete.")
        except Exception as e:
            st.error(f"Error loading fee records: {str(e)}")            

# -------------------------
elif menu == "Visitors":
    st.title("🛋️ Visitors Management")
    tab1, tab2, tab3 = st.tabs(["📋 View Visitors", "➕ Add Visitor", "✏️ Edit / Delete Records"])

    with tab1:
        try:
            df = pd.read_sql("""
                SELECT v.*, s.name as student_name 
                FROM visitors v
                LEFT JOIN students s ON v.roll_no = s.roll_no
                ORDER BY v.visit_date DESC
            """, engine)
            
            if not df.empty:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    date_range = st.date_input("Filter by Date Range", 
                                             [df["visit_date"].min(), df["visit_date"].max()])
                with col2:
                    student_filter = st.multiselect("Filter by Student", options=df["student_name"].dropna().unique())
                
                if len(date_range) == 2:
                    df = df[(df['visit_date'] >= pd.to_datetime(date_range[0])) & 
                           (df['visit_date'] <= pd.to_datetime(date_range[1]))]
                if student_filter:
                    df = df[df["student_name"].isin(student_filter)]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No visitors found.")
        except Exception as e:
            st.error(f"Error loading visitors: {e}")
    with tab2:  
        with st.form("add_visitor", clear_on_submit=True):
            # Get list of students
            students = pd.read_sql("SELECT roll_no, name FROM students ORDER BY name", engine)
            
            col1, col2 = st.columns(2)
            with col1:
                roll_no = st.selectbox("Student Roll Number*", options=students["roll_no"], 
                                     format_func=lambda x: f"{x} - {students[students['roll_no']==x]['name'].values[0]}")
                visitor_name = st.text_input("Visitor Name*")
            with col2:
                visit_date = st.date_input("Visit Date*", value=datetime.today())
                purpose = st.text_area("Purpose of Visit*", height=100)
            
            submitted = st.form_submit_button("Add Visitor")

            if submitted:
                errors = []
                if not visitor_name:
                    errors.append("Visitor name is required.")
                if not purpose:
                    errors.append("Purpose of visit is required.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    try:
                        with get_conn() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    INSERT INTO visitors (roll_no, visitor_name, visit_date, purpose) 
                                    VALUES (%s, %s, %s, %s)
                                """, (roll_no, visitor_name, visit_date, purpose))
                                conn.commit()
                                st.success("Visitor record added successfully!")
                                st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding visitor record: {e}")
    with tab3:
        try:
            df = pd.read_sql("""
                SELECT v.*, s.name as student_name 
                FROM visitors v
                LEFT JOIN students s ON v.roll_no = s.roll_no
                ORDER BY v.visit_date DESC
            """, engine)
            
            if not df.empty:
                visitor_ids = df["visitor_id"].tolist()
                selected_id = st.selectbox("Select Visitor Record to Edit/Delete", visitor_ids, 
                                         format_func=lambda x: f"ID: {x} - {df[df['visitor_id']==x]['visitor_name'].values[0]}")
                
                if selected_id:
                    selected_visitor = df[df["visitor_id"] == selected_id].iloc[0]
                    
                    with st.form("edit_visitor"):
                        col1, col2 = st.columns(2)
                        with col1:
                            roll_no = st.selectbox("Student Roll Number", options=students["roll_no"], 
                                                 format_func=lambda x: f"{x} - {students[students['roll_no']==x]['name'].values[0]}", 
                                                 index=students[students['roll_no']==selected_visitor["roll_no"]].index[0])
                            visitor_name = st.text_input("Visitor Name", value=selected_visitor["visitor_name"])
                        with col2:
                            visit_date = st.date_input("Visit Date", value=selected_visitor["visit_date"])
                            purpose = st.text_area("Purpose of Visit", value=selected_visitor["purpose"], height=100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Visitor")
                        with col2:
                            delete_button = st.form_submit_button("Delete Visitor")

                    if update_button:
                        errors = []
                        if not visitor_name:
                            errors.append("Visitor name is required.")
                        if not purpose:
                            errors.append("Purpose of visit is required.")

                        if errors:
                            for e in errors:
                                st.error(e)
                        else:
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("""
                                            UPDATE visitors 
                                            SET roll_no=%s, visitor_name=%s, visit_date=%s, purpose=%s 
                                            WHERE visitor_id=%s
                                        """, (roll_no, visitor_name, visit_date, purpose, selected_id))
                                        conn.commit()
                                        st.success("Visitor record updated successfully!")
                                        st.experimental_rerun() 
                            except Exception as e:
                                st.error(f"Error updating visitor record: {e}")
                    if delete_button:
                        if confirm_delete("Visitor Record", selected_visitor["visitor_name"]):
                            try:
                                with get_conn() as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM visitors WHERE visitor_id=%s", (selected_id,))
                                        conn.commit()
                                        st.success("Visitor record deleted successfully!")
                                        st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting visitor record: {e}")
            else:
                st.info("No visitor records found to edit or delete.")  
        except Exception as e:
            st.error(f"Error loading visitor records: {e}")
# ------------------------- 
elif menu == "Reports":
    st.title("📊 Reports")
    tab1, tab2 = st.tabs(["📈 Student Distribution", "📉 Fees Collection"])

    def get_student_distribution():
        try:
            # Example: Count of students per room
            query = """
                SELECT room_no, COUNT(*) as student_count
                FROM students
                GROUP BY room_no
                ORDER BY room_no
            """
            df = pd.read_sql(query, engine)
            df.rename(columns={"student_count": "Student Count"}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching student distribution: {e}")
            return pd.DataFrame()

    with tab1:
        try:
            df = get_student_distribution()
            if not df.empty:
                st.bar_chart(df.set_index('room_no'))
            else:
                st.info("No student distribution data found.")
        except Exception as e:
            st.error(f"Error loading student distribution data: {e}")

    with tab2:
        try:
            df = pd.read_sql("""
                SELECT date_trunc('month', due_date) as month, SUM(amount) as total_amount 
                FROM fees 
                GROUP BY month 
                ORDER BY month
            """, engine)
            
            if not df.empty:
                st.line_chart(df.set_index('month'))
            else:
                st.info("No fees collection data found.")
        except Exception as e:
            st.error(f"Error loading fees collection data: {e}")
# -------------------------
elif menu == "Settings":
    st.title("⚙️ Settings")
    st.write("Settings page is under construction.")
    st.info("This feature is not yet available.")
    
# -------------------------
# Footer