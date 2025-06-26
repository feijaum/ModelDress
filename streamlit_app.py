import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Gerador de Prompt para Provador Virtual", layout="wide")

# --- Gerenciamento de Estado (Session State) ---
# Inicializa o estado para armazenar o prompt gerado
if 'prompt_text' not in st.session_state:
    st.session_state.prompt_text = ""

# --- FUNÇÃO IA: Análise de Imagem para Texto ---
def describe_clothing_from_image(pil_image):
    """Usa o Gemini para analisar uma imagem e descrever a roupa."""
    try:
        # CORREÇÃO: Voltando para o 'gemini-1.5-flash'. Ele estava funcional
        # antes de esgotar a quota devido aos testes. É a opção mais estável.
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        prompt = "Você é um especialista em moda. Descreva esta peça de roupa em detalhes para ser usada como prompt em um gerador de imagens. Foque no tipo da peça, cor, estilo, tecido, corte e quaisquer estampas ou detalhes visíveis. Seja conciso e direto."
        response = model.generate_content([prompt, pil_image])
        return response.text
    except Exception as e:
        st.error(f"Erro ao analisar a imagem da roupa: {e}")
        return None

# --- Interface Principal da Aplicação ---
def main_app():
    # --- Barra Lateral (Menu de Controlo) ---
    st.sidebar.title("🤖 Controlo do Gerador de Prompt")
    st.sidebar.write("Configure as opções para gerar o prompt para o seu modelo.")
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
    faixa_etaria = st.sidebar.selectbox("Faixa Etária:", ("Adolescente", "Jovem Adulto", "Adulto", "Idoso"), key="age")
    genero = st.sidebar.selectbox("Gênero:", ("Feminino", "Masculino"), key="gender")
    etnia = st.sidebar.selectbox("Etnia:", ("Branco(a)", "Negro(a)", "Asiático(a)", "Indígena", "Pardo(a)"), key="ethnicity")
    tipo_corpo = st.sidebar.selectbox("Tipo de Corpo:", ("Plus Size", "Wellness (Padrão)", "Atleta", "Magro(a)"), key="body_type")
    angulo_modelo = st.sidebar.selectbox("Ângulo do Modelo:", ("De frente, a olhar para a câmara", "De perfil, 3/4", "Meio de costas"), key="angle")

    st.sidebar.write("---")

    # --- Upload da Roupa ---
    st.sidebar.header("Peça de Roupa")
    uploaded_file = st.sidebar.file_uploader(
        "Envie a foto da roupa (fundo branco é ideal):",
        type=["jpg", "jpeg", "png"]
    )

    st.sidebar.write("---")
    gerar_prompt_btn = st.sidebar.button("✨ Gerar Prompt")

    # --- Conteúdo da Página Principal ---
    st.title("👕 Gerador de Prompt para Provador Virtual 👖")
    st.markdown("Use o menu ao lado para enviar a foto da sua roupa, configurar o modelo e gerar um prompt detalhado para usar no seu gerador de imagens preferido (Gemini Pro, Flash, etc.).")

    # --- LÓGICA DE GERAÇÃO DO PROMPT ---
    if gerar_prompt_btn:
        if not uploaded_file:
            st.error("Por favor, envie a imagem de uma peça de roupa antes de gerar o prompt.")
        else:
            roupa_desc = None
            with st.spinner("Analisando a roupa com IA..."):
                pil_image = Image.open(uploaded_file)
                roupa_desc = describe_clothing_from_image(pil_image)

            if roupa_desc:
                st.success("Descrição da roupa gerada pela IA!")
                
                # Constrói o prompt final
                prompt_texto = (
                    f"Fotografia de moda ultrarrealista, 8k, de corpo inteiro. "
                    f"Um(a) modelo {genero.lower()} {etnia.lower()}, "
                    f"com idade aparente de {faixa_etaria.lower()} e corpo {tipo_corpo.lower()}, "
                    f"vestindo exatamente: '{roupa_desc}'. "
                    f"A pose do(a) modelo é: {angulo_modelo}. "
                    f"O cenário é um fundo de estúdio fotográfico branco e limpo. "
                    f"A iluminação é profissional e suave, destacando a roupa e o(a) modelo."
                )
                st.session_state.prompt_text = prompt_texto

    # --- EXIBIÇÃO DO PROMPT E BOTÃO DE COPIAR ---
    if st.session_state.prompt_text:
        st.write("---")
        st.subheader("✅ Prompt Gerado com Sucesso!")
        
        # Exibe o prompt em uma área de texto
        st.text_area("Prompt:", value=st.session_state.prompt_text, height=200, key="prompt_output")

        # HTML e JavaScript para o botão de copiar
        # Usamos document.execCommand que é mais compatível em iframes do que navigator.clipboard
        js_code = f"""
        <script>
        function copyToClipboard() {{
            const tempTextArea = document.createElement('textarea');
            tempTextArea.value = `{st.session_state.prompt_text.replace("`", "\\`")}`;
            document.body.appendChild(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextArea);
            
            // Fornece feedback visual no botão
            const copyBtn = document.getElementById('copyBtn');
            copyBtn.innerText = 'Copiado!';
            copyBtn.disabled = true;
            setTimeout(() => {{
                copyBtn.innerText = 'Copiar Prompt';
                copyBtn.disabled = false;
            }}, 2000);
        }}
        </script>
        <button id="copyBtn" onclick="copyToClipboard()">Copiar Prompt</button>
        """
        st.components.v1.html(js_code, height=40)


if __name__ == "__main__":
    main_app()
