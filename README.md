# Live ETF Race Track

A Streamlit dashboard that visualizes intraday % gains of a basket of ETFs as
positions on an oval "race track," auto-refreshing during market hours.

## What was fixed from the original draft

- **Auto-refresh**: replaced the blocking `time.sleep(15)` + `st.rerun()`
  loop with `streamlit_autorefresh`, which reruns the script on a timer
  without freezing the UI thread.
- **Race logic**: position on the track is now `% gain ÷ LAP_SCALE`, so a
  stock that's genuinely ahead is drawn further along — the old
  `(gain * 2.0) % 2π` formula could put a +0.5% and a +50% gainer at the same
  angle.
- **Data handling**: guards against `yfinance` returning a `Series` instead
  of a `DataFrame` when tracking closely-related ticker counts, and against
  gaps/NaNs in the 1-minute bars.
- **Market-hours awareness**: shows whether the market is currently open
  (9:30 AM–4:00 PM Eastern) so numbers aren't mistaken for live when they're
  stale.
- Added a plain leaderboard table below the chart so "who's winning" is
  never ambiguous.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a public (or private, on paid tiers) GitHub repo.
2. Go to https://share.streamlit.io → "New app."
3. Point it at your repo, branch, and `app.py`.
4. Deploy. Streamlit installs `requirements.txt` automatically.
5. The app is now live at `https://<your-app-name>.streamlit.app` and stays
   up continuously — the in-app auto-refresh keeps prices updating while
   anyone has the tab open.

## Switching from yfinance to a real-time API (optional)

`yfinance` intraday data is delayed and sometimes has gaps outside of very
recent minutes. For tighter real-time behavior:

- **Finnhub** (free tier, websocket + REST quotes): sign up for an API key,
  then replace `get_live_data` with calls to Finnhub's `/quote` endpoint.
- **Polygon.io** (paid tiers for real-time equities): similar REST swap.

Either way, store the API key in Streamlit's secrets manager rather than in
code:

```toml
# .streamlit/secrets.toml (do not commit this file)
FINNHUB_API_KEY = "your_key_here"
```

and access it in `app.py` via `st.secrets["FINNHUB_API_KEY"]`. On Streamlit
Community Cloud, add the same key under your app's Settings → Secrets.

## Customizing

- `TICKERS`: change the basket of symbols tracked.
- `LAP_SCALE`: % gain that equals one full lap — lower it to make small
  moves more visually dramatic, raise it to compress the range.
- `REFRESH_SECONDS` / `CACHE_TTL`: how often the page reruns vs. how often
  new data is actually fetched (keep `CACHE_TTL <= REFRESH_SECONDS` or
  you'll rerun without new data).
