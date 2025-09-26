import logging
import threading
import os
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.apify_service import ApifyService
from .services.google_sheets_service import GoogleSheetsService
from .services.processing_service import build_linkedin_url, process_contact_data

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# دریافت لاگر
logger = logging.getLogger(__name__)

# [IMPROVEMENT] ترتیب ستون‌های مورد انتظار در گوگل شیت
# این کار باعث می‌شود افزودن ردیف جدید به ترتیب ستون‌ها وابسته نباشد
EXPECTED_HEADERS = [
    'employmentType', 'companyName', 'companyCountry', 'companyWebsite', 'postedAt',
    'phones', 'emails', 'title', 'linkedin', 'link', 'fullCompanyAddress',
    'twitter', 'instagram', 'facebook', 'youtube'
]

def format_address(address_dict: dict) -> str:
    """
    [IMPROVEMENT] یک دیکشنری آدرس را به یک رشته خوانا تبدیل می‌کند.
    """
    if not isinstance(address_dict, dict):
        return str(address_dict) # بازگشت به حالت قبل برای انواع داده غیرمنتظره

    parts = [
        address_dict.get('addressStreet'),
        address_dict.get('addressLocality'),
        address_dict.get('addressRegion'),
        address_dict.get('postalCode'),
        address_dict.get('addressCountry')
    ]
    return ', '.join(filter(None, parts))


def run_scraping_task(country: str, job_keyword: str):
    """
    تابع اصلی که تمام منطق اسکرپینگ را در یک ترد جداگانه اجرا می‌کند.
    """
    logger.info(f"شروع فرآیند اسکرپینگ برای شغل '{job_keyword}' در '{country}'")
    
    # ۱. دریافت توکن‌ها و شناسه‌ها از متغیرهای محیطی
    try:
        apify_api_token = os.environ["APIFY_API_TOKEN"]
        google_sheet_id = os.environ["GOOGLE_SHEET_ID"]
        google_service_account_path = os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"]
    except KeyError as e:
        logger.error(f"متغیر محیطی ضروری یافت نشد: {e}. لطفاً فایل .env را بررسی کنید.")
        return

    # ۲. ساخت کلاینت‌های سرویس
    apify_service = ApifyService(apify_api_token)
    try:
        sheets_service = GoogleSheetsService(google_service_account_path, google_sheet_id)
        worksheet = sheets_service.get_worksheet("Sheet1")
        
        # [IMPROVEMENT] خواندن هدرها برای یافتن ایندکس ستون لینک به صورت داینامیک
        header_map = sheets_service.get_header_map(worksheet)
        if not header_map:
            logger.error("هدرهای Google Sheet خوانده نشد. فرآیند متوقف شد.")
            return
            
        link_column_index = header_map.get('link')
        if not link_column_index:
            logger.error("ستون 'link' در Google Sheet یافت نشد. فرآیند متوقف شد.")
            return

        existing_links = sheets_service.get_column_values(worksheet, link_column_index)
        logger.info(f"تعداد {len(existing_links)} لینک شغل از Google Sheets خوانده شد.")
    except Exception as e:
        logger.error(f"خطا در اتصال به Google Sheets: {e}")
        return

    # == ماژول اول: اجرای اکتور اول Apify برای استخراج مشاغل ==
    logger.info("ماژول ۱: در حال اجرای اکتور استخراج مشاغل...")
    search_url = build_linkedin_url(keyword=job_keyword, location_name=country)
    logger.info(f"URL جستجوی ساخته شده: {search_url}")

    job_items = apify_service.run_linkedin_job_scraper(search_url)

    if not job_items:
        logger.warning("ماژول ۱: هیچ شغلی برای پردازش یافت نشد. فرآیند متوقف شد.")
        return
        
    logger.info(f"ماژول ۱: تعداد {len(job_items)} شغل با موفقیت استخراج شد.")

    # == حلقه پردازش مشاغل ==
    for job in job_items:
        try:
            job_link = job.get('link')
            job_title = job.get('title')

            if not job_link:
                logger.warning(f"شغل '{job_title}' لینک ندارد و نادیده گرفته می‌شود.")
                continue

            if job_link in existing_links:
                logger.info(f"شغل '{job_title}' قبلاً در شیت موجود است. رد می‌شود.")
                continue

            logger.info(f"شروع پردازش برای شغل: '{job_title}'")
            company_website = job.get('companyWebsite')
            contact_info = {}

            # == ماژول دوم: اجرای اکتور دوم برای استخراج اطلاعات تماس ==
            if company_website:
                logger.info(f"ماژول ۲: در حال استخراج اطلاعات تماس از وب‌سایت: {company_website}")
                contact_results = apify_service.run_contact_detail_scraper(company_website)
                
                if contact_results:
                    contact_info = process_contact_data(contact_results, job)
                    logger.info(f"اطلاعات تماس برای '{job.get('companyName')}' با موفقیت پردازش شد.")
                else:
                    logger.warning(f"اطلاعات تماسی برای وب‌سایت {company_website} یافت نشد.")
            else:
                logger.info("وب‌سایت شرکت یافت نشد، از استخراج اطلاعات تماس صرف‌نظر می‌شود.")

            # == ماژول سوم: افزودن داده‌ها به Google Sheets ==
            logger.info("ماژول ۳: در حال آماده‌سازی و افزودن ردیف جدید به Google Sheets...")

            # [IMPROVEMENT] ساخت دیکشنری از داده‌ها برای افزودن به شیت
            row_data = {
                'employmentType': job.get('employmentType', ''),
                'companyName': job.get('companyName', ''),
                'companyCountry': job.get('companyAddress', {}).get('addressCountry', ''),
                'companyWebsite': job.get('companyWebsite', ''),
                'postedAt': job.get('postedAt', ''),
                'phones': contact_info.get('phones', ''),
                'emails': contact_info.get('emails', ''),
                'title': job.get('title', ''),
                'linkedin': contact_info.get('linkedin', ''),
                'link': job.get('link', ''),
                'fullCompanyAddress': format_address(job.get('companyAddress', {})),
                'twitter': contact_info.get('twitter', ''),
                'instagram': contact_info.get('instagram', ''),
                'facebook': contact_info.get('facebook', ''),
                'youtube': contact_info.get('youtube', ''),
            }

            # ساخت لیست نهایی بر اساس ترتیب هدرها
            new_row = [row_data.get(header, '') for header in EXPECTED_HEADERS]

            sheets_service.append_row(worksheet, new_row)
            logger.info(f"شغل '{job_title}' با موفقیت به Google Sheets اضافه شد.")
            # اضافه کردن لینک جدید به لیست لینک‌های موجود برای جلوگیری از پردازش مجدد در همین اجرا
            existing_links.add(job_link)

        except Exception as e:
            # مدیریت خطای داخل حلقه طبق توضیحات ویس
            logger.error(f"خطا در پردازش شغل '{job.get('title', 'Unknown')}': {e}. به سراغ آیتم بعدی می‌رویم.")
            continue # ادامه به شغل بعدی در حلقه

    logger.info("تمام مشاغل پردازش شدند. فرآیند با موفقیت به پایان رسید.")


class ScrapeJobsView(APIView):
    """
    این View درخواست POST را برای شروع فرآیند استخراج اطلاعات دریافت می‌کند.
    """
    def post(self, request, *args, **kwargs):
        country = request.data.get('country')
        job = request.data.get('job')

        # [FIXED] اعتبارسنجی ورودی‌ها بهبود یافت تا از خطای لیست خالی جلوگیری شود
        if not country or not job:
            return Response(
                {"error": "پارامترهای 'country' و 'job' الزامی هستند و نمی‌توانند خالی باشند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # اگر ورودی لیست بود، اولین آیتم را انتخاب کن
        country_to_process = country[0] if isinstance(country, list) and country else country
        job_to_process = job[0] if isinstance(job, list) and job else job

        # بررسی مجدد برای اطمینان از خالی نبودن مقادیر پس از پردازش
        if not country_to_process or not job_to_process:
            return Response(
                {"error": "مقادیر 'country' و 'job' نمی‌توانند خالی باشند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"درخواست جدید دریافت شد: Country='{country_to_process}', Job='{job_to_process}'")

        # ایجاد و اجرای ترد جدید برای جلوگیری از بلاک شدن پاسخ
        task_thread = threading.Thread(target=run_scraping_task, args=(country_to_process, job_to_process))
        task_thread.start()

        # بازگرداندن پاسخ فوری به کاربر
        return Response(
            {"message": "درخواست شما با موفقیت ثبت شد. فرآیند استخراج اطلاعات در پس‌زمینه شروع شده است."},
            status=status.HTTP_202_ACCEPTED
        )
