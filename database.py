import mysql.connector
import csv

# MySQL Connection Configuration
config = {
    'user': 'root',
    'password': 'spandana',  # Replace 'your_password' with your MySQL password
    'host': 'localhost',
    'database': 'employee',
    'raise_on_warnings': True
}

# SQL query to create the attendance table
create_table_query = """
CREATE TABLE IF NOT EXISTS attendance_report (
    EmployeeCode VARCHAR(255),
    AbsentDates TEXT,
    TotalPresent INT DEFAULT NULL,
    TotalAbsent INT DEFAULT NULL,
    PRIMARY KEY (EmployeeCode)
)
"""

try:
    # Establish connection to MySQL server
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Create table if not exists
    cursor.execute(create_table_query)

    # Read data from CSV file and insert into the table
    with open('db_attendance.csv', 'r') as file:
        reader = csv.reader(file, delimiter=',')  # Assuming CSV is comma-delimited
        next(reader)  # Skip header row
        for row in reader:
            # Extract values from the row
            employee_code, absent_dates, total_present, total_absent = row

            # Check if the record already exists in the table
            cursor.execute("SELECT EmployeeCode FROM attendance_report WHERE EmployeeCode = %s", (employee_code,))
            existing_record = cursor.fetchone()

            if existing_record:
                # Record already exists, handle accordingly (e.g., update existing record)
                # Example: cursor.execute("UPDATE attendance_report SET ... WHERE EmployeeCode = %s", (employee_code,))
                pass
            else:
                # Record does not exist, insert into the table
                cursor.execute("INSERT INTO attendance_report (EmployeeCode, AbsentDates, TotalPresent, TotalAbsent) VALUES (%s, %s, %s, %s)", (employee_code, absent_dates, total_present, total_absent))

    # Commit changes
    connection.commit()
    print("Data inserted successfully.")

except mysql.connector.Error as error:
    print("Failed to insert data into MySQL table:", error)

finally:
    # Close cursor and connection
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed.")
