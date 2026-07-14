from langchain_core.documents import Document

from accounts.models import (
    Resume,
    Job,
    Skill,
    Education,
    Experience,
    Project,
)


def load_resume_documents(user):

    documents = []

    resume = Resume.objects.filter(profile__user=user).first()

    if not resume:
        return documents

    text = ""

    profile = resume.profile

    text += f"Name: {profile.full_name}\n"
    text += f"Email: {profile.email}\n"
    text += f"Phone: {profile.phone}\n\n"

    # Skills
    skills = Skill.objects.filter(resume=resume)

    if skills.exists():

        text += "Skills:\n"

        for skill in skills:
            text += f"- {skill.skill_name}\n"

        text += "\n"

    # Education
    education = Education.objects.filter(resume=resume).first()

    if education:

        text += "Education:\n"

        text += f"""
Degree: {education.degree}
College: {education.college}
Qualification: {education.qualification_level}
CGPA: {education.cgpa}
Start: {education.start_year}
End: {education.end_year}

"""

    # Experience
    experiences = Experience.objects.filter(resume=resume)

    if experiences.exists():

        text += "Experience:\n"

        for exp in experiences:

            text += f"""
Job Title: {exp.job_title}
Company: {exp.company}
Start: {exp.start_date}
End: {exp.end_date}

"""

    # Projects
    projects = Project.objects.filter(resume=resume)

    if projects.exists():

        text += "Projects:\n"

        for project in projects:

            text += f"""
Title: {project.title}
Description: {project.description}
Technologies: {project.technologies}

"""

    documents.append(

        Document(

            page_content=text,

            metadata={
                "source": "resume"
            }

        )

    )

    return documents


def load_job_documents():

    documents = []

    jobs = Job.objects.all()

    for job in jobs:

        company = ""

        if job.company:

            company = job.company.company_name

        text = f"""
Job Title: {job.title}
Company: {company}
Location: {job.location}
Salary: {job.salary}
Experience: {job.experience}
Description:
{job.description}
"""

        documents.append(

            Document(

                page_content=text,

                metadata={
                    "job_id": job.id,
                    "source": "job"
                }

            )

        )

    return documents