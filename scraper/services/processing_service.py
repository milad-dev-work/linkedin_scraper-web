import re
from typing import List, Dict, Any, Set
from urllib.parse import urlencode

#=====================================================#
#  بخش مربوط به ساخت URL لینکدین
#=====================================================#

def build_linkedin_url(keyword: str, location_name: str) -> str:
    """
    یک URL معتبر برای جستجوی مشاغل در لینکدین با پارامترهای اصلی می‌سازد.
    این تابع ساده‌سازی شده تا با اکتور جدید که URL کامل را می‌پذیرد، سازگار باشد.
    """
    base_url = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": keyword,
        "location": location_name,
    }
    # سایر فیلترها مانند زمان انتشار یا نوع کار، باید توسط کاربر در فرانت‌اند
    # یا مستقیماً در URL اعمال شوند، مطابق با مستندات اکتور جدید.
    query_string = urlencode(params)
    return f"{base_url}?{query_string}"


#=====================================================#
#   بخش مربوط به پردازش داده
#=====================================================#

def _clean_and_get_unique_items(items: List[str]) -> List[str]:
    """یک لیست از رشته‌ها را فیلتر کرده و موارد منحصر به فرد را برمی‌گرداند."""
    if not items:
        return []
    return list(set(filter(None, items)))

def _clean_phones(phones: List[str]) -> List[str]:
    """لیستی از شماره تلفن‌ها را گرفته، کاراکترهای غیرعددی را حذف و موارد تکراری را پاک می‌کند."""
    if not phones:
        return []
    
    phone_set: Set[str] = set()
    for phone in phones:
        if phone and isinstance(phone, str):
            cleaned_phone = re.sub(r'\D', '', phone)
            if cleaned_phone:
                phone_set.add(cleaned_phone)
    return list(phone_set)

def _clean_emails(emails: List[str]) -> List[str]:
    """لیستی از ایمیل‌ها را گرفته، فضاهای خالی را حذف و موارد تکراری را پاک می‌کند."""
    if not emails:
        return []
        
    email_set: Set[str] = set()
    for email in emails:
        if email and isinstance(email, str):
            email_set.add(email.strip().lower())
    return list(email_set)


def process_contact_data(scraped_items: List[Dict[str, Any]], original_job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    داده‌های خام استخراج شده از اسکرپر اطلاعات تماس را پردازش و تجمیع می‌کند.
    """
    if not scraped_items:
        return {}

    all_emails: List[str] = []
    all_phones: List[str] = []
    all_linkedins: List[str] = []
    all_twitters: List[str] = []
    all_instagrams: List[str] = []
    all_facebooks: List[str] = []
    all_youtubes: List[str] = []
    all_tiktoks: List[str] = []
    all_pinterests: List[str] = []
    all_discords: List[str] = []
    
    for item in scraped_items:
        all_emails.extend(item.get('emails', []))
        all_phones.extend(item.get('phones', []))
        all_phones.extend(item.get('phonesUncertain', []))
        all_linkedins.extend(item.get('linkedIns', []))
        all_twitters.extend(item.get('twitters', []))
        all_instagrams.extend(item.get('instagrams', []))
        all_facebooks.extend(item.get('facebooks', []))
        all_youtubes.extend(item.get('youtubes', []))
        all_tiktoks.extend(item.get('tiktoks', []))
        all_pinterests.extend(item.get('pinterests', []))
        all_discords.extend(item.get('discords', []))
        
    unique_phones = _clean_phones(all_phones)
    unique_emails = _clean_emails(all_emails)
    
    def get_first_unique_link(links: list) -> str:
        unique_links = _clean_and_get_unique_items(links)
        return unique_links[0] if unique_links else ''

    clean_data = {
        "domain": scraped_items[0].get('domain', ''),
        "phones": ', '.join(unique_phones),
        "emails": ', '.join(unique_emails),
        "linkedin": get_first_unique_link(all_linkedins),
        "twitter": get_first_unique_link(all_twitters),
        "instagram": get_first_unique_link(all_instagrams),
        "facebook": get_first_unique_link(all_facebooks),
        "youtube": get_first_unique_link(all_youtubes),
        "tiktok": get_first_unique_link(all_tiktoks),
        "pinterest": get_first_unique_link(all_pinterests),
        "discord": get_first_unique_link(all_discords),
    }
    return clean_data
