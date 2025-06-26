!pip install google-generativeai
!pip install pillow
!pip install streamlit

import streamlit as st
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError
import io
import time

# --- Configuração da Página ---
st.set_page_config(page_title="Provador Virtual IA", layout="wide")

# --- Gerenciamento de Estado (Session State) ---
# Inicializa o estado da página e outras variáveis se ainda não existirem.
if 'page' not in st.session_state:
    st.session_state.page = 'config'
if 'generated_image' not in st.session_state: 
    st.session_state.generated_image = None
if 'user_selections' not in st.session_state:
    st.session_state.user_selections = {}


# --- FUNÇÃO IA Nº 1: Análise de Imagem para Texto ---
def describe_clothing_from_image(pil_image):
    """Usa o Gemini 1.5 Flash para analisar uma imagem e descrever a roupa."""
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = "Você é um especialista em moda. Descreva esta peça de roupa em detalhes para ser usada como prompt em um gerador de imagens. Foque no tipo da peça, cor, estilo, tecido, corte e quaisquer estampas ou detalhes visíveis. Seja conciso e direto."
        response = model.generate_content([prompt, pil_image])
        return response.text
    except Exception as e:
        st.error(f"Erro ao analisar a imagem da roupa: {e}")
        st.exception(e)
        return None

# --- FUNÇÃO IA Nº 2: Geração de Imagem a partir de Texto ---
def generate_images_from_api(prompt_texto):
    """Chama a API do Gemini para gerar uma única imagem a partir de um prompt de texto."""
    try:
        # CORREÇÃO: Usando o modelo 'gemini-2.0-flash-preview-image-generation' conforme
        # solicitado e especificando que a resposta deve ser uma imagem.
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-preview-image-generation")

        # Configuração para garantir que a resposta seja uma imagem PNG
        generation_config = genai.types.GenerationConfig(
            response_mime_type="image/png"
        )
        
        response = model.generate_content(prompt_texto, generation_config=generation_config)

        image_bytes = response.parts[0].inline_data.data
        return Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        st.error("A API retornou um resultado que não é uma imagem. Isso pode acontecer com prompts muito complexos ou restritos. Tente novamente com uma descrição diferente.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro na API de Geração de Imagem: {e}")
        st.exception(e)
        return None

# --- PÁGINA 1: CONFIGURAÇÃO ---
def page_config():
    # --- Barra Lateral (Menu de Controlo da IA) ---
    st.sidebar.title("🤖 Controlo do Provador Virtual")
    st.sidebar.write("Configure as opções para gerar o modelo com a roupa desejada.")
    st.sidebar.write("---")

    # --- Chave da API Gemini (Usando st.secrets para segurança) ---
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except (KeyError, AttributeError):
        st.error("A sua GOOGLE_API_KEY não foi encontrada. Por favor, configure-a no ficheiro .streamlit/secrets.toml")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google: {e}")
        st.stop()

    # --- Opções do Menu ---
    st.sidebar.header("Características do Modelo")
    faixa_etaria = st.sidebar.selectbox("Faixa Etária:", ("Adolescente", "Jovem Adulto", "Adulto", "Idoso"))
    genero = st.sidebar.selectbox("Gênero:", ("Feminino", "Masculino"))
    etnia = st.sidebar.selectbox("Etnia:", ("Branco(a)", "Negro(a)", "Asiático(a)", "Indígena", "Pardo(a)"))
    tipo_corpo = st.sidebar.selectbox("Tipo de Corpo:", ("Plus Size", "Wellness (Padrão)", "Atleta", "Magro(a)"))
    angulo_modelo = st.sidebar.selectbox("Ângulo do Modelo:", ("De frente, a olhar para a câmara", "De perfil, 3/4", "Meio de costas"))

    st.sidebar.write("---")

    # --- Upload da Roupa ---
    st.sidebar.header("Peça de Roupa")
    uploaded_file = st.sidebar.file_uploader(
        "Envie a foto da roupa (fundo branco é ideal):",
        type=["jpg", "jpeg", "png"]
    )

    st.sidebar.write("---")
    gerar_imagem_btn = st.sidebar.button("✨ Vestir Modelo e Gerar Imagem")

    # --- Conteúdo da Página Principal ---
    st.title("👕 Provador Virtual com IA Dupla 👖")
    st.markdown("Use o menu ao lado para enviar uma foto da roupa, configurar o modelo e deixar a IA trabalhar.")
    st.info("A aguardar o envio da foto da roupa e o comando para gerar...")

    if gerar_imagem_btn:
        if not uploaded_file:
            st.error("Por favor, envie a imagem de uma peça de roupa antes de gerar o modelo.")
        else:
            roupa_desc = None
            with st.spinner("Analisando a roupa com IA..."):
                pil_image = Image.open(uploaded_file)
                roupa_desc = describe_clothing_from_image(pil_image)

            if roupa_desc:
                st.success(f"Descrição gerada pela IA: {roupa_desc}")
                
                st.session_state.user_selections = {
                    "faixa_etaria": faixa_etaria, "genero": genero, "etnia": etnia,
                    "tipo_corpo": tipo_corpo, "angulo_modelo": angulo_modelo, "roupa_desc": roupa_desc
                }
                
                prompt_texto = (
                    f"Fotografia de moda ultrarrealista, 8k, de corpo inteiro. "
                    f"Um(a) modelo {genero.lower()} {etnia.lower()}, "
                    f"com idade aparente de {faixa_etaria.lower()} e corpo {tipo_corpo.lower()}, "
                    f"vestindo exatamente: '{roupa_desc}'. "
                    f"A pose do(a) modelo é: {angulo_modelo}. "
                    f"O cenário é um fundo de estúdio fotográfico branco e limpo. "
                    f"A iluminação é profissional e suave, destacando a roupa e o(a) modelo."
                )

                with st.spinner("A gerar a imagem... Isto pode levar um momento."):
                    img = generate_images_from_api(prompt_texto)
                    st.session_state.generated_image = img

                if st.session_state.generated_image:
                    st.session_state.page = 'results'
                    st.rerun() 

# --- PÁGINA 2: RESULTADOS ---
def page_results():
    st.title("🖼️ Imagem Gerada pela IA")
    st.markdown("Veja o resultado gerado e pode tentar novamente se desejar.")
    st.write("---")

    # --- Botões de Ação ---
    action_cols = st.columns([1, 1, 3])
    with action_cols[0]:
        if st.button("⬅️ Voltar"):
            st.session_state.page = 'config'
            st.session_state.generated_image = None
            st.rerun()
            
    with action_cols[1]:
        if st.button("🔄 Gerar Novamente"):
            selections = st.session_state.user_selections
            prompt_texto = (
                f"Fotografia de moda ultrarrealista, 8k, de corpo inteiro. "
                f"Um(a) modelo {selections['genero'].lower()} {selections['etnia'].lower()}, "
                f"com idade aparente de {selections['faixa_etaria'].lower()} e corpo {selections['tipo_corpo'].lower()}, "
                f"vestindo exatamente: '{selections['roupa_desc']}'. "
                f"A pose do(a) modelo é: {selections['angulo_modelo']}. "
                f"O cenário é um fundo de estúdio fotográfico branco e limpo. "
                f"A iluminação é profissional e suave."
            )
            with st.spinner("A gerar uma nova imagem..."):
                img = generate_images_from_api(prompt_texto)
                st.session_state.generated_image = img
                st.rerun()

    st.write("---")

    # --- Exibição da Imagem ---
    if not st.session_state.generated_image:
        st.warning("Nenhuma imagem foi gerada ou ocorreu um erro. Por favor, volte e tente novamente.")
        return

    # Exibe a imagem única dentro de um container (caixa) com borda.
    with st.container(border=True):
        st.image(st.session_state.generated_image, caption="Modelo Gerado", use_column_width=True)

        img_bytes = io.BytesIO()
        st.session_state.generated_image.save(img_bytes, format="PNG")
        
        st.download_button(
            label="💾 Guardar Imagem",
            data=img_bytes.getvalue(),
            file_name="modelo_gerado.png",
            mime="image/png",
        )
    
    st.write("---")
    st.subheader("Gerar noutros ângulos")
    st.info("A funcionalidade para gerar noutros ângulos será implementada aqui.")


# --- Roteador Principal ---
if st.session_state.page == 'config':
    page_config()
else:
    page_results()
