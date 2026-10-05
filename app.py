import os
import json
import re
import html

import streamlit as st
import pandas as pd
import plotly.express as px

from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Streamlit Skill Gap Detector",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = None

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None


# ============================================================
# CUSTOM CSS
# ============================================================

st.html(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background: #f7f9fc;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* ======================================================
       HERO
       ====================================================== */

    .hero {
        background: linear-gradient(
            135deg,
            #4f46e5 0%,
            #6366f1 45%,
            #7c3aed 100%
        );

        padding: 45px 40px;
        border-radius: 24px;
        margin-bottom: 30px;

        box-shadow:
            0 15px 35px rgba(79, 70, 229, 0.20);

        color: white;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 12px;
    }

    .hero-subtitle {
        font-size: 18px;
        line-height: 1.7;
        opacity: 0.95;
        max-width: 850px;
    }


    /* ======================================================
       NAVIGATION CARDS
       ====================================================== */

    .nav-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 28px;
        min-height: 230px;

        box-shadow:
            0 8px 25px rgba(15, 23, 42, 0.06);

        margin-bottom: 15px;
    }

    .nav-icon {
        font-size: 38px;
        margin-bottom: 12px;
    }

    .nav-title {
        font-size: 22px;
        font-weight: 750;
        color: #111827;
        margin-bottom: 10px;
    }

    .nav-description {
        color: #6b7280;
        font-size: 15px;
        line-height: 1.6;
    }


    /* ======================================================
       PAGE HEADER
       ====================================================== */

    .page-header {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 25px 30px;
        margin-bottom: 25px;

        box-shadow:
            0 6px 20px rgba(15, 23, 42, 0.05);
    }

    .page-title {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 8px;
    }

    .page-description {
        color: #6b7280;
        font-size: 16px;
        line-height: 1.6;
    }


    /* ======================================================
       RESULT CARDS
       ====================================================== */

    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;

        box-shadow:
            0 6px 20px rgba(15, 23, 42, 0.05);
    }

    .result-title {
        font-size: 21px;
        font-weight: 750;
        color: #111827;
        margin-bottom: 8px;
    }

    .result-text {
        color: #4b5563;
        line-height: 1.7;
    }


    /* ======================================================
       TAGS
       ====================================================== */

    .tag {
        display: inline-block;
        background: #eef2ff;
        color: #4338ca;

        padding: 7px 12px;
        border-radius: 999px;

        font-size: 13px;
        font-weight: 650;

        margin: 4px;
    }


    /* ======================================================
       INFO BOX
       ====================================================== */

    .info-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 18px;
    }

    .info-title {
        font-weight: 750;
        color: #1e293b;
        margin-bottom: 6px;
    }

    .info-text {
        color: #64748b;
        line-height: 1.6;
    }


    /* ======================================================
       QUESTION CARD
       ====================================================== */

    .question-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 18px;

        box-shadow:
            0 5px 18px rgba(15, 23, 42, 0.04);
    }

    .question-number {
        color: #4f46e5;
        font-weight: 750;
        font-size: 14px;
        margin-bottom: 6px;
    }

    .question-text {
        color: #111827;
        font-size: 18px;
        font-weight: 700;
        line-height: 1.5;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .footer {
        text-align: center;
        color: #6b7280;
        padding: 35px 10px 10px;
        font-size: 14px;
    }


    /* ======================================================
       STREAMLIT BUTTONS
       ====================================================== */

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 650;
        padding: 0.65rem 1rem;
    }


    /* ======================================================
       METRICS
       ====================================================== */

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px;

        box-shadow:
            0 5px 18px rgba(15, 23, 42, 0.05);
    }


    /* ======================================================
       MOBILE
       ====================================================== */

    @media (max-width: 768px) {

        .hero {
            padding: 30px 24px;
        }

        .hero-title {
            font-size: 30px;
        }

        .hero-subtitle {
            font-size: 15px;
        }

        .page-title {
            font-size: 25px;
        }

    }

    </style>
    """
)


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero">

        <div class="hero-title">
            🎯 Streamlit Skill Gap Detector
        </div>

        <div class="hero-subtitle">
            Analyze student performance, identify weak concepts,
            visualize skill gaps, and use AI to discover the
            right libraries and technologies for your projects.
        </div>

    </div>
    """
)


# ============================================================
# HOME PAGE
# ============================================================

def show_home():

    st.html(
        """
        <div class="page-header">

            <div class="page-title">
                🚀 Learning & Project Intelligence
            </div>

            <div class="page-description">
                Upload study material to generate an AI-powered
                assessment, analyze your skill gaps, or get
                technology recommendations for your project idea.
            </div>

        </div>
        """
    )

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # SKILL GAP
    # --------------------------------------------------------

    with col1:

        st.html(
            """
            <div class="nav-card">

                <div class="nav-icon">
                    📊
                </div>

                <div class="nav-title">
                    Skill Gap Analysis
                </div>

                <div class="nav-description">
                    Upload a study-material PDF and let AI
                    generate a personalized MCQ assessment.
                    Analyze performance chapter-wise,
                    topic-wise, and question-wise.
                </div>

            </div>
            """
        )

        if st.button(
            "Open Skill Gap Analysis",
            key="skill_gap_home"
        ):

            st.session_state.page = "skill_gap"
            st.rerun()

    # --------------------------------------------------------
    # AI RECOMMENDER
    # --------------------------------------------------------

    with col2:

        st.html(
            """
            <div class="nav-card">

                <div class="nav-icon">
                    🤖
                </div>

                <div class="nav-title">
                    AI Project Recommender
                </div>

                <div class="nav-description">
                    Enter your project idea and Gemini AI
                    recommends suitable libraries, frameworks,
                    installation commands, and implementation steps.
                </div>

            </div>
            """
        )

        if st.button(
            "Open AI Recommender",
            key="ai_home"
        ):

            st.session_state.page = "ai"
            st.rerun()

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    with col3:

        st.html(
            """
            <div class="nav-card">

                <div class="nav-icon">
                    ℹ️
                </div>

                <div class="nav-title">
                    About Project
                </div>

                <div class="nav-description">
                    Learn about the purpose, features,
                    technology stack, and workflow of
                    the Streamlit Skill Gap Detector.
                </div>

            </div>
            """
        )

        if st.button(
            "About This Project",
            key="about_home"
        ):

            st.session_state.page = "about"
            st.rerun()


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    try:

        reader = PdfReader(uploaded_file)

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if text:

                pages.append(
                    f"\n--- PAGE {page_number} ---\n{text}"
                )

        full_text = "\n".join(pages)

        return full_text.strip()

    except Exception as e:

        st.error(
            f"Unable to read the PDF: {e}"
        )

        return ""


# ============================================================
# GEMINI JSON CLEANER
# ============================================================

def clean_json_response(text):

    text = text.strip()

    # Remove markdown fences
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    text = text.strip()

    # Find JSON object if Gemini added extra text
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        text = text[start:end + 1]

    return text


# ============================================================
# GENERATE MCQ TEST FROM PDF
# ============================================================

def generate_mcq_test(
    pdf_text,
    number_of_questions,
    difficulty
):

    if not GEMINI_API_KEY:

        st.error(
            "GEMINI_API_KEY was not found in your .env file."
        )

        return None

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        # ----------------------------------------------------
        # Keep a practical amount of PDF text
        # ----------------------------------------------------

        max_chars = 90000

        if len(pdf_text) > max_chars:

            pdf_text = pdf_text[:max_chars]

            st.warning(
                "The PDF is very large, so only the first "
                "part of the extracted content was used."
            )

        # ----------------------------------------------------
        # PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are an expert educational assessment generator.

Your task is to create a multiple-choice assessment
STRICTLY from the study material provided below.

Do not use unrelated outside knowledge.

STUDY MATERIAL:
----------------
{pdf_text}
----------------

Generate exactly {number_of_questions} MCQ questions.

Difficulty:
{difficulty}

IMPORTANT REQUIREMENTS:

1. Every question must be answerable from the supplied PDF.
2. Do not invent information that is not supported by the PDF.
3. Identify the appropriate chapter from the PDF.
4. Identify the specific topic/concept tested by each question.
5. Each question must have exactly four options.
6. Only one option must be correct.
7. Questions should test understanding, not only memorization.
8. Avoid duplicate questions.
9. Distribute questions across available chapters/topics where possible.
10. If chapter names are not explicitly present, infer meaningful chapter
    or section names only from the organization of the supplied material.
11. Include a short explanation of the correct answer.
12. Return ONLY valid JSON.
13. Do not return Markdown.
14. Do not use ```json.

Return EXACTLY this JSON structure:

{{
    "assessment_title": "AI Generated Assessment",

    "chapters": [
        "Chapter 1",
        "Chapter 2"
    ],

    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_answer": "Exact correct option",
            "chapter": "Chapter or section name",
            "topic": "Specific topic/concept",
            "difficulty": "Easy",
            "explanation": "Short explanation based on the study material"
        }}
    ]
}}

Make sure the number of objects inside "questions"
is exactly {number_of_questions}.
"""

        # ----------------------------------------------------
        # GEMINI INTERACTIONS API
        # ----------------------------------------------------

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        response_text = interaction.output_text

        if not response_text:

            st.error(
                "Gemini returned an empty response."
            )

            return None

        # ----------------------------------------------------
        # CLEAN RESPONSE
        # ----------------------------------------------------

        response_text = clean_json_response(
            response_text
        )

        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        result = json.loads(
            response_text
        )

        questions = result.get(
            "questions",
            []
        )

        if not questions:

            st.error(
                "No questions were generated from the PDF."
            )

            return None

        # ----------------------------------------------------
        # VALIDATE QUESTIONS
        # ----------------------------------------------------

        valid_questions = []

        for question in questions:

            if not isinstance(question, dict):
                continue

            question_text = question.get(
                "question"
            )

            options = question.get(
                "options"
            )

            correct_answer = question.get(
                "correct_answer"
            )

            chapter = question.get(
                "chapter",
                "General"
            )

            topic = question.get(
                "topic",
                "General"
            )

            difficulty_value = question.get(
                "difficulty",
                difficulty
            )

            explanation = question.get(
                "explanation",
                ""
            )

            if not question_text:
                continue

            if not isinstance(options, list):
                continue

            if len(options) != 4:
                continue

            if not correct_answer:
                continue

            valid_questions.append(
                {
                    "question": str(question_text),
                    "options": [
                        str(option)
                        for option in options
                    ],
                    "correct_answer": str(
                        correct_answer
                    ),
                    "chapter": str(chapter),
                    "topic": str(topic),
                    "difficulty": str(
                        difficulty_value
                    ),
                    "explanation": str(
                        explanation
                    )
                }
            )

        if not valid_questions:

            st.error(
                "Gemini generated an invalid assessment."
            )

            return None

        return {
            "assessment_title": result.get(
                "assessment_title",
                "AI Generated Assessment"
            ),
            "chapters": result.get(
                "chapters",
                []
            ),
            "questions": valid_questions
        }

    except json.JSONDecodeError:

        st.error(
            "Gemini returned an invalid JSON response."
        )

        return None

    except Exception as e:

        st.error(
            f"Gemini API Error: {e}"
        )

        return None


# ============================================================
# CREATE PERFORMANCE DATAFRAME
# ============================================================

def create_performance_dataframe(
    questions,
    answers
):

    rows = []

    for index, question in enumerate(questions):

        selected_answer = answers.get(
            index,
            ""
        )

        correct_answer = question[
            "correct_answer"
        ]

        is_correct = (
            selected_answer == correct_answer
        )

        rows.append(
            {
                "Question": f"Q{index + 1}",
                "Question Text": question[
                    "question"
                ],
                "Chapter": question[
                    "chapter"
                ],
                "Topic": question[
                    "topic"
                ],
                "Difficulty": question[
                    "difficulty"
                ],
                "Selected Answer": selected_answer,
                "Correct Answer": correct_answer,
                "Correct": is_correct,
                "Score": 100 if is_correct else 0,
                "Explanation": question[
                    "explanation"
                ]
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# SKILL GAP ANALYSIS PAGE
# ============================================================

def show_skill_gap():

    if st.button(
        "← Back to Home",
        key="back_skill"
    ):

        st.session_state.page = "home"
        st.rerun()

    st.html(
        """
        <div class="page-header">

            <div class="page-title">
                📊 Student Skill Gap Analysis
            </div>

            <div class="page-description">
                Upload your study material and let AI generate
                a personalized assessment. Your performance
                will be analyzed question-wise, topic-wise,
                and chapter-wise.
            </div>

        </div>
        """
    )

    # ========================================================
    # PDF UPLOAD
    # ========================================================

    st.markdown("### 📄 Upload Study Material")

    uploaded_file = st.file_uploader(
        "Upload a PDF containing your study material",
        type=["pdf"],
        help=(
            "Upload a textbook chapter, lecture notes, "
            "study material, or syllabus PDF."
        )
    )

    if uploaded_file:

        st.success(
            f"PDF uploaded: **{uploaded_file.name}**"
        )

        col1, col2 = st.columns(2)

        with col1:

            number_of_questions = st.selectbox(
                "📝 Number of Questions",
                [5, 10, 15, 20, 25, 30],
                index=1
            )

        with col2:

            difficulty = st.selectbox(
                "🎯 Difficulty",
                [
                    "Easy",
                    "Medium",
                    "Hard",
                    "Mixed"
                ],
                index=3
            )

        # ----------------------------------------------------
        # GENERATE BUTTON
        # ----------------------------------------------------

        if st.button(
            "✨ Generate AI Assessment",
            type="primary",
            key="generate_test"
        ):

            with st.spinner(
                "📖 Reading PDF and generating your assessment..."
            ):

                pdf_text = extract_pdf_text(
                    uploaded_file
                )

            if not pdf_text:

                st.error(
                    "No readable text was found in this PDF. "
                    "Please upload a text-based PDF."
                )

            else:

                with st.spinner(
                    "🤖 Gemini is generating your MCQ assessment..."
                ):

                    assessment = generate_mcq_test(
                        pdf_text,
                        number_of_questions,
                        difficulty
                    )

                if assessment:

                    st.session_state.generated_questions = (
                        assessment["questions"]
                    )

                    st.session_state.pdf_name = (
                        uploaded_file.name
                    )

                    st.session_state.analysis_results = None

                    st.success(
                        f"Assessment generated successfully! "
                        f"{len(assessment['questions'])} questions are ready."
                    )

                    st.rerun()

    # ========================================================
    # DISPLAY GENERATED TEST
    # ========================================================

    questions = st.session_state.generated_questions

    if questions:

        st.markdown("---")

        st.html(
            f"""
            <div class="info-card">

                <div class="info-title">
                    📝 AI-Generated Assessment
                </div>

                <div class="info-text">
                    Study Material:
                    <strong>
                        {html.escape(
                            str(
                                st.session_state.pdf_name
                            )
                        )}
                    </strong>
                    <br>
                    Questions:
                    <strong>{len(questions)}</strong>
                    <br>
                    Answer all questions and click
                    <strong>Analyze My Skills</strong>
                    to generate your personalized report.
                </div>

            </div>
            """
        )

        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        with st.form(
            "assessment_form"
        ):

            answers = {}

            for index, question in enumerate(
                questions
            ):

                st.html(
                    f"""
                    <div class="question-card">

                        <div class="question-number">
                            QUESTION {index + 1}
                        </div>

                        <div class="question-text">
                            {html.escape(
                                question["question"]
                            )}
                        </div>

                    </div>
                    """
                )

                answers[index] = st.radio(
                    "Select your answer:",
                    question["options"],
                    key=f"generated_question_{index}",
                    label_visibility="collapsed"
                )

                st.caption(
                    f"Chapter: {question['chapter']}  •  "
                    f"Topic: {question['topic']}  •  "
                    f"Difficulty: {question['difficulty']}"
                )

                st.divider()

            submitted = st.form_submit_button(
                "🔍 Analyze My Skills",
                type="primary"
            )

        # ====================================================
        # ANALYZE TEST
        # ====================================================

        if submitted:

            df = create_performance_dataframe(
                questions,
                answers
            )

            st.session_state.analysis_results = df

            st.success(
                "Skill analysis completed successfully!"
            )

    # ========================================================
    # DISPLAY ANALYSIS RESULTS
    # ========================================================

    df = st.session_state.analysis_results

    if df is None:
        return

    st.markdown("---")

    # ========================================================
    # OVERALL PERFORMANCE
    # ========================================================

    total_questions = len(df)

    correct_answers = int(
        df["Correct"].sum()
    )

    overall_score = round(
        (correct_answers / total_questions) * 100,
        2
    )

    chapter_scores = (
        df.groupby("Chapter")["Score"]
        .mean()
        .reset_index()
    )

    chapter_scores["Score"] = (
        chapter_scores["Score"].round(2)
    )

    topic_scores = (
        df.groupby("Topic")["Score"]
        .mean()
        .reset_index()
    )

    topic_scores["Score"] = (
        topic_scores["Score"].round(2)
    )

    weak_topics = topic_scores[
        topic_scores["Score"] < 70
    ]["Topic"].tolist()

    strong_topics = topic_scores[
        topic_scores["Score"] >= 70
    ]["Topic"].tolist()

    weak_chapters = chapter_scores[
        chapter_scores["Score"] < 70
    ]["Chapter"].tolist()

    st.markdown("## 📈 Your Performance")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:

        st.metric(
            "Overall Score",
            f"{overall_score}%"
        )

    with metric2:

        st.metric(
            "Correct Answers",
            f"{correct_answers}/{total_questions}"
        )

    with metric3:

        st.metric(
            "Chapters Analyzed",
            len(chapter_scores)
        )

    with metric4:

        st.metric(
            "Weak Topics",
            len(weak_topics)
        )

    # ========================================================
    # PERFORMANCE STATUS
    # ========================================================

    if overall_score >= 80:

        st.success(
            "🌟 Excellent performance! You have demonstrated "
            "strong understanding of the uploaded material."
        )

    elif overall_score >= 60:

        st.info(
            "👍 Good performance. Review the highlighted "
            "weak topics to improve your understanding."
        )

    else:

        st.warning(
            "📚 More revision is recommended. Focus on the "
            "weak chapters and concepts identified below."
        )

    # ========================================================
    # QUESTION-WISE PERFORMANCE
    # ========================================================

    st.markdown("## 📊 Question-wise Performance")

    question_chart = px.bar(
        df,
        x="Question",
        y="Score",
        text="Score",
        title="Question-wise Correctness",
        labels={
            "Score": "Correctness (%)",
            "Question": "Question"
        },
        range_y=[0, 100]
    )

    question_chart.update_traces(
        textposition="outside"
    )

    question_chart.update_layout(
        height=450
    )

    st.plotly_chart(
        question_chart,
        use_container_width=True
    )

    # ========================================================
    # CHAPTER-WISE PERFORMANCE
    # ========================================================

    st.markdown("## 📚 Chapter-wise Performance")

    chapter_chart = px.bar(
        chapter_scores,
        x="Chapter",
        y="Score",
        text="Score",
        title="Chapter-wise Correctness",
        labels={
            "Score": "Correctness (%)",
            "Chapter": "Chapter"
        },
        range_y=[0, 100]
    )

    chapter_chart.update_traces(
        textposition="outside"
    )

    chapter_chart.update_layout(
        height=450
    )

    st.plotly_chart(
        chapter_chart,
        use_container_width=True
    )

    # ========================================================
    # TOPIC-WISE PERFORMANCE
    # ========================================================

    st.markdown("## 🎯 Topic-wise Performance")

    topic_chart = px.bar(
        topic_scores,
        x="Topic",
        y="Score",
        text="Score",
        title="Topic-wise Correctness",
        labels={
            "Score": "Correctness (%)",
            "Topic": "Topic"
        },
        range_y=[0, 100]
    )

    topic_chart.update_traces(
        textposition="outside"
    )

    topic_chart.update_layout(
        height=500
    )

    st.plotly_chart(
        topic_chart,
        use_container_width=True
    )

    # ========================================================
    # CHAPTER × TOPIC HEATMAP
    # ========================================================

    st.markdown(
        "## 🔥 Chapter & Topic Performance Heatmap"
    )

    heatmap_data = (
        df.groupby(
            ["Chapter", "Topic"]
        )["Score"]
        .mean()
        .reset_index()
    )

    heatmap_pivot = heatmap_data.pivot(
        index="Chapter",
        columns="Topic",
        values="Score"
    )

    if not heatmap_pivot.empty:

        heatmap = px.imshow(
            heatmap_pivot,
            text_auto=True,
            aspect="auto",
            title="Chapter × Topic Skill Gap Heatmap",
            labels={
                "x": "Topic",
                "y": "Chapter",
                "color": "Correctness (%)"
            }
        )

        heatmap.update_layout(
            height=max(
                400,
                len(heatmap_pivot) * 80
            )
        )

        st.plotly_chart(
            heatmap,
            use_container_width=True
        )

    # ========================================================
    # WEAK TOPICS
    # ========================================================

    st.markdown(
        "## ⚠️ Concepts That Need Revision"
    )

    if weak_topics:

        st.warning(
            "The following topics have a correctness rate "
            "below 70% and should be revised:"
        )

        for topic in weak_topics:

            score = topic_scores.loc[
                topic_scores["Topic"] == topic,
                "Score"
            ].iloc[0]

            st.html(
                f"""
                <span class="tag">
                    {html.escape(topic)}
                    — {score}%
                </span>
                """
            )

    else:

        st.success(
            "Excellent! No topic scored below 70%."
        )

    # ========================================================
    # WEAK CHAPTERS
    # ========================================================

    st.markdown(
        "## 📕 Chapters That Need More Attention"
    )

    if weak_chapters:

        for chapter in weak_chapters:

            score = chapter_scores.loc[
                chapter_scores["Chapter"] == chapter,
                "Score"
            ].iloc[0]

            st.html(
                f"""
                <span class="tag">
                    {html.escape(chapter)}
                    — {score}%
                </span>
                """
            )

    else:

        st.success(
            "No chapter scored below 70%."
        )

    # ========================================================
    # STRONG TOPICS
    # ========================================================

    st.markdown(
        "## 💪 Strong Concepts"
    )

    if strong_topics:

        for topic in strong_topics:

            score = topic_scores.loc[
                topic_scores["Topic"] == topic,
                "Score"
            ].iloc[0]

            st.html(
                f"""
                <span class="tag">
                    {html.escape(topic)}
                    — {score}%
                </span>
                """
            )

    # ========================================================
    # REVISION RECOMMENDATIONS
    # ========================================================

    st.markdown(
        "## 📚 Recommended Revision Topics"
    )

    if weak_topics:

        for topic in weak_topics:

            score = topic_scores.loc[
                topic_scores["Topic"] == topic,
                "Score"
            ].iloc[0]

            st.html(
                f"""
                <div class="result-card">

                    <div class="result-title">
                        {html.escape(topic)}
                    </div>

                    <div class="result-text">

                        Current performance:
                        <strong>{score}%</strong>

                        <br><br>

                        Focus on revising the concepts,
                        examples, definitions, and practical
                        applications related to
                        <strong>
                            {html.escape(topic)}
                        </strong>.

                    </div>

                </div>
                """
            )

    else:

        st.success(
            "Your performance is strong across all topics. "
            "Continue practicing through real-world problems."
        )

    # ========================================================
    # DETAILED RESULTS
    # ========================================================

    st.markdown(
        "## 📝 Detailed Assessment Results"
    )

    for index, row in df.iterrows():

        if row["Correct"]:

            status = "✅ Correct"

        else:

            status = "❌ Incorrect"

        with st.expander(
            f"{row['Question']} — {status}"
        ):

            st.write(
                f"**Question:** {row['Question Text']}"
            )

            st.write(
                f"**Chapter:** {row['Chapter']}"
            )

            st.write(
                f"**Topic:** {row['Topic']}"
            )

            st.write(
                f"**Difficulty:** {row['Difficulty']}"
            )

            st.write(
                f"**Your Answer:** "
                f"{row['Selected Answer']}"
            )

            st.write(
                f"**Correct Answer:** "
                f"{row['Correct Answer']}"
            )

            if row["Explanation"]:

                st.info(
                    f"💡 {row['Explanation']}"
                )

    # ========================================================
    # DOWNLOAD REPORT
    # ========================================================

    st.markdown(
        "## ⬇️ Download Skill Gap Report"
    )

    download_df = df.copy()

    download_df["Correct"] = (
        download_df["Correct"]
        .map(
            {
                True: "Correct",
                False: "Incorrect"
            }
        )
    )

    csv_data = download_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Skill Gap Report",
        data=csv_data,
        file_name="skill_gap_report.csv",
        mime="text/csv"
    )


# ============================================================
# GEMINI PROJECT LIBRARY RECOMMENDER
# ============================================================

def recommend_libraries(project_idea):

    if not GEMINI_API_KEY:

        st.error(
            "GEMINI_API_KEY was not found. "
            "Please add it to your .env file."
        )

        return None

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        prompt = f"""
You are an expert software architect and technology recommender.

Analyze this project idea:

{project_idea}

Recommend the most appropriate libraries, frameworks,
APIs, databases, and tools required to build this project.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "project_summary": "Short summary of the project",

    "recommended_libraries": [
        {{
            "name": "Library or framework name",
            "purpose": "What it is used for",
            "installation": "Exact installation command",
            "usage": "How it will be used in this project"
        }}
    ],

    "technology_stack": [
        "Technology 1",
        "Technology 2",
        "Technology 3"
    ],

    "implementation_steps": [
        "Step 1",
        "Step 2",
        "Step 3"
    ],

    "optional_libraries": [
        {{
            "name": "Library name",
            "purpose": "Why it is optional"
        }}
    ]
}}

Rules:

- Recommend only relevant technologies.
- Avoid unnecessary libraries.
- Prefer stable and commonly used technologies.
- Give practical installation commands.
- Explain the purpose of every recommended library.
- Do not return Markdown.
- Do not return ```json.
- Return JSON only.
"""

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        response_text = interaction.output_text

        if not response_text:

            st.error(
                "Gemini returned an empty response."
            )

            return None

        response_text = clean_json_response(
            response_text
        )

        return json.loads(
            response_text
        )

    except json.JSONDecodeError:

        st.error(
            "Gemini returned an invalid JSON response."
        )

        return None

    except Exception as e:

        st.error(
            f"Gemini API Error: {e}"
        )

        return None


# ============================================================
# AI PROJECT RECOMMENDER PAGE
# ============================================================

def show_ai_recommender():

    if st.button(
        "← Back to Home",
        key="back_ai"
    ):

        st.session_state.page = "home"
        st.rerun()

    st.html(
        """
        <div class="page-header">

            <div class="page-title">
                🤖 AI-Powered Project Library Recommender
            </div>

            <div class="page-description">
                Enter your project idea and Gemini AI will
                recommend the libraries, frameworks, APIs,
                technology stack, installation commands,
                and implementation steps required to build it.
            </div>

        </div>
        """
    )

    if not GEMINI_API_KEY:

        st.warning(
            "Gemini API key is not configured."
        )

        st.code(
            "GEMINI_API_KEY=YOUR_API_KEY",
            language="text"
        )

    # --------------------------------------------------------
    # PROJECT IDEA
    # --------------------------------------------------------

    st.markdown(
        "### 💡 Enter Your Project Idea"
    )

    project_idea = st.text_area(
        "Describe your project",
        placeholder=(
            "Example: Build an AI-powered student attendance "
            "system using face recognition and a dashboard."
        ),
        height=160,
        label_visibility="collapsed"
    )

    st.caption(
        "Tip: Describe what your project should do, "
        "who will use it, and its important features."
    )

    # --------------------------------------------------------
    # EXAMPLES
    # --------------------------------------------------------

    with st.expander(
        "💡 Example Project Ideas"
    ):

        example1 = st.button(
            "AI Resume Analyzer",
            key="example_resume"
        )

        example2 = st.button(
            "Student Attendance System",
            key="example_attendance"
        )

        example3 = st.button(
            "Hospital Queue Management",
            key="example_hospital"
        )

        if example1:

            project_idea = (
                "Build an AI-powered resume analyzer "
                "that accepts PDF resumes, extracts skills, "
                "identifies missing skills, and provides "
                "career recommendations."
            )

        if example2:

            project_idea = (
                "Build a student attendance management "
                "system with student registration, attendance "
                "tracking, reports, and an admin dashboard."
            )

        if example3:

            project_idea = (
                "Build a hospital queue management system "
                "where patients can book tokens, track their "
                "queue position, and receive estimated waiting times."
            )

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    if st.button(
        "✨ Analyze Project & Recommend Libraries",
        type="primary",
        key="generate_recommendations"
    ):

        if not project_idea.strip():

            st.warning(
                "Please enter a project idea first."
            )

        elif not GEMINI_API_KEY:

            st.error(
                "Please configure GEMINI_API_KEY."
            )

        else:

            with st.spinner(
                "🤖 Gemini is analyzing your project..."
            ):

                result = recommend_libraries(
                    project_idea
                )

            if result:

                st.success(
                    "AI recommendations generated successfully!"
                )

                # ------------------------------------------------
                # SUMMARY
                # ------------------------------------------------

                st.markdown(
                    "## 📌 Project Summary"
                )

                st.html(
                    f"""
                    <div class="result-card">

                        <div class="result-title">
                            Project Overview
                        </div>

                        <div class="result-text">
                            {html.escape(
                                result.get(
                                    "project_summary",
                                    "No summary available."
                                )
                            )}
                        </div>

                    </div>
                    """
                )

                # ------------------------------------------------
                # TECHNOLOGY STACK
                # ------------------------------------------------

                st.markdown(
                    "## 🧩 Recommended Technology Stack"
                )

                stack = result.get(
                    "technology_stack",
                    []
                )

                if stack:

                    cols = st.columns(
                        min(len(stack), 4)
                    )

                    for index, technology in enumerate(
                        stack
                    ):

                        with cols[
                            index % len(cols)
                        ]:

                            st.html(
                                f"""
                                <span class="tag">
                                    {html.escape(
                                        str(technology)
                                    )}
                                </span>
                                """
                            )

                # ------------------------------------------------
                # LIBRARIES
                # ------------------------------------------------

                st.markdown(
                    "## 📚 Recommended Libraries & Tools"
                )

                libraries = result.get(
                    "recommended_libraries",
                    []
                )

                for index, library in enumerate(
                    libraries,
                    start=1
                ):

                    name = library.get(
                        "name",
                        "Unknown"
                    )

                    purpose = library.get(
                        "purpose",
                        "No purpose provided."
                    )

                    installation = library.get(
                        "installation",
                        "Not provided."
                    )

                    usage = library.get(
                        "usage",
                        "Not provided."
                    )

                    with st.expander(
                        f"{index}. {name}"
                    ):

                        st.markdown(
                            "### 🎯 Purpose"
                        )

                        st.write(
                            purpose
                        )

                        st.markdown(
                            "### 📦 Installation"
                        )

                        st.code(
                            installation,
                            language="bash"
                        )

                        st.markdown(
                            "### 🛠️ Usage"
                        )

                        st.write(
                            usage
                        )

                # ------------------------------------------------
                # IMPLEMENTATION STEPS
                # ------------------------------------------------

                st.markdown(
                    "## 🚀 Implementation Steps"
                )

                steps = result.get(
                    "implementation_steps",
                    []
                )

                for index, step in enumerate(
                    steps,
                    start=1
                ):

                    st.markdown(
                        f"**Step {index}:** {step}"
                    )

                # ------------------------------------------------
                # OPTIONAL
                # ------------------------------------------------

                optional = result.get(
                    "optional_libraries",
                    []
                )

                if optional:

                    st.markdown(
                        "## 🔧 Optional Libraries"
                    )

                    for library in optional:

                        name = library.get(
                            "name",
                            "Unknown"
                        )

                        purpose = library.get(
                            "purpose",
                            "No description available."
                        )

                        st.html(
                            f"""
                            <div class="result-card">

                                <div class="result-title">
                                    {html.escape(
                                        str(name)
                                    )}
                                </div>

                                <div class="result-text">
                                    {html.escape(
                                        str(purpose)
                                    )}
                                </div>

                            </div>
                            """
                        )

                # ------------------------------------------------
                # DOWNLOAD
                # ------------------------------------------------

                st.markdown(
                    "## ⬇️ Download Recommendation"
                )

                json_data = json.dumps(
                    result,
                    indent=4
                )

                st.download_button(
                    label="Download AI Recommendation",
                    data=json_data,
                    file_name=(
                        "project_library_recommendation.json"
                    ),
                    mime="application/json"
                )


# ============================================================
# ABOUT PAGE
# ============================================================

def show_about():

    if st.button(
        "← Back to Home",
        key="back_about"
    ):

        st.session_state.page = "home"
        st.rerun()

    st.html(
        """
        <div class="page-header">

            <div class="page-title">
                ℹ️ About Streamlit Skill Gap Detector
            </div>

            <div class="page-description">
                A student-focused application that combines
                AI-generated assessments, learning analytics,
                skill-gap detection, and project technology
                recommendations.
            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # OBJECTIVE
    # --------------------------------------------------------

    st.markdown(
        "## 🎯 Project Objective"
    )

    st.write(
        """
        The Streamlit Skill Gap Detector helps students
        understand their strengths and weaknesses from
        their own study material.

        Students upload a PDF containing their learning
        material. AI analyzes the material and generates
        a personalized MCQ assessment.

        After completing the assessment, the application
        analyzes performance at question, topic, and
        chapter levels and recommends areas for revision.
        """
    )

    # --------------------------------------------------------
    # AI PROJECT RECOMMENDER
    # --------------------------------------------------------

    st.markdown(
        "## 🤖 AI-Powered Project Library Recommender"
    )

    st.write(
        """
        The application also provides an AI-powered project
        recommendation feature.

        Students can enter a project idea and Gemini AI
        recommends suitable libraries, frameworks, APIs,
        databases, installation commands, and implementation
        steps.
        """
    )

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    st.markdown(
        "## ✨ Key Features"
    )

    features = [
        "PDF study material upload",
        "AI-generated MCQ assessment",
        "Configurable number of questions",
        "Configurable assessment difficulty",
        "Question-wise performance analysis",
        "Topic-wise performance analysis",
        "Chapter-wise performance analysis",
        "Chapter × topic performance heatmap",
        "Weak concept identification",
        "Strong concept identification",
        "Revision recommendations",
        "Detailed answer explanations",
        "Downloadable skill-gap report",
        "AI-powered project analysis",
        "Library and framework recommendations",
        "Installation commands",
        "Implementation guidance"
    ]

    for feature in features:

        st.markdown(
            f"✅ {feature}"
        )

    # --------------------------------------------------------
    # TECHNOLOGY STACK
    # --------------------------------------------------------

    st.markdown(
        "## 🛠️ Technology Stack"
    )

    technologies = [
        "Python",
        "Streamlit",
        "Pandas",
        "Plotly",
        "PyPDF",
        "Google Gemini API",
        "google-genai",
        "python-dotenv"
    ]

    for technology in technologies:

        st.html(
            f"""
            <span class="tag">
                {html.escape(technology)}
            </span>
            """
        )

    # --------------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------------

    st.markdown(
        "## 🔄 Application Workflow"
    )

    st.markdown(
        """
        **1. Upload Study Material**

        The student uploads a PDF containing study material.

        **2. Extract Learning Content**

        The application extracts readable text from the PDF.

        **3. Generate Assessment**

        Gemini analyzes the material and generates MCQs
        mapped to chapters, topics, and difficulty levels.

        **4. Student Test**

        The student answers the generated questions.

        **5. Performance Analysis**

        The system calculates overall, question-wise,
        chapter-wise, and topic-wise performance.

        **6. Skill Gap Detection**

        Topics and chapters below the performance threshold
        are identified as areas requiring revision.

        **7. Revision Recommendations**

        The application highlights weak concepts and
        recommends targeted revision.

        **8. Project Technology Recommendation**

        Students can separately enter a project idea and
        receive AI-powered library and technology recommendations.
        """
    )


# ============================================================
# PAGE ROUTING
# ============================================================

if st.session_state.page == "home":

    show_home()

elif st.session_state.page == "skill_gap":

    show_skill_gap()

elif st.session_state.page == "ai":

    show_ai_recommender()

elif st.session_state.page == "about":

    show_about()


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">

        🎯 Streamlit Skill Gap Detector
        <br>

        Student Skill Analytics + AI-Powered
        Project Library Recommendations

    </div>
    """
)