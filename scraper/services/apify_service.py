import logging
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
        # شناسه‌های اکتورها در اینجا تعریف می‌شوند
        self.LINKEDIN_ACTOR_ID = "hKByXkMQaC5Qt9UMN"
        self.CONTACT_SCRAPER_ACTOR_ID = "2RxbxbuelHKumjdS6"

    def _run_actor(self, actor_id: str, run_input: dict) -> list:
        """
        یک متد عمومی برای اجرای هر اکتور و دریافت نتایج.
        """
        try:
            logger.info(f"در حال اجرای اکتور با شناسه: {actor_id}")
            actor_run = self.client.actor(actor_id).call(run_input=run_input)
            
            logger.info(f"در حال دریافت نتایج از دیتاست {actor_run['defaultDatasetId']}...")
            items = list(self.client.dataset(actor_run['defaultDatasetId']).iterate_items())
            logger.info(f"تعداد {len(items)} آیتم با موفقیت دریافت شد.")
            return items
            
        except Exception as e:
            logger.error(f"خطا در حین اجرای اکتور {actor_id}: {e}")
            # طبق توضیحات ویس، در صورت خطا، لیست خالی برمی‌گردانیم تا فرآیند اصلی متوجه خطا شود
            return []

    def run_linkedin_job_scraper(self, search_url: str, count: int = 100) -> list:
        """
        اکتور استخراج مشاغل لینکدین را اجرا می‌کند (ماژول اول).
        """
        run_input = {
            "urls": [search_url],
            "scrapeCompany": True,
            "count": count,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            },
            "maxConcurrency": 5
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
