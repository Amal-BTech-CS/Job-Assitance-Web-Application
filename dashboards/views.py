from pyexpat.errors import messages

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from accounts.ai.ats import extract_pdf_text,ats_score
from accounts.ai.mock_interview import evaluate_answer, generate_question
from accounts.ai.quiz import generate_quiz, parse_quiz
from accounts.models import Profile, Job, Application, Resume
from accounts.ai.recommender.recommender import get_recommended_jobs

@login_required
@never_cache
def jobseeker_dashboard(request):
    profile = Profile.objects.get(user=request.user)
    jobs = Job.objects.filter(status="Open").order_by("-created_at")[:3]
    applied_job_ids = Application.objects.filter(applicant=profile).values_list("job_id", flat=True)

    resume = getattr(profile, "resume", None)
    has_skills = bool(resume and resume.skills.exists())

    recommended_jobs = []
    if has_skills:
        try:
            recommended_jobs = get_recommended_jobs(profile)
        except Exception as e:
            print("AI recommendation error:", e)
            recommended_jobs = []

    return render(request, 'accounts/jobseeker_dashboard.html', {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'recommended_jobs': recommended_jobs,
    })

@login_required
@never_cache
def company_dashboard(request):
    return render(
        request,
        'accounts/company_dashboard.html'
    )
@login_required
@never_cache
def ats_calculator(request):

    profile = get_object_or_404(Profile, user=request.user)

    jobs = Job.objects.filter(status="Open").order_by("-created_at")

    result = None
    selected_job = None

    if request.method == "POST":

        latest_resume = Resume.objects.filter(
            profile=profile
        ).order_by("-id").first()

        if not latest_resume or not latest_resume.resume_file:
            messages.error(request, "Please upload a resume in your profile first.")
            return redirect("jobseeker_profile")

        job_id = request.POST.get("job_id")
        custom_jd = request.POST.get("custom_jd", "").strip()

        if job_id:
            selected_job = get_object_or_404(Job, id=job_id)
            job_description = selected_job.description
        elif custom_jd:
            job_description = custom_jd
        else:
            messages.error(request, "Please select a job or paste a job description.")
            return redirect("ats_calculator")

        # Resume lives on the DB/S3 now - open the FieldFile explicitly,
        # read it, then close it. Same pattern as the cover letter feature.
        latest_resume.resume_file.open("rb")
        resume_text = extract_pdf_text(latest_resume.resume_file)
        latest_resume.resume_file.close()

        result = ats_score(resume_text, job_description)

    return render(
        request,
        "accounts/ats_calculator.html",
        {
            "jobs": jobs,
            "result": result,
            "selected_job": selected_job,
        }
    )


@login_required
@never_cache
def quiz_home(request):

    if request.method == "POST":

        topic = request.POST.get("topic")
        difficulty = request.POST.get("difficulty")
        count = int(request.POST.get("count"))

        quiz_text = generate_quiz(
            topic,
            difficulty,
            count
        )

        questions = parse_quiz(quiz_text)

        request.session["quiz"] = questions
        request.session["current"] = 0
        request.session["score"] = 0

        return redirect("quiz_question")

    return render(
        request,
        "accounts/quiz.html"
    )
@login_required
@never_cache
def quiz_question(request):

    quiz = request.session.get("quiz")

    if not quiz:
        return redirect("quiz_home")

    current = request.session.get("current", 0)
    score = request.session.get("score", 0)

    if current >= len(quiz):
        return redirect("quiz_result")

    q = quiz[current]

    answered = False
    selected = None

    if request.method == "POST":

        # NEXT QUESTION
        if "next" in request.POST:

            request.session["current"] = current + 1

            if current + 1 >= len(quiz):
                return redirect("quiz_result")

            return redirect("quiz_question")

        # ANSWER CLICKED
        selected = request.POST.get("answer")
        answered = True

        if selected == q["answer"]:

            score += 1
            request.session["score"] = score
    is_last = (current == len(quiz) - 1)
    return render(
        request,
        "accounts/quiz_question.html",
        {
            "q": q,
            "answered": answered,
            "selected": selected,
            "current": current + 1,
            "total": len(quiz),
            "is_last": is_last,
        }
    )
@login_required
@never_cache
def quiz_result(request):

    quiz = request.session.get("quiz", [])

    score = request.session.get("score", 0)

    total = len(quiz)

    request.session.pop("quiz", None)
    request.session.pop("current", None)
    request.session.pop("score", None)

    return render(
        request,
        "accounts/quiz_result.html",
        {
            "score": score,
            "total": total,
        }
    )
@login_required
@never_cache
def mock_interview(request):

    if request.method == "POST":

        role = request.POST.get("role")

        request.session["role"] = role
        request.session["questions"] = []
        request.session["current"] = 0
        request.session["score"] = 0

        # Clear any leftover feedback from a previous interview attempt,
        # otherwise mock_question thinks question 0 is already answered.
        for i in range(5):
            request.session.pop(f"feedback_{i}", None)

        return redirect("mock_question")

    return render(request, "accounts/mock_interview.html")
@login_required
@never_cache
def mock_question(request):

    role = request.session.get("role")

    if not role:
        return redirect("mock_interview")

    questions = request.session.get("questions", [])
    current = request.session.get("current", 0)

    TOTAL = 5

    if current >= TOTAL:
        return redirect("mock_result")

    # Generate a new question only once
    if len(questions) <= current:
        question = generate_question(role, questions)
        questions.append(question)
        request.session["questions"] = questions
    else:
        question = questions[current]

    feedback = request.session.get(f"feedback_{current}")
    answered = feedback is not None

    if request.method == "POST":

        # User clicked "Next Question" (only shown after feedback appears)
        if "next" in request.POST:

            request.session["current"] = current + 1

            if current + 1 >= TOTAL:
                return redirect("mock_result")

            return redirect("mock_question")

        # User just submitted an answer to THIS question
        answer = request.POST.get("answer")

        feedback = evaluate_answer(role, question, answer)

        request.session[f"feedback_{current}"] = feedback

        answered = True

    is_last = (current == TOTAL - 1)

    return render(
        request,
        "accounts/mock_question.html",
        {
            "question": question,
            "feedback": feedback,
            "answered": answered,
            "current": current + 1,
            "total": TOTAL,
            "progress": int(((current + 1) / TOTAL) * 100),
            "is_last": is_last,
        },
    )
@login_required
@never_cache
def mock_result(request):

    total = 5

    questions = request.session.get("questions", [])

    feedbacks = []

    for i in range(total):
        fb = request.session.get(f"feedback_{i}")
        if fb:
            question_text = questions[i] if i < len(questions) else ""
            feedbacks.append({
                "question": question_text,
                "feedback": fb,
            })

    return render(
        request,
        "accounts/mock_result.html",
        {
            "feedbacks": feedbacks,
            "total": total,
        },
    )