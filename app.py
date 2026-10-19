
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="TikTok Tag Counter",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #0b0d12;
    color: #f5f7ff;
}
[data-testid="stSidebar"] {
    background: #121722;
}
div[data-testid="stMetric"] {
    background: #151b29;
    border: 1px solid #293247;
    padding: 16px;
    border-radius: 12px;
}
.stButton > button {
    border-radius: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 TikTok Tag Counter")
st.caption("Painel de análise de vídeos — versão gratuita")

with st.sidebar:
    st.header("⚙️ Configurações")

    perfil = st.text_input(
        "Perfil do TikTok",
        value="cortesbatalhasdosfamosos"
    )

    hashtag = st.text_input(
        "Hashtag",
        value="Casalcheck2Clips5K"
    )

    st.divider()

    arquivo = st.file_uploader(
        "Importar dados dos vídeos (CSV)",
        type=["csv"]
    )

st.write(f"**Perfil monitorado:** @{perfil}")
st.write(f"**Hashtag monitorada:** #{hashtag}")

if arquivo is not None:
    try:
        df = pd.read_csv(arquivo)
    except Exception as erro:
        st.error(f"Erro ao ler o CSV: {erro}")
        st.stop()
else:
    df = pd.DataFrame()

if not df.empty:
    df.columns = [
        str(coluna).strip().lower()
        for coluna in df.columns
    ]

    aliases = {
        "play_count": "views",
        "view_count": "views",
        "digg_count": "likes",
        "like_count": "likes",
        "comment_count": "comments",
        "share_count": "shares",
        "text": "description",
        "caption": "description",
        "url": "video_url",
        "link": "video_url"
    }

    df = df.rename(columns=aliases)

    for coluna in [
        "views", "likes", "comments", "shares"
    ]:
        if coluna not in df.columns:
            df[coluna] = 0

        df[coluna] = pd.to_numeric(
            df[coluna], errors="coerce"
        ).fillna(0)

    if "description" not in df.columns:
        df["description"] = ""

    if "video_url" not in df.columns:
        df["video_url"] = ""

    df["engagement_rate"] = (
        (
            df["likes"] +
            df["comments"] +
            df["shares"]
        ) / df["views"].replace(0, float("nan")) * 100
    ).fillna(0).round(2)

    df["revisar"] = (
        (df["views"] >= 1000) &
        (
            df["likes"] /
            df["views"].replace(0, 1) < 0.005
        )
    )

    total_views = int(df["views"].sum())
    total_likes = int(df["likes"].sum())
    media_engajamento = df["engagement_rate"].mean()
    videos_revisar = int(df["revisar"].sum())

else:
    total_views = 0
    total_likes = 0
    media_engajamento = 0
    videos_revisar = 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("🎬 Vídeos", len(df))
col2.metric("👁️ Visualizações", f"{total_views:,}")
col3.metric("❤️ Curtidas", f"{total_likes:,}")
col4.metric(
    "📈 Engajamento médio",
    f"{media_engajamento:.2f}%"
)

st.divider()

esquerda, direita = st.columns(2)

with esquerda:
    st.subheader("📊 Visualizações")

    if not df.empty:
        st.bar_chart(df["views"])
    else:
        st.info("Importe um CSV para visualizar os dados.")

with direita:
    st.subheader("🚩 Vídeos para revisar")
    st.metric("Sinais de engajamento baixo", videos_revisar)

    st.caption(
        "É uma estimativa para revisão, não uma "
        "confirmação de visualizações falsas."
    )

st.subheader("📋 Lista de vídeos")

if not df.empty:
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "📥 Baixar relatório CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=(
            "relatorio_tiktok_" +
            datetime.now().strftime("%Y%m%d_%H%M") +
            ".csv"
        ),
        mime="text/csv"
    )
else:
    st.info(
        "Nenhum dado carregado ainda. "
        "O painel ficará pronto para receber os dados."
    )

st.divider()

st.caption(
    "TikTok Tag Counter • Painel gratuito de análise"
)
