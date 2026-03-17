import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq


# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")


# ======================
# DARK UI THEME
# ======================

st.markdown("""
<style>


h1,h2,h3,h4,h5,h6{
color:#0C3838;
}

p,div,span,label{
color:#0C3838;
}

.stMarkdown{
color:#0C3838;
}

.news-card{
background:#1e293b;
padding:12px;
border-radius:10px;
border-left:5px solid #0C3838;
margin-bottom:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.2);
color:#27F5E4;
}

.stButton>button{
background:#27F5E4;
color:#0f172a;
border-radius:10px;
padding:8px 20px;
border:none;
}

.stButton>button:hover{
background:#22d3ee;
}

</style>
""", unsafe_allow_html=True)


# ======================
# GROQ AI CLIENT
# ======================

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    client = None


# ======================
# AI FUNCTION
# ======================

def run_ai(prompt):

    if client is None:
        return None

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are a financial analyst."},
                {"role":"user","content":prompt}
            ]
        )
        return completion.choices[0].message.content

    except:
        return None


# ======================
# LOAD NSE STOCK LIST
# ======================

@st.cache_data
def load_nse_stocks():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    df["ticker"] = df["SYMBOL"] + ".NS"
    return df


stocks_df = load_nse_stocks()


# ======================
# FEATURE ENGINEERING
# ======================

def add_features(df):

    df = df.copy()

    df["returns"] = df["Close"].pct_change()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["returns"].rolling(20).std()
    df["momentum"] = df["Close"] - df["Close"].shift(10)

    return df.dropna()


# ======================
# SIGNAL FUNCTION
# ======================

def generate_signal(df):

    latest = df.iloc[-1]

    if latest["Close"] > latest["ma20"] > latest["ma50"]:
        return "🟢 BUY"
    elif latest["Close"] < latest["ma20"] < latest["ma50"]:
        return "🔴 SELL"
    else:
        return "🟡 HOLD"


# ======================
# MARKET METRIC
# ======================

@st.cache_data(ttl=600)
def market_metric(symbol):

    try:
        df = yf.Ticker(symbol).history(period="5d")
        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2]
        change = ((latest-prev)/prev)*100
        return round(latest,2), round(change,2)
    except:
        return None,None


# ======================
# NEWS FUNCTION
# ======================

@st.cache_data(ttl=3600)
def fetch_news(query):

    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    headlines = []
    cutoff = datetime.now() - timedelta(hours=48)

    for entry in feed.entries:
        if hasattr(entry,"published_parsed"):
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                headlines.append(entry.title)

    return headlines[:10]


# ======================
# RECOMMEND STOCKS
# ======================

def recommend_stocks(risk_level):

    sample = stocks_df["ticker"].sample(120)

    recommendations = []

    for s in sample:
        try:
            df = yf.Ticker(s).history(period="6mo")

            if len(df) < 50:
                continue

            df["returns"] = df["Close"].pct_change()
            vol = df["returns"].std()
            momentum = df["Close"].iloc[-1] - df["Close"].iloc[0]

            if risk_level == "Low" and vol < 0.015:
                recommendations.append((s, vol, momentum))

            elif risk_level == "Medium" and 0.015 <= vol < 0.03:
                recommendations.append((s, vol, momentum))

            elif risk_level == "High" and vol >= 0.03:
                recommendations.append((s, vol, momentum))

        except:
            pass

    return pd.DataFrame(
        recommendations,
        columns=["Stock","Volatility","Momentum"]
    ).head(10)


# ======================
# AI PORTFOLIO ALLOCATION
# ======================

def ai_allocate_portfolio(recs, total_amount):

    if recs.empty:
        return None

    prompt = f"""
You are a professional portfolio manager.

Allocate investment across these stocks:

{recs.to_dict(orient='records')}

Total Investment: ₹{total_amount}

Rules:
- Assign weight (%) to each stock
- Total = 100
- Diversify
- Consider volatility and momentum

Return ONLY JSON:
[{{"stock":"ABC.NS","weight":20}}]
"""

    response = run_ai(prompt)

    try:
        import json
        allocation = json.loads(response)

        df = pd.DataFrame(allocation)

        df["Investment (₹)"] = (
            df["weight"]/100 * total_amount
        ).round(0)

        return df

    except:
        return None


# ======================
# UI
# ======================

st.title("📊 AI Investment Intelligence Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
"📊 Market Overview",
"🔥 Market Movers",
"📈 Company Analysis",
"👤 User Guidance",
"🎯 Risk Advisor"
])


# ======================
# TAB 5 (NEW)
# ======================

with tab5:

    st.subheader("🎯 AI Risk-Based Investment Advisor")

    risk = st.selectbox(
        "Select Risk Level",
        ["Low","Medium","High"]
    )

    investment = st.number_input(
        "Investment Amount (₹)",
        value=10000
    )

    if st.button("Generate AI Portfolio"):

        recs = recommend_stocks(risk)

        if not recs.empty:

            st.subheader("📊 Recommended Stocks")
            st.dataframe(recs)

            portfolio = ai_allocate_portfolio(recs, investment)

            if portfolio is not None:

                st.subheader("💼 Portfolio Allocation")
                st.dataframe(portfolio)

                st.bar_chart(
                    portfolio.set_index("stock")["Investment (₹)"]
                )

                # AI explanation
                prompt = f"""
Explain this portfolio:

{portfolio.to_dict(orient='records')}

Keep it simple for investors.
"""

                st.subheader("🤖 AI Strategy")
                st.write(run_ai(prompt))

            else:
                st.error("AI allocation failed")

        else:
            st.warning("No stocks found")
