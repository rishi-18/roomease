
DROP TABLE IF EXISTS room_inventory CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS visitors CASCADE;
DROP TABLE IF EXISTS complaints CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS room_allocations CASCADE;
DROP TABLE IF EXISTS notices CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;

-- Students table (simplified to match Python app)
CREATE TABLE students (
    roll_no VARCHAR(20) PRIMARY KEY, 
    name VARCHAR(100) NOT NULL,       
    department VARCHAR(50) NOT NULL,
    room_no VARCHAR(10),      
    year VARCHAR(10) CHECK (year IN ('1st', '2nd', '3rd', '4th')),  
    contact_no VARCHAR(15),
    email VARCHAR(100),
    date_joined DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'Active'
);


CREATE TABLE rooms (
    room_no VARCHAR(10) PRIMARY KEY, 
    capacity INT NOT NULL CHECK (capacity BETWEEN 1 AND 4),  
    status VARCHAR(20) NOT NULL DEFAULT 'Vacant' CHECK (status IN ('Vacant', 'Occupied', 'Maintenance')),  
    floor INT,
    room_type VARCHAR(20)
);

-- Fees table (matches Python app requirements)
CREATE TABLE fees (
    fee_id SERIAL PRIMARY KEY,
    roll_no VARCHAR(20) REFERENCES students(roll_no),
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Paid', 'Unpaid', 'Partial')),
    receipt_number VARCHAR(50)
);

-- Staff table (simplified to match Python app)
CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL CHECK (position IN ('Warden', 'Caretaker', 'Cleaner', 'Cook', 'Security', 'Other')),
    contact_no VARCHAR(15),
    salary DECIMAL(10,2),
    join_date DATE DEFAULT CURRENT_DATE
);

-- Complaints table (matches Python app requirements)
CREATE TABLE complaints (
    complaint_id SERIAL PRIMARY KEY,
    roll_no VARCHAR(20) REFERENCES students(roll_no),
    complaint TEXT NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('Maintenance', 'Cleanliness', 'Noise', 'Roommate', 'Other')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Resolved')),
    date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_resolved TIMESTAMP,
    resolution_notes TEXT
);

-- Visitors table (matches Python app requirements)
CREATE TABLE visitors (
    visitor_id SERIAL PRIMARY KEY,
    roll_no VARCHAR(20) REFERENCES students(roll_no),
    visitor_name VARCHAR(100) NOT NULL,
    visit_date DATE NOT NULL,
    purpose TEXT NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP
);

-- Users table for authentication (not in Python app but recommended)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Staff', 'Student')),
    linked_id INT, -- Can reference student roll_no or staff_id
    last_login TIMESTAMP,
    account_status VARCHAR(20) DEFAULT 'Active'
);

-- Add foreign key from students to rooms
ALTER TABLE students ADD CONSTRAINT fk_student_room 
    FOREIGN KEY (room_no) REFERENCES rooms(room_no);

-- Create indexes for performance
CREATE INDEX idx_students_room ON students(room_no);
CREATE INDEX idx_fees_roll_no ON fees(roll_no);
CREATE INDEX idx_fees_status ON fees(status);
CREATE INDEX idx_complaints_roll_no ON complaints(roll_no);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_visitors_roll_no ON visitors(roll_no);

-- Triggers for data integrity

-- Trigger to prevent room deletion if occupied
CREATE OR REPLACE FUNCTION prevent_occupied_room_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM students WHERE room_no = OLD.room_no) THEN
        RAISE EXCEPTION 'Cannot delete room % as it is currently occupied', OLD.room_no;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_prevent_occupied_room_deletion
BEFORE DELETE ON rooms
FOR EACH ROW
EXECUTE FUNCTION prevent_occupied_room_deletion();

-- Trigger to update room status when student is assigned/unassigned
CREATE OR REPLACE FUNCTION update_room_status()
RETURNS TRIGGER AS $$
BEGIN
    -- When a student is assigned to a room
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.room_no IS NOT NULL) THEN
        UPDATE rooms SET status = 'Occupied' WHERE room_no = NEW.room_no;
    END IF;
    
    -- When a student is unassigned from a room
    IF TG_OP = 'UPDATE' AND OLD.room_no IS NOT NULL AND (NEW.room_no IS NULL OR NEW.room_no != OLD.room_no) THEN
        UPDATE rooms SET status = 'Vacant' WHERE room_no = OLD.room_no;
    END IF;
    
    -- When a student is deleted
    IF TG_OP = 'DELETE' AND OLD.room_no IS NOT NULL THEN
        UPDATE rooms SET status = 'Vacant' WHERE room_no = OLD.room_no;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_update_room_status
AFTER INSERT OR UPDATE OR DELETE ON students
FOR EACH ROW
EXECUTE FUNCTION update_room_status();

-- Function to check room vacancy before student assignment
CREATE OR REPLACE FUNCTION check_room_vacancy()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.room_no IS NOT NULL AND 
       (SELECT status FROM rooms WHERE room_no = NEW.room_no) != 'Vacant' THEN
        RAISE EXCEPTION 'Room % is not vacant', NEW.room_no;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_check_room_vacancy
BEFORE INSERT OR UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION check_room_vacancy();