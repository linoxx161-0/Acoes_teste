import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Ações Brasileiras 2025", layout="wide")

TICKERS = {
    "Petrobras (PETR4)": "PETR4.SA",
    "Itaú (ITUB4)": "ITUB4.SA",
    "Vale (VALE3)": "VALE3.SA",
}

COLORS = {
    "Petrobras (PETR4)": "#1f77b4",
    "Itaú (ITUB4)": "#ff7f0e",
    "Vale (VALE3)": "#2ca02c",
}


@st.cache_data(ttl=3600)
def load_data(tickers: tuple, start: str, end: str) -> pd.DataFrame:
    return yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False)


def get_series(data: pd.DataFrame, metric: str, ticker: str) -> pd.Series:
    if isinstance(data.columns, pd.MultiIndex):
        return data[metric][ticker].dropna()
    return data[metric].dropna()


# --- Sidebar ---
st.sidebar.title("Filtros")

start_date = st.sidebar.date_input(
    "Data inicial", value=date(2025, 1, 2),
    min_value=date(2025, 1, 2), max_value=date(2025, 12, 31),
)
end_date = st.sidebar.date_input(
    "Data final", value=date(2025, 12, 31),
    min_value=date(2025, 1, 2), max_value=date(2025, 12, 31),
)

if start_date >= end_date:
    st.sidebar.error("A data inicial deve ser anterior à data final.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Ações")
selected_names = [
    name for name in TICKERS
    if st.sidebar.checkbox(name, value=True)
]

# --- Main ---
st.title("Cotação e Performance de Ações Brasileiras — 2025")
st.caption("Petrobras (PETR4) · Itaú (ITUB4) · Vale (VALE3)  |  Fonte: Yahoo Finance")

if not selected_names:
    st.warning("Selecione ao menos uma ação na barra lateral.")
    st.stop()

tickers_tuple = tuple(TICKERS[n] for n in selected_names)

with st.spinner("Carregando dados..."):
    data = load_data(tickers_tuple, str(start_date), str(end_date))

if data.empty:
    st.error("Não foi possível carregar os dados. Verifique sua conexão.")
    st.stop()

# --- Metric cards ---
st.subheader("Resumo do Período")
cols = st.columns(len(selected_names))
for col, name in zip(cols, selected_names):
    series = get_series(data, "Close", TICKERS[name])
    if len(series) >= 2:
        p_start = series.iloc[0]
        p_end = series.iloc[-1]
        pct = (p_end / p_start - 1) * 100
        col.metric(label=name, value=f"R$ {p_end:.2f}", delta=f"{pct:+.2f}%")
        col.caption(f"Máx: R$ {series.max():.2f}  |  Mín: R$ {series.min():.2f}")

st.markdown("---")

# --- Chart 1: Price ---
st.subheader("Evolução do Preço de Fechamento")
fig_price = go.Figure()
for name in selected_names:
    s = get_series(data, "Close", TICKERS[name])
    fig_price.add_trace(go.Scatter(
        x=s.index, y=s.values, mode="lines", name=name,
        line=dict(color=COLORS[name], width=2),
        hovertemplate="%{x|%d/%m/%Y}<br><b>R$ %{y:.2f}</b><extra>" + name + "</extra>",
    ))
fig_price.update_layout(
    xaxis_title="Data", yaxis_title="Preço (R$)",
    hovermode="x unified", height=430,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
st.plotly_chart(fig_price, use_container_width=True)

# --- Chart 2: Cumulative return ---
st.subheader("Performance Acumulada no Período (%)")
fig_perf = go.Figure()
for name in selected_names:
    s = get_series(data, "Close", TICKERS[name])
    perf = (s / s.iloc[0] - 1) * 100
    fig_perf.add_trace(go.Scatter(
        x=perf.index, y=perf.values, mode="lines", name=name,
        line=dict(color=COLORS[name], width=2),
        hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:+.2f}%</b><extra>" + name + "</extra>",
    ))
fig_perf.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.4)
fig_perf.update_layout(
    xaxis_title="Data", yaxis_title="Retorno acumulado (%)",
    hovermode="x unified", height=430,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
st.plotly_chart(fig_perf, use_container_width=True)

# --- Chart 3: Monthly volume ---
st.subheader("Volume Negociado por Mês (milhões de ações)")
vol_frames = []
for name in selected_names:
    s = get_series(data, "Volume", TICKERS[name])
    monthly = (s.resample("ME").sum() / 1_000_000).reset_index()
    monthly.columns = ["Data", "Volume (M)"]
    monthly["Ação"] = name
    vol_frames.append(monthly)

if vol_frames:
    df_vol = pd.concat(vol_frames, ignore_index=True)
    df_vol["Mês"] = df_vol["Data"].dt.strftime("%b/%Y")
    fig_vol = px.bar(
        df_vol, x="Mês", y="Volume (M)", color="Ação",
        barmode="group", color_discrete_map=COLORS, height=420,
        labels={"Volume (M)": "Volume (milhões)"},
    )
    fig_vol.update_layout(
        xaxis_title="Mês", yaxis_title="Volume (milhões de ações)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_vol, use_container_width=True)

# --- Raw data table ---
with st.expander("Ver dados brutos"):
    frames = []
    for name in selected_names:
        close = get_series(data, "Close", TICKERS[name]).rename("Fechamento (R$)")
        volume = get_series(data, "Volume", TICKERS[name]).rename("Volume")
        df_t = pd.concat([close, volume], axis=1).reset_index()
        df_t.rename(columns={"Date": "Data"}, inplace=True)
        df_t["Data"] = pd.to_datetime(df_t["Data"]).dt.strftime("%d/%m/%Y")
        df_t["Ação"] = name
        frames.append(df_t[["Data", "Ação", "Fechamento (R$)", "Volume"]])
    if frames:
        st.dataframe(pd.concat(frames, ignore_index=True), use_container_width=True)
