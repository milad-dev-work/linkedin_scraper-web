from django.urls import path
from .views import ScrapeJobsView, ScrapeStatusView

urlpatterns = [
    # The main endpoint to start the scraping process
    path('scrapJobs', ScrapeJobsView.as_view(), name='scrap-jobs'),
    
    # [NEW] The endpoint to check the status of a running task
    path('scrapStatus/<str:task_id>', ScrapeStatusView.as_view(), name='scrap-status'),
]
