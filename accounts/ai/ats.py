import pdfplumber
import re
import nltk

from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

# Download stopwords only once
try:
    STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    STOP_WORDS = set(stopwords.words("english"))

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================
# EXTRACT PDF TEXT
# ==========================================

def extract_pdf_text(path):

    text = []

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:

                page_text = re.sub(
                    r'([a-z])([A-Z])',
                    r'\1 \2',
                    page_text
                )

                page_text = page_text.replace(
                    "•",
                    "\n• "
                )

                page_text = re.sub(
                    r'-\n',
                    '',
                    page_text
                )

                page_text = re.sub(
                    r'\s+',
                    ' ',
                    page_text
                )

                text.append(page_text)

    return "\n".join(text)


# ==========================================
# CLEAN TEXT
# ==========================================

def preprocess(text):

    text = str(text)

    text = re.sub(
        r'\S+@\S+',
        ' ',
        text
    )

    text = re.sub(
        r'http\S+',
        ' ',
        text
    )

    text = re.sub(
        r'\+?\d[\d\s\-]{8,}',
        ' ',
        text
    )

    text = text.lower()

    text = re.sub(
        r'[^a-z0-9\s]',
        ' ',
        text
    )

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    return text.strip()


# ==========================================
# IMPORTANT RESUME SECTIONS
# ==========================================

def extract_relevant_sections(text):

    text = text.replace("\r", "\n")

    lines = [x.strip() for x in text.split("\n") if x.strip()]

    target_headers = [

        "skills",
        "technical skills",
        "projects",
        "experience",
        "work experience",
        "internship"

    ]

    stop_headers = [

        "education",
        "certification",
        "certifications",
        "summary",
        "objective",
        "languages",
        "achievements",
        "contact"

    ]

    collecting = False

    extracted = []

    for line in lines:

        lower = line.lower()

        if any(h in lower for h in target_headers):
            collecting = True

        elif any(h in lower for h in stop_headers):
            collecting = False

        if collecting:
            extracted.append(line)

    result = "\n".join(extracted)

    if len(result.strip()) < 200:
        return text

    return result


# ==========================================
# SEMANTIC SCORE
# ==========================================

def semantic_score(resume, job):

    emb = model.encode(

        [

            preprocess(resume),

            preprocess(job)

        ]

    )

    similarity = cosine_similarity(
        [emb[0]],
        [emb[1]]
    )[0][0]

    return similarity * 100


# ==========================================
# KEYWORDS
# ==========================================

def extract_keywords(text, max_terms=80):

    text = preprocess(text)

    if not text:
        return []

    vectorizer = TfidfVectorizer(

        stop_words=list(STOP_WORDS),

        ngram_range=(1, 2),

        max_features=max_terms

    )

    vectorizer.fit_transform([text])

    terms = vectorizer.get_feature_names_out().tolist()

    remove_words = {

        "candidate",
        "comfortable",
        "years",
        "work",
        "location",
        "solutions",
        "related",
        "field",
        "document",
        "vision data",
        "education"

    }

    clean = []

    for term in terms:

        if len(term.split()) <= 2 and term not in remove_words:
            clean.append(term)

    return clean


# ==========================================
# KEYWORD SCORE
# ==========================================

def keyword_score(resume, job, threshold=0.45):

    resume_terms = extract_keywords(resume, 100)

    jd_terms = extract_keywords(job, 60)

    if len(resume_terms) == 0 or len(jd_terms) == 0:

        return 0, [], []

    resume_emb = model.encode(
        resume_terms,
        convert_to_tensor=True
    )

    jd_emb = model.encode(
        jd_terms,
        convert_to_tensor=True
    )

    similarity = util.cos_sim(
        jd_emb,
        resume_emb
    )

    matched = []

    missing = []

    for i, term in enumerate(jd_terms):

        best = similarity[i].max().item()

        if best >= threshold:
            matched.append(term)
        else:
            missing.append(term)

    score = (len(matched) / len(jd_terms)) * 100

    return score, matched, missing


# ==========================================
# EXPERIENCE SCORE
# ==========================================

def experience_score(resume):

    resume = preprocess(resume)

    indicators = [

        "intern",

        "experience",

        "project",

        "developed",

        "implemented",

        "built",

        "trained",

        "certification"

    ]

    score = 0

    for word in indicators:

        if word in resume:
            score += 12

    return min(score, 100)


# ==========================================
# FINAL ATS
# ==========================================

def ats_score(resume, job):

    important_resume = extract_relevant_sections(resume)

    semantic = semantic_score(
        important_resume,
        job
    )

    keyword, matched, missing = keyword_score(
        important_resume,
        job
    )

    experience = experience_score(
        important_resume
    )

    final = (

        semantic * 0.50 +

        keyword * 0.35 +

        experience * 0.15

    )

    return {

        "semantic": round(semantic, 2),

        "keyword": round(keyword, 2),

        "experience": round(experience, 2),

        "final": round(final, 2),

        "matched": matched,

        "missing": missing,

        "important_resume": important_resume

    }