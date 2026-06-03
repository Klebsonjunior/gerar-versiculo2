import streamlit as st
import asyncio
import edge_tts
import requests
import random
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip
import tempfile

# Correção para o erro de compatibilidade do Pillow/MoviePy
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# Configuração da página do Streamlit
st.set_page_config(page_title="Gerador de Vídeos Bíblicos", page_icon="📖", layout="centered")

st.title("📖 Gerador de Vídeos Bíblicos Premium")
st.write("Crie vídeos verticais com tipografia elegante e narração suave.")

# Sidebar para configurações de chaves
st.sidebar.header("Configurações Básicas")
pexels_key = st.sidebar.text_input("Sua API Key do Pexels", type="password", help="Insira sua chave gratuita do Pexels.")

# Função assíncrona para gerar a voz com edge-tts (Versão Limpa para Textos Longos)
async def gerar_voz(texto, voz, arquivo_audio):
    # Remove aspas e caracteres que quebram a API da Microsoft
    texto_limpo = texto.replace('"', '').replace(';', '.').replace('\n', ' ').strip()
    communicate = edge_tts.Communicate(texto_limpo, voz)
    await communicate.save(arquivo_audio)

# Função para buscar vídeo no Pexels filtrando estritamente por MP4
def baixar_video_pexels(api_key, busca="nature"):
    try:
        url = f"https://api.pexels.com/videos/search?query={busca}&orientation=portrait&per_page=15"
        headers = {"Authorization": api_key}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            videos = dados.get("videos", [])
            if videos:
                random.shuffle(videos)
                for video in videos:
                    for arquivo in video.get("video_files", []):
                        link = arquivo.get("link", "")
                        # Só aceita se o link contiver explicitamente .mp4 ou for tipo mp4
                        if "mp4" in arquivo.get("file_type", "").lower() or ".mp4" in link.lower():
                            return link
    except Exception:
        pass
    return None

# Função para quebrar o texto em linhas harmoniosas
def quebrar_texto(texto, max_caracteres=24):
    palavras = texto.split()
    linhas = []
    linha_atual = []
    for palavra in palavras:
        if len(" ".join(linha_atual + [palavra])) <= max_caracteres:
            linha_atual.append(palavra)
        else:
            linhas.append(" ".join(linha_atual))
            linha_atual = [palavra]
    if linha_atual:
        linhas.append(" ".join(linha_atual))
    return "\n".join(linhas)

# Função para baixar a fonte Montserrat Bold
def obter_fonte_premium(tamanho):
    caminho_fonte = os.path.join(tempfile.gettempdir(), "Montserrat-Bold.ttf")
    if not os.path.exists(caminho_fonte):
        url_fonte = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
        try:
            r = requests.get(url_fonte, timeout=10)
            with open(caminho_fonte, "wb") as f:
                f.write(r.content)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.truetype(caminho_fonte, tamanho)

# Interface de entrada do usuário
texto_versiculo = st.text_area("Digite o Versículo Bíblico:", placeholder="Ex: O Senhor é o meu pastor, nada me faltará.")
referencia = st.text_input("Referência Bíblica:", placeholder="Ex: Salmos 23:1")

opcao_voz = st.selectbox(
    "Escolha o estilo de Narração Suave:",
    options=[
        "pt-BR-FabioNeural (Masculina - Voz Profunda/Narrador)", 
        "pt-BR-ThalitaNeural (Feminina - Voz Suave/Calma)",
        "pt-BR-AntonioNeural (Masculina - Padrão)", 
        "pt-BR-FranciscaNeural (Feminina - Padrão)"
    ],
    index=0
)
voz_code = opcao_voz.split(" ")[0]

estilo_fundo = st.selectbox(
    "Estilo do vídeo de fundo (Pexels):",
    options=["nature", "sea", "mountains", "forest", "waterfall"],
    index=0
)

if st.button("✨ Gerar Vídeo Premium"):
    if not pexels_key:
        st.error("Por favor, insira sua API Key do Pexels na barra lateral.")
    elif not texto_versiculo or not referencia:
        st.error("Por favor, preencha o versículo e a referência.")
    else:
        with st.spinner("Editando seu vídeo... Por favor aguarde."):
            try:
                temp_dir = tempfile.gettempdir()
                caminho_audio = os.path.join(temp_dir, "voztmp.mp3")
                caminho_video_bruto = os.path.join(temp_dir, "fundo_bruto.mp4")
                caminho_final = os.path.join(temp_dir, "video_gospel_pronto.mp4")

                # 1. Gerar o Áudio
                st.text("🎙️ Sintetizando narração...")
                texto_completo = f"{texto_versiculo}. {referencia}"
                asyncio.run(gerar_voz(texto_completo, voz_code, caminho_audio))

                audio_clip = AudioFileClip(caminho_audio)
                duracao_audio = audio_clip.duration

                # 2. Buscar vídeo no Pexels com Fallback Automático Securitário
                st.text("🌊 Buscando vídeo de fundo...")
                link_video = baixar_video_pexels(pexels_key, estilo_fundo)
                
                usa_fundo_gerado = False
                if link_video:
                    try:
                        res_video = requests.get(link_video, timeout=15)
                        with open(caminho_video_bruto, "wb") as f:
                            f.write(res_video.content)
                        video_fundo = VideoFileClip(caminho_video_bruto).resize(newsize=(1080, 1920))
                        if video_fundo.duration < duracao_audio:
                            video_fundo = video_fundo.loop(duration=duracao_audio)
                        else:
                            video_fundo = video_fundo.subclip(0, duracao_audio)
                    except Exception:
                        usa_fundo_gerado = True
                else:
                    usa_fundo_gerado = True

                # Se o Pexels falhar ou trouxer formato inválido, gera um fundo Dark Estético nativo
                if usa_fundo_gerado:
                    st.text("🎨 Formato externo indisponível. Criando fundo Dark Estético...")
                    def fazer_frame_fundo(t):
                        # Cria uma imagem cinza bem escuro quase preto (estilo elegante)
                        return np.full((1920, 1080, 3), 18, dtype=np.uint8)
                    video_fundo = VideoClip(fazer_frame_fundo, duration=duracao_audio)

                # 3. Formatar as Legendas e Renderizar
                st.text("🎬 Aplicando tipografia Montserrat...")
                texto_legenda = quebrar_texto(texto_versiculo)
                texto_final_tela = f'{texto_legenda}\n\n{referencia.upper()}'

                def criar_frame_com_texto(gf, t):
                    frame = gf(t)
                    imagem_pil = Image.fromarray(frame)
                    draw = ImageDraw.Draw(imagem_pil)
                    
                    font = obter_fonte_premium(55)
                    largura, altura = imagem_pil.size
                    x, y = largura / 2, altura / 2
                    
                    # Se for fundo gerado (escuro), usa contorno sutil. Se for paisagem, usa contorno forte.
                    st_width = 2 if usa_fundo_gerado else 5
                    draw.text((x, y), texto_final_tela, font=font, fill="white", anchor="mm", align="center", 
                              stroke_width=st_width, stroke_fill=(0, 0, 0))
                    
                    return np.array(imagem_pil)

                video_com_texto = video_fundo.fl(criar_frame_com_texto, keep_duration=True)
                video_final = video_com_texto.set_audio(audio_clip)

                # Exportação Otimizada
                video_final.write_videofile(
                    caminho_final, 
                    fps=24, 
                    codec="libx264", 
                    audio_codec="aac",
                    bitrate="1500k",
                    threads=2,
                    logger=None
                )

                video_final.close()
                video_fundo.close()
                audio_clip.close()

                st.success("🎉 Seu vídeo foi gerado com sucesso!")
                st.video(caminho_final)

                with open(caminho_final, "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar Vídeo Pronto",
                        data=file,
                        file_name="versiculo_final.mp4",
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"Ocorreu um erro na renderização: {e}")

            except Exception as e:
                st.error(f"Erro no processador visual: {e}")
