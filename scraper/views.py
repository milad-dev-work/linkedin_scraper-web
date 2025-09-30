import logging
import threading
import os
import uuid
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.apify_service import ApifyService
from .services.google_sheets_service import GoogleSheetsService
from .services.processing_service import build_linkedin_url, process_contact_data

# Load environment variables from .env file
load_dotenv()

# Get the logger
logger = logging.getLogger(__name__)

# --- Task Status Tracking ---
tasks_status = {}
tasks_lock = threading.Lock()  # قفل برای مدیریت دسترسی همزمان به دیکشنری تسک‌ها

# هدرها برای هماهنگی با داکیومنت جدید و n8n
EXPECTED_HEADERS = [
    'employmentType', 'companyName', 'companyCountry', 'companyWebsite', 'postedAt',
    'phones', 'emails', 'title', 'linkedin', 'link', 'fullCompanyAddress',
    'twitter', 'instagram', 'facebook', 'youtube', 'tiktok', 'pinterest', 'discord', 'email sent'
]

def format_address(job_dict: dict) -> str:
    """
    آدرس را از فیلدهای مستقیم آبجکت شغل می‌خواند و به رشته تبدیل می‌کند.
    """
    if not isinstance(job_dict, dict):
        return ""

    parts = [
        job_dict.get('company_street'),
        job_dict.get('company_locality'),
        job_dict.get('company_region'),
        job_dict.get('company_postal_code'),
        job_dict.get('company_country')
    ]
    return ', '.join(filter(None, parts))


def run_scraping_task(country: str, job_keyword: str, task_id: str, current_job_index: int, total_jobs: int):
    """
    منطق اصلی اسکرپینگ برای یک ترکیب کشور و کلیدواژه شغل.
    """
    status_message = f"Processing {current_job_index}/{total_jobs}: '{job_keyword}' in '{country}'"
    with tasks_lock:
        tasks_status[task_id]['status'] = 'running'
        tasks_status[task_id]['progress'] = status_message
    logger.info(f"Task [{task_id}]: {status_message}")

    try:
        apify_api_token = os.environ["APIFY_API_TOKEN"]
        google_sheet_id = os.environ["GOOGLE_SHEET_ID"]
        google_service_account_path = os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"]
    except KeyError as e:
        error_message = f"Missing essential environment variable: {e}. Please check your .env file."
        logger.error(f"Task [{task_id}]: {error_message}")
        with tasks_lock:
            tasks_status[task_id]['status'] = 'failed'
            tasks_status[task_id]['error'] = error_message
            tasks_status[task_id]['finished_at'] = datetime.utcnow()
        return

    apify_service = ApifyService(apify_api_token)
    try:
        sheets_service = GoogleSheetsService(google_service_account_path, google_sheet_id)
        worksheet = sheets_service.get_worksheet("Sheet1")
        
        header_map = sheets_service.get_header_map(worksheet)
        if not header_map:
            raise Exception("Could not read headers from the Google Sheet.")

        # [اصلاح شد] بررسی وجود تمام هدرهای مورد انتظار در شیت
        missing_headers = set(EXPECTED_HEADERS) - set(header_map.keys())
        if missing_headers:
            raise Exception(f"The following required columns are missing from the Google Sheet: {', '.join(missing_headers)}")
            
        link_column_index = header_map.get('link')
        if not link_column_index:
            raise Exception("Column 'link' not found in the Google Sheet.")

        existing_links = sheets_service.get_column_values(worksheet, link_column_index)
        logger.info(f"Task [{task_id}]: Successfully read {len(existing_links)} existing job links from Google Sheets.")
    except Exception as e:
        error_message = f"Error connecting to or validating Google Sheets: {e}"
        logger.error(f"Task [{task_id}]: {error_message}")
        with tasks_lock:
            tasks_status[task_id]['status'] = 'failed'
            tasks_status[task_id]['error'] = error_message
            tasks_status[task_id]['finished_at'] = datetime.utcnow()
        return

    logger.info(f"Task [{task_id}]: Module 1: Running job scraper actor...")
    search_url = build_linkedin_url(keyword=job_keyword, location_name=country)
    logger.info(f"Task [{task_id}]: Built search URL: {search_url}")

    job_items = apify_service.run_linkedin_job_scraper(search_url, max_results=10, proxy_group="DATACENTER")

    if not job_items:
        logger.warning(f"Task [{task_id}]: Module 1: No jobs found for this query. Moving to the next item.")
        return
        
    logger.info(f"Task [{task_id}]: Module 1: Successfully scraped {len(job_items)} jobs.")

    for job in job_items:
        try:
            job_link = job.get('job_url')
            job_title = job.get('title')

            if not job_link:
                logger.warning(f"Task [{task_id}]: Job '{job_title}' has no link and will be skipped.")
                continue

            if job_link in existing_links:
                logger.info(f"Task [{task_id}]: Job '{job_title}' already exists in the sheet. Skipping.")
                continue

            logger.info(f"Task [{task_id}]: Starting processing for job: '{job_title}'")
            company_website = job.get('company_website')
            contact_info = {}

            if company_website:
                logger.info(f"Task [{task_id}]: Module 2: Scraping contact info from: {company_website}")
                contact_results = apify_service.run_contact_detail_scraper(company_website)
                
                if contact_results:
                    contact_info = process_contact_data(contact_results, job)
                    logger.info(f"Task [{task_id}]: Successfully processed contact info for '{job.get('company_name')}'.")
                else:
                    logger.warning(f"Task [{task_id}]: No contact info found for website {company_website}.")
            else:
                logger.info(f"Task [{task_id}]: Company website not found, skipping contact info scraping.")

            logger.info(f"Task [{task_id}]: Module 3: Preparing and appending new row to Google Sheets...")

            row_data = {
                'employmentType': job.get('employment_type', ''),
                'companyName': job.get('company_name', ''),
                'companyCountry': job.get('company_country', ''),
                'companyWebsite': job.get('company_website', ''),
                'postedAt': job.get('posted_datetime', ''),
                'phones': contact_info.get('phones', ''),
                'emails': contact_info.get('emails', ''),
                'title': job.get('title', ''),
                'linkedin': contact_info.get('linkedin', ''),
                'link': job.get('job_url', ''),
                'fullCompanyAddress': format_address(job),
                'twitter': contact_info.get('twitter', ''),
                'instagram': contact_info.get('instagram', ''),
                'facebook': contact_info.get('facebook', ''),
                'youtube': contact_info.get('youtube', ''),
                'tiktok': contact_info.get('tiktok', ''),
                'pinterest': contact_info.get('pinterest', ''),
                'discord': contact_info.get('discord', ''),
                'email sent': '',
            }
            new_row = [row_data.get(header, '') for header in EXPECTED_HEADERS]

            sheets_service.append_row(worksheet, new_row)
            logger.info(f"Task [{task_id}]: Job '{job_title}' successfully added to Google Sheets.")
            existing_links.add(job_link)

        except Exception as e:
            logger.error(f"Task [{task_id}]: Error processing job '{job.get('title', 'Unknown')}': {e}. Continuing to the next job.")
            continue

    logger.info(f"Task [{task_id}]: Finished processing all jobs for '{job_keyword}' in '{country}'.")


def run_task_for_all_combinations(task_id: str, job_combinations: list):
    """
    اجراکننده اصلی تسک که تمام ترکیبات کشور و شغل را پیمایش می‌کند.
    """
    total_jobs = len(job_combinations)
    logger.info(f"Task [{task_id}]: Starting main task runner for {total_jobs} combinations.")
    
    for i, combo in enumerate(job_combinations):
        run_scraping_task(
            country=combo['country'],
            job_keyword=combo['job'],
            task_id=task_id,
            current_job_index=i + 1,
            total_jobs=total_jobs
        )
    
    with tasks_lock:
        if tasks_status.get(task_id) and tasks_status[task_id]['status'] != 'failed':
            tasks_status[task_id]['status'] = 'completed'
            tasks_status[task_id]['progress'] = f"Completed all {total_jobs} tasks."
            tasks_status[task_id]['finished_at'] = datetime.utcnow()
    
    logger.info(f"Task [{task_id}]: All combinations have been processed. Task completed.")

def cleanup_old_tasks():
    """
    این تابع به صورت دوره‌ای اجرا شده و تسک‌های قدیمی را از حافظه پاک می‌کند تا از نشت حافظه جلوگیری شود.
    """
    while True:
        try:
            time.sleep(3600)  # هر یک ساعت یک بار اجرا می‌شود
            
            with tasks_lock:
                tasks_to_delete = []
                cleanup_threshold = datetime.utcnow() - timedelta(hours=1)
                
                for task_id, info in tasks_status.items():
                    finished_at = info.get('finished_at')
                    if finished_at and finished_at < cleanup_threshold:
                        tasks_to_delete.append(task_id)
                
                if tasks_to_delete:
                    logger.info(f"Cleaning up {len(tasks_to_delete)} old tasks.")
                    for task_id in tasks_to_delete:
                        del tasks_status[task_id]
        except Exception as e:
            logger.error(f"Error during task cleanup: {e}")

class ScrapeJobsView(APIView):
    """
    این View درخواست POST را برای شروع فرآیند اسکرپینگ دریافت می‌کند.
    """
    def post(self, request, *args, **kwargs):
        countries = request.data.get('country')
        jobs = request.data.get('job')

        if not countries or not jobs:
            return Response(
                {"error": "'country' and 'job' parameters are required and cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if isinstance(countries, str):
            countries = [countries]
        if isinstance(jobs, str):
            jobs = [jobs]

        job_combinations = [{'country': c, 'job': j} for c in countries for j in jobs if c and j]

        if not job_combinations:
            return Response(
                {"error": "No valid country/job combinations to process after filtering empty values."},
                status=status.HTTP_400_BAD_REQUEST
            )

        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks_status[task_id] = {
                'status': 'queued',
                'progress': 'Task is waiting to be processed.',
                'total_combinations': len(job_combinations),
                'started_at': datetime.utcnow(),
                'finished_at': None
            }
        logger.info(f"New request received. Task ID [{task_id}] created for {len(job_combinations)} combinations.")

        task_thread = threading.Thread(target=run_task_for_all_combinations, args=(task_id, job_combinations))
        task_thread.start()

        return Response(
            {
                "message": "Your request has been successfully submitted. The scraping process has started in the background.",
                "task_id": task_id
            },
            status=status.HTTP_202_ACCEPTED
        )


class ScrapeStatusView(APIView):
    """
    این View به کلاینت‌ها اجازه می‌دهد تا وضعیت یک تسک را با استفاده از شناسه آن بررسی کنند.
    """
    def get(self, request, task_id, *args, **kwargs):
        with tasks_lock:
            task_info = tasks_status.get(task_id)

        if not task_info:
            return Response(
                {"error": "Task ID not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(task_info.copy(), status=status.HTTP_200_OK)

# اجرای نخ پاکسازی در پس‌زمینه به صورت دائم
cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
cleanup_thread.start()
