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

# SQL query to create the master table
create_table_query = """
CREATE TABLE IF NOT EXISTS master_table (
    EmployeeCode VARCHAR(255),
    EmployeeName VARCHAR(255),
    Designation VARCHAR(255),
    Building VARCHAR(255),
    ReportingManager VARCHAR(255),
    BU VARCHAR(255),
    Project VARCHAR(255),
    Location VARCHAR(255),
    PRIMARY KEY (EmployeeCode)
)
"""

# Establish connection to MySQL server
try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Create table if not exists
    cursor.execute(create_table_query)

    # Read data from CSV file and insert into the table
    with open('db_master.csv', 'r') as file:
        reader = csv.reader(file, delimiter=';')  # Set delimiter to semicolon
        next(reader)  # Skip header row
        for row in reader:
            # Split the row into individual values
            employee_code, employee_name, designation, building, reporting_manager, bu, project, location = row
            # Insert data into the table
            cursor.execute("INSERT INTO master_table (EmployeeCode, EmployeeName, Designation, Building, ReportingManager, BU, Project, Location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (employee_code, employee_name, designation, building, reporting_manager, bu, project, location))

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
        
