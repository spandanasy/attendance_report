from flask import Flask, render_template, request, Response, session
from flask_mysqldb import MySQL
import mysql.connector
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="spandana",
    database="employee"
)
cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index_db(new).html')

@app.route('/search', methods=['POST'])
def search():
    try:
        psi_id = request.form.get('psi_id')
        location = request.form.get('location')
        bu = request.form.get('BU')
        project = request.form.get('project')

        if psi_id and not any(request.form.get(key) for key in ['location', 'BU', 'project']):
            # Query manager info
            cursor.execute("SELECT * FROM master_table WHERE EmployeeCode = %s", (psi_id,))
            manager_info = cursor.fetchone()

            if not manager_info:
                return "Manager not found."

            # Query employee details with left join to include all employees
            cursor.execute("""
                SELECT m.EmployeeCode, m.EmployeeName, m.ReportingManager, a.TotalPresent, a.TotalAbsent
                FROM master_table m
                LEFT JOIN attendance_report a ON m.EmployeeCode = a.EmployeeCode
                WHERE m.ReportingManager = %s
                ORDER BY m.EmployeeCode ASC
            """, (psi_id,))
            emp_details = cursor.fetchall()

            # Retrieve attendance records
            cursor.execute("""
                SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates 
                FROM attendance_report 
                WHERE EmployeeCode IN (SELECT EmployeeCode FROM master_table WHERE ReportingManager = %s)
            """, (psi_id,))
            attendance_records = cursor.fetchall()

            # Combine employee details and attendance records
            combined_data = []
            for employee in emp_details:
                emp_code, emp_name, _, total_present, total_absent = employee
                combined_data.append((emp_code, emp_name, total_present, total_absent))

            # Store combined_data and manager_info in session
            session['combined_data'] = combined_data
            session['manager_info'] = manager_info

            return render_template('results.html', manager_info=manager_info, combined_data=combined_data)

        elif location:
            # Query employees by location
            employee_query = """
                SELECT e.EmployeeCode, e.EmployeeName, m.EmployeeName AS ReportingManager, e.BU
                FROM master_table e
                LEFT JOIN master_table m ON e.ReportingManager = m.EmployeeCode
                WHERE e.Location = %s
            """
            cursor.execute(employee_query, (location,))
            employee_details = cursor.fetchall()

            session['employee_details'] = employee_details
            session['search_type'] = f"Location: {location}"

            # Retrieve attendance records for employees in this location
            attendance_query = """
                SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates 
                FROM attendance_report 
                WHERE EmployeeCode IN (SELECT EmployeeCode FROM master_table WHERE Location = %s)
            """
            cursor.execute(attendance_query, (location,))
            attendance_records = cursor.fetchall()

            # Combine employee details with attendance records
            for i, employee in enumerate(employee_details):
                employee_code = employee[0]
                for record in attendance_records:
                    if record[0] == employee_code:
                        employee_details[i] += record[1:]  # Append attendance data to employee details
                        break
                else:
                    # No attendance record found for this employee, add empty data
                    employee_details[i] += ("", "", "")

            return render_template('search.html', employee_details=employee_details,
                                   search_type=f"Employees working in {location}")

        elif bu:
            # Query employees by business unit
            employee_query = """
                SELECT e.EmployeeCode, e.EmployeeName, m.EmployeeName AS ReportingManager, e.Location
                FROM master_table e
                LEFT JOIN master_table m ON e.ReportingManager = m.EmployeeCode
                WHERE e.BU = %s
            """
            cursor.execute(employee_query, (bu,))
            employee_details = cursor.fetchall()

            session['employee_details'] = employee_details
            session['search_type'] = f"BU: {bu}"

            # Retrieve attendance records for employees in this BU
            attendance_query = """
                SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates 
                FROM attendance_report 
                WHERE EmployeeCode IN (SELECT EmployeeCode FROM master_table WHERE BU = %s)
            """
            cursor.execute(attendance_query, (bu,))
            attendance_records = cursor.fetchall()

            # Combine employee details with attendance records
            for i, employee in enumerate(employee_details):
                employee_code = employee[0]
                for record in attendance_records:
                    if record[0] == employee_code:
                        employee_details[i] += record[1:]  # Append attendance data to employee details
                        break
                else:
                    # No attendance record found for this employee, add empty data
                    employee_details[i] += ("", "", "")

            return render_template('search.html', employee_details=employee_details,
                                   search_type=f"Employees working in business unit {bu}")

        else:
            return "Error: invalid search request"

    except Exception as e:
        print("An error occurred:", str(e))
        return "An error occurred while processing the request."

@app.route('/download_csv')
def download_csv():
    try:
        employee_details = session.get('employee_details')

        if not employee_details:
            return "No data to download."

        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)

        # Write CSV header
        csv_writer.writerow(["Employee Code", "Employee Name", "Reporting Manager", "Location", "Total Present", "Total Absent"])

        # Write data to CSV
        for employee in employee_details:
            csv_writer.writerow(employee)

        # Move buffer to beginning
        csv_output.seek(0)

        # Prepare response
        return Response(
            csv_output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=employee_details.csv'}
        )

    except Exception as e:
        return f"An error occurred while downloading CSV: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
