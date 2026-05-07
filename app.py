import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import urllib.request
import urllib.parse
import json
import datetime
import plotly.graph_objects as go
import os
# pip install supabase
from supabase import create_client # type: ignore

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
# --- KONFIGURATION & STYLING ---
st.set_page_config(page_title="Portfolio · Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .stApp { background-color: #f0f0f2; }

    header[data-testid="stHeader"]          { display: none !important; }
    [data-testid="stToolbar"]               { display: none !important; }
    [data-testid="stDecoration"]            { display: none !important; }
    #MainMenu                               { display: none !important; }
    footer                                  { display: none !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid rgba(0,0,0,0.07) !important;
    }
    /* Alle nativen Sidebar-Toggle-Buttons verstecken — eigener JS-Button ersetzt sie */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* ── Sidebar-Buttons als unsichtbare Klick-Proxies */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
        position: relative !important;
        margin-top: -48px !important;
        height: 44px !important;
        width: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
    }

    /* ── Topbar ── */
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 54px;
        background: rgba(255,255,255,0.82);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0,0,0,0.08);
        display: flex; align-items: center; padding: 0 2.8rem; z-index: 99999;
    }
    .topbar-logo { font-size: 1rem; font-weight: 700; letter-spacing: -0.03em; color: #1d1d1f; }
    .topbar-accent { color: #3a9e7e; margin-right: 0.5rem; }
    .topbar-right {
        margin-left: auto; font-size: 0.71rem; font-weight: 600;
        letter-spacing: 0.07em; text-transform: uppercase; color: #8e8e93;
    }

    .block-container { padding: 5rem 3rem 4rem 3rem !important; max-width: 1400px; }

    h1 { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.04em !important; color: #1d1d1f !important; margin-bottom: 0.1rem !important; }
    h2, h3 { font-weight: 600 !important; letter-spacing: -0.02em !important; color: #1d1d1f !important; }
    p, span, label, div { color: #3a3a3c; }

    [data-testid="stMetric"] { background: #fff; border-radius: 16px; padding: 1.4rem 1.6rem !important; box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04); }
    [data-testid="stMetricLabel"] { font-size: 0.74rem !important; font-weight: 600 !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; color: #8e8e93 !important; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.03em !important; color: #1d1d1f !important; }
    [data-testid="stMetricDelta"] { font-size: 0.85rem !important; font-weight: 500 !important; }

    .stButton > button { background: #ffffff !important; color: #1d1d1f !important; border: 1px solid #d1d1d6 !important; border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.875rem !important; font-weight: 500 !important; padding: 0.55rem 1.4rem !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; transition: all 0.15s ease !important; }
    .stButton > button:hover { background: #f5f5f7 !important; border-color: #b0b0b8 !important; }

    [data-testid="stBaseButton-primary"], button[kind="primary"], .stButton > button[kind="primary"] {
        background: #2c2c2e !important; color: #ffffff !important; border: 1px solid #2c2c2e !important;
        border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important;
        font-size: 0.875rem !important; font-weight: 500 !important; padding: 0.55rem 1.4rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2) !important; transition: all 0.15s ease !important;
    }
    [data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover { background: #3d3d3f !important; border-color: #3d3d3f !important; color: #ffffff !important; }
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"] span, button[kind="primary"] p, button[kind="primary"] span { color: #ffffff !important; }

    .stTextInput > div > div > input { background: #fff !important; border: 1px solid #e5e5ea !important; border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important; color: #1d1d1f !important; padding: 0.6rem 1rem !important; }
    .stTextInput > div > div > input:focus { border-color: #2c2c2e !important; box-shadow: 0 0 0 3px rgba(44,44,46,0.1) !important; }
    .stSelectbox > div > div { background: #fff !important; border: 1px solid #e5e5ea !important; border-radius: 10px !important; }
    hr { border: none !important; border-top: 1px solid #e5e5ea !important; margin: 2.2rem 0 !important; }
    .stSpinner > div { border-top-color: #2c2c2e !important; }
    .stAlert { border-radius: 12px !important; font-size: 0.9rem !important; }
    </style>
""", unsafe_allow_html=True)


# ── Passwort-Schutz ──
if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False

if not st.session_state.eingeloggt:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1.5, 1, 1.5])
    with col_c:
        st.markdown("## 🔒 Zugang")
        st.markdown("<p style='color:#8e8e93;font-size:0.85rem;margin-top:-0.5rem;'>Bitte Kürzel eingeben</p>", unsafe_allow_html=True)
        kuerzel = st.text_input("", type="password", placeholder="Kürzel …", label_visibility="collapsed")
        if st.button("Eintreten", use_container_width=True):
            if kuerzel == "bwb":
                st.session_state.eingeloggt = True
                st.rerun()
            else:
                st.error("Falsches Kürzel.")
    st.stop()




def save_depot():
    sb = get_supabase()
    # Alles löschen, dann neu schreiben
    sb.table("depot").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    if st.session_state.depot:
        # RSI None-Werte bereinigen (Supabase mag kein NaN)
        clean = []
        for p in st.session_state.depot:
            row = dict(p)
            if row.get("RSI") is None or (isinstance(row.get("RSI"), float) and pd.isna(row["RSI"])):
                row["RSI"] = None
            clean.append(row)
        sb.table("depot").insert(clean).execute()

def load_depot():
    try:
        sb = get_supabase()
        res = sb.table("depot").select("*").execute()
        # "id"-Spalte von Supabase wieder entfernen
        return [{k: v for k, v in r.items() if k != "id"} for r in res.data]
    except:
        return []

if "depot" not in st.session_state:
    st.session_state.depot = load_depot()
if "page" not in st.session_state:
    st.session_state.page = "Home"


# ── Hilfsfunktionen ──
MONATE_DE = ["Januar","Februar","März","April","Mai","Juni",
             "Juli","August","September","Oktober","November","Dezember"]

def get_greeting():
    h = datetime.datetime.now().hour
    return "Guten Morgen" if h < 10 else ("Guten Tag" if h < 18 else "Guten Abend")

def format_date_de(dt):
    return f"{dt.day}. {MONATE_DE[dt.month - 1]} {dt.year}"

def calculate_rsi(data, window=14):
    if len(data) < window: return None
    delta = data['Close'].diff()
    gain  = (delta.where(delta > 0, 0)).fillna(0)
    loss  = (-delta.where(delta < 0, 0)).fillna(0)
    rs    = gain.rolling(window, min_periods=window).mean() / loss.rolling(window, min_periods=window).mean()
    return 100 - (100 / (1 + rs)).iloc[-1]

@st.cache_data(ttl=300)
def get_fear_and_greed_data():
    urls = [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://fear-and-greed-index.p.rapidapi.com/v1/fgi",   # Fallback-Endpunkt
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://edition.cnn.com/',
        'Origin': 'https://edition.cnn.com',
    }
    try:
        req = urllib.request.Request(urls[0], headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode())
            score  = d['fear_and_greed']['score']
            rating = d['fear_and_greed']['rating'].lower()
            if "extreme fear" in rating:    status = "Extreme Angst"
            elif "fear" in rating:          status = "Angst"
            elif "extreme greed" in rating: status = "Extreme Gier"
            elif "greed" in rating:         status = "Gier"
            else:                           status = "Neutral"
            return round(score), status, False
    except:
        # VIX-Proxy als stiller Fallback – kein Hinweis anzeigen
        try:
            vix   = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
            score = max(0, min(100, 100 - ((vix - 10) / (35 - 10)) * 100))
            if score < 25:   status = "Extreme Angst"
            elif score < 45: status = "Angst"
            elif score < 55: status = "Neutral"
            elif score < 75: status = "Gier"
            else:            status = "Extreme Gier"
            return round(score), status, False   # False = kein Hinweis
        except:
            return 50, "Neutral", False

@st.cache_data(ttl=300)
@st.cache_data(ttl=300)
def get_eur_rate(from_currency):
    """Gibt den Faktor zurück, mit dem ein Kurs in from_currency in EUR umgerechnet wird."""
    if not from_currency or from_currency == "EUR":
        return 1.0
    pence = from_currency == "GBp"          # Londoner Tickers: Pence statt Pfund
    base  = "GBP" if pence else from_currency
    try:
        pair = f"EUR{base}=X"               # z. B. EURUSD=X, EURGBP=X
        rate = yf.Ticker(pair).history(period="1d")['Close'].iloc[-1]
        factor = 1 / rate                   # EUR pro 1 Einheit Fremdwährung
        return factor / 100 if pence else factor
    except:
        return 1.0
def get_market_indices():
    indices = {"DAX": "^GDAXI", "S&P 500": "^GSPC", "MSCI World": "EUNL.DE"}
    data = {}
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist   = ticker.history(period="5d", interval="15m")
            hist   = hist[hist.index.dayofweek < 5].between_time("07:00", "23:00")
            if not hist.empty and len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev = ticker.history(period="2d")['Close'].iloc[-2]
                data[name] = {"current": curr, "delta": ((curr-prev)/prev)*100,
                              "history": hist['Close'].reset_index(drop=True)}
        except:
            data[name] = None
    return data

def score_color(s):
    if s < 25: return "#e05c5c"
    if s < 45: return "#d4963a"
    if s < 55: return "#8e8e93"
    if s < 75: return "#3a9e7e"
    return "#2d7a5f"

def create_gauge(score, status, is_proxy):
    c = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={'font': {'size': 64, 'color': '#1d1d1f', 'family': 'DM Sans'}},
        title={'text': f"<b>{status}{'  ¹' if is_proxy else ''}</b>",
               'font': {'size': 15, 'color': '#3a3a3c', 'family': 'DM Sans'}},
        gauge={'axis': {'range': [0,100], 'tickvals': [0,25,50,75,100],
                        'ticktext': ['0','25','50','75','100'],
                        'tickfont': {'size':10,'color':'#8e8e93'}, 'tickwidth':1, 'tickcolor':'#e5e5ea'},
               'bar': {'color': c, 'thickness': 0.55}, 'bgcolor': '#f5f5f7', 'borderwidth': 0,
               'steps': [{'range': [0,100], 'color': '#e5e5ea'}],
               'threshold': {'line': {'color': c, 'width': 3}, 'thickness': 0.75, 'value': score}}
    ))
    fig.update_layout(height=260, margin=dict(l=20,r=20,t=50,b=10),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font={'family':'DM Sans'})
    return fig

def create_mini_chart(history, delta):
    lc = "#3a9e7e" if delta >= 0 else "#e05c5c"
    fc = "rgba(58,158,126,0.10)" if delta >= 0 else "rgba(224,92,92,0.10)"
    v  = history.dropna().values
    if len(v) > 1:
        pad  = max((v.max()-v.min())*0.15, v.mean()*0.005)
        rng  = [v.min()-pad, v.max()+pad]
    else:
        rng = [None, None]
    fig = go.Figure(go.Scatter(x=list(range(len(v))), y=v, mode='lines', fill='tozeroy',
                               fillcolor=fc, line=dict(color=lc, width=2, shape='spline'),
                               hovertemplate='%{y:,.0f}<extra></extra>'))
    fig.update_layout(height=90, margin=dict(l=0,r=0,t=4,b=0),
                      xaxis=dict(visible=False, showgrid=False),
                      yaxis=dict(visible=False, showgrid=False, range=rng),
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      hovermode='x unified')
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:1rem 1rem 1rem 1.2rem;border-bottom:1px solid #f0f0f2;margin-bottom:0.8rem;
                    display:flex;align-items:center;justify-content:space-between;">
            <span style="font-size:0.95rem;font-weight:700;letter-spacing:-0.03em;color:#1d1d1f;">
                <span style="color:#3a9e7e;">●</span>&nbsp; Portfolio
            </span>
            <div id="_close_ham" style="
                width:32px;height:32px;background:#f5f5f7;border-radius:8px;
                display:flex;align-items:center;justify-content:center;
                cursor:pointer;font-size:16px;color:#3a3a3c;flex-shrink:0;
                transition:background 0.15s;">&#9776;</div>
        </div>
    """, unsafe_allow_html=True)

    nav_items = [("🏠", "Home"), ("🌤️", "Wetter"), ("👥", "Über uns")]

    for icon, label in nav_items:
        active  = st.session_state.page == label
        bg      = "#f0f0f2" if active else "transparent"
        weight  = "600" if active else "500"
        color   = "#1d1d1f" if active else "#3a3a3c"
        border  = "border-left:3px solid #3a9e7e;" if active else "border-left:3px solid transparent;"

        st.markdown(f"""
            <div style="margin:2px 0.5rem;">
                <div style="background:{bg};border-radius:10px;{border}
                            padding:0.6rem calc(0.9rem - 3px);display:flex;align-items:center;">
                    <span style="font-size:0.92rem;font-weight:{weight};color:{color};">
                        {icon}&nbsp;&nbsp;{label}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()


# ── Topbar mit integriertem Hamburger-Button ──
now = datetime.datetime.now()
st.markdown(f"""
    <div class="topbar">
        <div id="_ham" style="
            width:36px; height:36px; margin-right:14px; flex-shrink:0;
            background:#ffffff; border:1px solid rgba(0,0,0,0.10);
            border-radius:9px; box-shadow:0 1px 6px rgba(0,0,0,0.10);
            display:flex; align-items:center; justify-content:center;
            cursor:pointer; font-size:16px; color:#1d1d1f;
            transition:background 0.15s;">&#9776;</div>
        <span class="topbar-logo"><span class="topbar-accent">●</span>&nbsp; Portfolio Dashboard</span>
        <span class="topbar-right">{get_greeting()} &nbsp;·&nbsp; {format_date_de(now)}</span>
    </div>
""", unsafe_allow_html=True)

# ── Hamburger JS via components (einzige zuverlässige Methode in Streamlit) ──
components.html("""
<script>
(function() {
    var SEL = [
        '[data-testid="stSidebarCollapseButton"] button',
        '[data-testid="collapsedControl"] button',
        '[data-testid="stSidebarCollapsedControl"] button'
    ];

    function triggerToggle(doc) {
        for (var i = 0; i < SEL.length; i++) {
            var btn = doc.querySelector(SEL[i]);
            if (btn) { btn.click(); return; }
        }
    }

    function attachBtn(doc, id, bgDefault, bgHover) {
        var el = doc.getElementById(id);
        if (!el) return false;
        if (el._hamAttached) return true;
        el._hamAttached = true;
        el.addEventListener('click', function() { triggerToggle(doc); });
        el.addEventListener('mouseenter', function() { this.style.background = bgHover; });
        el.addEventListener('mouseleave', function() { this.style.background = bgDefault; });
        return true;
    }

    function poll() {
        try {
            var doc = window.parent.document;
            var hamOk   = attachBtn(doc, '_ham',       '#ffffff', '#f5f5f7');
            var closeOk = attachBtn(doc, '_close_ham', '#f5f5f7', '#e8e8ea');
            if (!hamOk) setTimeout(poll, 150);
            // Keep polling for _close_ham (appears/disappears with sidebar)
            setTimeout(function reattach() {
                try { attachBtn(window.parent.document, '_close_ham', '#f5f5f7', '#e8e8ea'); }
                catch(e) {}
                setTimeout(reattach, 500);
            }, 500);
        } catch(e) { setTimeout(poll, 150); }
    }
    poll();
})();
</script>
""", height=0, scrolling=False)


# ═══════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "Home":

    st.markdown("""
        <div style="margin-bottom:1.6rem;">
            <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.3rem 0;">Marktübersicht</p>
            <h1 style="font-size:2.2rem;font-weight:700;letter-spacing:-0.04em;color:#1d1d1f;margin:0;">Wie läuft der Markt?</h1>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    col_gauge, _, col_indices = st.columns([1.1, 0.08, 2.8])

    with col_gauge:
        st.markdown("""
            <div style="background:#fff;border-radius:20px;padding:1.2rem 1.4rem 0.6rem 1.4rem;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);">
                <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin-bottom:0.1rem;">Fear & Greed Index</p>
            </div>
        """, unsafe_allow_html=True)
        score, status, is_proxy = get_fear_and_greed_data()
        st.plotly_chart(create_gauge(score, status, is_proxy), use_container_width=True, config={'displayModeBar': False})
        if is_proxy:
            st.caption("¹ Berechnet aus VIX (CNN-Daten nicht verfügbar)")

    with col_indices:
        market_data  = get_market_indices()
        idx_cols     = st.columns(3)
        index_names  = ["DAX", "S&P 500", "MSCI World"]
        currencies   = ["EUR", "USD", "EUR"]

        for name, currency, col in zip(index_names, currencies, idx_cols):
            m = market_data.get(name)
            with col:
                dv  = m['delta'] if m else 0
                dc  = "#3a9e7e" if dv >= 0 else "#e05c5c"
                ds  = "+" if dv >= 0 else ""
                kf  = f"{m['current']:,.0f}".replace(',', '.') if m else "–"
                st.markdown(f"""
                    <div style="background:#fff;border-radius:20px;padding:1.3rem 1.4rem 0.8rem 1.4rem;
                                box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);">
                        <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.35rem 0;">{currency}</p>
                        <p style="font-size:1.05rem;font-weight:600;color:#1d1d1f;letter-spacing:-0.01em;margin:0 0 0.15rem 0;">{name}</p>
                        <p style="font-size:1.7rem;font-weight:600;color:#1d1d1f;letter-spacing:-0.03em;margin:0;">{kf}</p>
                        <p style="font-size:0.88rem;font-weight:500;color:{dc};margin:0.2rem 0 0 0;">{ds}{dv:.2f}%</p>
                    </div>
                """, unsafe_allow_html=True)
                if m:
                    st.plotly_chart(create_mini_chart(m['history'], m['delta']),
                                    use_container_width=True, config={'displayModeBar': False}, key=f"chart_{name}")

    st.divider()

    # ── Musterdepot ──
    st.markdown("""
        <div style="margin-bottom:1.4rem;margin-top:0.5rem;">
            <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.3rem 0;">Musterdepot</p>
            <h1 style="font-size:2.2rem;font-weight:700;letter-spacing:-0.04em;color:#1d1d1f;margin:0;">Deine Positionen</h1>
            <p style="color:#8e8e93;font-size:0.88rem;margin:0.3rem 0 0 0;">Fiktive Käufe · je 1.000 €</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        suchbegriff = st.text_input("", placeholder="Aktienname eingeben, z. B. Allianz oder Apple …", label_visibility="collapsed")
    with col_btn:
        st.markdown("<div style='margin-top:0.15rem;'>", unsafe_allow_html=True)
        suchen = st.button("Suchen", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    if suchen and suchbegriff:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(suchbegriff)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode())
                st.session_state.results = [
                    {"name": q['shortname'], "symbol": q['symbol'], "exchange": q.get('exchDisp','–')}
                    for q in data.get('quotes', []) if 'symbol' in q and 'shortname' in q
                ]
        except:
            st.error("Suche fehlgeschlagen.")

    if "results" in st.session_state and st.session_state.results:
        st.markdown("<br>", unsafe_allow_html=True)

        def format_option(opt):
            s = opt['symbol'].upper()
            if s.endswith((".DE",".F",".SG",".MU",".AS",".MI",".PA",".VI")): w = "EUR"
            elif s.endswith(".L"): w = "GBP"
            elif "." not in s:    w = "USD"
            else:                  w = "Lokal"
            return f"{opt['name']} ({opt['symbol']})  ·  {w}  ·  {opt['exchange']}"

        col_sel, col_kauf = st.columns([3, 1])
        with col_sel:
            sel = st.selectbox("", st.session_state.results, format_func=format_option, label_visibility="collapsed")
        with col_kauf:
            if st.button("Kaufen", use_container_width=True):
                try:
                    with st.spinner("Daten werden geladen …"):
                        t          = yf.Ticker(sel['symbol'])
                        currency   = t.fast_info.get('currency', 'EUR')
                        eur_factor = get_eur_rate(currency)
                        price_nat  = t.history(period="1d")['Close'].iloc[-1]
                        price_eur  = price_nat * eur_factor
                        st.session_state.depot.append({
                            "Aktie":            sel['name'],
                            "Symbol":           sel['symbol'],
                            "Währung":          currency,          # ← neu gespeichert
                            "Kaufkurs (€)":     price_eur,
                            "Aktueller Kurs (€)": price_eur,
                            "Anteile":          1000 / price_eur,
                            "RSI":              calculate_rsi(t.history(period="3mo"))
                        })
                        save_depot()
                    st.success(f"{sel['name']} wurde ins Depot aufgenommen.")
                    del st.session_state.results
                    st.rerun()
                except Exception as e:
                    st.error(f"Kauf fehlgeschlagen: {e}")

    st.divider()

    col_dt, col_rf = st.columns([3, 1])
    with col_dt:
        st.markdown("### Positionen")
    with col_rf:
        if st.session_state.depot:
            if st.button("Aktualisieren", use_container_width=True, type="primary"):
                with st.spinner("Kurse werden aktualisiert …"):
                    for p in st.session_state.depot:
                        try:
                            t          = yf.Ticker(p['Symbol'])
                            currency   = p.get('Währung', 'EUR')
                            eur_factor = get_eur_rate(currency)
                            p['Aktueller Kurs (€)'] = t.history(period="1d")['Close'].iloc[-1] * eur_factor
                            p['RSI'] = calculate_rsi(t.history(period="3mo"))
                        except:
                            pass
                    save_depot()
                st.rerun()

    if st.session_state.depot:
        hs = "font-size:0.72rem;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.3rem 0;"
        h1,h2,h3,h4,h5,h6,h7,h8 = st.columns([2.4, 1.0, 1.1, 1.1, 1.1, 1.1, 0.9, 0.55])
        h1.markdown(f"<p style='{hs}'>Aktie</p>",      unsafe_allow_html=True)
        h2.markdown(f"<p style='{hs}'>Symbol</p>",     unsafe_allow_html=True)
        h3.markdown(f"<p style='{hs}'>Investiert</p>", unsafe_allow_html=True)
        h4.markdown(f"<p style='{hs}'>Kaufkurs</p>",   unsafe_allow_html=True)
        h5.markdown(f"<p style='{hs}'>Aktuell</p>",    unsafe_allow_html=True)
        h6.markdown(f"<p style='{hs}'>Differenz</p>",  unsafe_allow_html=True)
        h7.markdown(f"<p style='{hs}'>RSI</p>",         unsafe_allow_html=True)
        h8.markdown(f"<p style='{hs}'></p>",            unsafe_allow_html=True)

        to_delete = None
        for i, p in enumerate(st.session_state.depot):
            diff       = (p["Aktueller Kurs (€)"] - p["Kaufkurs (€)"]) * p["Anteile"]
            diff_color = "#3a9e7e" if diff >= 0 else "#e05c5c"
            diff_str   = f"+{diff:.2f} €" if diff >= 0 else f"{diff:.2f} €"
            rsi        = p.get("RSI")
            rsi_str    = f"{rsi:.1f}" if rsi is not None and pd.notnull(rsi) else "–"
            investiert = p["Anteile"] * p["Kaufkurs (€)"]

            if rsi is not None and pd.notnull(rsi):
                if rsi > 70:   rsi_bg, rsi_col = "#fce8e8", "#c0392b"
                elif rsi < 30: rsi_bg, rsi_col = "#e8f7f2", "#1e8449"
                else:          rsi_bg, rsi_col = "#f5f5f7", "#3a3a3c"
            else:
                rsi_bg, rsi_col = "#f5f5f7", "#8e8e93"

            cell = "font-size:0.9rem;font-weight:500;color:#1d1d1f;margin:0;"
            rs   = "background:#fff;border-radius:14px;padding:0.85rem 1rem;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 0 0 1px rgba(0,0,0,0.04);margin-bottom:0.5rem;"

            c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2.4, 1.0, 1.1, 1.1, 1.1, 1.1, 0.9, 0.55])
            c1.markdown(f"<div style='{rs}'><p style='{cell}'>{p['Aktie']}</p></div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='{rs}'><p style='{cell};color:#8e8e93;'>{p['Symbol']}</p></div>", unsafe_allow_html=True)
            # ── Investiert-Badge ──
            c3.markdown(f"""
                <div style='{rs}'>
                    <p style='{cell}'>
                        <span style='background:#f0faf6;color:#2d7a5f;border-radius:6px;
                                     padding:3px 8px;font-size:0.84rem;font-weight:600;'>
                            {f"{investiert:,.0f}".replace(',', '.')} €
                        </span>
                    </p>
                </div>""", unsafe_allow_html=True)
            c4.markdown(f"<div style='{rs}'><p style='{cell}'>{p['Kaufkurs (€)']:.2f} €</p></div>", unsafe_allow_html=True)
            c5.markdown(f"<div style='{rs}'><p style='{cell}'>{p['Aktueller Kurs (€)']:.2f} €</p></div>", unsafe_allow_html=True)
            c6.markdown(f"<div style='{rs}'><p style='{cell};color:{diff_color};'>{diff_str}</p></div>", unsafe_allow_html=True)
            c7.markdown(f"<div style='{rs}'><p style='{cell};background:{rsi_bg};color:{rsi_col};border-radius:6px;padding:2px 6px;display:inline-block;'>{rsi_str}</p></div>", unsafe_allow_html=True)
            with c8:
                st.markdown("<div style='height:0.62rem;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{i}", help=f"{p['Aktie']} löschen"):
                    to_delete = i

        if to_delete is not None:
            st.session_state.depot.pop(to_delete)
            save_depot()
            st.rerun()

        total_diff     = sum((p["Aktueller Kurs (€)"] - p["Kaufkurs (€)"]) * p["Anteile"] for p in st.session_state.depot)
        total_invested = sum(p["Anteile"] * p["Kaufkurs (€)"] for p in st.session_state.depot)
        pct   = (total_diff / total_invested) * 100 if total_invested else 0
        color = "#3a9e7e" if total_diff >= 0 else "#e05c5c"
        sign  = "+" if total_diff >= 0 else ""

        st.markdown(f"""
            <div style="background:#fff;border-radius:16px;padding:1.2rem 1.6rem;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);
                        margin-top:1rem;display:flex;align-items:center;gap:2.5rem;">
                <div>
                    <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin:0;">Gesamtinvestiert</p>
                    <p style="font-size:1.6rem;font-weight:600;color:#1d1d1f;letter-spacing:-0.02em;margin:0.2rem 0 0 0;">{f"{total_invested:,.0f} ".replace(',', '.')}€</p>
                </div>
                <div>
                    <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin:0;">Gesamtergebnis</p>
                    <p style="font-size:1.6rem;font-weight:600;color:{color};letter-spacing:-0.02em;margin:0.2rem 0 0 0;">{sign}{total_diff:.2f} €</p>
                </div>
                <div>
                    <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin:0;">Performance</p>
                    <p style="font-size:1.6rem;font-weight:600;color:{color};letter-spacing:-0.02em;margin:0.2rem 0 0 0;">{sign}{pct:.2f} %</p>
                </div>
                <div>
                    <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8e8e93;margin:0;">Positionen</p>
                    <p style="font-size:1.6rem;font-weight:600;color:#1d1d1f;letter-spacing:-0.02em;margin:0.2rem 0 0 0;">{len(st.session_state.depot)}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
            <div style="background:#fff;border-radius:16px;padding:2.5rem;text-align:center;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);">
                <p style="font-size:1.4rem;margin:0;">📭</p>
                <p style="color:#8e8e93;font-size:0.9rem;margin:0.5rem 0 0 0;">Noch keine Positionen im Depot.</p>
            </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# WETTER
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "Wetter":

    st.markdown("""
        <div style="margin-bottom:1.6rem;">
            <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.3rem 0;">Wetter</p>
            <h1 style="font-size:2.2rem;font-weight:700;letter-spacing:-0.04em;color:#1d1d1f;margin:0;">Wie ist das Wetter?</h1>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("""
        <div style="background:#fff;border-radius:20px;padding:3.5rem;text-align:center;
                    box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);">
            <p style="font-size:2.8rem;margin:0;">🌤️</p>
            <p style="font-size:1.1rem;font-weight:600;color:#1d1d1f;margin:0.8rem 0 0.4rem 0;">Kommt bald</p>
            <p style="color:#8e8e93;font-size:0.9rem;margin:0;">Die Wetterseite wird noch gebaut.</p>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ÜBER UNS
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "Über uns":

    st.markdown("""
        <div style="margin-bottom:1.6rem;">
            <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8e8e93;margin:0 0 0.3rem 0;">Das Team</p>
            <h1 style="font-size:2.2rem;font-weight:700;letter-spacing:-0.04em;color:#1d1d1f;margin:0;">Über uns</h1>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Team-Daten – Namen, Farben und Texte hier anpassen ──
    team = [
        {
            "name":      "Max Mustermann",
            "farbe":     "#3a9e7e",
            "initialen": "MM",
            "bild":      None,   # echtes Foto: URL als String eintragen, z. B. "https://…/foto.jpg"
            "bio": (
                "Max ist seit über zehn Jahren im Finanzbereich tätig und hat eine Leidenschaft "
                "für datengetriebene Anlagestrategien. Er studierte Wirtschaftswissenschaften in "
                "Frankfurt und verantwortet die Portfolioanalyse des Teams."
            ),
        },
        {
            "name":      "Anna Schmidt",
            "farbe":     "#5b8dee",
            "initialen": "AS",
            "bild":      None,
            "bio": (
                "Anna bringt tiefes Know-how in der technischen Analyse mit. Nach ihrem "
                "Masterstudium in Mathematik spezialisierte sie sich auf quantitative Modelle "
                "und entwickelt die algorithmischen Grundlagen unserer Marktauswertungen."
            ),
        },
        {
            "name":      "Jonas Weber",
            "farbe":     "#d4963a",
            "initialen": "JW",
            "bild":      None,
            "bio": (
                "Jonas verbindet Technologie und Finance: Als Fullstack-Entwickler hat er "
                "dieses Dashboard von Grund auf gebaut und sorgt dafür, dass Daten stets "
                "aktuell, übersichtlich und zuverlässig dargestellt werden."
            ),
        },
    ]

    cols = st.columns(3, gap="large")
    for col, m in zip(cols, team):
        with col:
            if m["bild"]:
                avatar = f"""<img src="{m['bild']}"
                                 style="width:100px;height:100px;border-radius:50%;object-fit:cover;
                                        display:block;margin:0 auto 1.2rem auto;" />"""
            else:
                avatar = f"""
                    <div style="width:100px;height:100px;border-radius:50%;background:{m['farbe']};
                                margin:0 auto 1.2rem auto;display:flex;align-items:center;
                                justify-content:center;font-size:1.7rem;font-weight:700;color:#fff;">
                        {m['initialen']}
                    </div>"""

            st.markdown(f"""
                <div style="background:#fff;border-radius:20px;padding:2.2rem 1.8rem 2rem 1.8rem;
                            box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px rgba(0,0,0,0.04);
                            text-align:center;height:100%;">
                    {avatar}
                    <p style="font-size:1.05rem;font-weight:600;color:#1d1d1f;
                              letter-spacing:-0.01em;margin:0 0 0.6rem 0;">{m['name']}</p>
                    <p style="font-size:0.84rem;color:#6e6e73;line-height:1.65;margin:0;">{m['bio']}</p>
                </div>
            """, unsafe_allow_html=True)