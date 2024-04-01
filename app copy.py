from flask import Flask, render_template, request, Response, session
import mysql.connector
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="spandana",
    database="employee"
)
cursor = db.cursor()

@app.route('/')
def index():
    return render_template('index_db.html')

@app.route('/search', methods=['POST'])
def search():
    psi_id = request.form.get('psi_id')
    location = request.form.get('location')
    bu = request.form.get('BU')
    project = request.form.get('project')
    # building = request.form.get('building')

    try:
        if psi_id and not any(request.form.get(key) for key in ['location', 'bu', 'project']):
            cursor.execute("SELECT * FROM master_table WHERE `EmployeeCode` = %s", (psi_id,))
            manager_info = cursor.fetchone()
            if not manager_info:
                return "Manager not found."

            # Query employee details with left join to include all employees
            cursor.execute("""
                SELECT m.`EmployeeCode`, m.`EmployeeName`, m.`ReportingManager`, 
                COALESCE(a.`TotalPresent`, 0) AS TotalPresent, 
                COALESCE(a.`TotalAbsent`, 0) AS TotalAbsent,
                COALESCE(m.`Building`, 'NA') AS Building,
                COALESCE(m.`BU`, 'NA') AS BU,
                COALESCE(m.`Location`, 'NA') AS Location
                FROM master_table m
                LEFT JOIN attendance_report a ON m.`EmployeeCode` = a.`EmployeeCode`
                WHERE m.`ReportingManager` = %s
                ORDER BY 
                SUBSTRING_INDEX(m.EmployeeCode, ' - ', 1), 
                CAST(SUBSTRING_INDEX(m.EmployeeCode, ' - ', -1) AS UNSIGNED) ASC
                """, (psi_id,))
            emp_details = cursor.fetchall()

            # No need for a separate query to fetch attendance records

            combined_data = []
            for employee in emp_details:
                emp_code = employee[0]
                emp_name = employee[1]
                total_present = employee[3]  # Extract TotalPresent directly from emp_details
                total_absent = employee[4]   # Extract TotalAbsent directly from emp_details
                bu = employee[6]  # Corrected index for BU
                location = employee[7]  # Corrected index for Location
                # building = employee[5]
                combined_data.append((emp_code, emp_name, total_present, total_absent, bu, location))

            session['combined_data'] = combined_data
            session['manager_info'] = manager_info
            csv_data = "Employee Code,Employee Name,Total Present,Total Absent,BU,Location\n"
            for emp in combined_data:
                csv_data += "{},{},{},{},{},{}\n".format(emp[0], emp[1], emp[2], emp[3], emp[4], emp[5])

            # Store CSV data in session
            session['csv_data'] = csv_data

            return render_template('results.html', manager_info=manager_info, combined_data=combined_data)


        elif location:
            employee_query = """
                SELECT e.`EmployeeCode`, e.`EmployeeName`, m.`EmployeeName` AS `ReportingManager`, e.`BU`
                FROM master_table e
                LEFT JOIN master_table m ON e.`ReportingManager` = m.`EmployeeCode`
                WHERE e.Location = %s
                ORDER BY 
                SUBSTRING_INDEX(e.EmployeeCode, ' - ', 1), 
                CAST(SUBSTRING_INDEX(e.EmployeeCode, ' - ', -1) AS UNSIGNED) ASC
            """

            cursor.execute(employee_query, (location,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details
            session['search_type'] = location
            attendance_data = {}
            attendance_query = "SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates FROM attendance_report WHERE EmployeeCode IN (SELECT `EmployeeCode` FROM master_table WHERE Location = %s)"
            cursor.execute(attendance_query, (location,))
            attendance_records = cursor.fetchall()

            for record in attendance_records:
                attendance_data[record[0]] = {'TotalPresent': record[1], 'TotalAbsent': record[2],
                                              'AbsentDates': record[3]}

            for i, employee in enumerate(employee_details):
                employee_code = employee[0]

                if employee_code in attendance_data:
                    total_present = attendance_data[employee_code]['TotalPresent']
                    total_absent = attendance_data[employee_code]['TotalAbsent']
                    absent_dates = attendance_data[employee_code]['AbsentDates']
                    employee_details[i] += (total_present, total_absent, absent_dates)

                else:
                    employee_details[i] += ("", "", "")
            return render_template('search_result.html', employee_details=employee_details,
                                   search_type=location)

        elif project:
            query = "SELECT `EmployeeCode`, `EmployeeName`, `ReportingManager` FROM master_table WHERE Project = %s"
            cursor.execute(query, (project,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details  # Storing data in session
            return render_template('search_result.html', employee_details=employee_details,
                                   search_type="Employees working in: " + project)

        elif bu:
            employee_query = """
                SELECT e.`EmployeeCode`, e.`EmployeeName`, m.`EmployeeName` AS `ReportingManager`, e.`Location`
                FROM master_table e
                LEFT JOIN master_table m ON e.`ReportingManager` = m.`EmployeeCode`
                WHERE e.BU = %s
                ORDER BY 
                SUBSTRING_INDEX(e.EmployeeCode, ' - ', 1), 
                CAST(SUBSTRING_INDEX(e.EmployeeCode, ' - ', -1) AS UNSIGNED) ASC
            """
            cursor.execute(employee_query, (bu,))
            employee_details = cursor.fetchall()
            session['employee_details'] = employee_details
            session['search_type'] = bu
            attendance_data = {}
            attendance_query = "SELECT EmployeeCode, TotalPresent, TotalAbsent, AbsentDates FROM attendance_report WHERE EmployeeCode IN (SELECT `EmployeeCode` FROM master_table WHERE BU = %s)"
            cursor.execute(attendance_query, (bu,))
            attendance_records = cursor.fetchall()

            for record in attendance_records:
                attendance_data[record[0]] = {'TotalPresent': record[1], 'TotalAbsent': record[2],
                                              'AbsentDates': record[3]}
            for i, employee in enumerate(employee_details):
                employee_code = employee[0]

                if employee_code in attendance_data:
                    total_present = attendance_data[employee_code]['TotalPresent']
                    total_absent = attendance_data[employee_code]['TotalAbsent']
                    absent_dates = attendance_data[employee_code]['AbsentDates']
                    employee_details[i] += (total_present, total_absent, absent_dates)

                else:
                    employee_details[i] += ("", "", "")
            return render_template('search_result.html', employee_details=employee_details,
                                   search_type=bu)

        else:
            return "Error: invalid search request"

    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route("/download_csv_emp")
def download_csv_emp():
    # Retrieve CSV data from session
    csv_data = session.pop('csv_data', None)
    manager_info = session.get('manager_info')

    if csv_data and manager_info:
        # Send CSV as a response
        manager_name = manager_info[1]
        #cursor.execute("SELECT MIN(Date), MAX(Date) FROM attendance_report WHERE EmployeeCode = %s", (manager_info[0],))
        absent_dates = fetch_absent_dates(manager_info[0])
        if absent_dates:
            min_date = min(absent_dates)
            max_date = max(absent_dates)
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "No date range available"
        header_lines = [
            f"Reporting Manager- {manager_name}",
            f"Date Range: {date_range}"
        ]
        csv_data_with_headers = "\n".join(header_lines) + "\n" + csv_data

        filename = f"manager_{manager_name}.csv"
        return Response(
            csv_data_with_headers,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    else:
        # Handle case when CSV data is not available
        return "No CSV data available"
    
def fetch_absent_dates(manager_id):
    try:
        query = """
        SELECT AbsentDate
        FROM attendance_report
        WHERE EmployeeCode IN (
            SELECT EmployeeCode
            FROM master_table
            WHERE ReportingManager = %s
        )
        """
        cursor.execute(query, (manager_id,))
        results = cursor.fetchall()
        absent_dates = [result[0] for result in results]
        cursor.close()
        db.close()

        return absent_dates
    except Exception as e:
        print(f"An error occurred while fetching absent dates: {str(e)}")
        return []
    
@app.route('/download_csv')
def download_csv():
    try:
        employee_details = session.get('employee_details')
        if not employee_details:
            return "No data to download."

        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)
        search_type = session.get('search_type')
        # search_value = search_type.split(': ')[-1]

        if "Employees" in search_type:
            department_name = search_type.split(': ')[1]

        else:
            department_name = ""

        start_date = session.get('Mar-1')
        end_date = session.get('Mar-26')

        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else "01-Mar"
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else "26-Mar"

        csv_writer.writerow(["Attendance report: {}".format(search_type)])
        csv_writer.writerow(["Date Range: {} to {}".format(start_date_str, end_date_str)])

        if search_type.startswith("Employees"):
            headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present',
                        'Total Absent']
        else:
            headings = ['Employee Code', 'Employee Name', 'Reporting Manager', 'Location', 'Total Present', 'Total Absent']

        csv_writer.writerow(headings)

        for employee in employee_details:
            csv_writer.writerow([employee[0], employee[1], employee[2], employee[3], employee[4], employee[5]])

        csv_output.seek(0)

        filename = f"{search_type}.csv"
        if department_name:
            filename = f"Attendance Report: {department_name}.csv"

        return Response(
            csv_output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )

    except Exception as e:
        return f"An error occurred while downloading CSV: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)



