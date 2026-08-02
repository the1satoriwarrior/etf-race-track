import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
st.set_page_config(page_title="Live ETF Race Track", layout="wide")
st.title("🏇 Live ETF Intraday Race Track")

TICKERS = ['VV', 'VOOV', 'VONV', 'VTI', 'SCHB', 'RWL', 'ALVL', 'EQWL', 'GSEW', 'EQAL', 'RSP', 'EUSA']
REFRESH_SECONDS = 15          # how often the page reruns 
CACHE_TTL = 10                # how often new data is actually fetched
LAP_SCALE = 3.0               # % gain that equals one full lap around the track
TRACK_RX, TRACK_RY = 300, 180 # oval track radii

EASTERN = pytz.timezone("US/Eastern")


def market_is_open() -> bool: 
    now = datetime.now(EASTERN)
    if now.weekday() >= 5:
        return False
    open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t <= now <= close_t


# ---------------------------------------------------------------
# AUTO-REFRESH (replaces the blocking time.sleep + st.rerun loop)
# ---------------------------------------------------------------
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="datarefresh")


# ---------------------------------------------------------------
# DATA
# ---------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL)
def get_live_data(tickers):
    """Return % change from today's open for each ticker."""
    df = yf.download(tickers, period="1d", interval="1m", progress=False)["Close"]

    # yfinance returns a Series instead of DataFrame if only 1 ticker
    if isinstance(df, pd.Series):
        df = df.to_frame(name=tickers[0])

    df = df.dropna(how="all")
    if df.empty:
        return pd.Series({t: 0.0 for t in tickers})

    first_valid = df.apply(lambda col: col.dropna().iloc[0] if col.dropna().size else np.nan)
    last_valid = df.apply(lambda col: col.dropna().iloc[-1] if col.dropna().size else np.nan)

    pct_change = ((last_valid - first_valid) / first_valid) * 100
    return pct_change.reindex(tickers)


try:
    pct_gains = get_live_data(TICKERS)
except Exception as e:
    st.error(f"Data fetch failed: {e}")
    st.stop()

status = "🟢 Market Open" if market_is_open() else "🔴 Market Closed (showing last available data)"
st.caption(f"{status} · Last refreshed: {datetime.now(EASTERN).strftime('%I:%M:%S %p %Z')}")


# ---------------------------------------------------------------
# BUILD THE RACE TRACK
# ---------------------------------------------------------------
fig = go.Figure()

# Oval track background
theta = np.linspace(0, 2 * np.pi, 200)
fig.add_trace(go.Scatter(
    x=TRACK_RX * np.cos(theta), y=TRACK_RY * np.sin(theta),
    mode="lines", line=dict(color="lightgray", width=24),
    showlegend=False, hoverinfo="skip",
))

# Start/finish line marker
fig.add_trace(go.Scatter(
    x=[TRACK_RX], y=[0], mode="markers", marker=dict(symbol="line-ns", size=24, color="black"),
    showlegend=False, hoverinfo="skip",
))

colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# Sort so the leader is drawn/labelled clearly (optional, purely cosmetic)
ranked = pct_gains.sort_values(ascending=False)

for i, (ticker, gain) in enumerate(ranked.items()):
    gain_val = 0.0 if pd.isna(gain) else float(gain)

    # Position around the oval is directly proportional to % gain.
    # LAP_SCALE% gain = one full lap, so relative standing is meaningful:
    # a stock further along has genuinely gained more, not just "wrapped" further.
    fraction_of_lap = (gain_val / LAP_SCALE) % 1.0
    angle = fraction_of_lap * 2 * np.pi

    x = TRACK_RX * np.cos(angle)
    y = TRACK_RY * np.sin(angle)

    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode="markers+text",
        name=f"{ticker} ({gain_val:+.2f}%)",
        text=[f"<b>{ticker}</b><br>{gain_val:+.2f}%"],
        textposition="top center",
        marker=dict(size=20, color=colors[i % len(colors)], line=dict(width=2, color="white")),
    ))

fig.update_layout(
    xaxis=dict(visible=False, range=[-TRACK_RX * 1.3, TRACK_RX * 1.3]),
    yaxis=dict(visible=False, range=[-TRACK_RY * 1.3, TRACK_RY * 1.3], scaleanchor="x", scaleratio=1),
    height=550,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.1),
)

st.plotly_chart(fig, use_container_width=True)

# Leaderboard table underneath, for a non-ambiguous read of who's actually winning
st.subheader("Leaderboard")
board = ranked.reset_index()
board.columns = ["Ticker", "% Change Today"]
board.index = board.index + 1
st.dataframe(board.style.format({"% Change Today": "{:+.2f}%"}), use_container_width=True)

st.caption(
    f"Position on track = % gain relative to a {LAP_SCALE}% full lap. "
    "This is a visualization, not a literal race — leaders are simply whoever gained the most today."
)
