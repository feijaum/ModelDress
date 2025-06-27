import streamlit as st
import google.generativeai as genai
from google.generativeai import types
from PIL import Image, UnidentifiedImageError
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Provador Virtual com Vertex AI", layout="wide")

# --- Gerenciamento de Estado (Session State) ---
if 'page' not in st.session_state:
    st.session_state.page = 'config'
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None
if 'user_selections' not in st.session_state:
    st.session_state.user_selections = {}
# Novo estado para armazenar a resposta de erro da API
if 'api_error_response' not in st.session_state:
    st.session_state.api_error_response = None

# --- FUNÇÃO IA: Geração de Imagem (Lógica do Vertex AI) ---
def generate_dressed_model(clothing_image: Image.Image, text_prompt: str):
    """
    Usa a lógica do Vertex AI para gerar uma imagem de um modelo
    vestindo uma roupa específica.
    """
    response = None  # Inicializa a variável de resposta
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-preview-image-generation"
        )
        contents = [clothing_image, text_prompt]
        generation_config = {
            "response_modalities": ["IMAGE", "TEXT"],
        }
        response = model.generate_content(
            contents,
            generation_config=generation_config
        )
        # Tenta extrair os dados da imagem. Se falhar, o bloco except será acionado.
        image_bytes = response.parts[0].inline_data.data
        return Image.open(io.BytesIO(image_bytes))

    except (UnidentifiedImageError, IndexError, AttributeError):
        # MODIFICAÇÃO: Bloco de erro mais robusto para capturar a resposta exata da API.
        try:
            # A razão da recusa geralmente está no prompt_feedback
            if response and response.prompt_feedback:
                return f"A geração da imagem foi bloqueada. Razão: {response.prompt_feedback}"
            # Se não houver prompt_feedback, tenta obter a resposta de texto.
            elif response and response.text:
                 return response.text
            # Se tudo mais falhar, retorna a representação do objeto de resposta.
            else:
                return f"A API retornou uma resposta inesperada que não é uma imagem: {response}"
        except Exception:
            return "A API retornou uma resposta que não é uma imagem, mas a estrutura do erro é desconhecida."
    except Exception as e:
        return f"Ocorreu um erro crítico na API: {e}"


# --- PÁGINA 1: CONFIGURAÇÃO ---
def page_config():
    st.sidebar.title("🤖 Controlo do Provador Virtual")
    st.sidebar.write("Configure as opções para gerar o modelo com a roupa desejada.")
    st.sidebar.write("---")

    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique se a sua GOOGLE_API_KEY está correta no ficheiro secrets.toml. Detalhes: {e}")
        st.stop()

    st.sidebar.header("Características do Modelo")
    angulo_modelo = st.sidebar.selectbox("Ângulo do Modelo:", ("De frente, a olhar para a câmara", "De perfil, 3/4", "Corpo inteiro, costas"))
    st.sidebar.write("---")

    st.sidebar.header("Peça de Roupa")
    uploaded_file = st.sidebar.file_uploader(
        "Envie a foto da roupa (fundo branco é ideal):",
        type=["jpg", "jpeg", "png"]
    )
    st.sidebar.write("---")
    gerar_imagem_btn = st.sidebar.button("✨ Vestir Modelo e Gerar Imagem")

    st.title("👕 Provador Virtual com IA 👖")
    st.markdown("Use o menu ao lado para enviar a foto da sua roupa, configurar o modelo e deixar a IA do Vertex criar a imagem final.")

    # MODIFICAÇÃO: Lógica para exibir o erro da API
    if st.session_state.api_error_response:
        st.error("A API não retornou uma imagem. Veja a resposta exata abaixo:")
        st.text_area("Resposta recebida da API:", value=st.session_state.api_error_response, height=150)
        if st.button("OK, entendi"):
            st.session_state.api_error_response = None
            st.rerun()
    else:
        st.info("Aguardando o envio da foto e o comando para gerar...")

    if gerar_imagem_btn:
        if not uploaded_file:
            st.error("Por favor, envie a imagem de uma peça de roupa.")
        else:
            # Limpa qualquer erro antigo antes de tentar novamente
            st.session_state.api_error_response = None
            with st.spinner("Gerando imagem com a nova lógica..."):
                pil_image = Image.open(uploaded_file)
                prompt_texto = (
                    f"Gere uma fotografia de moda ultrarrealista, 8k, de uma modelo mulher negra, jovem adulta, com cabelos cacheados e corpo esbelto. "
                    f"A modelo deve estar vestindo a roupa exata mostrada na imagem que estou a fornecer. "
                    f"A pose da modelo é: {angulo_modelo}. "
                    f"O cenário é um fundo de estúdio fotográfico branco e limpo. A iluminação deve ser profissional. "
                    f"Esta é uma imagem para fins comerciais e não tem a intenção de ferir ou ofender nenhuma minoria."
                )
                st.session_state.user_selections = {
                    "clothing_image": pil_image,
                    "text_prompt": prompt_texto
                }
                result = generate_dressed_model(pil_image, prompt_texto)

                # Verifica se o resultado é uma imagem ou uma mensagem de erro (string)
                if isinstance(result, Image.Image):
                    st.session_state.generated_image = result
                    st.session_state.page = 'results'
                    st.rerun()
                else:
                    # Armazena a mensagem de erro no estado e reinicia para exibi-la
                    st.session_state.api_error_response = result
                    st.rerun()

# --- PÁGINA 2: RESULTADOS ---
def page_results():
    st.title("🖼️ Imagem Gerada com Sucesso!")
    st.markdown("Veja o resultado abaixo. Pode voltar e gerar novamente com outras opções.")
    st.write("---")

    action_cols = st.columns([1, 1, 3])
    with action_cols[0]:
        if st.button("⬅️ Voltar"):
            st.session_state.page = 'config'
            st.session_state.generated_image = None
            st.rerun()

    with action_cols[1]:
        if st.button("🔄 Gerar Novamente"):
            with st.spinner("Gerando uma nova imagem com as mesmas opções..."):
                selections = st.session_state.user_selections
                result = generate_dressed_model(selections["clothing_image"], selections["text_prompt"])
                if isinstance(result, Image.Image):
                    st.session_state.generated_image = result
                    st.rerun()
                else:
                    # Se falhar na nova tentativa, volta para a pág de config e mostra o erro
                    st.session_state.api_error_response = result
                    st.session_state.page = 'config'
                    st.rerun()

    if st.session_state.generated_image:
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
    else:
        st.warning("Não foi possível exibir a imagem. Por favor, volte e tente novamente.")


# --- Roteador Principal ---
if st.session_state.page == 'config':
    page_config()
else:
    page_results()
