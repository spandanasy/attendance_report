import mysql.connector
import csv

# MySQL Connection Configuration
config = {
    'user': 'root',
    'password': 'spandana',
    'host': 'localhost',
    'database': 'employee',
    'raise_on_warnings': True
}

# SQL query to create the attendance table
create_table_query1 = """
CREATE TABLE IF NOT EXISTS attendance_report (
    EmployeeCode VARCHAR(255),
    AbsentDates TEXT,
    TotalPresent INT DEFAULT NULL,
    TotalAbsent INT DEFAULT NULL,
    PRIMARY KEY (EmployeeCode)
)
"""
create_table_query2 = """
CREATE TABLE IF NOT EXISTS attendance_report (
    Employee Code VARCHAR(255),
    Employee Name varchar(255),
    Designation varchar(255),
    Building varchar(255),
    Reporting Manager varchar(255),
    BU varchar(255),
    Project varchar(255),
    Location varchar(255),
    PRIMARY KEY (Employee Code)
)
"""
# Establish connection to MySQL server
try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Create table if not exists
    cursor.execute(create_table_query1)

    # Read data from CSV file and insert into the table
    with open('db_attendance.csv', 'r') as file:
        reader = csv.reader(file, delimiter=';')  # Set delimiter to semicolon
        next(reader)  # Skip header row
        for row in reader:
            # Split the row into individual values
            employee_code, absent_dates, total_present, total_absent = row
            # Insert data into the table
            cursor.execute("INSERT INTO attendance_report (EmployeeCode, AbsentDates, TotalPresent, TotalAbsent) VALUES (%s, %s, %s, %s)", (employee_code, absent_dates, total_present, total_absent))

    # Commit changes
    connection.commit()
    print("Data inserted successfully.")

except mysql.connector.Error as error:
    print("Failed to insert data into MySQL table:", error)

finally:
    # Close cursor and connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed.")
