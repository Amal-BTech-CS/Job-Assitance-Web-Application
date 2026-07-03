from django.shortcuts import render, redirect
from .forms import JobSeekerRegisterForm, CompanyRegisterForm
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from .ai.resume_parser import extract_resume_text
from .models import Profile, Education, Experience, CompanyProfile,Job
from django.views.decorators.cache import never_cache
from django.contrib.auth import login
from django.contrib.auth import authenticate, login
from .ai.cover import generate_cover_letter
from .ai.quiz import generate_quiz, parse_quiz
from .ai.mock_interview import generate_question, evaluate_answer
from .ai.ats import extract_pdf_text,ats_score

@login_required
@never_cache
def jobseeker_dashboard(request):
    jobs = Job.objects.all().order_by('-id') # Fetch all jobs, newest first
    
    return render(request, 'accounts/jobseeker_dashboard.html', {'jobs': jobs})

@login_required
@never_cache
def company_dashboard(request):
    return render(
        request,
        'accounts/company_dashboard.html'
    )



def jobseeker_register(request):

    if request.method == "POST":

        form = JobSeekerRegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.user_type = "jobseeker"

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()


            Profile.objects.create(

                user=user

            )


            return redirect(
                "jobseeker_login"
            )


    else:

        form = JobSeekerRegisterForm()


    return render(

        request,

        "accounts/jobseeker_register.html",

        {
            "form": form
        }

    )
def company_register(request):

    if request.method == "POST":

        form = CompanyRegisterForm(request.POST)


        if form.is_valid():


            user = form.save(commit=False)


            user.user_type = "company"


            user.set_password(
                form.cleaned_data["password"]
            )


            user.save()

            
            CompanyProfile.objects.create(
                    user=user
            )


            return redirect(
                "company_login"
            )



        else:

            print(form.errors)



    else:

        form = CompanyRegisterForm()



    return render(

        request,

        "accounts/company_register.html",

        {
            "form":form
        }

    )

@never_cache
def jobseeker_login(request):

    error = None


    if request.method == "POST":


        username = request.POST.get("username")

        password = request.POST.get("password")



        user = authenticate(

            request,

            username=username,

            password=password

        )



        if user is None:


            from django.contrib.auth import get_user_model

            User = get_user_model()


            try:

                existing_user = User.objects.get(
                    username=username
                )


                error = "Wrong password. Please try again."


            except User.DoesNotExist:


                error = "Username not found. Please register first."



        elif user.user_type != "jobseeker":


            error = "This account is not a Job Seeker account."



        else:


            login(
                request,
                user
            )



            profile, created = Profile.objects.get_or_create(
                user=user
            )



            if profile.full_name:


                return redirect(
                    "jobseeker_dashboard"
                )


            else:


                return redirect(
                    "jobseeker_profile"
                )



    return render(

        request,

        "accounts/jobseeker_login.html",

        {
            "error": error
        }

    )
@never_cache
def company_login(request):

    error = None


    if request.method == "POST":


        username = request.POST.get("username")

        password = request.POST.get("password")



        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user is None:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:

                existing_user = User.objects.get(
                    username=username
                )


                error = "Wrong password. Please try again."



            except User.DoesNotExist:


                error = "Username not found. Please register first."



        elif user.user_type != "company":


            error = "This account is not an Employer account."



        else:


            login(
                request,
                user
            )



            profile, created = CompanyProfile.objects.get_or_create(
                user=user
            )

            if profile.company_name:

                    
                return redirect(
                    "company_dashboard"
                )


            else:


                return redirect(
                    
                    "company_profile"
                )



    return render(

        request,

        "accounts/company_login.html",

        {
            "error": error
        }

    )
from .models import Profile
from django.shortcuts import render, redirect


def home(request):

    if request.user.is_authenticated:


        if request.user.user_type == "jobseeker":


            profile, created = Profile.objects.get_or_create(
                user=request.user
            )


            if (
                profile.full_name
                and profile.skills
            ):

                return redirect(
                    "profile_view"
                )


            else:

                return redirect(
                    "jobseeker_profile"
                )



        elif request.user.user_type == "company":

            return redirect(
                "company_dashboard"
            )


    return render(
        request,
        "accounts/home.html"
    )

from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect('home')

from django.shortcuts import render, redirect
from .models import Profile
from .models import Education, Experience
from .ai.resume_parser import (
    extract_resume_text,
    analyze_resume
)
@never_cache
@login_required
def jobseeker_profile(request):
    if request.user.is_staff or request.user.is_superuser:

        return redirect("admin:index")
    
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )


    if request.method == "POST":


        # ==========================
        # SAVE PROFILE
        # ==========================

        if "save_profile" in request.POST:


            profile.full_name = request.POST.get(
                "full_name",
                ""
            )

            profile.email = request.POST.get(
                "email",
                ""
            )


            profile.phone = request.POST.get(
                "phone",
                ""
            )


            profile.linkedin = request.POST.get(
                "linkedin",
                ""
            )


            profile.github = request.POST.get(
                "github",
                ""
            )


            profile.skills = request.POST.get(
                "skills",
                ""
            )


            profile.save()


            return redirect(
                "profile_view"
            )



        # ==========================
        # ADD MANUAL EXPERIENCE
        # ==========================


        elif "add_experience" in request.POST:



            Experience.objects.create(

                profile=profile,


                job_title=request.POST.get(
                    "job_title",
                    ""
                ),


                company=request.POST.get(
                    "company",
                    ""
                ),


                start_date=request.POST.get(
                    "start_date",
                    ""
                ),


                end_date=request.POST.get(
                    "end_date",
                    ""
                )

            )


            return redirect(
                "jobseeker_profile"
            )

        elif "delete_experience" in request.POST:

            exp_id = request.POST.get("experience_id")

            Experience.objects.filter(
                id=exp_id,
                profile=profile
            ).delete()

            return redirect("jobseeker_profile")



        # ==========================
        # RESUME UPLOAD
        # ==========================


        elif "upload_resume" in request.POST:


            resume = request.FILES.get(
                "resume"
            )


            if resume:


                profile.resume = resume

                profile.save()



                text = extract_resume_text(

                    profile.resume.path

                )


                data = analyze_resume(text)



                profile.extracted_data = data




                # ==========================
                # PERSONAL DATA
                # ==========================


                profile.full_name = data.get(
                    "name",
                    ""
                )


                profile.email = data.get(
                    "email",
                    ""
                )


                profile.phone = data.get(
                    "phone",
                    ""
                )


                profile.linkedin = data.get(
                    "linkedin",
                    ""
                )


                profile.github = data.get(
                    "github",
                    ""
                )



                # ==========================
                # SKILLS
                # ==========================


                skills = data.get(
                    "skills",
                    []
                )


                if isinstance(
                    skills,
                    list
                ):

                    profile.skills = ", ".join(
                        skills
                    )


                elif isinstance(
                    skills,
                    dict
                ):

                    all_skills=[]


                    for value in skills.values():

                        all_skills.extend(
                            value
                        )


                    profile.skills = ", ".join(
                        all_skills
                    )



                profile.save()






                # ==========================
                # HIGHEST EDUCATION
                # ==========================


                Education.objects.filter(
                    profile=profile
                ).delete()



                education = data.get(
                    "education",
                    {}
                )



                if education:


                    Education.objects.create(

                        profile=profile,


                        qualification_level=education.get(
                            "qualification_level",
                            ""
                        ),


                        degree=education.get(
                            "degree",
                            ""
                        ),


                        college=education.get(
                            "college",
                            ""
                        ),


                        cgpa=education.get(
                            "cgpa",
                            ""
                        ),


                        start_year=education.get(
                            "start_year",
                            ""
                        ),


                        end_year=education.get(
                            "end_year",
                            ""
                        )

                    )





                # ==========================
                # ALL EXPERIENCE
                # ==========================


                Experience.objects.filter(
                    profile=profile
                ).delete()



                experiences = data.get(
                    "experience",
                    []
                )


                for exp in experiences:


                    Experience.objects.create(

                        profile=profile,


                        job_title=exp.get(
                            "job_title",
                            ""
                        ),


                        company=exp.get(
                            "company",
                            ""
                        ),


                        start_date=exp.get(
                            "start_date",
                            ""
                        ),


                        end_date=exp.get(
                            "end_date",
                            ""
                        )

                    )



                return redirect(
                    "jobseeker_profile"
                )





    education = Education.objects.filter(

        profile=profile

    ).first()



    experience = Experience.objects.filter(

        profile=profile

    )



    return render(

        request,


        "accounts/jobseeker_profile.html",


        {

        "profile":profile,

        "education":education,

        "experience":experience

        }

    )

@login_required
@never_cache
def profile_view(request):

    profile = Profile.objects.get(
        user=request.user
    )


    education = Education.objects.filter(
        profile=profile
    ).first()


    experience = Experience.objects.filter(
        profile=profile
    )


    skills = []

    if profile.skills:

        skills = [
            skill.strip()
            for skill in profile.skills.split(",")
        ]


    return render(

        request,

        "accounts/profile_view.html",

        {

            "profile": profile,

            "education": education,

            "experience": experience,

            "skills": skills

        }

    )
from .models import CompanyProfile


@login_required
@never_cache
def company_profile(request):

    profile, created = CompanyProfile.objects.get_or_create(
        user=request.user
    )


    if request.method == "POST":


        profile.company_name = request.POST.get(
            "company_name"
        )


        profile.company_email = request.POST.get(
            "company_email"
        )


        profile.company_phone = request.POST.get(
            "company_phone"
        )


        profile.website = request.POST.get(
            "website"
        )


        profile.description = request.POST.get(
            "description"
        )


        profile.save()



        return redirect(
            "company_profile_view"
        )



    return render(

        request,

        "accounts/company_profile.html",

        {
            "profile": profile
        }

    )
@login_required
@never_cache
def company_profile_view(request):

    profile = CompanyProfile.objects.get(
        user=request.user
    )


    return render(

        request,

        "accounts/company_profile_view.html",

        {
            "profile": profile
        }

    )
@login_required
def create_job(request):
    company, created = CompanyProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        Job.objects.create(
            company=company,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            location=request.POST.get("location"),
            salary=request.POST.get("salary"),
            # Capture the new experience field
            experience=request.POST.get("experience"),
            # Capture the employment type if you added it to the form
            employment_type=request.POST.get("employment_type"),
            # Capture skills
            skills=request.POST.get("skills")
        )
        return redirect("manage_jobs")

    return render(request, "accounts/create_job.html")
@login_required
def manage_jobs(request):


    company, created = CompanyProfile.objects.get_or_create(
    user=request.user
    )


    jobs = Job.objects.filter(
        company=company
    )



    return render(

        request,

        "accounts/manage_jobs.html",

        {
            "jobs": jobs
        }

    )
@login_required
def edit_job(request, id):
    company = CompanyProfile.objects.get(user=request.user)
    job = Job.objects.get(id=id, company=company)

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.description = request.POST.get("description")
        job.location = request.POST.get("location")
        job.salary = request.POST.get("salary")
        # Add this line to update the experience field
        job.experience = request.POST.get("experience")
        job.save()
        return redirect("manage_jobs")

    return render(
        request, 
        "accounts/edit_job.html", 
        {"job": job}
    )
@login_required
def delete_job(request,id):


    company = CompanyProfile.objects.get(
        user=request.user
    )


    job = Job.objects.get(

        id=id,

        company=company

    )


    job.delete()


    return redirect(
        "manage_jobs"
    )
@login_required
@never_cache
def cover_letter(request):

    profile = Profile.objects.get(user=request.user)

    cover_letter_text = ""

    if request.method == "POST":

        job_title = request.POST.get("job_title")
        company_name = request.POST.get("company_name")

        if profile.resume:

            cover_letter_text = generate_cover_letter(
                profile.resume.path,
                job_title,
                company_name
            )

    return render(
        request,
        "accounts/cover_letter.html",
        {
            "cover_letter": cover_letter_text
        }
    )
@login_required
@never_cache
def quiz_home(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        difficulty = request.POST.get("difficulty")
        count = int(request.POST.get("count"))

        request.session["quiz"] = []
        request.session["index"] = 0
        request.session["score"] = 0

        quiz_text = generate_quiz(topic, difficulty, count)
        questions = parse_quiz(quiz_text)

        request.session["quiz"] = questions

        return redirect("quiz_question")

    return render(request, "accounts/quiz.html")


@login_required
@never_cache
def quiz_question(request):
    quiz = request.session.get("quiz", [])
    index = request.session.get("index", 0)

    if index >= len(quiz):
        return redirect("quiz_result")

    q = quiz[index]

    selected = None
    answered = False

    if request.method == "POST":

        # User clicked an option
        if "answer" in request.POST:

            selected = request.POST.get("answer").upper()
            answered = True

            if selected == q["answer"]:
                request.session["score"] = request.session.get("score", 0) + 1

        # User clicked Next
        elif "next" in request.POST:

            request.session["index"] = index + 1
            return redirect("quiz_question")

    return render(request, "accounts/quiz_question.html", {
        "q": q,
        "selected": selected,
        "answered": answered,
    })


@login_required
@never_cache
def quiz_result(request):
    return render(request, "accounts/quiz_result.html", {
        "score": request.session.get("score", 0),
        "total": len(request.session.get("quiz", []))
    })
@login_required
@never_cache
def interview_home(request):

    if request.method == "POST":

        role = request.POST.get("role")

        request.session["role"] = role
        request.session["asked_questions"] = []
        request.session["question_no"] = 1
        request.session["evaluations"] = []

        return redirect("interview_question")

    return render(request, "accounts/interview.html")


@login_required
@never_cache
def interview_question(request):

    role = request.session.get("role")
    asked_questions = request.session.get("asked_questions", [])
    question_no = request.session.get("question_no", 1)
    evaluations = request.session.get("evaluations", [])

    # Finished 5 questions
    if question_no > 5:
        return redirect("interview_result")

    # Generate question only once
    if "current_question" not in request.session:
        question = generate_question(role, asked_questions)
        request.session["current_question"] = question
    else:
        question = request.session["current_question"]

    evaluation = None

    if request.method == "POST":

        # Submit Answer
        if "submit_answer" in request.POST:

            answer = request.POST.get("answer", "")

            evaluation = evaluate_answer(
                role,
                question,
                answer
            )

            evaluations.append({
                "question": question,
                "answer": answer,
                "evaluation": evaluation
            })

            request.session["evaluations"] = evaluations

        # Next Question
        elif "next_question" in request.POST:

            asked_questions.append(question)

            request.session["asked_questions"] = asked_questions
            request.session["question_no"] = question_no + 1

            if "current_question" in request.session:
                del request.session["current_question"]

            return redirect("interview_question")

    return render(
        request,
        "accounts/interview_question.html",
        {
            "question": question,
            "question_no": question_no,
            "evaluation": evaluation
        }
    )


@login_required
@never_cache
def interview_result(request):

    evaluations = request.session.get("evaluations", [])

    return render(
        request,
        "accounts/interview_result.html",
        {
            "evaluations": evaluations
        }
    )
@login_required
@never_cache
def ats_checker(request):

    profile = Profile.objects.get(user=request.user)

    result = None

    if request.method == "POST":

        job_description = request.POST.get("job_description")

        if profile.resume:

            resume_text = extract_pdf_text(profile.resume.path)

            result = ats_score(
                resume_text,
                job_description
            )

    return render(
        request,
        "accounts/ats.html",
        {
            "result": result
        }
    )