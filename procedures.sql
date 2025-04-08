-- ✅ 1. Procedure to allot a student to a room
CREATE OR REPLACE PROCEDURE allot_room(
    p_student_id IN VARCHAR2,
    p_room_no IN VARCHAR2
) AS
    v_current_capacity NUMBER;
    v_max_capacity NUMBER;
BEGIN
    -- Check if room exists
    SELECT capacity INTO v_max_capacity FROM ROOM WHERE room_no = p_room_no;

    -- Count current students
    SELECT COUNT(*) INTO v_current_capacity FROM STUDENT WHERE room_no = p_room_no;

    IF v_current_capacity < v_max_capacity THEN
        UPDATE STUDENT SET room_no = p_room_no WHERE student_id = p_student_id;
        DBMS_OUTPUT.PUT_LINE('Room allotted successfully.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Room is full.');
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('Room does not exist.');
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
END;
/

-- ✅ 2. Procedure to record a fee payment
CREATE OR REPLACE PROCEDURE pay_fee(
    p_student_id IN VARCHAR2,
    p_amount IN NUMBER
) AS
    v_total_fee NUMBER := 50000; -- assumed total fee
BEGIN
    INSERT INTO PAYMENT(student_id, amount_paid, payment_date)
    VALUES (p_student_id, p_amount, SYSDATE);

    DBMS_OUTPUT.PUT_LINE('Fee payment recorded.');
END;
/

-- ✅ 3. Procedure to register a complaint
CREATE OR REPLACE PROCEDURE register_complaint(
    p_student_id IN VARCHAR2,
    p_details IN VARCHAR2
) AS
BEGIN
    INSERT INTO COMPLAINT(student_id, complaint_date, complaint_details, status)
    VALUES (p_student_id, SYSDATE, p_details, 'Pending');

    DBMS_OUTPUT.PUT_LINE('Complaint registered.');
END;
/

-- ✅ 4. Procedure to vacate a room (remove student from room)
CREATE OR REPLACE PROCEDURE vacate_room(
    p_student_id IN VARCHAR2
) AS
BEGIN
    UPDATE STUDENT SET room_no = NULL WHERE student_id = p_student_id;
    DBMS_OUTPUT.PUT_LINE('Room vacated.');
END;
/

-- ✅ 5. Procedure to check room capacity
CREATE OR REPLACE PROCEDURE check_room_capacity(
    p_room_no IN VARCHAR2
) AS
    v_current_capacity NUMBER;
    v_max_capacity NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_current_capacity FROM STUDENT WHERE room_no = p_room_no;
    SELECT capacity INTO v_max_capacity FROM ROOM WHERE room_no = p_room_no;

    DBMS_OUTPUT.PUT_LINE('Room ' || p_room_no || ': ' || v_current_capacity || '/' || v_max_capacity);
END;
/
