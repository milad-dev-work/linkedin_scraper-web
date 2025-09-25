from django.urls import path
from .views import ScrapeJobsView

urlpatterns = [
    # آدرس اندپوینت اصلی طبق توضیحات شما
    path('scrapJobs', ScrapeJobsView.as_view(), name='scrap-jobs'),
]
