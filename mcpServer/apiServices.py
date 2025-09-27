import pandas as pd
from flask import Flask, jsonify, request
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
# Define the path to your Excel file.
# This script assumes the Excel file is in the same directory.
EXCEL_FILE = 'src\\schedule.xlsm'
# Define the non-date columns to separate them from schedule columns.
# UPDATED: This list now matches the new column names from your Excel file.
STATIC_COLUMNS = [
    'Location', '01_Manager', 'EDGers', 'Email', 'MATLAB Answers', 'Phone',
    'Has Salesforce License', 'Email or Phone status',
    'Schedule as per the week #54', 'GL', 'Support', 'IN - BM/GL',
    'ML - Lead', 'SF_ML Answers', 'AU', 'CM_ML Answers', 'ML - Lead.1'
]

# --- Helper Function ---
def load_data():
    """Loads and preprocesses data from the Excel file."""
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(EXCEL_FILE,header=1)
        # Convert all date-like column headers to strings in YYYY-MM-DD format
        # This handles Excel's automatic date conversion
        new_columns = {}
        for col in df.columns:
            if isinstance(col, datetime):
                new_columns[col] = col.strftime('%Y-%m-%d')
        df.rename(columns=new_columns, inplace=True)
        return df, None
    except FileNotFoundError:
        return None, {"error": "Internal Server Error", "message": f"Data source '{EXCEL_FILE}' not found."}
    except Exception as e:
        return None, {"error": "Internal Server Error", "message": f"An error occurred while processing the data file: {str(e)}"}

# --- API Endpoints ---

@app.route('/api/edgers', methods=['GET'])
def get_edgers_by_role_and_date():
    """
    API endpoint to fetch all edgers with a specific role on a particular day.
    Query parameters: ?date=YYYY-MM-DD&role=ROLE
    """
    # 1. Get query parameters from the request URL
    query_date = request.args.get('date')
    query_role = request.args.get('role')

    # 2. Validate the presence of required parameters
    if not query_date or not query_role:
        return jsonify({
            "error": "Bad Request",
            "message": "Both 'date' (in YYYY-MM-DD format) and 'role' query parameters are required."
        }), 400

    # 3. Validate date format
    try:
        datetime.strptime(query_date, '%Y-%m-%d')
    except ValueError:
         return jsonify({
            "error": "Bad Request",
            "message": "Invalid date format. Please use YYYY-MM-DD."
        }), 400
    
    # 4. Load data from Excel
    df, error = load_data()
    if error:
        return jsonify(error), 500
    print("Available columns:", df.columns.tolist())

    # 5. Check if the requested date exists as a column
    if query_date not in df.columns:
        return jsonify({
            "error": "Not Found",
            "message": f"No schedule data found for the date '{query_date}'."
        }), 404

    # 6. Filter the DataFrame to find matching rows and extract EDGer names
    try:
        # Filter rows where the column for the query_date has the value of query_role
        filtered_edgers = df[df[query_date] == query_role]
        
        # Get the list of names from the 'EDGers' column
        edger_names = filtered_edgers['EDGers'].tolist()

        # 7. Build and return the successful JSON response
        response = {
            "date": query_date,
            "role": query_role,
            "count": len(edger_names),
            "edgers": edger_names
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/api/edgers/<string:edger_name>/schedule', methods=['GET'])
def get_schedule_by_edger(edger_name):
    """
    API endpoint to fetch the full schedule for a specific EDGer.
    URL Parameter: /api/edgers/Priya%20Sharma/schedule
    """
    # 1. Load data
    df, error = load_data()
    if error:
        return jsonify(error), 500

    # 2. Find the row for the specified EDGer
    edger_data = df[df['EDGers'] == edger_name]

    # 3. Handle case where EDGer is not found
    if edger_data.empty:
        return jsonify({"error": "Not Found", "message": f"EDGer with name '{edger_name}' not found."}), 404

    # 4. Prepare the response
    # Convert the single-row DataFrame to a dictionary
    edger_record = edger_data.iloc[0].to_dict()

    # Separate static details from the schedule
    details = {key: edger_record[key] for key in STATIC_COLUMNS if key != 'EDGers'}
    schedule = {key: edger_record[key] for key in edger_record if key not in STATIC_COLUMNS and pd.notna(edger_record[key])}

    response = {
        "edger": edger_name,
        "details": details,
        "schedule": schedule
    }

    return jsonify(response)

@app.route('/api/managers/<string:manager_name>/edgers', methods=['GET'])
def get_edgers_by_manager(manager_name):
    """
    API endpoint to fetch all EDGers reporting to a specific manager.
    URL Parameter: /api/managers/Anjali%20Mehta/edgers
    """
    # 1. Load data
    df, error = load_data()
    if error:
        return jsonify(error), 500

    # 2. Filter the DataFrame for the specified manager
    manager_edgers = df[df['01_Manager'] == manager_name]

    # 3. Handle case where manager is not found
    if manager_name not in df['01_Manager'].unique():
        return jsonify({"error": "Not Found", "message": f"Manager with name '{manager_name}' not found."}), 404

    # 4. Get the list of EDGer names
    edger_names = manager_edgers['EDGers'].tolist()

    # 5. Build and return the successful JSON response
    response = {
        "manager": manager_name,
        "count": len(edger_names),
        "edgers": edger_names
    }
    return jsonify(response)

@app.route('/api/edgers/solo-salesforce', methods=['GET'])
def get_solo_salesforce_edgers():
    """
    API endpoint to fetch all EDGers who are solo in Salesforce ML Answers.
    This assumes the column 'SF_ML Answers' contains boolean values.
    """
    df, error = load_data()
    if error:
        return jsonify(error), 500
    
    try:
        # Filter where 'SF_ML Answers' is True. Pandas handles various boolean representations.
        solo_edgers = df[df['Email'] == "Solo"]
        edger_names = solo_edgers['EDGers'].tolist()
        
        response = {
            "filter": "Solo in Salesforce ML Answers",
            "count": len(edger_names),
            "edgers": edger_names
        }
        return jsonify(response)
    except KeyError:
        return jsonify({"error": "Not Found", "message": "Column 'SF_ML Answers' not found in the data source."}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/api/edgers/solo-ml-answers', methods=['GET'])
def get_solo_ml_answers_edgers():
    """
    API endpoint to fetch all EDGers who are solo in MATLAB Answers.
    This assumes the column 'MATLAB Answers' contains boolean values.
    """
    df, error = load_data()
    if error:
        return jsonify(error), 500
    
    try:
        # Filter where 'MATLAB Answers' is True.
        solo_edgers = df[df['MATLAB Answers'] == "Solo"]
        edger_names = solo_edgers['EDGers'].tolist()
        
        response = {
            "filter": "Solo in MATLAB Answers",
            "count": len(edger_names),
            "edgers": edger_names
        }
        return jsonify(response)
    except KeyError:
        return jsonify({"error": "Not Found", "message": "Column 'MATLAB Answers' not found in the data source."}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# --- Main execution block ---
if __name__ == '__main__':
    # To run this app:
    # 1. Make sure you have an Excel file named 'schedule.xlsx' in the same directory.
    # 2. Run this script: python app.py
    # 3. Open your browser or API client to access the endpoints, e.g.,
    #    http://1227.0.0.1:5000/api/edgers?date=2025-01-01&role=IN-Base
    app.run(debug=True)

