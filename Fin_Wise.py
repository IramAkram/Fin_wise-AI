from __future__ import annotations
import os
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="FinWise AI - Personal Finance Assistant",
    page_icon="💰",
    layout="wide"
)

# --- HIGH-CONTRAST SKY BLUE & RED THEME CSS STYLING ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Sky Blue & Red (Light)"

def apply_theme():
    if st.session_state.theme_mode == "Sky Blue & Red (Light)":
        return """
            <style>
            .stApp { background-color: #f0f8ff; color: #0d3b66; }
            h1, h2, h3, h4, h5, h6, p, span, label { color: #0d3b66 !important; }
            .stButton>button {
                background-color: #0077b6; color: white; border-radius: 8px; font-weight: 600; border: none; width: 100%;
            }
            .stButton>button:hover { background-color: #d90429; color: white; }
            [data-testid="stSidebar"] { background-color: #e2eafc; border-right: 2px solid #ffb703; }
            /* Fixing text visibility for uploaders and widgets */
            .stFileUploader label, .stSelectbox label, .stTextInput label, .stNumberInput label {
                color: #0d3b66 !important;
                font-weight: bold;
            }
            </style>
        """
    else:
        return """
            <style>
            .stApp { background-color: #121212; color: #e0e0e0; }
            h1, h2, h3, h4, h5, h6, p, span, label { color: #ffffff !important; }
            .stButton>button {
                background-color: #0077b6; color: white; border-radius: 8px; font-weight: 600; border: none; width: 100%;
            }
            .stButton>button:hover { background-color: #d90429; color: white; }
            [data-testid="stSidebar"] { background-color: #1e1e1e; border-right: 2px solid #d90429; }
            .stFileUploader label, .stSelectbox label, .stTextInput label, .stNumberInput label {
                color: #ffffff !important;
                font-weight: bold;
            }
            </style>
        """

st.markdown(apply_theme(), unsafe_allow_html=True)

# Session State Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

def calculate_finances(income: float, expenses_dict: dict, savings: float) -> dict:
    total_expenses = sum(expenses_dict.values())
    remaining_income = income - total_expenses
    
    if income > 0:
        savings_ratio = (savings / income) * 100
        expense_ratio = (total_expenses / income) * 100
    else:
        savings_ratio = 0.0
        expense_ratio = 0.0
        
    base_score = 50
    score_adjustment = (savings_ratio * 0.5) - ((expense_ratio - 50) * 0.3)
    preliminary_score = max(0, min(100, int(base_score + score_adjustment)))
    
    return {
        "total_expenses": round(total_expenses, 2),
        "remaining_income": round(remaining_income, 2),
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
        "preliminary_score": preliminary_score
    }

def generate_pdf_report(data_dict: dict, calc_data: dict, currency: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="FinWise AI - Financial Analysis Report", ln=True, align="center")
    pdf.ln(5)
    
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(200, 8, txt="DETERMINISTIC METRICS:", ln=True)
    pdf.set_font("Arial", size=10)
    for k, v in calc_data.items():
        pdf.cell(200, 6, txt=f"- {k.upper()}: {v} {currency}", ln=True)
    pdf.ln(5)
    
    for key, value in data_dict.items():
        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(200, 8, txt=f"{key.upper()}:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, txt=str(value))
        pdf.ln(3)
        
    return pdf.output(dest='S').encode('latin1')

def main():
    # --- STEP 1: API Key Entry Screen ---
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image("https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    with col2:
        st.title("💰 FinWise AI - Authentication")
        st.markdown("<p style='color: #d90429; font-weight: 600;'>AI-Powered Personal Financial Analysis & Smart Budget Assistant.</p>", unsafe_allow_html=True)
    with col3:
        st.image("https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=300&q=80", use_container_width=True)
        
    entered_key = st.text_input("Enter your OpenAI API Key to proceed:", type="password", value=st.session_state.api_key)
    
    if st.button("Login / Start App"):
        if entered_key.strip():
            st.session_state.api_key = entered_key.strip()
            st.rerun()
        else:
            st.error("⚠️ Please enter a valid OpenAI API key first!")
            
    if not st.session_state.api_key:
        st.info("💡 Please enter your OpenAI API key above and click the button to start the application.")
        return

    # --- STEP 2: Main Project Dashboard ---
    client = OpenAI(api_key=st.session_state.api_key)

    with st.sidebar:
        st.image("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=400&q=80", use_container_width=True)
        st.title("💰 FinWise AI Dashboard")
        st.markdown("---")
        st.error("⚠️ **EDUCATIONAL DISCLAIMER:**\n\nThis app is an educational prototype. It does not provide certified financial advice.")
        st.markdown("---")
        st.subheader("⚙️ Settings & Controls")
        
        selected_theme = st.selectbox("Theme Mode", ["Sky Blue & Red (Light)", "Dark Mode"])
        if selected_theme != st.session_state.theme_mode:
            st.session_state.theme_mode = selected_theme
            st.rerun()
            
        selected_model = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-4o"])
        currency = st.selectbox("Currency", ["USD ($)", "PKR (Rs)", "EUR (€)", "GBP (£)"])
        
        st.markdown("---")
        if st.button("Logout / Change API Key"):
            st.session_state.api_key = ""
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 📊 Analytics Overview")
        if st.session_state.analytics_data:
            df_a = pd.DataFrame(st.session_state.analytics_data)
            st.metric("Total Analyses", len(df_a))
        else:
            st.info("No analyses recorded yet.")

    st.image("https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    st.title("Personal Financial Analysis & Smart Budget Assistant")
    st.write("Enter your monthly income, expenses, and savings below to receive deterministic calculations and AI-driven insights.")

    tab_form, tab_csv, tab_history, tab_analytics = st.tabs([
        "📝 Budget Form", "📁 CSV Upload (Bonus)", "📜 Session History", "📊 Analytics Dashboard"
    ])

    with tab_form:
        with st.form("fin_form"):
            col1, col2 = st.columns(2)
            with col1:
                income = st.number_input("Monthly Income", min_value=0.0, value=5000.0, step=100.0)
                housing = st.number_input("Housing / Rent", min_value=0.0, value=1500.0, step=50.0)
                food = st.number_input("Food", min_value=0.0, value=600.0, step=50.0)
                transport = st.number_input("Transportation", min_value=0.0, value=300.0, step=50.0)
                utilities = st.number_input("Utilities", min_value=0.0, value=200.0, step=50.0)
            with col2:
                education = st.number_input("Education", min_value=0.0, value=100.0, step=50.0)
                healthcare = st.number_input("Healthcare", min_value=0.0, value=150.0, step=50.0)
                entertainment = st.number_input("Entertainment", min_value=0.0, value=200.0, step=50.0)
                loan = st.number_input("Loan / Debt Repayment", min_value=0.0, value=400.0, step=50.0)
                other = st.number_input("Other Expenses", min_value=0.0, value=150.0, step=50.0)
                
            savings = st.number_input("Current Monthly Savings", min_value=0.0, value=1000.0, step=50.0)
            goal = st.selectbox("Financial Goal", ["Save Money", "Emergency Fund", "Pay Off Debt", "Vacation", "Start a Business", "Improve Budgeting"])
            
            submitted = st.form_submit_button("Run Analysis")

        if submitted:
            expenses_dict = {
                "Housing": housing, "Food": food, "Transportation": transport,
                "Utilities": utilities, "Education": education, "Healthcare": healthcare,
                "Entertainment": entertainment, "Loan/Debt": loan, "Other": other
            }
            
            calc = calculate_finances(income, expenses_dict, savings)
            
            prompt = f"""
            You are FinWise AI, an educational personal financial analysis and smart budget assistant. 
            Analyze the following client financial data and return valid JSON with exact keys:
            - "financial_summary": string summary
            - "financial_health_score": integer (0-100)
            - "spending_analysis": list of dicts with keys 'category', 'observation', 'recommendation'
            - "risk_level": string (LOW, MEDIUM, HIGH)
            - "top_priorities": list of strings
            - "budget_recommendations": list of strings
            - "savings_strategy": list of strings
            - "next_month_action_plan": list of strings

            Data:
            - Monthly Income: {income} {currency}
            - Total Expenses: {calc['total_expenses']} {currency}
            - Remaining Income: {calc['remaining_income']} {currency}
            - Current Savings: {savings} {currency}
            - Savings Ratio: {calc['savings_ratio']}%
            - Expense Ratio: {calc['expense_ratio']}%
            - Financial Goal: {goal}
            - Expense Breakdown: {str(expenses_dict)}
            
            Return ONLY raw JSON, no markdown code blocks if possible.
            """
            
            with st.spinner("Analyzing financial health via OpenAI..."):
                try:
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": "system", "content": "You are a financial budgeting assistant that outputs strictly in JSON format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                    raw_text = response.choices[0].message.content.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                        
                    parsed_data = json.loads(raw_text.strip())
                    
                    st.session_state.chat_history.append({"input": income, "output": parsed_data})
                    st.session_state.analytics_data.append({"Risk Level": parsed_data.get("risk_level", "LOW")})
                    
                    st.success("Analysis Complete!")
                    
                    st.subheader("📈 Deterministic Calculations")
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Total Expenses", f"{calc['total_expenses']} {currency}")
                    mc2.metric("Remaining Balance", f"{calc['remaining_income']} {currency}")
                    mc3.metric("Savings Ratio", f"{calc['savings_ratio']}%")
                    mc4.metric("Expense Ratio", f"{calc['expense_ratio']}%")
                    
                    st.subheader("📊 Expense Visualization (Bonus)")
                    fig, ax = plt.subplots(figsize=(6, 3))
                    sns.barplot(x=list(expenses_dict.keys()), y=list(expenses_dict.values()), ax=ax, palette="Blues_d")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                    
                    st.subheader("🤖 AI Financial Dashboard")
                    risk = parsed_data.get("risk_level", "LOW").upper()
                    if risk == "HIGH":
                        st.error(f"🚨 Risk Level: {risk} - Immediate cost-cutting advised!")
                    elif risk == "MEDIUM":
                        st.warning(f"⚠️ Risk Level: {risk} - Monitor spending patterns.")
                    else:
                        st.success(f"🟢 Risk Level: {risk} - Strong financial health.")
                        
                    st.info(f"**Summary:** {parsed_data.get('financial_summary')}")
                    
                    health_score = parsed_data.get("financial_health_score", calc["preliminary_score"])
                    st.write(f"**Financial Health Score:** {health_score} / 100")
                    st.progress(health_score / 100)
                    
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.markdown("### 📊 Spending Breakdown")
                        for item in parsed_data.get("spending_analysis", []):
                            st.write(f"- **{item.get('category')}**: {item.get('observation')} -> *Tip:* {item.get('recommendation')}")
                        st.markdown("### 🎯 Top Priorities")
                        for p in parsed_data.get("top_priorities", []):
                            st.write(f"- {p}")
                    with col_res2:
                        st.markdown("### 💡 Budget Recommendations")
                        for b in parsed_data.get("budget_recommendations", []):
                            st.write(f"- {b}")
                        st.markdown("### 💰 Savings Strategy")
                        for s in parsed_data.get("savings_strategy", []):
                            st.write(f"- {s}")
                        st.markdown("### 🚀 Next Month Action Plan")
                        for n in parsed_data.get("next_month_action_plan", []):
                            st.write(f"- {n}")

                    pdf_bytes = generate_pdf_report(parsed_data, calc, currency)
                    st.download_button(
                        label="📥 Download Financial Report as PDF (Bonus)",
                        data=pdf_bytes,
                        file_name="finwise_report.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Error during execution: {e}")

    with tab_csv:
        st.subheader("📁 CSV Expense Upload (Bonus Feature)")
        uploaded_file = st.file_uploader("Upload CSV file containing financial records", type=["csv"])
        if uploaded_file is not None:
            df_csv = pd.read_csv(uploaded_file)
            st.dataframe(df_csv)
            st.success("CSV file successfully loaded and parsed!")

    with tab_history:
        st.subheader("📜 Session History")
        if not st.session_state.chat_history:
            st.info("No session history found yet.")
        else:
            for idx, item in enumerate(st.session_state.chat_history):
                with st.expander(f"Analysis Record #{idx+1}"):
                    st.json(item["output"])

    with tab_analytics:
        st.subheader("📊 Risk Distribution Analytics")
        if st.session_state.analytics_data:
            df_an = pd.DataFrame(st.session_state.analytics_data)
            st.bar_chart(df_an["Risk Level"].value_counts())
        else:
            st.info("No analytics data available yet.")

if __name__ == "__main__":
    main()