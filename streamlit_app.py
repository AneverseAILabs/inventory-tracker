import streamlit as st
import feedparser
import google.generativeai as genai
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")

SECTORS = {
    "Technology": ["TCS", "Infosys", "Wipro"],
    "Banking": ["HDFC Bank", "ICICI Bank", "SBI"],
    "Energy": ["Reliance Industries", "ONGC"],
}

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# CSS (WHITE FINTECH STYLE)
# =========================
st.markdown("""
<style>

.stApp {
    background-color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

.navbar {
    display: flex;
    justify-content: space-between;
    padding: 15px 0;
    border-bottom: 1px solid #eeeeee;
    margin-bottom: 30px;
}

.logo {
    font-size: 22px;
    font-weight: 700;
    color: #6A0DAD;
}

.company-card {
    background: #ffffff;
    padding: 25px;
    border-radius: 14px;
    border: 1px solid #eeeeee;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    margin-bottom: 25px;
    transition: 0.3s ease;
}

.company-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(106, 13, 173, 0.12);
}

.stButton>button {
    background-color: #6A0DAD;
    color: white;
    border-radius: 8px;
    padding: 10px 25px;
    font-weight: 600;
    border: none;
}

.stButton>button:hover {
    background-color: #8A2BE2;
    color: white;
}

.kpi-card {
    background: #ffffff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #eeeeee;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    text-align: center;
}

.kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: #6A0DAD;
}

.kpi-label {
    font-size: 14px;
    color: #777;
}

</style>
""", unsafe_allow_html=True)

# =========================
# NAVBAR
# =========================
st.markdown("""
<div class="navbar">
    <div class="logo">AI Investo</div>
    <div>Dashboard | Insights | Sectors</div>
</div>
""", unsafe_allow_html=True)

st.title("📊 Investment Intelligence Dashboard")

sector = st.selectbox("Select Sector", list(SECTORS.keys()))
companies = SECTORS[sector]

# =========================
# FUNCTIONS
# =========================
def fetch_recent_news(company, hours=48):
    url = f"https://news.google.com/rss/search?q={company}+stock&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    recent = []
    cutoff = datetime.now() - timedelta(hours=hours)

    for entry in feed.entries:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                recent.append(entry.title)

    return recent


def extract_investor_insight(company, headlines):

    text = "\n".join(headlines)

    prompt = f"""
    Analyze these headlines for {company}.

    Return ONLY JSON:
    sentiment,
    growth_signals,
    risk_signals,
    forward_guidance,
    investment_summary,
    confidence_score (1-10)

    Headlines:
    {text}
    """

    response = model.generate_content(prompt)
    return response.text


# =========================
# KPI PLACEHOLDER
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-value">Live</div>
        <div class="kpi-label">Market Mode</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-value">48h</div>
        <div class="kpi-label">News Window</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-value">AI</div>
        <div class="kpi-label">Insight Engine</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================
# MAIN ACTION
# =========================
if st.button("Get Latest Investor News"):

    for company in companies:

        news = fetch_recent_news(company)

        if not news:
            continue

        st.markdown('<div class="company-card">', unsafe_allow_html=True)
        st.subheader(company)

        for headline in news:
            st.write(f"- {headline}")

        with st.spinner(f"Analyzing {company}..."):
            insight = extract_investor_insight(company, news)

        st.code(insight, language="json")
        st.markdown('</div>', unsafe_allow_html=True)
