# =========================================================
# AI INVESTO — OpenAI Only Investment Intelligence Dashboard
# =========================================================

import streamlit as st
import feedparser
from openai import OpenAI
import os
import json
import urllib.parse
from datetime import datetime, timedelta

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="AI Investo", layout="wide")

# =========================================================
# OPENAI CLIENT
# =========================================================
client = OpenAI(
    api_key=st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
)

# =========================================================
# SECTOR DATA
# =========================================================
SECTORS = {
    "Technology": ["TCS", "Infosys", "Wipro"],
    "Banking": ["HDFC Bank", "ICICI Bank", "SBI"],
    "Energy": ["Reliance Industries", "ONGC"],
}

# =========================================================
# STYLING
# =========================================================
st.markdown("""
<style>
.stApp { background-color: #ffffff; font-family: 'Segoe UI', sans-serif; }
.navbar {
    display:flex; justify-content:space-between;
    padding:15px 0; border-bottom:1px solid #eeeeee;
    margin-bottom:30px;
}
.logo { font-size:22px; font-weight:700; color:#6A0DAD; }
.company-card {
    background:#ffffff; padding:25px;
    border-radius:14px; border:1px solid #eeeeee;
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
    margin-bottom:25px;
}
.stButton>button {
    background-color:#6A0DAD; color:white;
    border-radius:8px; padding:10px 25px;
    font-weight:600; border:none;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# NAVBAR
# =========================================================
st.markdown("""
<div class="navbar">
    <div class="logo">AI Investo</div>
    <div>Dashboard | Insights | Sectors</div>
</div>
""", unsafe_allow_html=True)

st.title("📊 Investment Intelligence Dashboard")

# =========================================================
# SELECTION
# =========================================================
sector = st.selectbox("Select Sector", list(SECTORS.keys()))
companies = SECTORS[sector]

# =========================================================
# FUNCTIONS
# =========================================================

def fetch_recent_news(company, hours=48):
    query = urllib.parse.quote(f"{company} stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    recent = []
    cutoff = datetime.now() - timedelta(hours=hours)

    for entry in feed.entries:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                recent.append(entry.title)

    return recent


def openai_structured_analysis(company, headlines):

    text = "\n".join(headlines[:15])

    prompt = f"""
You are a senior equity research analyst.

Analyze the following recent headlines about {company}.

Return STRICT JSON in this format:

{{
    "sentiment": "Bullish | Bearish | Neutral",
    "growth_score": number_1_to_10,
    "risk_score": number_1_to_10,
    "confidence_score": number_1_to_10,
    "key_growth_drivers": ["point1","point2"],
    "major_risks": ["point1","point2"],
    "forward_outlook": "3-4 lines",
    "final_investment_verdict": "Buy | Watch | Caution"
}}

Headlines:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["📰 Latest News", "🤖 AI Intelligence"])

# =========================================================
# MAIN ACTION
# =========================================================
if st.button("Get Latest Investor News"):

    for company in companies:

        news = fetch_recent_news(company)

        if not news:
            continue

        # =========================
        # TAB 1 — NEWS
        # =========================
        with tab1:
            st.markdown('<div class="company-card">', unsafe_allow_html=True)
            st.subheader(company)

            for headline in news:
                st.write(f"- {headline}")

            st.markdown('</div>', unsafe_allow_html=True)

        # =========================
        # TAB 2 — AI ANALYSIS
        # =========================
        with tab2:
            st.markdown('<div class="company-card">', unsafe_allow_html=True)
            st.subheader(f"{company} – AI Insight")

            with st.spinner(f"Analyzing {company}..."):
                ai_output = openai_structured_analysis(company, news)

            try:
                parsed = json.loads(ai_output)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Sentiment", parsed["sentiment"])
                with col2:
                    st.metric("Growth Score", parsed["growth_score"])
                with col3:
                    st.metric("Risk Score", parsed["risk_score"])

                st.markdown("### 📈 Growth Drivers")
                for g in parsed["key_growth_drivers"]:
                    st.write(f"- {g}")

                st.markdown("### ⚠ Major Risks")
                for r in parsed["major_risks"]:
                    st.write(f"- {r}")

                st.markdown("### 🔮 Outlook")
                st.info(parsed["forward_outlook"])

                st.markdown("### 🎯 Verdict")
                st.success(parsed["final_investment_verdict"])

                st.markdown("### 🔍 Confidence Score")
                st.progress(parsed["confidence_score"] / 10)

            except Exception:
                st.warning("AI response format issue.")
                st.code(ai_output, language="json")

            st.markdown('</div>', unsafe_allow_html=True)
