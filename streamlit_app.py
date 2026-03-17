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
        return "AI failed"

# ======================
# LOAD STOCKS
# ======================
@st.cache_data
def load_nse():
    df = pd.read_csv("https://archives.nseindia.com/content/equities/EQUITY_L.csv")
    df["ticker"] = df["SYMBOL"] + ".NS"
    return df

stocks_df = load_nse()

# ======================
# FUNCTIONS
# ======================
def market_metric(symbol):
    try:
        df = yf.Ticker(symbol).history(period="5d")
        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2]
        change = ((latest-prev)/prev)*100
        return round(latest,2), round(change,2)
    except:
        return None,None

def fetch_news(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:10]]

def add_features(df):
    df["returns"] = df["Close"].pct_change()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma50"] = df["Close"].rolling(50).mean()
    return df.dropna()

def signal(df):
    latest = df.iloc[-1]
    if latest["Close"] > latest["ma20"] > latest["ma50"]:
        return "🟢 BUY"
    elif latest["Close"] < latest["ma20"] < latest["ma50"]:
        return "🔴 SELL"
    return "🟡 HOLD"

def recommend(risk):
    sample = stocks_df["ticker"].sample(100)
    data=[]
    for s in sample:
        try:
            df = yf.Ticker(s).history(period="6mo")
            vol = df["Close"].pct_change().std()
            if (risk=="Low" and vol<0.015) or \
               (risk=="Medium" and vol<0.03) or \
               (risk=="High"):
                data.append((s,vol))
        except: pass
    return pd.DataFrame(data,columns=["Stock","Volatility"]).head(10)

def ai_alloc(recs, amt):
    prompt=f"""
Allocate ₹{amt} across:
{recs.to_dict(orient='records')}

Return JSON:
[{{"stock":"ABC","weight":20}}]
"""
    res = run_ai(prompt)
    try:
        import json
        df = pd.DataFrame(json.loads(res))
        df["Investment"]=df["weight"]/100*amt
        return df
    except:
        return None

# ======================
# TITLE
# ======================
st.title("📊 AI Investment Dashboard")

# ======================
# TABS
# ======================
tab1,tab2,tab3,tab4,tab5 = st.tabs([
"📊 Market",
"🔥 Movers",
"📈 Company",
"👤 Guide",
"🎯 Advisor"
])

# ======================
# TAB1
# ======================
with tab1:
    st.subheader("Indian Market")

    for name,sym in {
        "NIFTY":"^NSEI",
        "SENSEX":"^BSESN",
        "BANK":"^NSEBANK"
    }.items():
        p,c = market_metric(sym)
        st.metric(name,p,str(c)+"%")

    st.subheader("News")
    for n in fetch_news("stock market"):
        st.markdown(f"<div class='news-card'>{n}</div>",unsafe_allow_html=True)

# ======================
# TAB2
# ======================
with tab2:
    st.subheader("Top Movers")
    df = stocks_df.sample(50)
    data=[]
    for s in df["ticker"]:
        try:
            h=yf.Ticker(s).history(period="2d")
            ch=(h["Close"].iloc[-1]-h["Close"].iloc[-2])
            data.append((s,ch))
        except: pass
    st.dataframe(pd.DataFrame(data,columns=["Stock","Change"]))

# ======================
# TAB3
# ======================
with tab3:
    comp = st.selectbox("Select",stocks_df["SYMBOL"])
    t = comp+".NS"
    if st.button("Analyze"):
        df = yf.Ticker(t).history(period="2y")
        df = add_features(df)
        st.line_chart(df[["Close","ma20","ma50"]])
        st.write("Signal:",signal(df))
        st.write(run_ai(f"Analyze {comp} stock"))

# ======================
# TAB4
# ======================
with tab4:
    st.markdown("""
### How to use
- View markets  
- Check movers  
- Analyze stock  
- Use advisor  

⚠️ Educational only
""")

# ======================
# TAB5 (AI ADVISOR)
# ======================
with tab5:

    risk = st.selectbox("Risk",["Low","Medium","High"])
    amt = st.number_input("Amount ₹",10000)

    if st.button("Generate Portfolio"):

        recs = recommend(risk)

        st.subheader("Stocks")
        st.dataframe(recs)

        pf = ai_alloc(recs,amt)

        if pf is not None:
            st.subheader("Portfolio")
            st.dataframe(pf)
            st.bar_chart(pf.set_index("stock")["Investment"])

            st.write(run_ai(f"Explain portfolio {pf.to_dict()}"))
