import oracledb

# 🔐 Replace these credentials with your actual Oracle DB info
ORACLE_USER = "your_username"
ORACLE_PASSWORD = "your_password"
ORACLE_DSN = "localhost/XEPDB1"  # Example: hostname/service_name

connection = None

def get_connection():
    global connection
    if connection is None:
        try:
            connection = oracledb.connect(
                user=ORACLE_USER,
                password=ORACLE_PASSWORD,
                dsn=ORACLE_DSN
            )
        except oracledb.DatabaseError as e:
            raise Exception(f"Oracle DB Connection Error: {e}")
    return connection

def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or {})
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print("Query Execution Error:", e)
        return []
    finally:
        cursor.close()

def execute_non_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or {})
        conn.commit()
        return True
    except Exception as e:
        print("Non-query Execution Error:", e)
        return False
    finally:
        cursor.close()

def call_procedure(proc_name, args=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if args:
            cursor.callproc(proc_name, args)
        else:
            cursor.callproc(proc_name)
        conn.commit()
        return True
    except Exception as e:
        print(f"Procedure Call Error: {e}")
        return False
    finally:
        cursor.close()

def close_connection():
    global connection
    if connection:
        connection.close()
        connection = None
