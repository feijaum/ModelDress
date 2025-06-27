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

# --- FUNÇÃO IA: Geração de Imagem (Lógica do Vertex AI) ---
def generate_dressed_model(clothing_image: Image.Image, text_prompt: str):
    """
    Usa a lógica do Vertex AI para gerar uma imagem de um modelo
    vestindo uma roupa específica.
    """
    try:
        # CORREÇÃO: Usando o modelo 2.0 solicitado pelo usuário,
        # com a estrutura de chamada correta.
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-preview-image-generation"
        )

        # Criamos o conteúdo multimodal: a imagem da roupa + o prompt de texto
        contents = [clothing_image, text_prompt]

        response = model.generate_content(contents)

        # Extrai os bytes da imagem da resposta
        image_bytes = response.parts[0].inline_data.data
        return Image.open(io.BytesIO(image_bytes))

    except (UnidentifiedImageError, IndexError, AttributeError):
        st.error("A API não retornou uma imagem. Isto pode acontecer se a imagem da roupa não for clara ou o pedido for muito complexo.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro crítico na API: {e}")
        return None


# --- PÁGINA 1: CONFIGURAÇÃO ---
def page_config():
    st.sidebar.title("🤖 Controlo do Provador Virtual")
    st.sidebar.write("Configure as opções para gerar o modelo com a roupa desejada.")
    st.sidebar.write("---")

    # --- Chave da API Gemini (Usando st.secrets para segurança) ---
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Erro ao configurar a API do Google. Verifique se a sua GOOGLE_API_KEY está correta no ficheiro secrets.toml. Detalhes: {e}")
        st.stop()

    # --- Opções do Menu ---
    st.sidebar.header("Características do Modelo")
    faixa_etaria = st.sidebar.selectbox("Faixa Etária:", ("Adolescente", "Jovem Adulto", "Adulto", "Idoso"))
    genero = st.sidebar.selectbox("Gênero:", ("Feminino", "Masculino"))
    etnia = st.sidebar.selectbox("Etnia:", ("Branco(a)", "Negro(a)", "Asiático(a)", "Indígena", "Pardo(a)"))
    tipo_corpo = st.sidebar.selectbox("Tipo de Corpo:", ("Plus Size", "Wellness (Padrão)", "Atleta", "Magro(a)"))
    angulo_modelo = st.sidebar.selectbox("Ângulo do Modelo:", ("De frente, a olhar para a câmara", "De perfil, 3/4", "Corpo inteiro, costas"))

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
    st.title("👕 Provador Virtual com IA 👖")
    st.markdown("Use o menu ao lado para enviar a foto da sua roupa, configurar o modelo e deixar a IA do Vertex criar a imagem final.")
    st.info("Aguardando o envio da foto e o comando para gerar...")

    if gerar_imagem_btn:
        if not uploaded_file:
            st.error("Por favor, envie a imagem de uma peça de roupa.")
        else:
            with st.spinner("Gerando imagem com a nova lógica..."):
                pil_image = Image.open(uploaded_file)

                # Construindo o prompt de texto que descreve o MODELO
                prompt_texto = (
                    f"Gere uma fotografia de moda ultrarrealista, 8k, de um(a) modelo {genero.lower()} {etnia.lower()}, "
                    f"com idade aparente de {faixa_etaria.lower()} e corpo {tipo_corpo.lower()}. "
                    f"O(A) modelo deve estar vestindo a roupa exata mostrada na imagem que estou a fornecer. "
                    f"A pose do(a) modelo é: {angulo_modelo}. "
                    f"O cenário é um fundo de estúdio fotográfico branco e limpo. A iluminação deve ser profissional."
                )

                st.session_state.user_selections = {
                    "clothing_image": pil_image,
                    "text_prompt": prompt_texto
                }

                # Chamada da função de geração
                result = generate_dressed_model(pil_image, prompt_texto)

                if result:
                    st.session_state.generated_image = result
                    st.session_state.page = 'results'
                    st.rerun()

# --- PÁGINA 2: RESULTADOS ---
def page_results():
    st.title("🖼️ Imagem Gerada com Sucesso!")
    st.markdown("Veja o resultado abaixo. Pode voltar e gerar novamente com outras opções.")
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
            with st.spinner("Gerando uma nova imagem com as mesmas opções..."):
                selections = st.session_state.user_selections
                result = generate_dressed_model(selections["clothing_image"], selections["text_prompt"])
                if result:
                    st.session_state.generated_image = result
                    st.rerun()

    # --- Exibição da Imagem ---
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
