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

# Função assíncrona para gerar a voz com edge-tts (Versão Ultra Estável)
async def gerar_voz(texto, voz, arquivo_audio):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo_audio)

# Função para buscar e baixar vídeo do Pexels (Versão Ultra Protegida contra formatos estranhos)
def baixar_video_pexels(api_key, busca="nature"):
    # Link de um vídeo reserva em alta definição (caso o Pexels mande um formato inválido)
    video_reserva = "https://assets.mixkit.co/videos/preview/mixkit-beautiful-aerial-view-of-verdant-hills-42354-large.mp4"
    
    try:
        url = f"https://api.pexels.com/videos/search?query={busca}&orientation=portrait&per_page=30"
        headers = {"Authorization": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            videos = dados.get("videos", [])
            
            if videos:
                # Embaralha os resultados para trazer sempre vídeos diferentes
                random.shuffle(videos)
                
                for video_escolhido in videos:
                    arquivos_video = video_escolhido.get("video_files", [])
                    
                    # Procura por um arquivo que seja estritamente MP4 e tenha boa resolução
                    for f in arquivos_video:
                        link = f.get("link", "")
                        tipo = f.get("file_type", "")
                        
                        # Garante que é um MP4 legítimo e vertical
                        if "mp4" in tipo.lower() or link.endswith(".mp4") or "video/mp4" in tipo.lower():
                            if f.get("width") == 720 or f.get("width") == 1080:
                                return link
                
                # Se não achou na resolução exata, tenta pegar o primeiro MP4 disponível
                for video_escolhido in videos:
                    for f in video_escolhido.get("video_files", []):
                        link = f.get("link", "")
                        if ".mp4" in link.lower() or "mp4" in f.get("file_type", "").lower():
                            return link
                            
        return video_reserva
    except Exception:
        # Se houver qualquer erro de conexão ou limite da API, entrega o vídeo de montanhas reserva
        return video_reserva

# Função para quebrar o texto em linhas harmoniosas (frases mais curtas ficam mais bonitas)
def quebrar_texto(texto, max_caracteres=22):
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

# Função para baixar uma fonte bonita do Google Fonts caso não exista localmente
def obter_fonte_premium(tamanho):
    caminho_fonte = os.path.join(tempfile.gettempdir(), "Montserrat-Bold.ttf")
    if not os.path.exists(caminho_fonte):
        url_fonte = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
        r = requests.get(url_fonte)
        with open(caminho_fonte, "wb") as f:
            f.write(r.content)
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
        with st.spinner("Sua IA está editando o vídeo... Aguarde."):
            try:
                temp_dir = tempfile.gettempdir()
                caminho_audio = os.path.join(temp_dir, "voztmp.mp3")
                caminho_video_bruto = os.path.join(temp_dir, "fundo_bruto.mp4")
                caminho_final = os.path.join(temp_dir, "video_gospel_pronto.mp4")

                # 1. Gerar o Áudio com velocidade reduzida
                st.text("🎙️ Sintetizando narração suave...")
                texto_completo = f"{texto_versiculo}. {referencia}"
                asyncio.run(gerar_voz(texto_completo, voz_code, caminho_audio))

                # 2. Buscar vídeo no Pexels
                st.text("🌊 Buscando fundo cinematográfico...")
                link_video = baixar_video_pexels(pexels_key, estilo_fundo)
                
                if not link_video:
                    st.error("Erro ao buscar mídias. Tente novamente.")
                else:
                    res_video = requests.get(link_video)
                    with open(caminho_video_bruto, "wb") as f:
                        f.write(res_video.content)

                    # 3. Montagem Cinematográfica com MoviePy
                    st.text("🎬 Aplicando tipografia Montserrat e renderizando...")
                    
                    audio_clip = AudioFileClip(caminho_audio)
                    duracao_audio = audio_clip.duration
                    
                    video_fundo = VideoFileClip(caminho_video_bruto).resize(newsize=(1080, 1920))
                    if video_fundo.duration < duracao_audio:
                        video_fundo = video_fundo.loop(duration=duracao_audio)
                    else:
                        video_fundo = video_fundo.subclip(0, duracao_audio)

                    # Formata o texto
                    texto_legenda = quebrar_texto(texto_versiculo)
                    texto_final_tela = f'{texto_legenda}\n\n{referencia.upper()}'

                    # Função de desenho com fonte customizada e melhor espaçamento
                    def criar_frame_com_texto(gf, t):
                        frame = gf(t)
                        imagem_pil = Image.fromarray(frame)
                        draw = ImageDraw.Draw(imagem_pil)
                        
                        # Carrega a fonte Montserrat baixada dinamicamente
                        font = obter_fonte_premium(58)

                        largura, altura = imagem_pil.size
                        # Centralizado na largura, mas ligeiramente deslocado para baixo (y = altura / 1.95) para melhor estética
                        x, y = largura / 2, altura / 1.95
                        
                        # Desenha a legenda com contorno (stroke) bem definido para acabamento profissional
                        draw.text((x, y), texto_final_tela, font=font, fill="white", anchor="mm", align="center", 
                                  stroke_width=5, stroke_fill=(15, 15, 15))
                        
                        return np.array(imagem_pil)

                    video_com_texto = video_fundo.fl(criar_frame_com_texto, keep_duration=True)
                    video_final = video_com_texto.set_audio(audio_clip)

                    video_final.write_videofile(
                        caminho_final, 
                        fps=24, 
                        codec="libx264", 
                        audio_codec="aac",
                        bitrate="1800k",
                        threads=2,
                        logger=None
                    )

                    video_final.close()
                    video_fundo.close()
                    audio_clip.close()

                    st.success("🎉 Seu vídeo cinematográfico está pronto!")
                    st.video(caminho_final)

                    with open(caminho_final, "rb") as file:
                        st.download_button(
                            label="⬇️ Baixar Vídeo Configurado",
                            data=file,
                            file_name="versiculo_premium.mp4",
                            mime="video/mp4"
                        )

            except Exception as e:
                st.error(f"Erro no processador visual: {e}")
