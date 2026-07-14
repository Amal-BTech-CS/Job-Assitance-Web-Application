import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_resume(user_data: dict) -> str:
    prompt = f"""
    Create an ATS-friendly professional resume using the following details:
    Name: {user_data.get('name')}
    Email: {user_data.get('email')}
    Phone: {user_data.get('phone')}
    Summary: {user_data.get('summary')}
    Skills: {user_data.get('skills')}
    Experience: {user_data.get('experience')}
    Education: {user_data.get('education')}

    Format it cleanly with clear section headers.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert resume writer specializing in ATS-optimized resumes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200,
        temperature=0.7,
    )

    return response.choices[0].message.content