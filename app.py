import streamlit as st
import asyncio
import nest_asyncio
import edge_tts
import requests
import random
import os
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip, CompositeVideoClip
import tempfile

# ── Compatibilidade Pillow ──────────────────────────────────────────────────
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# ── Fix: asyncio dentro do Streamlit ───────────────────────────────────────
nest_asyncio.apply()

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN PREMIUM — CSS INJETADO
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VerseClip · Gerador de Vídeos Bíblicos",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap');

  /* ─ Reset & Base ─ */
  html, body, [data-testid="stAppViewContainer"] {
    background: #0b0c0e !important;
    color: #e8e3db !important;
  }
  [data-testid="stHeader"] { background: transparent !important; }
  [data-testid="stSidebar"] {
    background: #111316 !important;
    border-right: 1px solid #1e2025;
  }
  .block-container { padding-top: 2rem !important; max-width: 720px !important; }

  /* ─ Typography ─ */
  h1, h2, h3 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.04em;
  }
  p, label, div, span, input, textarea, select {
    font-family: 'DM Sans', sans-serif !important;
  }

  /* ─ Hero Header ─ */
  .hero {
    text-align: center;
    padding: 3rem 0 2.5rem;
    border-bottom: 1px solid #1e2025;
    margin-bottom: 2.5rem;
  }
  .hero-badge {
    display: inline-block;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c8a96e;
    border: 1px solid #c8a96e44;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
  }
  .hero-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 3.2rem !important;
    font-weight: 300 !important;
    color: #f0ebe2 !important;
    line-height: 1.1 !important;
    margin: 0 0 0.6rem !important;
    letter-spacing: 0.02em;
  }
  .hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #6b6b72;
    letter-spacing: 0.04em;
  }

  /* ─ Section Labels ─ */
  .section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c8a96e;
    margin-bottom: 0.5rem;
    display: block;
  }

  /* ─ Cards / Panels ─ */
  .card {
    background: #111316;
    border: 1px solid #1e2025;
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
  }
  .card-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    color: #e8e3db;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* ─ Inputs ─ */
  [data-testid="stTextArea"] textarea,
  [data-testid="stTextInput"] input {
    background: #16181d !important;
    border: 1px solid #2a2d35 !important;
    border-radius: 8px !important;
    color: #e8e3db !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: #c8a96e !important;
  }
  [data-testid="stTextArea"] textarea:focus,
  [data-testid="stTextInput"] input:focus {
    border-color: #c8a96e88 !important;
    box-shadow: 0 0 0 2px #c8a96e22 !important;
  }
  [data-testid="stSelectbox"] > div > div {
    background: #16181d !important;
    border: 1px solid #2a2d35 !important;
    border-radius: 8px !important;
    color: #e8e3db !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  /* ─ Labels Streamlit ─ */
  [data-testid="stTextArea"] label,
  [data-testid="stTextInput"] label,
  [data-testid="stSelectbox"] label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6b6b72 !important;
  }

  /* ─ Botão Principal ─ */
  [data-testid="stButton"] > button {
    width: 100%;
    background: linear-gradient(135deg, #c8a96e, #a8894e) !important;
    color: #0b0c0e !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2rem !important;
    cursor: pointer !important;
    transition: opacity 0.2s, transform 0.15s !important;
  }
  [data-testid="stButton"] > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
  }

  /* ─ Mensagens ─ */
  [data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
  }
  .stSuccess { border-color: #2a4a35 !important; background: #0f2018 !important; }
  .stError   { border-color: #4a2a2a !important; background: #200f0f !important; }

  /* ─ Spinner ─ */
  [data-testid="stSpinner"] { color: #c8a96e !important; }

  /* ─ Download button ─ */
  [data-testid="stDownloadButton"] > button {
    width: 100%;
    background: transparent !important;
    border: 1px solid #c8a96e88 !important;
    color: #c8a96e !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin-top: 0.8rem !important;
  }
  [data-testid="stDownloadButton"] > button:hover {
    background: #c8a96e18 !important;
  }

  /* ─ Divider ─ */
  hr { border-color: #1e2025 !important; margin: 2rem 0 !important; }

  /* ─ Video player ─ */
  video { border-radius: 12px; border: 1px solid #1e2025; }

  /* ─ Sidebar ─ */
  [data-testid="stSidebar"] label {
    color: #6b6b72 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
  }
  [data-testid="stSidebar"] input {
    background: #16181d !important;
    border: 1px solid #2a2d35 !important;
    color: #e8e3db !important;
    border-radius: 8px !important;
  }

  /* ─ Step indicator ─ */
  .step-row {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 2rem;
  }
  .step {
    flex: 1;
    height: 3px;
    background: #1e2025;
    border-radius: 2px;
  }
  .step.active { background: #c8a96e; }

  /* ─ Tip box ─ */
  .tip {
    background: #0f1a12;
    border: 1px solid #1e3a24;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    font-size: 0.8rem;
    color: #6b9e78;
    margin-top: 1rem;
  }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — Configuração da API
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ✦ Configuração")
    st.markdown("---")
    pexels_key = st.text_input(
        "Pexels API Key",
        type="password",
        placeholder="Cole sua chave aqui",
        help="Chave gratuita em pexels.com/api"
    )
    st.markdown("""
    <div style="font-size:0.72rem; color:#6b6b72; line-height:1.6; margin-top:1rem;">
    Obtenha sua chave gratuita em<br>
    <a href="https://www.pexels.com/api/" target="_blank" style="color:#c8a96e;">pexels.com/api</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.7rem; color:#3a3a40; line-height:1.6;">
    VerseClip v1.0<br>
    Vídeos 1080×1920 · 24fps<br>
    Formato MP4 · H.264
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-badge">✦ Criador de Conteúdo Bíblico</div>
  <div class="hero-title">VerseClip</div>
  <div class="hero-sub">Vídeos verticais para TikTok & Shorts — em segundos</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FORMULÁRIO
# ══════════════════════════════════════════════════════════════════════════════

# ── Bloco 1: Conteúdo ──
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">① Versículo</div>', unsafe_allow_html=True)

texto_versiculo = st.text_area(
    "Texto do versículo",
    placeholder="O Senhor é o meu pastor, nada me faltará...",
    height=110,
    label_visibility="collapsed",
)
referencia = st.text_input(
    "Referência",
    placeholder="Ex: Salmos 23:1",
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── Bloco 2: Narração ──
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">② Narração</div>', unsafe_allow_html=True)

VOZES = {
    "Fábio — Masculina Profunda (Narrador)": "pt-BR-FabioNeural",
    "Thalita — Feminina Suave (Calma)":       "pt-BR-ThalitaNeural",
    "Antônio — Masculina Padrão":             "pt-BR-AntonioNeural",
    "Francisca — Feminina Padrão":            "pt-BR-FranciscaNeural",
}
voz_label = st.selectbox("Voz", list(VOZES.keys()), label_visibility="collapsed")
voz_code  = VOZES[voz_label]
st.markdown('</div>', unsafe_allow_html=True)

# ── Bloco 3: Visual ──
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">③ Fundo Visual</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    FUNDOS = {
        "🌿 Natureza":   "nature",
        "🌊 Mar":        "sea",
        "⛰️ Montanhas": "mountains",
        "🌲 Floresta":   "forest",
        "💧 Cachoeira":  "waterfall",
        "🌅 Pôr do Sol": "sunset",
    }
    fundo_label = st.selectbox("Cenário", list(FUNDOS.keys()), label_visibility="collapsed")
    estilo_fundo = FUNDOS[fundo_label]

with col2:
    COR_TEXTO = {
        "Branco": (255, 255, 255),
        "Creme":  (255, 245, 220),
        "Dourado": (255, 215, 140),
    }
    cor_label = st.selectbox("Cor do texto", list(COR_TEXTO.keys()), label_visibility="collapsed")
    cor_texto = COR_TEXTO[cor_label]

st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES UTILITÁRIAS
# ══════════════════════════════════════════════════════════════════════════════

async def _gerar_voz_async(texto: str, voz: str, arquivo: str):
    texto_limpo = (
        texto.replace('"', "")
             .replace(";", ".")
             .replace("\n", " ")
             .strip()
    )
    communicate = edge_tts.Communicate(texto_limpo, voz)
    await communicate.save(arquivo)


def gerar_voz(texto: str, voz: str, arquivo: str):
    """Roda o gerador de voz compatível com o event loop do Streamlit."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_gerar_voz_async(texto, voz, arquivo))


def baixar_video_pexels(api_key: str, busca: str = "nature") -> str | None:
    try:
        url = (
            f"https://api.pexels.com/videos/search"
            f"?query={busca}&orientation=portrait&per_page=15"
        )
        resp = requests.get(url, headers={"Authorization": api_key}, timeout=10)
        if resp.status_code != 200:
            return None
        videos = resp.json().get("videos", [])
        random.shuffle(videos)
        for video in videos:
            for arq in video.get("video_files", []):
                link = arq.get("link", "")
                tipo = arq.get("file_type", "").lower()
                if "mp4" in tipo or ".mp4" in link.lower():
                    return link
    except Exception:
        pass
    return None


def quebrar_texto(texto: str, max_chars: int = 26) -> str:
    palavras = texto.split()
    linhas, linha_atual = [], []
    for palavra in palavras:
        if len(" ".join(linha_atual + [palavra])) <= max_chars:
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(" ".join(linha_atual))
            linha_atual = [palavra]
    if linha_atual:
        linhas.append(" ".join(linha_atual))
    return "\n".join(linhas)


@st.cache_data(show_spinner=False)
def obter_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    caminho = os.path.join(tempfile.gettempdir(), "Montserrat-Bold.ttf")
    if not os.path.exists(caminho):
        url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(r.content)
    return ImageFont.truetype(caminho, tamanho)


def session_tempfile(suffix: str) -> str:
    """Arquivo temporário único por sessão para evitar colisões entre usuários."""
    uid = st.session_state.setdefault("uid", str(uuid.uuid4())[:8])
    return os.path.join(tempfile.gettempdir(), f"{uid}{suffix}")


# ══════════════════════════════════════════════════════════════════════════════
#  GERAÇÃO DO VÍDEO
# ══════════════════════════════════════════════════════════════════════════════
gerar = st.button("✦ GERAR VÍDEO")

if gerar:
    if not pexels_key:
        st.error("Insira a Pexels API Key na barra lateral antes de continuar.")
        st.stop()
    if not texto_versiculo.strip() or not referencia.strip():
        st.error("Preencha o versículo e a referência para continuar.")
        st.stop()

    caminho_audio  = session_tempfile("_audio.mp3")
    caminho_bruto  = session_tempfile("_fundo.mp4")
    caminho_final  = session_tempfile("_final.mp4")

    progress = st.progress(0, text="Iniciando...")
    status   = st.empty()

    try:
        # ── 1. Áudio ───────────────────────────────────────────────────────
        status.markdown("🎙️ **Sintetizando narração...**")
        progress.progress(10, text="Gerando voz...")
        gerar_voz(f"{texto_versiculo}. {referencia}", voz_code, caminho_audio)
        audio_clip    = AudioFileClip(caminho_audio)
        duracao_audio = audio_clip.duration

        # ── 2. Vídeo de fundo ──────────────────────────────────────────────
        status.markdown("🌊 **Buscando vídeo de fundo (Pexels)...**")
        progress.progress(30, text="Buscando fundo...")

        usa_fundo_gerado = False
        link_video = baixar_video_pexels(pexels_key, estilo_fundo)

        if link_video:
            try:
                status.markdown("📥 **Baixando vídeo...**")
                res = requests.get(link_video, timeout=20)
                res.raise_for_status()
                with open(caminho_bruto, "wb") as f:
                    f.write(res.content)
                video_fundo = VideoFileClip(caminho_bruto).resize(newsize=(1080, 1920))
                if video_fundo.duration < duracao_audio:
                    video_fundo = video_fundo.loop(duration=duracao_audio)
                else:
                    video_fundo = video_fundo.subclip(0, duracao_audio)
            except Exception:
                usa_fundo_gerado = True
        else:
            usa_fundo_gerado = True

        if usa_fundo_gerado:
            status.markdown("🎨 **Criando fundo dark elegante...**")
            # Gradiente escuro elegante gerado em numpy
            _h, _w = 1920, 1080
            _base = np.zeros((_h, _w, 3), dtype=np.uint8)
            for i in range(_h):
                v = int(10 + 20 * (i / _h))
                _base[i, :] = [v, v + 2, v + 4]
            _bg_frame = _base.copy()

            def fazer_frame_fundo(t):
                return _bg_frame

            video_fundo = VideoClip(fazer_frame_fundo, duration=duracao_audio)

        # ── 3. Overlay de texto ────────────────────────────────────────────
        status.markdown("✍️ **Aplicando tipografia...**")
        progress.progress(60, text="Renderizando texto...")

        texto_formatado = quebrar_texto(texto_versiculo)
        texto_tela      = f"{texto_formatado}\n\n— {referencia.upper()}"

        # Pré-carrega fonte fora do loop de frames (performance)
        font_verso = obter_fonte(56)
        font_ref   = obter_fonte(36)

        def criar_frame_com_texto(get_frame, t):
            frame    = get_frame(t)
            img      = Image.fromarray(frame).convert("RGBA")
            overlay  = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw     = ImageDraw.Draw(overlay)

            W, H = img.size
            cx, cy = W // 2, H // 2

            # Sombra difusa (simula blur com múltiplos offsets)
            shadow_offsets = [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (4, 0)]
            for dx, dy in shadow_offsets:
                draw.text(
                    (cx + dx, cy + dy),
                    texto_tela,
                    font=font_verso,
                    fill=(0, 0, 0, 160),
                    anchor="mm",
                    align="center",
                )

            # Texto principal
            draw.text(
                (cx, cy),
                texto_tela,
                font=font_verso,
                fill=(*cor_texto, 255),
                anchor="mm",
                align="center",
            )

            resultado = Image.alpha_composite(img, overlay).convert("RGB")
            return np.array(resultado)

        video_com_texto = video_fundo.fl(criar_frame_com_texto, keep_duration=True)
        video_final     = video_com_texto.set_audio(audio_clip)

        # ── 4. Exportação ──────────────────────────────────────────────────
        status.markdown("🎬 **Exportando vídeo final...**")
        progress.progress(80, text="Codificando MP4...")

        video_final.write_videofile(
            caminho_final,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            bitrate="1800k",
            threads=2,
            logger=None,
        )

        # ── Limpeza correta de recursos ────────────────────────────────────
        try:
            video_final.close()
        except Exception:
            pass
        try:
            video_fundo.close()
        except Exception:
            pass
        try:
            audio_clip.close()
        except Exception:
            pass

        progress.progress(100, text="Concluído!")
        status.empty()

        # ── 5. Exibição ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; margin-bottom:1rem;">
          <span style="font-family:'Cormorant Garamond',serif; font-size:1.4rem; color:#c8a96e;">
            ✦ Vídeo pronto
          </span>
        </div>
        """, unsafe_allow_html=True)

        st.video(caminho_final)

        with open(caminho_final, "rb") as f:
            st.download_button(
                label="⬇️ BAIXAR VÍDEO · MP4",
                data=f,
                file_name=f"verseclip_{referencia.replace(' ', '_').replace(':', '-')}.mp4",
                mime="video/mp4",
            )

        st.markdown("""
        <div class="tip">
          💡 <strong>Dica para TikTok:</strong> Poste entre 18h–21h para maior alcance orgânico.
          Use hashtags como #palavra #versiculo #shorts no caption.
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"Erro durante a geração: {e}")
        st.markdown("""
        <div style="font-size:0.8rem; color:#6b6b72; margin-top:0.5rem;">
        Verifique sua API Key do Pexels e tente novamente.
        Se o problema persistir, o fundo dark será usado automaticamente.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center; font-size:0.7rem; color:#3a3a40; padding:1rem 0;">
  VerseClip · Vídeos 1080×1920 · TikTok & YouTube Shorts<br>
  <span style="color:#1e2025;">✦</span>
</div>
""", unsafe_allow_html=True)
