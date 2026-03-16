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
# UI STYLE
# ======================

st.markdown("""
<style>

.stApp{
background:#f4f7fb;
}

h1{
color:#2e8b57;
}

h2,h3,h4{
color:#6a5acd;
}

.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid #6a5acd;
margin-bottom:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
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
        return "AI not configured"

    try:

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are a financial market analyst."},
                {"role":"user","content":prompt}
            ]
        )

        return completion.choices[0].message.content

    except:
        return "AI service unavailable"


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
# TITLE
# ======================

st.title("📊 AI Investment Intelligence Dashboard")


# ======================
# TABS
# ======================

tab1, tab2, tab3, tab4 = st.tabs([
"📊 Market Overview",
"🔥 Market Movers",
"📈 Company Analysis",
"👤 User Guidance"
])


# ======================
# TAB 1 MARKET OVERVIEW
# ======================

with tab1:

    st.subheader("Indian Market Indices")

    indices = {
        "NIFTY 50":"^NSEI",
        "SENSEX":"^BSESN",
        "BANK NIFTY":"^NSEBANK",
        "NIFTY IT":"^CNXIT",
        "NIFTY AUTO":"^CNXAUTO",
        "NIFTY PHARMA":"^CNXPHARMA"
    }

    cols = st.columns(3)

    i = 0

    for name,symbol in indices.items():

        p,c = market_metric(symbol)

        with cols[i%3]:

            st.metric(name,p,str(c)+"%")

        i+=1


    st.subheader("🌍 Global Markets")

    global_markets = {

        "S&P 500":"^GSPC",
        "NASDAQ":"^IXIC",
        "DOW JONES":"^DJI",
        "NIKKEI":"^N225",
        "HANG SENG":"^HSI"
    }

    cols = st.columns(3)

    i=0

    for name,symbol in global_markets.items():

        p,c = market_metric(symbol)

        with cols[i%3]:

            st.metric(name,p,str(c)+"%")

        i+=1


    st.subheader("📰 Market News")

    news = fetch_news("Indian stock market")

    for n in news:

        st.markdown(f"""
        <div class="news-card">
        {n}
        </div>
        """, unsafe_allow_html=True)


    st.subheader("🧠 AI Market Sentiment")

    if news:

        text = "\n".join(news)

        prompt = f"""
Analyze Indian stock market sentiment based on news:

{text}

Return:
Market sentiment
Key drivers
Short term outlook
"""

        result = run_ai(prompt)

        st.write(result)



# ======================
# TAB 2 MARKET MOVERS
# ======================

with tab2:

    st.subheader("Top Market Movers")

    sample = stocks_df["ticker"].head(80)

    data = []

    for s in sample:

        try:

            df = yf.Ticker(s).history(period="2d")

            latest = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]

            change = ((latest-prev)/prev)*100

            data.append((s,change))

        except:
            pass


    move_df = pd.DataFrame(data,columns=["Stock","Change %"])


    gainers = move_df.sort_values("Change %",ascending=False).head(10)

    losers = move_df.sort_values("Change %").head(10)


    col1,col2 = st.columns(2)

    with col1:
        st.write("🚀 Top Gainers")
        st.dataframe(gainers,width=500)

    with col2:
        st.write("🔻 Top Losers")
        st.dataframe(losers,width=500)



# ======================
# TAB 3 COMPANY ANALYSIS
# ======================

with tab3:

    st.subheader("Analyze Company")

    company = st.selectbox(
        "Select Company",
        stocks_df["SYMBOL"].sort_values()
    )

    ticker = company + ".NS"


    if st.button("Analyze"):

        df = yf.Ticker(ticker).history(period="10y")

        if not df.empty:

            st.line_chart(df["Close"])

        news = fetch_news(company)

        st.subheader("Company News")

        for n in news:
            st.write("•", n)


        prompt = f"""
Analyze investment outlook for {company}.

Return:
Sentiment
Growth signals
Risk factors
Investment summary
Confidence score
"""

        result = run_ai(prompt)

        st.subheader("AI Investment Insight")

        st.write(result)



# ======================
# TAB 4 USER GUIDANCE
# ======================

with tab4:

    st.subheader("How to Use This Dashboard")

    st.markdown("""

### Market Overview
Shows major Indian and global indices.

### Market Movers
Displays top gainers and losers in the market.

### Company Analysis
Select any NSE company (1800+ available) to analyze:

• Historical stock chart  
• Latest company news  
• AI investment insights  

---

### Understanding AI Signals

| Signal | Meaning |
|------|------|
Buy | Positive outlook |
Hold | Stable but limited upside |
Sell | Risky or negative outlook |

---

### Important Disclaimer

This tool is for **educational purposes only**.

Always do your own research before investing.

""")


# ======================
# FOOTER
# ======================

st.markdown("""
<hr>

<div style="text-align:center;color:gray">

AI Investment Dashboard<br>
Developed by Ankit

</div>
""", unsafe_allow_html=True)
