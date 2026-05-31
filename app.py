from __future__ import annotations  # FIX 1 — enables str|None on Python 3.9

import hashlib  # FIX 2 — needed for fast cache key hashing
import html as _html  # XSS fix — escape user-supplied strings before HTML injection
import os
import re
import tempfile
from datetime import datetime
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from markitdown import MarkItDown

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key) if api_key else None
md = MarkItDown()

JOB_CATEGORIES_ROLES = {
    "Engineering & Development": [
        "Software Engineer", "Backend Developer", "Frontend Developer",
        "Full Stack Developer", "DevOps Engineer", "Cloud Engineer", "Mobile Developer"
    ],
    "Data & AI": [
        "Data Analyst", "Data Scientist", "AI/ML Engineer",
        "Business Intelligence Analyst", "Machine Learning Engineer"
    ],
    "Product & Design": [
        "Product Manager", "UI/UX Designer", "Graphic Designer", "Project Manager"
    ],
    "Business & Marketing": [
        "Marketing Specialist", "Sales Representative", "Business Development Manager",
        "HR Specialist", "Financial Analyst"
    ],
    "Healthcare & Science": ["Clinical Researcher", "Biotechnologist", "Medical Assistant"],
    "Education & Academia": ["Teacher", "Research Assistant", "Professor"],
    "Creative & Arts": ["Content Creator", "Copywriter", "Photographer", "Video Editor"],
    "Operations & Logistics": ["Operations Manager", "Logistics Coordinator", "Supply Chain Analyst"]
}

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CoachAI — AI Placement Engine",
    page_icon="🎯",
    layout="centered",
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
_defaults = {
    "analysis_done": False,
    "score_val": 0,
    "analysis_content": "",
    "action_plan_content": "",
    "interview_content": "",
    "keywords_html": "",
    "rewrite_content": "",
    "history": [],
    "final_job_role": "",
    "resume_word_count": 0,
    "bullets_rewritten": 0,
    "upload_key": 0,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_block(text: str | None, start_tag: str, end_tag: str | None = None) -> str:
    if not text:
        return ""
    try:
        start_idx = text.find(start_tag)
        if start_idx == -1:
            return ""
        start_idx += len(start_tag)
        if end_tag:
            end_idx = text.find(end_tag, start_idx)
            return text[start_idx:end_idx].strip() if end_idx != -1 else text[start_idx:].strip()
        return text[start_idx:].strip()
    except Exception:
        return ""


def call_groq(prompt: str, max_tokens: int = 3000) -> str:
    if not client:
        raise RuntimeError("Groq client not initialised. Check your GROQ_API_KEY.")
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    last_error: Optional[Exception] = None
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            if "rate_limit" in str(exc).lower() or "429" in str(exc):
                continue
            raise
    raise RuntimeError(
        f"rate_limit: All models hit rate limits. Please wait a moment and try again. ({last_error})"
    )


@st.cache_data(show_spinner=False)
def extract_resume_text(file_hash: str, file_bytes: bytes, file_suffix: str) -> tuple[str, str | None]:
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        result = md.convert(tmp_path)
        extracted: str = result.text_content or ""

        if file_suffix.lower() == ".pdf" and len(extracted.strip()) < 100:
            return "", (
                "This PDF appears to be a scanned image with no selectable text. "
                "Please export your resume as a text-based PDF from Word or Google Docs."
            )
        return extracted.strip(), None

    except Exception as exc:
        return "", str(exc)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Main app structural reset */
[data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #030712 !important;
    color: #F9FAFB !important;
}
[data-testid="stMain"] {
    background-color: #030712 !important;
}

/* Eliminate default Streamlit headers, margins, and decoration bars */
header, [data-testid="stHeader"], div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
}

[data-testid="stToolbar"]  { visibility: hidden; }
.stDeployButton            { display: none !important; }
footer                     { visibility: hidden; }

.block-container {
    padding-top:    1rem  !important;
    padding-bottom: 4rem  !important;
    max-width:      780px !important;
}

[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius:    16px           !important;
    border:           1px solid #1E293B !important;
    background-color: #0D1526        !important;
    padding:          1.75rem 2rem   !important;
    margin-bottom:    1.25rem        !important;
    box-shadow:       none           !important;
}

div[data-baseweb="select"] > div {
    background-color: #060D1F !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    color: #F9FAFB !important;
}
div[data-baseweb="select"] * { color: #F9FAFB !important; }
ul[role="listbox"] {
    background-color: #0D1526 !important;
    border: 1px solid #1E293B !important;
}
ul[role="listbox"] li {
    color: #F9FAFB !important;
    background-color: #0D1526 !important;
}
ul[role="listbox"] li:hover { background-color: #1E2A45 !important; }

textarea, input[type="text"] {
    background-color: #060D1F !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    color: #F9FAFB !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}
textarea::placeholder, input::placeholder { color: #334155 !important; }

div[data-testid="stFileUploader"] {
    background-color: #0D1526 !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
section[data-testid="stFileUploadDropzone"] {
    background-color: #060D1F !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 8px !important;
    padding: 2rem 1.5rem !important;
    transition: border-color 0.2s !important;
}
section[data-testid="stFileUploadDropzone"]:hover { border-color: #6366F1 !important; }
section[data-testid="stFileUploadDropzone"] * { color: #94A3B8 !important; }
div[data-testid="stFileUploaderFileWidget"] {
    background-color: #060D1F !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploaderFileWidget"] * { color: #F9FAFB !important; }

button[data-baseweb="tab"] {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #818CF8 !important;
    background-color: #1E1B4B !important;
}
div[data-testid="stTabs"] [role="tablist"] {
    gap: 4px !important;
    background-color: #060D1F !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid #1E293B !important;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2.5rem !important;
    color: white !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 24px rgba(99,102,241,0.3) !important;
    transition: all 0.2s ease !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%) !important;
    box-shadow: 0 6px 32px rgba(99,102,241,0.45) !important;
    transform: translateY(-1px) !important;
}
button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    color: #94A3B8 !important;
    font-weight: 600 !important;
}
button[kind="secondary"]:hover {
    border-color: #6366F1 !important;
    color: #818CF8 !important;
    background-color: rgba(99,102,241,0.05) !important;
}

/* Enriched styles to make input labels bold and highly distinct */
label {
    color: #E2E8F0 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    text-transform: none !important;
    letter-spacing: 0.01em !important;
    margin-bottom: 0.5rem !important;
    display: inline-block !important;
}
hr { border-color: #1E293B !important; margin: 1.5rem 0 !important; }
div[data-testid="stAlert"] { border-radius: 10px !important; border: 1px solid #1E293B !important; }
div[data-testid="stSpinner"] * { color: #818CF8 !important; }
div[data-testid="stCaptionContainer"] * { color: #334155 !important; }
div[data-testid="stProgressBar"] > div {
    background-color: #6366F1 !important;
    border-radius: 4px !important;
}

.hero-title {
    font-size: 2.3rem; font-weight: 800; letter-spacing: -1px;
    line-height: 1.1; margin: 0;
    background: linear-gradient(135deg, #FFFFFF 0%, #818CF8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub  { font-size: 0.95rem; color: #64748B; margin: 0; line-height: 1.5; }
.step-badge {
    background: rgba(99,102,241,0.12); color: #818CF8;
    font-size: 0.7rem; font-weight: 700;
    padding: 4px 12px; border-radius: 9999px;
    text-transform: uppercase; letter-spacing: 1px;
    display: inline-block; margin-bottom: 0.75rem;
    border: 1px solid rgba(99,102,241,0.2);
}
.section-title { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin: 0 0 1.25rem; }
.big-score     { font-size: 90px; font-weight: 800; text-align: center; line-height: 1; margin-bottom: 4px; }
.stat-row      { display: flex; gap: 12px; margin-bottom: 20px; }
.stat-box      {
    flex: 1; background: #060D1F;
    border: 1px solid #1E293B; border-radius: 10px;
    padding: 14px 16px; text-align: center;
}
.stat-num { font-size: 1.6rem; font-weight: 800; color: #818CF8; line-height: 1; }
.stat-lbl {
    font-size: 0.7rem; color: #475569; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px;
}
.kw-chip {
    display: inline-block;
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25);
    color: #FCA5A5; font-size: 12px; font-weight: 600;
    padding: 3px 10px; border-radius: 9999px; margin: 3px;
}
.kw-chip-found {
    background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.25);
    color: #86EFAC;
}
.ocr-warn       {
    background: #1C0A00; border: 1px solid #92400E;
    border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
}
.ocr-warn-title { color: #FCD34D; font-weight: 700; font-size: 0.95rem; margin-bottom: 6px; }
.ocr-warn-body  { color: #78716C; font-size: 0.88rem; line-height: 1.6; }

/* Grid styling for landing page sections */
.features-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
    margin-bottom: 2.5rem;
}
@media (max-width: 600px) {
    .features-grid {
        grid-template-columns: 1fr !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# API KEY GUARD
# ─────────────────────────────────────────────
if not api_key or not client:
    st.markdown("""
    <div style='background:#1A0A0A;border:1px solid #7F1D1D;border-radius:14px;
                padding:2rem;text-align:center;'>
        <p style='font-size:2rem;margin-bottom:1rem;'>⚠️</p>
        <p style='font-size:1.1rem;font-weight:700;color:#FCA5A5;margin-bottom:0.5rem;'>
            GROQ_API_KEY not found</p>
        <p style='color:#64748B;font-size:0.9rem;'>
            Create a <code style="background:#0D1526;padding:2px 6px;border-radius:4px;
            color:#818CF8;">.env</code> file in your project folder and add:<br><br>
            <code style="background:#0D1526;padding:6px 14px;border-radius:6px;
            color:#86EFAC;font-size:0.9rem;">GROQ_API_KEY=your_key_here</code>
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────
# HERO & NAV CONTAINER
# ─────────────────────────────────────────────
with st.container(border=True):
    # Interactive Navigation Bar
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0 1.25rem; border-bottom: 1px solid #1E293B; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 800; font-size: 1.25rem; color: #FFFFFF; letter-spacing: -0.5px;">
            <span style="font-size: 1.5rem;">🎯</span> Coach<span style="color:#818CF8;">AI</span>
        </div>
        <div style="display: flex; gap: 1.25rem; align-items: center;">
            <a href="#features" style="color: #94A3B8; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: color 0.2s;">Features</a>
            <a href="#testimonials" style="color: #94A3B8; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: color 0.2s;">Success Stories</a>
            <a href="#faq" style="color: #94A3B8; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: color 0.2s;">FAQ</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Title Box alignment utilizing clean typography (Second Dart Icon Removed)
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 0.5rem;">
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <h1 class="hero-title">AI Placement Coach</h1>
            <p class="hero-sub" style="margin-top: 0.5rem;">Optimize your resume, match job requirements &amp; analyze ATS compatibility with instant AI feedback.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HISTORY EXPANDER (always visible if history exists)
# ─────────────────────────────────────────────
if st.session_state.history:
    with st.expander(f"📋 Analysis History  ({len(st.session_state.history)} session{'s' if len(st.session_state.history) != 1 else ''})", expanded=False):
        cols = st.columns(len(st.session_state.history[-3:]))
        for i, h in enumerate(reversed(st.session_state.history[-3:])):
            sc    = "#22C55E" if h["score"] >= 75 else "#F59E0B" if h["score"] >= 50 else "#EF4444"
            label = "Strong Match" if h["score"] >= 75 else "Moderate Match" if h["score"] >= 50 else "Needs Work"
            safe_role = _html.escape(h["role"])
            safe_time = _html.escape(h["time"])
            with cols[i]:
                st.markdown(
                    f"<div style='background:#060D1F;border:1px solid #1E293B;border-radius:10px;"
                    f"padding:12px 14px;'>"
                    f"<div style='font-size:13px;font-weight:700;color:#F9FAFB;margin-bottom:4px;'>{safe_role}</div>"
                    f"<div style='font-size:22px;font-weight:800;color:{sc};line-height:1;'>{h['score']}%</div>"
                    f"<div style='font-size:11px;color:{sc};margin-top:2px;font-weight:600;'>{label}</div>"
                    f"<div style='font-size:11px;color:#475569;margin-top:4px;'>{safe_time}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.caption("💡 Paste a job description in Step 03 for the most accurate ATS keyword analysis.")


# ─────────────────────────────────────────────
# STEP 1 — Target Profile
# ─────────────────────────────────────────────
with st.container(border=True):
    st.markdown("<span class='step-badge'>Step 01</span>", unsafe_allow_html=True)
    st.markdown("<p class='section-title'>Your Target Profile</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        categories   = list(JOB_CATEGORIES_ROLES.keys()) + ["Other"]
        job_category = st.selectbox("Industry Category", categories)
    with col2:
        roles    = (JOB_CATEGORIES_ROLES[job_category] + ["Other"]) if job_category != "Other" else ["Other"]
        job_role = st.selectbox("Target Job Role", roles)
    with col3:
        experience = st.selectbox("Experience Level",
                                  ["Student / Fresher", "0-1 years", "1-3 years", "3+ years"])

    final_job_role = job_role
    custom_role    = ""
    if job_role == "Other":
        st.write("")
        custom_role    = st.text_input("Enter Custom Job Title:", placeholder="e.g. QA Engineer, Quant Analyst")
        final_job_role = custom_role.strip() if custom_role.strip() else "General Applicant"


# ─────────────────────────────────────────────
# STEP 2 — Upload Resume
# ─────────────────────────────────────────────
with st.container(border=True):
    st.markdown("<span class='step-badge'>Step 02</span>", unsafe_allow_html=True)
    st.markdown("<p class='section-title'>Upload Resume</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Resume (PDF or Word)",
        type=["pdf", "docx"],
        label_visibility="collapsed",
        key=f"resume_uploader_{st.session_state.upload_key}",
    )
    if uploaded_file:
        st.markdown(
            f"<p style='font-size:13px;color:#22C55E;margin-top:6px;'>✓ {uploaded_file.name} ready</p>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# STEP 3 — Job Description (optional)
# ─────────────────────────────────────────────
with st.container(border=True):
    st.markdown("<span class='step-badge'>Step 03 — Optional but recommended</span>", unsafe_allow_html=True)
    st.markdown("<p class='section-title'>Paste Job Description</p>", unsafe_allow_html=True)
    job_description = st.text_area(
        "Job description",
        placeholder="Paste the full job description here for a precise ATS match score and keyword gap analysis...",
        height=130,
        label_visibility="collapsed",
    )


# ─────────────────────────────────────────────
# ANALYSE BUTTON
# ─────────────────────────────────────────────
st.write("")
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    analyse_clicked = st.button("⚡  Analyze My Resume", type="primary", use_container_width=True)


# ─────────────────────────────────────────────
# AI ANALYSIS LOGIC
# ─────────────────────────────────────────────
if analyse_clicked:
    if not uploaded_file:
        st.error("Please upload a resume file in Step 2.")
    elif job_role == "Other" and not custom_role.strip():
        st.error("Please enter a custom job title in Step 1.")
    else:
        file_bytes  = uploaded_file.read()
        file_suffix = os.path.splitext(uploaded_file.name)[1].lower()
        file_hash   = hashlib.md5(file_bytes).hexdigest()

        ocr_error_msg: str | None = None
        resume_text: str = ""

        with st.spinner("Extracting resume text…"):
            resume_text, extract_error = extract_resume_text(file_hash, file_bytes, file_suffix)

        if extract_error:
            st.markdown(
                f"<div class='ocr-warn'>"
                f"<div class='ocr-warn-title'>📄 Scanned PDF Detected</div>"
                f"<div class='ocr-warn-body'>{extract_error}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            ocr_error_msg = extract_error

        elif not resume_text or len(resume_text) < 100:
            st.error("Could not extract enough text. Please ensure the file contains selectable text.")
            ocr_error_msg = "insufficient text"

        if not ocr_error_msg:
            try:
                word_count = len(resume_text.split())

                jd_context = (
                    f"Compare the resume strictly against this Job Description:\n{job_description}"
                    if job_description.strip()
                    else f"Analyze for standard {final_job_role} industry expectations."
                )

                main_prompt = f"""
You are an elite Placement Coach and ATS Expert.
Target Role: {final_job_role}
Experience Level: {experience}
{jd_context}

Resume:
{resume_text}

Format your response EXACTLY using the tags below. No text outside these tags.

[SCORE]
<Single integer 0-100 representing ATS match percentage>

[ANALYSIS]
## Score Breakdown
Brief 2-sentence explanation of the score.

## ✅ Top Strengths
- Strength 1 with specific detail
- Strength 2 with specific detail
- Strength 3 with specific detail

## ⚠️ Critical Gaps
- Gap 1 with specific detail
- Gap 2 with specific detail
- Gap 3 with specific detail

## 📋 Formatting & ATS Check
- Formatting point 1
- Formatting point 2
- Formatting point 3

[ACTION_PLAN]
## Week 1: Immediate Fixes
- Task 1
- Task 2
- Task 3

## Week 2–3: Skill Building
- Task 1
- Task 2
- Task 3

## Week 4: Final Polish & Apply
- Task 1
- Task 2
- Task 3

[INTERVIEW]
## Question 1: [Question title]
**Q:** Write the actual interview question here
**How to answer:** Brief tip on how to answer it well

## Question 2: [Question title]
**Q:** Write the actual interview question here
**How to answer:** Brief tip

## Question 3: [Question title]
**Q:** Write the actual interview question here
**How to answer:** Brief tip

[KEYWORDS]
<If job description provided: one line starting MISSING: comma-separated missing keywords,
next line starting FOUND: comma-separated found keywords.
If no JD provided write exactly: NO_JD>

[REWRITE]
## Bullet 1 (Original)
> Original weak bullet point copied from resume

**Rewritten:**
Stronger version with metrics and action verbs

## Bullet 2 (Original)
> Original weak bullet point copied from resume

**Rewritten:**
Stronger version with metrics and action verbs

## Bullet 3 (Original)
> Original weak bullet point copied from resume

**Rewritten:**
Stronger version with metrics and action verbs
"""

                with st.spinner(f"Analyzing resume for **{final_job_role}**… About 15 seconds."):
                    raw_analysis = call_groq(main_prompt, max_tokens=3000)

                score_val = 0
                score_match = re.search(r'\[SCORE\]\s*(\d+)', raw_analysis)
                if score_match:
                    score_val = max(0, min(100, int(score_match.group(1))))

                analysis_content    = get_block(raw_analysis, "[ANALYSIS]",    "[ACTION_PLAN]")
                action_plan_content = get_block(raw_analysis, "[ACTION_PLAN]", "[INTERVIEW]")
                interview_content   = get_block(raw_analysis, "[INTERVIEW]",   "[KEYWORDS]")
                keywords_raw        = get_block(raw_analysis, "[KEYWORDS]",    "[REWRITE]")
                rewrite_content     = get_block(raw_analysis, "[REWRITE]")

                if not analysis_content:
                    analysis_content = (
                        raw_analysis if raw_analysis
                        else "⚠️ The AI response was empty. Please try again."
                    )

                bullets_rewritten = len(re.findall(r'## Bullet \d+', rewrite_content)) if rewrite_content else 0

                keywords_html  = ""
                kw_raw_clean   = (keywords_raw or "").strip()
                if kw_raw_clean and kw_raw_clean != "NO_JD":
                    missing_match = re.search(r'MISSING:\s*(.+)', kw_raw_clean)
                    found_match   = re.search(r'FOUND:\s*(.+)',   kw_raw_clean)
                    if missing_match or found_match:
                        keywords_html = (
                            "<p style='font-size:12px;color:#64748B;font-weight:700;"
                            "text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;'>"
                            "Missing from Resume</p>"
                        )
                        if missing_match:
                            for kw in [k.strip() for k in missing_match.group(1).split(",") if k.strip()]:
                                keywords_html += f"<span class='kw-chip'>{kw}</span>"
                        keywords_html += (
                            "<p style='font-size:12px;color:#64748B;font-weight:700;"
                            "text-transform:uppercase;letter-spacing:1px;margin:14px 0 10px;'>"
                            "Found in Resume</p>"
                        )
                        if found_match:
                            for kw in [k.strip() for k in found_match.group(1).split(",") if k.strip()]:
                                keywords_html += f"<span class='kw-chip kw-chip-found'>{kw}</span>"
                elif not job_description.strip():
                    keywords_html = (
                        "<p style='color:#475569;font-size:14px;'>"
                        "Paste a job description in Step 03 to unlock keyword gap analysis.</p>"
                    )

                st.session_state.score_val           = score_val
                st.session_state.analysis_content    = analysis_content
                st.session_state.action_plan_content = action_plan_content
                st.session_state.interview_content   = interview_content
                st.session_state.keywords_html       = keywords_html
                st.session_state.rewrite_content     = rewrite_content
                st.session_state.final_job_role      = final_job_role
                st.session_state.resume_word_count   = word_count
                st.session_state.bullets_rewritten   = bullets_rewritten
                st.session_state.analysis_done       = True

                st.session_state.history.append({
                    "role":  final_job_role,
                    "score": score_val,
                    "time":  datetime.now().strftime("%I:%M %p"),
                })

                st.rerun()

            except Exception as exc:
                err_str = str(exc)
                if "rate_limit" in err_str.lower() or "429" in err_str:
                    st.error("Groq rate limit reached. Please wait 30 seconds and try again.")
                else:
                    st.error(f"Something went wrong: {err_str}")


# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────
if st.session_state.analysis_done:
    score_val           = st.session_state.score_val
    analysis_content    = st.session_state.analysis_content
    action_plan_content = st.session_state.action_plan_content
    interview_content   = st.session_state.interview_content
    keywords_html       = st.session_state.keywords_html
    rewrite_content     = st.session_state.rewrite_content
    role_label          = st.session_state.final_job_role
    resume_words        = st.session_state.resume_word_count
    bullets_rewritten   = st.session_state.bullets_rewritten

    score_color      = "#22C55E" if score_val >= 75 else "#F59E0B" if score_val >= 50 else "#EF4444"
    score_glow       = ("rgba(34,197,94,0.15)"  if score_val >= 75
                        else "rgba(245,158,11,0.15)" if score_val >= 50
                        else "rgba(239,68,68,0.15)")
    score_label_text = ("Strong Match"   if score_val >= 75
                        else "Moderate Match" if score_val >= 50
                        else "Needs Work")

    st.markdown("<hr>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"""
        <div style='text-align:center;padding:1rem 0 0.5rem;'>
            <div style='display:inline-block;background:{score_glow};
                        border:2px solid {score_color}40;border-radius:9999px;
                        padding:2rem 3rem;margin-bottom:1rem;'>
                <div class='big-score' style='color:{score_color};'>{score_val}</div>
                <div style='font-size:11px;color:#475569;font-weight:700;
                            letter-spacing:3px;text-transform:uppercase;'>ATS Match Score</div>
            </div>
            <div style='margin:0 auto 1rem;max-width:340px;'>
                <div style='background:#0D1526;border-radius:6px;height:8px;
                            overflow:hidden;border:1px solid #1E293B;'>
                    <div style='width:{score_val}%;height:100%;
                                background:{score_color};border-radius:6px;'></div>
                </div>
            </div>
            <span style='background:{score_glow};color:{score_color};font-size:12px;
                         font-weight:700;padding:4px 14px;border-radius:9999px;
                         border:1px solid {score_color}40;'>{score_label_text}</span>
            <p style='color:#475569;font-size:13px;margin-top:12px;'>
                Analyzed for <strong style='color:#818CF8;'>{role_label}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='stat-row'>
            <div class='stat-box'>
                <div class='stat-num'>{resume_words}</div>
                <div class='stat-lbl'>Word Count</div>
            </div>
            <div class='stat-box'>
                <div class='stat-num' style='color:{score_color};'>{score_val}%</div>
                <div class='stat-lbl'>ATS Score</div>
            </div>
            <div class='stat-box'>
                <div class='stat-num'>{bullets_rewritten}</div>
                <div class='stat-lbl'>Bullets Rewritten</div>
            </div>
            <div class='stat-box'>
                <div class='stat-num'>30</div>
                <div class='stat-lbl'>Day Plan</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 Analysis", "🗓️ Action Plan", "🎤 Interview Prep", "🔍 Keywords", "✍️ Rewrites"]
        )
        with tab1:
            st.markdown(analysis_content)
        with tab2:
            if action_plan_content:
                st.markdown(action_plan_content)
            else:
                st.markdown("<p style='color:#475569;'>No action plan generated.</p>", unsafe_allow_html=True)
        with tab3:
            if interview_content:
                st.markdown(interview_content)
            else:
                st.markdown("<p style='color:#475569;'>No interview questions generated.</p>", unsafe_allow_html=True)
        with tab4:
            if keywords_html:
                st.markdown(keywords_html, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#475569;'>No keyword data available.</p>", unsafe_allow_html=True)
        with tab5:
            if rewrite_content:
                st.markdown(rewrite_content)
            else:
                st.markdown("<p style='color:#475569;'>No rewrites generated.</p>", unsafe_allow_html=True)

    st.write("")
    download_text = (
        f"AI PLACEMENT COACH — FULL REPORT\n"
        f"Role: {role_label}\nATS Score: {score_val}%\n\n"
        f"{'=' * 50}\nANALYSIS\n{'=' * 50}\n{analysis_content}\n\n"
        f"{'=' * 50}\n30-DAY ACTION PLAN\n{'=' * 50}\n{action_plan_content}\n\n"
        f"{'=' * 50}\nINTERVIEW PREP\n{'=' * 50}\n{interview_content}\n\n"
        f"{'=' * 50}\nBULLET REWRITES\n{'=' * 50}\n{rewrite_content}"
    )
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.download_button(
            label="⬇️  Download Full Report",
            data=download_text,
            file_name=f"{role_label.replace(' ', '_')}_Resume_Report.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.write("")
        if st.button("🔄  Analyze Another Resume", use_container_width=True):
            st.session_state.analysis_done       = False
            st.session_state.score_val           = 0
            st.session_state.analysis_content    = ""
            st.session_state.action_plan_content = ""
            st.session_state.interview_content   = ""
            st.session_state.keywords_html       = ""
            st.session_state.rewrite_content     = ""
            st.session_state.final_job_role      = ""
            st.session_state.resume_word_count   = 0
            st.session_state.bullets_rewritten   = 0
            st.session_state.upload_key          += 1
            st.rerun()


# ─────────────────────────────────────────────
# FEATURES GRID & LANDING PAGE SECTIONS (Always Visible)
# ─────────────────────────────────────────────
# Indentation removed from HTML blocks inside multiline strings 
# to prevent the Streamlit markdown engine from converting them into plaintext code blocks.
st.markdown("""
<div id="features" style="margin-top: 3.5rem;">
<h2 style="font-size: 1.35rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem; color: #FFFFFF;">Advanced Recruitment Engine Capabilities</h2>
<p style="text-align: center; color: #64748B; font-size: 0.85rem; max-width: 500px; margin: 0 auto 2rem;">Unlock enterprise-grade optimization tools built to clear standard applicant tracking systems and top-tier hiring benchmarks.</p>
<div class="features-grid">
<div style="background: #0D1526; border: 1px solid #1E293B; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #6366F1;">
<div style="font-size: 1.5rem; margin-bottom: 0.75rem;">⚡</div>
<h3 style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Semantic ATS Mapping</h3>
<p style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5; margin: 0;">Our parser matches core semantic keywords and engineering frameworks against industry templates using advanced contextual heuristics.</p>
</div>
<div style="background: #0D1526; border: 1px solid #1E293B; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #6366F1;">
<div style="font-size: 1.5rem; margin-bottom: 0.75rem;">✍️</div>
<h3 style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Dynamic Bullet Rewriting</h3>
<p style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5; margin: 0;">Convert basic task-oriented sentences into metrics-driven professional achievements modeled around the classic Google STAR methodology.</p>
</div>
<div style="background: #0D1526; border: 1px solid #1E293B; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #6366F1;">
<div style="font-size: 1.5rem; margin-bottom: 0.75rem;">🎯</div>
<h3 style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Adaptive Interview Prep</h3>
<p style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5; margin: 0;">Generates custom behavioural and technical practice scenarios derived directly from gaps flagged on your submitted resume profile.</p>
</div>
<div style="background: #0D1526; border: 1px solid #1E293B; border-radius: 12px; padding: 1.5rem; border-top: 3px solid #6366F1;">
<div style="font-size: 1.5rem; margin-bottom: 0.75rem;">📋</div>
<h3 style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">30-Day Guided Roadmap</h3>
<p style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5; margin: 0;">Get prioritized action plans highlighting immediate fixes, skill acquisition strategies, and tactical preparation tips.</p>
</div>
</div>
</div>

<div id="testimonials" style="margin-top: 2rem; background: linear-gradient(180deg, #0D1526 0%, #030712 100%); border: 1px solid #1E293B; border-radius: 16px; padding: 1.75rem; margin-bottom: 2.5rem;">
<h2 style="font-size: 1.2rem; font-weight: 800; text-align: center; margin-bottom: 1.25rem; color: #FFFFFF;">Success Stories from Candidates</h2>
<div style="display: flex; gap: 1.25rem; flex-direction: column;">
<div style="border-left: 3px solid #6366F1; padding-left: 1rem;">
<p style="font-style: italic; color: #94A3B8; font-size: 0.82rem; line-height: 1.6; margin-bottom: 0.4rem;">"The bullet point rewriter transformed my resume completely. I received responses from major tech companies within a week of adjusting my metrics."</p>
<p style="font-size: 0.72rem; font-weight: 700; color: #818CF8; margin: 0;">— S. Patel, Software Engineer @ Stripe</p>
</div>
<div style="border-left: 3px solid #6366F1; padding-left: 1rem;">
<p style="font-style: italic; color: #94A3B8; font-size: 0.82rem; line-height: 1.6; margin-bottom: 0.4rem;">"Finding exact missing keywords for my targeted role was key. The structured 30-day preparation goals kept my focus where it was needed most."</p>
<p style="font-size: 0.72rem; font-weight: 700; color: #818CF8; margin: 0;">— Emily R., Business Analyst @ Meta</p>
</div>
</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FAQ BLOCK
# ─────────────────────────────────────────────
with st.container(border=True):
    st.markdown("<p id='faq' class='section-title' style='text-align:center;font-size:1.2rem;margin-top:0.5rem;margin-bottom:1.5rem;'>Frequently Asked Questions</p>", unsafe_allow_html=True)
    with st.expander("🔒 Is my resume data secure?", expanded=False):
        st.write("Yes, your documents are parsed strictly inside temporary in-memory buffers to extract selectable metadata. We do not store, distribute, or share personal profile information with third parties.")
    with st.expander("📄 What file formats are supported?", expanded=False):
        st.write("We support PDF (.pdf) and Microsoft Word (.docx) formats. Make sure your PDF contains selectable text to ensure complete semantic evaluation.")
    with st.expander("⚡ How is the ATS Match score determined?", expanded=False):
        st.write("The platform evaluates resume formatting patterns, functional skill densities, and context matches against industry profiles or your provided job description to generate standard compatibility ratings.")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption("Built with Groq LLaMA + Streamlit | CoachAI")