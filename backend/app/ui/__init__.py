from app.ui.applications_page import applications_page
from app.ui.job_detail_page import job_detail_page
from app.ui.jobs_page import jobs_page
from app.ui.match_detail_page import match_detail_page
from app.ui.match_page import match_page
from app.ui.resume_page import resume_page


def register_pages():
    resume_page()
    jobs_page()
    job_detail_page()
    match_page()
    match_detail_page()
    applications_page()
