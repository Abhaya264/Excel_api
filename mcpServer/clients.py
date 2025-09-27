# This script acts as a client application that consumes the APIs from the MCP server.
# It demonstrates how another program would interact with your API endpoints.

import requests
import json

# Define the base URL for the API server
BASE_URL = "http://127.0.0.1:5000/api"

def print_response(title, response):
    """Helper function to pretty-print the JSON response."""
    print("-" * 60)
    print(f"RESPONSE FOR: {title}")
    print(f"URL: {response.url}")
    print("-" * 60)
    try:
        # Pretty print the JSON
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Could not decode JSON response.")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
    print("\n")

def run_all_api_tests():
    """Runs a series of requests to test all available API endpoints."""
    print("--- Starting MCP Client API Demonstration ---")

    try:
        # 1. Get EDGers by Role and Date
        url = f"{BASE_URL}/edgers?date=2025-09-15&role=IN-Base"
        response = requests.get(url)
        print_response("Get EDGers by Role and Date (IN-Base on 2025-09-15)", response)

        # 2. Get Schedule for a Specific EDGer
        edger_name = "Saanvi Gupta"
        url = f"{BASE_URL}/edgers/{edger_name}/schedule"
        response = requests.get(url)
        print_response(f"Get Schedule for '{edger_name}'", response)
        
        # 3. Get EDGers by Manager
        manager_name = "Anjali Mehta"
        url = f"{BASE_URL}/managers/{manager_name}/edgers"
        response = requests.get(url)
        print_response(f"Get EDGers for Manager: '{manager_name}'", response)

        # 4. Get EDGers Solo in Salesforce
        url = f"{BASE_URL}/edgers/solo-salesforce"
        response = requests.get(url)
        print_response("Get EDGers Solo in Salesforce", response)
        
        # 5. Get EDGers Solo in MATLAB Answers
        url = f"{BASE_URL}/edgers/solo-ml-answers"
        response = requests.get(url)
        print_response("Get EDGers Solo in MATLAB Answers", response)

    except requests.exceptions.ConnectionError:
        print("\n" + "="*60)
        print("CONNECTION ERROR: Could not connect to the MCP Server.")
        print("Please make sure the server is running by executing 'python mcp_server.py' in another terminal.")
        print("="*60 + "\n")

if __name__ == '__main__':
    run_all_api_tests()
