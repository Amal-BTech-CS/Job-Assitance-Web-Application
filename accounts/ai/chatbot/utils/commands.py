def process_command(command):

    command = command.lower()

    if command == "/help":

        return """
/help
/match
/missing-skills
/resume-summary
/exit
"""

    elif command == "/match":

        return """
How well does my resume match the job?
"""

    elif command == "/missing-skills":

        return """
What skills are missing from my resume
for this job?
"""

    elif command == "/resume-summary":

        return """
Summarize my resume.
"""

    return None