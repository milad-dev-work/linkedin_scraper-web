Django Web Service for LinkedIn Job Scraping
This project is a web-based, redesigned version of the previous Python script, implemented with a modular architecture as a Django service. This service provides a /scrapJobs API endpoint that accepts POST requests to initiate the data extraction process.

It now supports batch processing with array inputs and provides a status tracking endpoint to monitor background tasks.

Architecture and Workflow
The workflow is designed for asynchronous and robust execution:

Receive Request: The server receives a POST request to the /scrapJobs endpoint with country and job parameters in the JSON body. These can be single strings or arrays of strings.

Immediate Response: The server immediately returns a 202 Accepted response, including a unique task_id to track the process.

Background Execution: A new thread is created to run the time-consuming scraping task in the background, preventing the API from timing out.

Module 1 (First Apify Actor): The initial list of jobs is extracted based on each country and job keyword combination.

Processing Loop: A loop iterates over the results from Module 1.

Module 2 (Second Apify Actor): In each iteration, the contact information for the respective company is extracted.

Module 3 (Google Sheets): The combined job and contact data is saved as a new row in the Google Sheet.

Error Handling
If an error occurs while connecting to services or fetching the initial job list, the entire task is terminated and marked as failed.

If an error occurs while processing a single job within the loop (Module 2 or 3), that job is skipped, an error is logged, and the process continues to the next item.

Setup and Execution
1. Prerequisites
Python 3.8+

pip and venv (for creating a virtual environment)

2. Installation and Setup
A) Create a Virtual Environment and Install Dependencies:

Bash

# Navigate to the linkedin_scraper folder
cd linkedin_scraper

# Create a new virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the project dependencies
pip install -r requirements.txt
B) Configure Environment Variables:

Create a .env file in the project root (linkedin_scraper/.env) and fill in the following values:

APIFY_API_TOKEN: Your Apify account API token.

GOOGLE_SHEET_ID: Your Google Spreadsheet ID.

GOOGLE_SERVICE_ACCOUNT_PATH: The path to the credentials.json file. If it's in the root, the value should be "credentials.json".

C) Run the Django Server:

After activating the virtual environment, start the Django development server:

Bash

python manage.py runserver
The server will run by default at http://127.0.0.1:8000/.

3. Sending API Requests
Your web service is now ready to receive requests. You can use tools like Postman to interact with the API.

A) Start a Scraping Task
Send a POST request to initiate the process. The body can contain single strings or arrays for batch processing.

Endpoint: http://127.0.0.1:8000/scrapJobs

Method: POST

Request Body (JSON) - Array Example:

JSON

{
    "country": ["United States", "Canada"],
    "job": ["Django Developer", "Python Developer"]
}
Success Response:

JSON

{
    "message": "Your request has been successfully submitted...",
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
B) Check Task Status
Use the task_id from the previous response to monitor the progress of your request.

Endpoint: http://127.0.0.1:8000/scrapStatus/<task_id>

Method: GET

Example URL: http://127.0.0.1:8000/scrapStatus/a1b2c3d4-e5f6-7890-1234-567890abcdef

Example Response:

JSON

{
    "status": "running",
    "progress": "Processing 2/4: 'Python Developer' in 'United States'",
    "total_combinations": 4
}
You can monitor the detailed process logs in the console where the server is running.
