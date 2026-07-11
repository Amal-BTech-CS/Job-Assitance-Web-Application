from django.urls import path
from . import views

urlpatterns = [

    path(
        "jobseeker/dashboard/",
        views.jobseeker_dashboard,
        name="jobseeker_dashboard"
    ),

    path(
        "company/dashboard/",
        views.company_dashboard,
        name="company_dashboard"
    ),

    path(
        "ats-calculator/",
        views.ats_calculator,
        name="ats_calculator"
    ),
    
    path(
        "quiz/", 
        views.quiz_home, 
        name="quiz_home"
        ),
    path(
        "quiz/question/",
        views.quiz_question, 
        name="quiz_question"
        ),
    path
    (
        "quiz/result/", 
        views.quiz_result, 
        name="quiz_result"
        ),
    path(
        "mock-interview/", 
        views.mock_interview, 
        name="mock_interview"
        ),
    path(
        "mock-interview/question/", 
        views.mock_question, 
        name="mock_question"
        ),
    path(
        "mock-interview/result/", 
        views.mock_result, 
        name="mock_result"
        ),
]

