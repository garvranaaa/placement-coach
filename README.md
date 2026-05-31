<div align="center">

# ◈ ResumeIQ — AI Placement Coach

**Upload your resume. Get brutally honest AI feedback in under 20 seconds.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-garvrana--placement--coach.streamlit.app-C17A3A?style=for-the-badge&logo=streamlit&logoColor=white)](https://garvrana-placement-coach.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.14-1A1714?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=for-the-badge)](https://groq.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

</div>

---

## What is ResumeIQ?

ResumeIQ is an AI-powered resume coach built for students and job seekers. Paste your resume and a job description — and get a full structured breakdown of where you stand and exactly what to fix.

No fluff. No generic tips. Just direct, role-specific analysis powered by Groq's LLaMA 3.3 70B.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **ATS Score** | 0–100 match score for your target role |
| 🔍 **Keyword Gap Analysis** | Exact keywords missing from your resume vs the JD |
| ✍️ **Bullet Point Rewriter** | AI rewrites your 3 weakest lines with metrics and action verbs |
| 🎤 **Interview Prep** | 3 hard questions tailored to your specific profile |
| 🗓️ **30-Day Action Plan** | Week-by-week plan to close your gaps before applying |
| 📥 **Downloadable Report** | Full analysis as a text file |
| 📂 **PDF & Word support** | Works with both .pdf and .docx resumes |

---

## Demo

> **Try it live →** [garvrana-placement-coach.streamlit.app](https://garvrana-placement-coach.streamlit.app)

Upload any resume, select a role, and optionally paste a job description for the most accurate results.

---

## How It Works

```
User uploads resume (PDF / DOCX)
        ↓
MarkItDown extracts clean text
        ↓
Resume + Job Description → Groq LLaMA 3.3 70B
        ↓
Structured prompt returns tagged response
        ↓
Parsed into 5 sections: Score · Analysis · Plan · Keywords · Rewrites
        ↓
Displayed in tabbed dashboard with download option
```

---

## Tech Stack

```
Frontend / UI     →  Streamlit
AI Model          →  Groq LLaMA 3.3 70B (free tier)
Fallback Model    →  Groq LLaMA 3.1 8B (on rate limit)
File Parsing      →  Microsoft MarkItDown
Language          →  Python 3.14
Deployment        →  Streamlit Cloud (free)
```

---

## Run Locally

### Prerequisites
- Python 3.10+
- A free Groq API key from [console.groq.com](https://console.groq.com) — no credit card required

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/garvranaaa/placement-coach.git
cd placement-coach
```

**2. Set up virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure your API key**

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

**5. Start the app**
```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## Project Structure

```
placement-coach/
│
├── app.py                  # Main application — all logic and UI
├── requirements.txt        # Python dependencies
├── .env                    # API key (local only, never committed)
├── .gitignore              # Excludes .env and venv/
└── README.md               # This file
```

---

## Requirements

```
groq
streamlit
markitdown
python-dotenv
```

---

## Design Decisions

**Why Groq?**
Groq's free tier gives access to LLaMA 3.3 70B with no credit card and no expiry. Inference is extremely fast — typically under 5 seconds for a full resume analysis.

**Why Streamlit?**
Zero frontend code required. Deploy in minutes. Free hosting on Streamlit Cloud. The right tool for a solo AI project.

**Why MarkItDown?**
Microsoft's MarkItDown handles both PDF and Word files in one library, producing cleaner text extraction than PyMuPDF for structured resume formats.

**Why tagged prompts?**
Using `[SCORE]`, `[ANALYSIS]`, `[ACTION_PLAN]` etc. as delimiters makes the AI output reliably parseable without JSON overhead or schema enforcement.

---

## Roadmap

- [ ] LinkedIn profile analysis (URL input)
- [ ] Multi-resume comparison mode
- [ ] Email the report directly
- [ ] GitHub profile integration
- [ ] Mobile-optimised layout

---

## Origin

Built as part of the **GFF AI Future Builders — DTU Challenge**:
*"Build Something Real in 30 Days."*

> *"Don't tell us what courses you completed. Show us what intelligence you built."*

---

## Author

**Garv Sanjeev Rana**
B.Tech Electrical Engineering · Delhi Technological University · Semester 4

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Garv%20Rana-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/garv-rana)
[![GitHub](https://img.shields.io/badge/GitHub-garvranaaa-1A1714?style=flat-square&logo=github)](https://github.com/garvranaaa)

---

<div align="center">
<sub>Free to use · Built with curiosity · No credit card ever required</sub>
</div>
