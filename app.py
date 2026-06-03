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

# Configuração da página do Streamlit
st.set_page_config(page_title="Gerador de Vídeos Bíblicos", page_icon="📖", layout="centered")

st.title("📖 Gerador de Vídeos Bíblicos Curtos")
st.write("Crie vídeos verticais para Reels, TikTok e Shorts totalmente de graça.")

# Sidebar para configurações de chaves e créditos
st.sidebar.header("Configurações Básicas")
pexels_key = st.sidebar.text_input("Sua API Key do Pexels", type="password", help="Insira sua chave gratuita do Pexels.")

# Função assíncrona para gerar a voz com edge-tts
async def gerar_voz(texto, voz, arquivo_audio):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo_audio)

# Função para buscar e baixar vídeo do Pexels
def baixar_video_pexels(api_key, busca="nature"):
    url = f"https://api.pexels.com/videos/search?query={busca}&orientation=portrait&per_page=15"
    headers = {"Authorization": api_key}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dados = response.json()
        videos = dados.get("videos", [])
        if videos:
            video_escolhido = random.choice(videos)
            # Pega o arquivo de menor resolução/vertical para economizar memória do Streamlit
            arquivos_video = video_escolhido.get("video_files", [])
            for f in arquivos_video:
                if f.get("width") == 720 or f.get("width") == 1080:
                    return f.get("link")
            return arquivos_video[0].get("link") if arquivos_video else None
    return None

# Função para quebrar o texto em linhas para caber na tela do celular
def quebrar_texto(texto, max_caracteres=25):
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

# Interface de entrada do usuário
texto_versiculo = st.text_area("Digite o Versículo Bíblico:", placeholder="Ex: O Senhor é o meu pastor, nada me faltará.")
referencia = st.text_input("Referência Bíblica:", placeholder="Ex: Salmos 23:1")

opcao_voz = st.selectbox(
    "Escolha a voz da Narração:",
    options=["pt-BR-AntonioNeural (Masculina)", "pt-BR-FranciscaNeural (Feminina)"],
    index=0
)
voz_code = opcao_voz.split(" ")[0]

estilo_fundo = st.selectbox(
    "Estilo do vídeo de fundo (Pexels):",
    options=["nature", "sea", "mountains", "forest", "waterfall"],
    index=0
)

# Botão principal de execução
if st.button("✨ Gerar Vídeo"):
    if not pexels_key:
        st.error("Por favor, insira sua API Key do Pexels na barra lateral.")
    elif not texto_versiculo or not referencia:
        st.error("Por favor, preencha o versículo e a referência.")
    else:
        with st.spinner("Processando... Isso pode levar de 1 a 2 minutos."):
            try:
                # Criando arquivos temporários para não estourar o armazenamento do servidor
                temp_dir = tempfile.gettempdir()
                caminho_audio = os.path.join(temp_dir, "voztmp.mp3")
                caminho_video_bruto = os.path.join(temp_dir, "fundo_bruto.mp4")
                caminho_final = os.path.join(temp_dir, "video_gospel_pronto.mp4")

                # Passo 1: Gerar o Áudio da Voz
                st.text("🎙️ Gerando a narração...")
                texto_completo = f"{texto_versiculo}. {referencia}"
                asyncio.run(gerar_voz(texto_completo, voz_code, caminho_audio))

                # Passo 2: Buscar vídeo no Pexels
                st.text("🌊 Buscando vídeo de paisagem de graça...")
                link_video = baixar_video_pexels(pexels_key, estilo_fundo)
                
                if not link_video:
                    st.error("Não encontramos vídeos no Pexels com essa palavra-chave. Tente outra.")
                else:
                    # Download do vídeo de fundo
                    res_video = requests.get(link_video)
                    with open(caminho_video_bruto, "wb") as f:
                        f.write(res_video.content)

                    # Passo 3: Montagem do vídeo com MoviePy e Legenda manual (Pillow)
                    st.text("🎬 Juntando áudio, vídeo e aplicando as legendas...")
                    
                    audio_clip = AudioFileClip(caminho_audio)
                    duracao_audio = audio_clip.duration
                    
                    video_fundo = VideoFileClip(caminho_video_bruto).resize(newsize=(1080, 1920))
                    # Se o vídeo de fundo for menor que o áudio, ele entra em loop
                    if video_fundo.duration < duracao_audio:
                        video_fundo = video_fundo.loop(duration=duracao_audio)
                    else:
                        video_fundo = video_fundo.subclip(0, duracao_audio)

                    # Prepara o texto formatado com quebras de linha
                    texto_legenda = quebrar_texto(texto_versiculo)
                    texto_final_tela = f'"{texto_legenda}"\n\n- {referencia}'

                    # Função interna para desenhar o texto em cada frame sem depender de ImageMagick
                    def criar_frame_com_texto(gf, t):
                        frame = gf(t) # pega o frame original do vídeo (Matriz NumPy)
                        imagem_pil = Image.fromarray(frame)
                        draw = ImageDraw.Draw(imagem_pil)
                        
                        # Usando a fonte padrão do sistema disponível no Linux/Streamlit Cloud
                        try:
                            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 55)
                        except IOError:
                            font = ImageFont.load_default()

                        # Desenha uma leve sombra preta atrás para dar leitura
                        largura, altura = imagem_pil.size
                        x, y = largura / 2, altura / 2
                        
                        # Renderiza o texto de forma centralizada
                        draw.text((x, y), texto_final_tela, font=font, fill="white", anchor="mm", align="center", 
                                  stroke_width=4, stroke_fill="black")
                        
                        return np.array(imagem_pil)

                    # Aplica a função de renderização de texto frame por frame no vídeo
                    video_com_texto = video_fundo.fl(criar_frame_com_texto, keep_duration=True)
                    video_final = video_com_texto.set_audio(audio_clip)

                    # Exporta o vídeo final reduzindo o bitrate para não estourar a memória do Streamlit
                    video_final.write_videofile(
                        caminho_final, 
                        fps=24, 
                        codec="libx264", 
                        audio_codec="aac",
                        bitrate="1500k",
                        threads=2,
                        logger=None
                    )

                    # Fecha os arquivos abertos na memória
                    video_final.close()
                    video_fundo.close()
                    audio_clip.close()

                    # Exibe o resultado final na tela do site
                    st.success("🎉 Seu vídeo está pronto!")
                    st.video(caminho_final)

                    # Botão para baixar o vídeo gerado
                    with open(caminho_final, "rb") as file:
                        st.download_button(
                            label="⬇️ Baixar Vídeo para o Dispositivo",
                            data=file,
                            file_name="video_biblico_diario.mp4",
                            mime="video/mp4"
                        )

            except Exception as e:
                st.error(f"Ocorreu um erro inesperado no processamento: {e}")
