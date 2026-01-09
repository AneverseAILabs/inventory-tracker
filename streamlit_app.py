import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# -------- Load API Key --------
load_dotenv()
key='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'
client = OpenAI(api_key=key)

# -------- Page Config --------
st.set_page_config(page_title="Mutual Fund News & Insights", layout="wide")

# -------- Styles --------
st.markdown("""
<style>
.title {
    background: linear-gradient(90deg, #00897b, #26a69a);
    color: white;
    padding: 18px;
    border-radius: 12px;
    font-size: 30px;
    text-align: center;
    font-weight: bold;
}
.teal-box {
    background-color: #e0f2f1;
    color: #00695c;
    padding: 16px;
    border-left: 6px solid #00897b;
    border-radius: 10px;
    font-size: 16px;
    line-height: 1.7;
    white-space: pre-wrap;
}
</style>

<div class="title">💹 Mutual Fund News & AI Insights</div>
""", unsafe_allow_html=True)

# -------- Helper --------
def ask_openai(prompt, max_tokens=500):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

# -------- UI --------
st.markdown("### 📌 Select Mutual Fund Category")

category = st.selectbox(
    "Fund Type",
    [
        "Equity Mutual Funds",
        "Debt Mutual Funds",
        "Hybrid Mutual Funds",
        "Index Funds",
        "ELSS (Tax Saving)",
        "Sectoral / Thematic Funds"
    ]
)

risk_profile = st.selectbox(
    "Investor Risk Profile",
    ["Conservative", "Moderate", "Aggressive"]
)

if st.button("🧠 Get Latest Mutual Fund News & Insights"):
    with st.spinner("Analyzing market trends using OpenAI..."):

        prompt = f"""
        Act as a senior mutual fund analyst in India.

        Provide:
        1. Latest news & trends for {category}
        2. Market outlook (3–6 months)
        3. Impact of interest rates, inflation & global events
        4. Risks to watch
        5. Advice for a {risk_profile} investor

        Keep it simple, factual, and investor-friendly.
        """

        result = ask_openai(prompt)

    st.success("✅ Analysis Ready")

    st.markdown(
        f'<div class="teal-box">{result}</div>',
        unsafe_allow_html=True
    )

    st.download_button(
        "📥 Download Insight Report",
        data=result,
        file_name="Mutual_Fund_AI_Insights.txt"
    )
