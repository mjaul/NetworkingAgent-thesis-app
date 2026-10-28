import streamlit as st
import os
import csv
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

# ==========================================
# 1. INITIALIZATION & STYLING
# ==========================================
load_dotenv()

st.set_page_config(page_title="Computer Networking Exam", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main-header {
        color: #1f497d;
        font-family: 'Arial', sans-serif;
        text-align: center;
        border-bottom: 2px solid #1f497d;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f497d;
        color: white;
        font-weight: bold;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #132e51;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MULTI-AGENT ARCHITECTURE
# ==========================================
class GradeReport(BaseModel):
    score: int = Field(description="The student's final score out of 100")
    strengths: list[str] = Field(description="Networking concepts understood well")
    weaknesses: list[str] = Field(description="Areas where the student struggled")
    justification: str = Field(description="Explanation of the final grade")

@st.cache_resource
def setup_agents_v2():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # ... (keep your existing prompt code here)
    
    # UPDATED: The prompt is now strictly forbidden from giving feedback or scores during the exam.
    examiner_prompt = (
       
        "You are an AI examiner agent conducting a conversational assessment in Computer Networking. "
        "Your goal is to evaluate the student through a natural, flowing academic discussion rather than a rigid interrogation. "
        "EXAM STRUCTURE & RULES: "
        "1. Conversational Tone: Acknowledge the student's previous input naturally. Maintain a supportive discussion flow. Do NOT reveal if their answer was entirely correct or incorrect, and NEVER output a score. "
        "2. Question Variety: Prioritize open-ended discussion questions where the student must explain concepts in their own words (e.g., 'Can you explain how...?' or 'Why do we use...?'). "
        "   - Use Multiple Choice or True/False formats rarely (only about 20% of the time) to quickly check specific terminology or facts. "
        "3. Adaptive Difficulty: Silently evaluate their previous answer. If they show strong understanding, steer the conversation toward harder concepts. If they struggle, guide the discussion back to fundamental principles. "
        "4. Output: Ask ONLY ONE question or present ONLY ONE scenario at a time. Wait for the student to reply."
    
    )    
    evaluator_prompt = (
        "You are an objective academic evaluator. Review the following exam transcript. "
        "Grade the student's understanding based ONLY on this transcript. "
        "Output the exact structured format requested."
    )
    
    examiner_template = ChatPromptTemplate.from_messages([
        ("system", examiner_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{user_input}")
    ])
    
    evaluator_template = ChatPromptTemplate.from_messages([
        ("system", evaluator_prompt),
        ("human", "Here is the exam transcript:\n{transcript}")
    ])
    
    examiner = examiner_template | llm
    evaluator = evaluator_template | llm.with_structured_output(GradeReport)
    
    return examiner, evaluator

examiner_agent, evaluator_agent = setup_agents_v2()
# ==========================================
# 3. SESSION STATE (MEMORY, ROLES & COUNTERS)
# ==========================================
if "role" not in st.session_state:
    st.session_state.role = None
if "student_first" not in st.session_state:
    st.session_state.student_first = ""
if "student_last" not in st.session_state:
    st.session_state.student_last = ""
if "student_email" not in st.session_state:
    st.session_state.student_email = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""
if "exam_finished" not in st.session_state:
    st.session_state.exam_finished = False
    
# NEW: The counter memory variable starts at question 1
if "question_count" not in st.session_state:
    st.session_state.question_count = 1

# ==========================================
# 4. PORTAL LOGIN (ROLE SELECTOR)
# ==========================================
if st.session_state.role is None:
    st.markdown("<h1 class='main-header'>🎓 Computer Networks Portal</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        role_choice = st.radio("Select Portal Access:", ["Student", "Admin"], horizontal=True)
        st.divider()
        
        if role_choice == "Student":
            with st.form("registration_form"):
                st.write("**Student Registration**")
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                email = st.text_input("University Email")
                submitted = st.form_submit_button("Start Exam")
                
                if submitted:
                    if first_name and last_name and email:
                        st.session_state.student_first = first_name
                        st.session_state.student_last = last_name
                        st.session_state.student_email = email
                        st.session_state.role = "Student"
                        st.rerun()
                    else:
                        st.error("Please fill out all credential fields to begin.")
                        
        elif role_choice == "Admin":
            with st.form("admin_login"):
                st.write("**Administrator Access**")
                password = st.text_input("Password", type="password")
                prof_submitted = st.form_submit_button("Access Dashboard")
                
               # Assuming this is inside your login section where user_role is selected
if user_role == "Admin":
    # 1. Create a form for the login
    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        # 2. Define the admin_submitted variable here
        admin_submitted = st.form_submit_button("Login")
        
        # 3. Check it immediately inside the same block
        if admin_submitted:
            if password == "tuke_admin":
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Incorrect password.")

# ==========================================
# 5. Admin DASHBOARD VIEW
# ==========================================
elif st.session_state.role == "Admin":
    st.markdown("<h1 class='main-header'>📊 Administration Dashboard</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.info("**Logged in as:** System Administrator")
        if st.button("Log Out"):
            st.session_state.role = None
            st.rerun()
            
    csv_file = "thesis_exam_results.csv"
    if os.path.isfile(csv_file):
        df = pd.read_csv(csv_file)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Exams Taken", len(df))
        with col2:
            if "Score" in df.columns:
                avg_score = df["Score"].mean()
                st.metric("Average Class Score", f"{avg_score:.1f}/100")
                
        st.divider()
        st.subheader("Student Database")
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        if "Score" in df.columns:
            st.subheader("Score Distribution")
            st.bar_chart(df["Score"])
    else:
        st.info("No exam records found yet.")

# ==========================================
# 6. STUDENT EXAM VIEW
# ==========================================
elif st.session_state.role == "Student":
    with st.sidebar:
        st.header("⚙️ Exam Controls")
        st.info(f"**Student:**\n\n{st.session_state.student_first} {st.session_state.student_last}\n\n*{st.session_state.student_email}*")
        st.divider()
        st.info("You can quit early by clicking below, otherwise the exam will automatically finish after 10 questions.")
        
        if st.button("Submit Exam Early"):
            st.session_state.exam_finished = True
            st.rerun()

    st.markdown("<h1 class='main-header'>🎓 Computer Networks Oral Exam</h1>", unsafe_allow_html=True)
    
    if not st.session_state.exam_finished:
        st.write(f"Welcome, **{st.session_state.student_first}**. This exam consists of exactly 10 adaptive questions.")
        
        # NEW: Visual Progress Bar
        st.progress(st.session_state.question_count / 10)
        st.caption(f"Question {st.session_state.question_count} of 10")
        
        # NEW: Automatically generates the first question without the user typing anything
        if not st.session_state.chat_history:
            with st.spinner("Generating first question..."):
                response = examiner_agent.invoke({
                    "user_input": "Begin the exam by asking the first question directly.",
                    "chat_history": []
                })
                st.session_state.chat_history.append(AIMessage(content=response.content))
                st.session_state.transcript_text += f"Agent: {response.content}\n\n"
        
        for msg in st.session_state.chat_history:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.write(msg.content)

        user_input = st.chat_input("Type your answer here...")
        
        if user_input:
            with st.chat_message("user"):
                st.write(user_input)
                
            st.session_state.chat_history.append(HumanMessage(content=user_input))
            st.session_state.transcript_text += f"Student: {user_input}\n\n"
            
            # NEW: Automated 10-Question Limit Logic
            if st.session_state.question_count >= 10:
                st.session_state.exam_finished = True
                st.rerun()
            else:
                st.session_state.question_count += 1
                
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    for chunk in examiner_agent.stream({
                        "user_input": user_input,
                        "chat_history": st.session_state.chat_history
                    }):
                        full_response += chunk.content
                        message_placeholder.markdown(full_response + "▌") 
                    message_placeholder.markdown(full_response)
                        
                st.session_state.chat_history.append(AIMessage(content=full_response))
                st.session_state.transcript_text += f"Agent: {full_response}\n\n"
                st.rerun()

    if st.session_state.exam_finished:
        st.divider()
        st.markdown("<h2 style='text-align: center; color: #1f497d;'>📊 Final Evaluation Report</h2>", unsafe_allow_html=True)
        
        if st.session_state.transcript_text == "":
            st.warning("No exam data to evaluate. Please refresh the page and talk to the agent first.")
        else:
            with st.spinner("Evaluator agent is analyzing the transcript..."):
                grade_report = evaluator_agent.invoke({"transcript": st.session_state.transcript_text})
                
                st.metric(label="Final Score", value=f"{grade_report.score}/100")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**✅ Strengths:**")
                    for strength in grade_report.strengths:
                        st.write(f"- {strength}")
                with col2:
                    st.write("**🎯 Areas for Improvement:**")
                    for weakness in grade_report.weaknesses:
                        st.write(f"- {weakness}")
                        
                st.write("**📝 Academic Justification:**")
                st.info(grade_report.justification)
                
                csv_file = "thesis_exam_results.csv"
                file_exists = os.path.isfile(csv_file)
                with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Timestamp", "First Name", "Last Name", "Email", "Score", "Strengths", "Weaknesses", "Justification"])
                    strengths_str = " | ".join(grade_report.strengths)
                    weaknesses_str = " | ".join(grade_report.weaknesses)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        st.session_state.student_first,
                        st.session_state.student_last,
                        st.session_state.student_email,
                        grade_report.score,
                        strengths_str,
                        weaknesses_str,
                        grade_report.justification
                    ])
                    
                st.success("✅ You have successfully submitted the exam.")
