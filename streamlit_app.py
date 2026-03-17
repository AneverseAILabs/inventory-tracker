
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
        return "AI not configured"

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
        return "AI analysis unavailable"


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
# MARKET METRIC FUNCTION
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
# AI STOCK ADVISOR
# ======================

def ai_stock_advisor(risk, amount):

    sample = stocks_df["ticker"].sample(20).tolist()

    prompt = f"""
You are a professional stock advisor.

Suggest best Indian stocks based on:

Risk level: {risk}
Investment amount: ₹{amount}

Stocks to choose from:
{sample}

Return:
1. Top 5 stocks to buy
2. Reason for each
3. Allocation suggestion (₹ split)
4. Final advice (Buy/Hold)

Keep it simple and practical.
"""

    return run_ai(prompt)
# ======================
# TITLE
# ======================

st.title("📊 AI Investment Intelligence Dashboard")


# ======================
# TABS
# ======================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
"📊 Market Overview",
"🔥 Market Movers",
"📈 Company Analysis",
"🧠 AI Advisor",
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
Analyze Indian stock market sentiment from the following news:

{text}

Return:
Market sentiment
Key drivers
Short outlook
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

        st.subheader("🤖 AI Investment Insight")

        st.write(result)




# ======================
# TAB 5 AI ADVISOR
# ======================

with tab4:

    st.subheader("🧠 AI Investment Advisor")

    st.markdown("Get AI-powered stock suggestions based on your risk profile.")

    risk = st.selectbox(
        "Select Your Risk Level",
        ["Low","Medium","High"]
    )

    amount = st.number_input(
        "Investment Amount (₹)",
        value=10000,
        step=500
    )

    if st.button("Get AI Advice"):

        with st.spinner("Analyzing market..."):

            result = ai_stock_advisor(risk, amount)

            st.subheader("📊 AI Recommendation")

            st.write(result)
# ======================
# TAB 4 USER GUIDANCE
# ======================

with tab5:

    st.subheader("How to Use This Dashboard")

    st.markdown("""

### Market Overview
Shows Indian and global market indicators.

### Market Movers
Displays top gaining and losing stocks.

### Company Analysis
Choose any NSE company (1800+ companies available) to analyze.

Includes:
• Stock price history  
• Latest news  
• AI investment insights  

---

### AI Signals

Buy → Positive outlook  
Hold → Neutral outlook  
Sell → Negative outlook  

---

### Disclaimer

This dashboard is for **educational purposes only**.

Always perform your own research before investing.

""")
# ======================
# FOOTER
# ======================

st.markdown("""
<hr>
<div style="text-align:center;color:#27F5E4">
AI Investment Dashboard<br>
Developed by Ankit Srivastava / 9616216095 
</div>
""", unsafe_allow_html=True)

