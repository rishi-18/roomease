import streamlit as st

# ---------- PAGE CONFIG ---------- 
st.set_page_config(page_title="RoomEase", layout="wide")
st.title("🏠 RoomEase - Hostel Management System")

# ---------- NAVIGATION ----------
menu = ["🏠 Home", "📝 Register Student", "🚪 Allot Room", "💳 Pay Fee", "📣 File Complaint", "📊 Dashboards"]
choice = st.sidebar.selectbox("Navigate", menu)

# ---------- HOME ----------
if choice == "🏠 Home":
    st.subheader("Welcome to RoomEase")
    st.markdown("""
    - Register students
    - Allot rooms
    - Manage fees
    - Handle complaints
    """)

# ---------- STUDENT REGISTRATION ----------
elif choice == "📝 Register Student":
    st.subheader("📝 Register New Student")

    student_id = st.text_input("Student ID")
    name = st.text_input("Name")
    phone = st.text_input("Phone (10-digit)")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    dept = st.text_input("Department")
    year = st.number_input("Year", min_value=1, max_value=5, step=1)
    guardian_name = st.text_input("Guardian Name")
    guardian_contact = st.text_input("Guardian Contact (10-digit)")

    if st.button("Register"):
        # Simulating registration (mock behavior)
        st.success(f"Student {name} registered successfully!")

# ---------- ROOM ALLOTMENT ----------
elif choice == "🚪 Allot Room":
    st.subheader("🚪 Allot Room to Student")

    student_id = st.text_input("Student ID")
    room_no = st.text_input("Room Number")

    if st.button("Allot Room"):
        # Simulating room allotment (mock behavior)
        st.success(f"Room {room_no} allotted to student {student_id} successfully.")

# ---------- PAY FEES ----------
elif choice == "💳 Pay Fee":
    st.subheader("💳 Pay Hostel Fees")

    fee_id = st.text_input("Fee ID")
    amount = st.number_input("Amount", min_value=1, max_value=10000, step=100)

    if st.button("Pay Now"):
        # Simulating fee payment (mock behavior)
        st.success(f"₹{amount} paid successfully for Fee ID {fee_id}.")

# ---------- FILE COMPLAINT ----------
elif choice == "📣 File Complaint":
    st.subheader("📣 File a Complaint")

    complaint_id = st.text_input("Complaint ID")
    student_id = st.text_input("Student ID")
    description = st.text_area("Complaint Description")

    if st.button("Submit Complaint"):
        # Simulating complaint submission (mock behavior)
        st.success(f"Complaint {complaint_id} submitted successfully by student {student_id}.")

# ---------- DASHBOARDS ----------
elif choice == "📊 Dashboards":
    st.subheader("📊 Admin Dashboard")

    dashboard_tab = st.selectbox("Choose View", ["All Students", "Room Status", "Complaints", "Fees Due"])

    # Simulating mock data for dashboard views
    if dashboard_tab == "All Students":
        students = [
            {"Student ID": "S123", "Name": "John Doe", "Room No": "101"},
            {"Student ID": "S124", "Name": "Priya Sharma", "Room No": "102"},
            {"Student ID": "S125", "Name": "Amit Kumar", "Room No": "103"}
        ]
        st.table(students)

    elif dashboard_tab == "Room Status":
        rooms = [
            {"Room No": "101", "Status": "Occupied", "Student ID": "S123"},
            {"Room No": "102", "Status": "Occupied", "Student ID": "S124"},
            {"Room No": "103", "Status": "Vacant", "Student ID": None}
        ]
        st.table(rooms)

    elif dashboard_tab == "Complaints":
        complaints = [
            {"Complaint ID": "C101", "Student ID": "S123", "Description": "No hot water"},
            {"Complaint ID": "C102", "Student ID": "S124", "Description": "Broken window"},
        ]
        st.table(complaints)

    elif dashboard_tab == "Fees Due":
        fees_due = [
            {"Fee ID": "F101", "Student ID": "S123", "Amount": "₹2000", "Status": "Due"},
            {"Fee ID": "F102", "Student ID": "S124", "Amount": "₹2500", "Status": "Paid"}
        ]
        st.table(fees_due)
