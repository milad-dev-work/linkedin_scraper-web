import logging
import os
from apify_client import ApifyClient

logger = logging.getLogger(__name__)

class ApifyService:
    """
    این کلاس مسئولیت تمام تعاملات با Apify را بر عهده دارد.
    """

    def __init__(self, api_token: str):
        if not api_token:
            raise ValueError("Apify API token is required.")
        self.client = ApifyClient(api_token)

        # [اصلاح شد] شناسه‌ها از متغیرهای محیطی خوانده می‌شوند
        self.LINKEDIN_ACTOR_ID = os.environ.get("LINKEDIN_ACTOR_ID")
        self.CONTACT_SCRAPER_ACTOR_ID = os.environ.get("CONTACT_SCRAPER_ACTOR_ID")

        if not self.LINKEDIN_ACTOR_ID or not self.CONTACT_SCRAPER_ACTOR_ID:
            raise ValueError("Actor IDs (LINKEDIN_ACTOR_ID, CONTACT_SCRAPER_ACTOR_ID) must be set in the .env file.")


    def _run_actor(self, actor_id: str, run_input: dict) -> list:
        """
        یک متد عمومی برای اجرای هر اکتور و دریافت نتایج.
        """
        try:
            logger.info(f"در حال اجرای اکتور با شناسه: {actor_id} و ورودی: {run_input}")
            actor_run = self.client.actor(actor_id).call(run_input=run_input)
            
            logger.info(f"در حال دریافت نتایج از دیتاست {actor_run['defaultDatasetId']}...")
            items = list(self.client.dataset(actor_run['defaultDatasetId']).iterate_items())
            logger.info(f"تعداد {len(items)} آیتم با موفقیت دریافت شد.")
            return items
            
        except Exception as e:
            logger.error(f"خطا در حین اجرای اکتور {actor_id}: {e}")
            return []

    def run_linkedin_job_scraper(self, search_url: str, max_results: int = 100, proxy_group: str = "RESIDENTIAL") -> list:
        """
        اکتور استخراج مشاغل لینکدین را اجرا می‌کند.
        [اصلاح شد] پارامتر proxy_group اضافه شد تا با فراخوانی هماهنگ باشد.
        """
        run_input = {
            "search_url": search_url,
            "include_company_details": True,
            "max_results": max_results,
            "proxy_group": proxy_group.upper()
        }
        return self._run_actor(self.LINKEDIN_ACTOR_ID, run_input)

    def run_contact_detail_scraper(self, website_url: str) -> list:
        """
        اکتور استخراج اطلاعات تماس از وب‌سایت را اجرا می‌کند (ماژول دوم).
        """
        run_input = {
            "startUrls": [{"url": website_url, "method": "GET"}],
            "maxDepth": 2,
            "maxRequests": 5,
            "sameDomain": True,
            "considerChildFrames": True,
        }
        return self._run_actor(self.CONTACT_SCRAPER_ACTOR_ID, run_input)
