import gspread
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    یک Wrapper برای سادگی کار با gspread جهت تعامل با Google Sheets (ماژول سوم).
    """

    def __init__(self, service_account_path: str, spreadsheet_id: str):
        try:
            self.gc = gspread.service_account(filename=service_account_path)
            self.spreadsheet = self.gc.open_by_key(spreadsheet_id)
            logger.info("اتصال به Google Sheets با موفقیت برقرار شد.")
        except Exception as e:
            logger.error(f"عدم موفقیت در احراز هویت یا باز کردن Google Sheet: {e}")
            raise

    def get_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"ورک‌شیت با نام '{sheet_name}' یافت نشد.")
            raise

    def get_column_values(self, worksheet: gspread.Worksheet, column_index: int) -> set:
        try:
            values = worksheet.col_values(column_index)
            # اولین مقدار هدر است، آن را حذف می‌کنیم
            return set(values[1:]) if values else set()
        except Exception as e:
            logger.error(f"خطا در دریافت مقادیر ستون: {e}")
            return set()

    def get_header_map(self, worksheet: gspread.Worksheet) -> dict:
        """
        ردیف اول (هدرها) را می‌خواند و یک دیکشنری از نام هدر به شماره ستون برمی‌گرداند.
        این کار باعث می‌شود کد نسبت به جابجایی ستون‌ها مقاوم باشد.
        """
        try:
            headers = worksheet.row_values(1)
            return {header: i + 1 for i, header in enumerate(headers)}
        except Exception as e:
            logger.error(f"خطا در خواندن هدرهای شیت: {e}")
            return {}

    def append_row(self, worksheet: gspread.Worksheet, row_data: list):
        try:
            worksheet.append_row(row_data)
        except Exception as e:
            logger.error(f"خطا در افزودن ردیف: {e}")
            raise
