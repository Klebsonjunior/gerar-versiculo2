import streamlit as st
import asyncio
import threading
import edge_tts
import requests
import random
import os
import uuid
import subprocess
import tempfile
import json

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VerseClip",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #13161d !important;
    color: #ddd8cf !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 0 !important; max-width: 680px !important; }

/* HERO */
.hero { text-align:center; padding: 3.5rem 0 2.8rem; border-bottom: 1px solid #252b38; margin-bottom: 2.4rem; }
.hero-eyebrow { font-family:'DM Sans',sans-serif; font-size:0.6rem; font-weight:500; letter-spacing:0.25em; text-transform:uppercase; color:#8a7355; margin-bottom:1.4rem; }
.hero-title { font-family:'Cormorant Garamond',serif; font-size:3.6rem; font-weight:300; color:#ede8df; line-height:1; margin:0 0 0.5rem; letter-spacing:0.06em; }
.hero-title em { font-style:italic; color:#c4a96a; }
.hero-sub { font-family:'DM Sans',sans-serif; font-size:0.8rem; color:#4a4d55; letter-spacing:0.06em; }

/* CARDS */
.card { background:#1e2330; border:1px solid #252b38; border-radius:10px; padding:1.5rem 1.7rem; margin-bottom:1rem; }
.card-label { font-family:'DM Sans',sans-serif; font-size:0.58rem; font-weight:500; letter-spacing:0.22em; text-transform:uppercase; color:#8a7355; margin-bottom:0.8rem; display:block; }

/* INPUTS */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background:#252b38 !important; border:1px solid #343d50 !important; border-radius:7px !important;
    color:#eeeae2 !important; font-family:'DM Sans',sans-serif !important; font-size:0.9rem !important;
    caret-color:#c4a96a !important; line-height:1.6 !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color:#c4a96a66 !important; box-shadow:0 0 0 2px #c4a96a18 !important;
}
[data-testid="stSelectbox"] > div > div {
    background:#252b38 !important; border:1px solid #343d50 !important;
    border-radius:7px !important; color:#eeeae2 !important; font-family:'DM Sans',sans-serif !important;
}
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label {
    display:none !important;
}

/* BOTÃO */
[data-testid="stButton"] > button {
    width:100%; background:linear-gradient(135deg,#c4a96a,#a08848) !important;
    color:#080a0d !important; border:none !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important; font-weight:500 !important;
    font-size:0.75rem !important; letter-spacing:0.2em !important;
    text-transform:uppercase !important; padding:0.85rem 2rem !important;
    transition:opacity .2s, transform .15s !important;
}
[data-testid="stButton"] > button:hover { opacity:.85 !important; transform:translateY(-1px) !important; }

/* DOWNLOAD */
[data-testid="stDownloadButton"] > button {
    width:100%; background:transparent !important; border:1px solid #c4a96a55 !important;
    color:#c4a96a !important; border-radius:8px !important;
    font-family:'DM Sans',sans-serif !important; font-size:0.72rem !important;
    letter-spacing:0.16em !important; text-transform:uppercase !important; margin-top:.6rem !important;
}
[data-testid="stDownloadButton"] > button:hover { background:#c4a96a14 !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background:#0b0d11 !important; border-right:1px solid #181c22 !important; }
[data-testid="stSidebar"] label { color:#4a4d55 !important; font-size:0.7rem !important; letter-spacing:0.1em !important; text-transform:uppercase !important; font-family:'DM Sans',sans-serif !important; }
[data-testid="stSidebar"] input { background:#12151a !important; border:1px solid #21252e !important; color:#ddd8cf !important; border-radius:7px !important; }

/* ALERTS */
[data-testid="stAlert"] { border-radius:8px !important; font-family:'DM Sans',sans-serif !important; font-size:0.82rem !important; }

/* MISC */
hr { border-color:#181c22 !important; margin:2rem 0 !important; }
video { border-radius:10px; border:1px solid #252b38; }
[data-testid="stSpinner"] > div { border-top-color:#c4a96a !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">✦ Criador de Conteúdo Bíblico</div>
  <div class="hero-title">Verse<em>Clip</em></div>
  <div class="hero-sub">TikTok · YouTube Shorts · Reels — em segundos</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  FORMULÁRIO
# ══════════════════════════════════════════════════════════════════════════════

# (API Key e Coleção do Pexels não ficam mais na tela — vêm do st.secrets,
#  configurado uma única vez no painel do Streamlit Cloud)

def obter_secret(nome: str, default: str = "") -> str:
    """Lê um valor de st.secrets sem quebrar se o arquivo secrets.toml não existir."""
    try:
        return st.secrets.get(nome, default)
    except Exception:
        return default


pexels_key     = obter_secret("PEXELS_API_KEY")
colecao_pexels = obter_secret("PEXELS_COLLECTION")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<span class="card-label">① Versículo</span>', unsafe_allow_html=True)
texto_versiculo = st.text_area("Versículo", placeholder="O Senhor é o meu pastor, nada me faltará...", height=100, label_visibility="collapsed")
referencia = st.text_input("Referência", placeholder="Ex: Salmos 23:1", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<span class="card-label">② Voz da Narração</span>', unsafe_allow_html=True)
VOZES = {
    "Fábio — Masculina Profunda": "pt-BR-FabioNeural",
    "Thalita — Feminina Suave":   "pt-BR-ThalitaNeural",
    "Antônio — Masculina Padrão": "pt-BR-AntonioNeural",
    "Francisca — Feminina Padrão":"pt-BR-FranciscaNeural",
}
voz_label = st.selectbox("Voz", list(VOZES.keys()), label_visibility="collapsed")
voz_code  = VOZES[voz_label]
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<span class="card-label">③ Cor da Legenda</span>', unsafe_allow_html=True)
COR_LEGENDA = {
    "Branco":  "#FFFFFF",
    "Creme":   "#FFF5DC",
    "Dourado": "#FFD68C",
}
cor_label = st.selectbox("Cor da legenda", list(COR_LEGENDA.keys()), label_visibility="collapsed")
cor_hex   = COR_LEGENDA[cor_label]
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<span class="card-label">④ Velocidade da Narração</span>', unsafe_allow_html=True)
velocidade = st.slider(
    "Velocidade",
    min_value=0.6,
    max_value=1.0,
    value=0.8,
    step=0.05,
    format="%.2fx",
    label_visibility="collapsed",
)
# Converte para o formato do Edge TTS: 0.8 → "-20%", 0.6 → "-40%", 1.0 → "0%"
_pct = int((velocidade - 1.0) * 100)
voz_rate = f"{_pct}%" if _pct >= 0 else f"{_pct}%"
st.markdown(
    f'<div style="font-size:.72rem;color:#5a6070;margin-top:.2rem;">'
    f'{"Narração mais lenta" if velocidade < 0.9 else "Velocidade normal"} — {velocidade:.2f}x</div>',
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<span class="card-label">⑤ Filtro Cinematográfico</span>', unsafe_allow_html=True)
FILTROS = {
    "✦ Nenhum":                   None,
    "🎬 Teal & Orange":           "teal_orange",
    "🌫️ Fade Claro":              "fade",
    "⬛ Preto e Branco":           "bw",
    "🌅 Dourado (Warm)":          "warm",
    "🌊 Frio (Cool Blue)":        "cool",
    "🎞️ Vintage":                 "vintage",
}
filtro_label = st.selectbox("Filtro", list(FILTROS.keys()), label_visibility="collapsed")
filtro_code  = FILTROS[filtro_label]
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES
# ══════════════════════════════════════════════════════════════════════════════

def session_tmp(suffix: str) -> str:
    uid = st.session_state.setdefault("uid", str(uuid.uuid4())[:8])
    return os.path.join(tempfile.gettempdir(), f"vc_{uid}{suffix}")


async def _gerar_audio_com_timing(texto: str, voz: str, audio_path: str) -> list[dict]:
    """
    Gera o áudio E coleta os WordBoundary timestamps.
    Retorna lista de {word, start_ms, duration_ms}.
    """
    communicate = edge_tts.Communicate(texto, voz, boundary="WordBoundary", rate=voz_rate)
    words = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "word":        chunk["text"],
                "start_ms":    chunk["offset"] // 10000,       # 100ns → ms
                "duration_ms": chunk["duration"] // 10000,
            })

    if not audio_chunks:
        raise edge_tts.exceptions.NoAudioReceived()

    with open(audio_path, "wb") as f:
        for c in audio_chunks:
            f.write(c)

    return words


# Vozes de fallback por voz principal
_FALLBACK_VOZ = {
    "pt-BR-FabioNeural":     "pt-BR-AntonioNeural",
    "pt-BR-ThalitaNeural":   "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural":   "pt-BR-FabioNeural",
    "pt-BR-FranciscaNeural": "pt-BR-ThalitaNeural",
}


def gerar_audio_com_timing(texto: str, voz: str, audio_path: str, rate: str = "-20%") -> tuple[list[dict], str]:
    """
    Roda o async em thread dedicada com event loop próprio.
    Tenta até 3x com a voz escolhida; se falhar, tenta a voz de fallback.
    Retorna (words, voz_usada).
    """
    MAX_TENTATIVAS = 3
    vozes_tentar = [voz]
    fallback = _FALLBACK_VOZ.get(voz)
    if fallback:
        vozes_tentar.append(fallback)

    ultimo_erro = None

    for voz_atual in vozes_tentar:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            resultado = {}

            def _run(v=voz_atual):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    resultado["words"] = loop.run_until_complete(
                        _gerar_audio_com_timing(texto, v, audio_path, rate=rate)
                    )
                except Exception as e:
                    resultado["error"] = e
                finally:
                    loop.close()

            t = threading.Thread(target=_run)
            t.start()
            t.join()

            if "error" not in resultado:
                return resultado["words"], voz_atual
            ultimo_erro = resultado["error"]

    raise ultimo_erro


# ══════════════════════════════════════════════════════════════════════════════
#  COLEÇÃO DO PEXELS (vídeos salvos/favoritados por você no site do Pexels)
# ══════════════════════════════════════════════════════════════════════════════

def extrair_collection_id(valor: str) -> str:
    """
    Aceita o ID puro da coleção (ex: '9mp14cx') ou o link completo copiado
    do site do Pexels (ex: https://www.pexels.com/collections/favoritos-9mp14cx/)
    e retorna apenas o ID.
    """
    valor = valor.strip()
    if not valor:
        return ""
    ultimo = valor.rstrip("/").split("/")[-1]
    if "-" in ultimo:
        return ultimo.split("-")[-1]
    return ultimo


def buscar_videos_da_colecao(api_key: str, collection_id: str, max_paginas: int = 5) -> list[dict]:
    """
    Busca todos os vídeos (ignora fotos) dentro de uma Coleção do Pexels.
    Pagina até max_paginas × 80 itens, o suficiente para qualquer coleção pessoal.
    """
    videos = []
    pagina = 1
    while pagina <= max_paginas:
        try:
            url = (
                f"https://api.pexels.com/v1/collections/{collection_id}"
                f"?type=videos&per_page=80&page={pagina}"
            )
            resp = requests.get(url, headers={"Authorization": api_key}, timeout=15)
            if resp.status_code != 200:
                break
            data = resp.json()
            media = data.get("media", [])
            videos.extend([m for m in media if m.get("type") == "Video"])
            if not data.get("next_page"):
                break
            pagina += 1
        except Exception:
            break
    return videos


def escolher_link_video(videos: list[dict]) -> str | None:
    """
    Sorteia um vídeo da coleção e escolhe o melhor arquivo .mp4 vertical disponível.
    Se o vídeo sorteado não tiver versão vertical boa, tenta outros (até 5);
    no limite, usa o melhor arquivo visto, mesmo que horizontal.
    """
    if not videos:
        return None

    candidatos = videos.copy()
    random.shuffle(candidatos)

    melhor_fallback = None  # (area, width, link)

    for video in candidatos[:5]:
        verticais = []
        for arq in video.get("video_files", []):
            link = arq.get("link", "")
            tipo = arq.get("file_type", "").lower()
            w    = arq.get("width",  0) or 0
            h    = arq.get("height", 0) or 0
            if not ("mp4" in tipo or ".mp4" in link.lower()):
                continue
            if h > w:
                verticais.append((w * h, w, link))
            elif melhor_fallback is None or w * h > melhor_fallback[0]:
                melhor_fallback = (w * h, w, link)
        verticais.sort(reverse=True)
        for _, w, link in verticais:
            if w >= 720:
                return link
        if verticais:
            return verticais[0][2]

    return melhor_fallback[2] if melhor_fallback else None


def baixar_arquivo(url: str, dest: str) -> bool:
    """Baixa com limit de 80 MB para não travar."""
    MAX_BYTES = 80 * 1024 * 1024
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    total += len(chunk)
                    if total > MAX_BYTES:
                        return False
                    f.write(chunk)
        return True
    except Exception:
        return False


def construir_ass(words: list[dict], referencia: str, cor_hex: str, duracao_total_ms: int) -> str:
    """
    Gera arquivo .ass com:
    - Legenda principal: 3–4 palavras por linha, aparece/desaparece sincronizado
    - Referência bíblica: aparece no último terço do vídeo, centralizada embaixo
    """

    def ms_to_ass(ms: int) -> str:
        h   = ms // 3600000
        ms -= h * 3600000
        m   = ms // 60000
        ms -= m * 60000
        s   = ms // 1000
        ms -= s * 1000
        cs  = ms // 10
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    # Cor ASS: &H00BBGGRR (sem alpha)
    r_hex = cor_hex[1:3]
    g_hex = cor_hex[3:5]
    b_hex = cor_hex[5:7]
    ass_color = f"&H00{b_hex}{g_hex}{r_hex}"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
Collisions: Normal

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,PlayfairDisplay-Bold,88,{ass_color},&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,1.5,0,1,4,3,5,80,80,220,1
Style: Ref,PlayfairDisplay-Bold,52,{ass_color},&H000000FF,&H00000000,&HAA000000,0,1,0,0,100,100,3,0,1,3,2,2,80,80,160,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    # Agrupa palavras em blocos de 3–4 palavras
    WORDS_PER_LINE = 3
    lines = []
    i = 0
    while i < len(words):
        bloco = words[i: i + WORDS_PER_LINE]
        start = bloco[0]["start_ms"]
        end   = bloco[-1]["start_ms"] + bloco[-1]["duration_ms"] + 120  # 120ms gap
        text  = " ".join(w["word"] for w in bloco)
        lines.append((start, end, text))
        i += WORDS_PER_LINE

    events = []
    for start, end, text in lines:
        events.append(
            f"Dialogue: 0,{ms_to_ass(start)},{ms_to_ass(end)},Main,,0,0,0,,{text}"
        )

    # Referência: último terço do vídeo
    ref_start = int(duracao_total_ms * 0.70)
    ref_end   = duracao_total_ms + 500
    ref_text  = referencia.upper()
    events.append(
        f"Dialogue: 0,{ms_to_ass(ref_start)},{ms_to_ass(ref_end)},Ref,,0,0,0,,{ref_text}"
    )

    return header + "\n".join(events) + "\n"


def obter_fonte_montserrat() -> str:
    """Baixa Playfair Display Bold para /tmp se não existir."""
    caminho = os.path.join(tempfile.gettempdir(), "PlayfairDisplay-Bold.ttf")
    if not os.path.exists(caminho):
        url = "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf"
        r = requests.get(url, timeout=15, allow_redirects=True)
        r.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(r.content)
    return caminho


# ── Filtros cinematográficos (FFmpeg curves/colorchannelmixer) ────────────
def _filtro_cinematografico(codigo: str | None) -> str:
    """Retorna o fragmento de filtro FFmpeg para o efeito escolhido."""
    if not codigo:
        return ""
    filtros = {
        # Teal & Orange: sombras frias, altas luzes quentes
        "teal_orange": (
            ",colorchannelmixer=rr=1.1:rg=0.05:rb=-0.05:"
            "gr=-0.05:gg=0.95:gb=0.1:"
            "br=-0.1:bg=0.15:bb=1.05,"
            "curves=red=\'0/0 0.5/0.58 1/1\':"
            "blue=\'0/0 0.5/0.52 1/0.9\'"
        ),
        # Fade: levanta negros, reduz contraste (estilo filme antigo)
        "fade": (
            ",curves=all=\'0/0.08 1/0.92\'"
        ),
        # Preto e branco alto contraste
        "bw": (
            ",hue=s=0,"
            "curves=all=\'0/0 0.3/0.15 0.7/0.9 1/1\'"
        ),
        # Warm: empurra vermelhos/amarelos
        "warm": (
            ",colortemperature=temperature=7000,"
            "curves=red=\'0/0 0.5/0.55 1/1\'"
        ),
        # Cool blue: empurra azuis/cianos
        "cool": (
            ",colortemperature=temperature=4500,"
            "curves=blue=\'0/0 0.5/0.55 1/1\'"
        ),
        # Vintage: dessatura + vinheta de cor + fade
        "vintage": (
            ",hue=s=0.5,"
            "curves=red=\'0/0.05 1/0.95\':"
            "blue=\'0/0 1/0.85\',"
            "vignette=PI/4"
        ),
    }
    return filtros.get(codigo, "")


def montar_video_ffmpeg(
    video_path:  str,
    audio_path:  str,
    ass_path:    str,
    output_path: str,
    duracao:     float,
    fonte_path:  str,
    filtro_code: str | None = None,
) -> tuple[bool, str]:
    """
    Monta o vídeo final via FFmpeg puro:
    1. Redimensiona/crop para 1080×1920
    2. Loop ou trim conforme duração do áudio
    3. Aplica filtro cinematográfico (opcional)
    4. Queima legendas ASS (libass)
    5. Mescla áudio
    """
    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    fonts_dir   = os.path.dirname(fonte_path)
    fx          = _filtro_cinematografico(filtro_code)

    # setpts=2.0*PTS = vídeo em 0.5x (dobra a duração visual).
    # scale + crop garante 1080x1920 sem distorção independente da origem.
    # Se portrait: escala pela largura (1080) e corta altura.
    # Se landscape (fallback): escala pela altura (1920) e corta largura.
    filtro = (
        f"[0:v]setpts=2.0*PTS,"
        f"scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop=1080:1920,setsar=1"
        f"{fx},"
        f"ass='{ass_escaped}':fontsdir='{fonts_dir}'[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-t", str(duracao + 0.3),
        "-filter_complex", filtro,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        return False, result.stderr[-1500:]
    return True, ""


def montar_video_sem_fundo(
    audio_path:  str,
    ass_path:    str,
    output_path: str,
    duracao:     float,
    fonte_path:  str,
) -> tuple[bool, str]:
    """Fallback: fundo gradiente escuro gerado pelo próprio FFmpeg."""
    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    fonts_dir   = os.path.dirname(fonte_path)

    filtro = (
        f"color=c=0x0b0c0e:size=1080x1920:rate=24:duration={duracao + 0.5},"
        f"ass='{ass_escaped}':fontsdir='{fonts_dir}'[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x0b0c0e:size=1080x1920:rate=24:duration={duracao + 0.5}",
        "-i", audio_path,
        "-t", str(duracao + 0.5),
        "-filter_complex", f"[0:v]ass='{ass_escaped}':fontsdir='{fonts_dir}'[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return False, result.stderr[-1500:]
    return True, ""


def get_audio_duration_ms(audio_path: str) -> int:
    """Extrai duração do áudio via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        duration_s = float(data["streams"][0]["duration"])
        return int(duration_s * 1000)
    except Exception:
        return 15000  # fallback 15s


# ══════════════════════════════════════════════════════════════════════════════
#  GERAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
gerar = st.button("✦  GERAR VÍDEO")

if gerar:
    if not pexels_key:
        st.error("PEXELS_API_KEY não configurada. Adicione nos Secrets do app (veja secrets.toml.example).")
        st.stop()
    if not colecao_pexels.strip():
        st.error("PEXELS_COLLECTION não configurada. Adicione nos Secrets do app (veja secrets.toml.example).")
        st.stop()
    if not texto_versiculo.strip() or not referencia.strip():
        st.error("Preencha o versículo e a referência.")
        st.stop()

    audio_path  = session_tmp("_audio.mp3")
    video_path  = session_tmp("_fundo.mp4")
    ass_path    = session_tmp("_legendas.ass")
    output_path = session_tmp("_final.mp4")

    prog   = st.progress(0, text="Iniciando...")
    status = st.empty()

    try:
        # ── 1. Narração + timestamps ───────────────────────────────────────
        status.markdown("🎙️ **Sintetizando narração...**")
        prog.progress(10, text="Gerando voz...")

        texto_narrado = f"{texto_versiculo.strip()}. {referencia.strip()}"
        words, voz_usada = gerar_audio_com_timing(texto_narrado, voz_code, audio_path, rate=voz_rate)

        if not words:
            st.error("Não foi possível gerar a narração. Tente novamente.")
            st.stop()

        if voz_usada != voz_code:
            nome_fallback = next((k for k, v in VOZES.items() if v == voz_usada), voz_usada)
            st.warning(f"⚠️ A voz selecionada está indisponível no momento. Usando **{nome_fallback}** automaticamente.")

        duracao_ms = get_audio_duration_ms(audio_path)
        duracao_s  = duracao_ms / 1000

        # ── 2. Legenda ASS ─────────────────────────────────────────────────
        status.markdown("📝 **Gerando legendas sincronizadas...**")
        prog.progress(25, text="Sincronizando legendas...")

        fonte_path = obter_fonte_montserrat()
        ass_content = construir_ass(words, referencia.strip(), cor_hex, duracao_ms)
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        # ── 3. Vídeo de fundo ──────────────────────────────────────────────
        status.markdown("🌊 **Buscando vídeo na sua coleção...**")
        prog.progress(40, text="Buscando na coleção...")

        collection_id  = extrair_collection_id(colecao_pexels)
        videos_colecao = buscar_videos_da_colecao(pexels_key, collection_id)

        if not videos_colecao:
            st.warning("⚠️ Não encontrei vídeos nessa coleção. Verifique o link/ID e se há vídeos salvos nela.")

        link = escolher_link_video(videos_colecao)
        tem_fundo = False

        if link:
            status.markdown("📥 **Baixando vídeo da coleção...**")
            prog.progress(55, text="Baixando fundo...")
            tem_fundo = baixar_arquivo(link, video_path)

        # ── 4. Montagem FFmpeg ─────────────────────────────────────────────
        status.markdown("🎬 **Montando vídeo final...**")
        prog.progress(70, text="Renderizando...")

        if tem_fundo:
            ok, err = montar_video_ffmpeg(video_path, audio_path, ass_path, output_path, duracao_s, fonte_path, filtro_code)
        else:
            status.markdown("🎨 **Sem fundo disponível — usando fundo escuro...**")
            ok, err = montar_video_sem_fundo(audio_path, ass_path, output_path, duracao_s, fonte_path)

        if not ok:
            st.error(f"Erro no FFmpeg:\n```\n{err}\n```")
            st.stop()

        prog.progress(100, text="Pronto!")
        status.empty()

        # ── 5. Resultado ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center;margin-bottom:1rem;">
          <span style="font-family:'Cormorant Garamond',serif;font-size:1.5rem;color:#c4a96a;font-weight:300;">
            ✦ Vídeo pronto
          </span>
        </div>
        """, unsafe_allow_html=True)

        st.video(output_path)

        nome_arquivo = f"verseclip_{referencia.strip().replace(' ','_').replace(':','-')}.mp4"
        with open(output_path, "rb") as f:
            st.download_button("⬇  BAIXAR VÍDEO · MP4", data=f, file_name=nome_arquivo, mime="video/mp4")

        # Debug: mostra timing das palavras em expander
        with st.expander("🔍 Timing das legendas (debug)"):
            for w in words[:20]:
                st.text(f"{w['start_ms']:>6}ms  {w['word']}")

    except Exception as e:
        prog.empty()
        status.empty()
        st.error(f"Erro: {e}")
        import traceback
        st.code(traceback.format_exc())

# FOOTER
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-size:.65rem;color:#2a2d35;padding:.8rem 0;">
  VerseClip v2.0 · 1080×1920 · TikTok & YouTube Shorts<br>
  <span style="color:#181c22;">✦</span>
</div>
""", unsafe_allow_html=True)
