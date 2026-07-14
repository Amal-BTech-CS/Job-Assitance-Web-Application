import os
import smtplib
from email.message import EmailMessage

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")

# ==========================================
# STATUS -> EMAIL CONTENT
# Add more statuses here later (e.g. "shortlisted")
# if you want automatic emails for those stages too.
# ==========================================

EMAIL_TEMPLATES = {

    "interview": {
        "subject": "Interview Invitation",
        "body": """
Congratulations!

We are pleased to inform you that your application has been shortlisted
for the next stage of the interview process for the position of "{job_title}"
at {company_name}.

Our recruitment team will contact you shortly with further details
regarding the interview schedule.

Thank you for your interest and we look forward to speaking with you.
""",
    },

    "rejected": {
        "subject": "Application Status Update",
        "body": """
Thank you for applying for the position of "{job_title}" at {company_name}.

After reviewing your application, we have decided not to proceed with
your profile for this position at this time.

We appreciate your interest and wish you success in your future
opportunities.
""",
    },

    "hired": {
        "subject": "Job Offer",
        "body": """
Congratulations!

We are delighted to inform you that you have been selected for the
position of "{job_title}" at {company_name}.

Our team will be in touch shortly with the next steps and offer details.

Welcome aboard, and congratulations once again!
""",
    },

}


def send_status_email(application):
    """
    Sends an automatic email to the candidate when their application
    status changes to one of the stages defined in EMAIL_TEMPLATES.

    Silently does nothing (returns False) if:
      - the new status has no template configured
      - the candidate has no email on file
      - EMAIL / APP_PASSWORD aren't configured in .env

    Never raises - a failed email should never block the employer's
    status-update action.
    """

    template = EMAIL_TEMPLATES.get(application.status)

    if not template:
        return False

    receiver = application.applicant.email
    print("DEBUG: attempting to send email")
    print("DEBUG: status =", application.status)
    print("DEBUG: receiver =", repr(receiver))
    print("DEBUG: EMAIL configured =", bool(EMAIL))
    print("DEBUG: PASSWORD configured =", bool(PASSWORD))
    if not receiver:
        return False

    if not EMAIL or not PASSWORD:
        print("EMAIL / APP_PASSWORD not configured in .env - skipping email.")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = EMAIL
        msg["To"] = receiver
        msg["Subject"] = template["subject"]

        body = template["body"].format(
            job_title=application.job.title,
            company_name=application.job.company.company_name,
        )

        msg.set_content(body)

        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(EMAIL, PASSWORD)
            s.send_message(msg)
        print("DEBUG: email sent successfully to", receiver)
        return True

    except Exception as e:
        import traceback
        print("DEBUG: SMTP send failed:")
        traceback.print_exc()
        return False