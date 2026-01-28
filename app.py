import streamlit as st

# =========================================================
# 1. PARÂMETROS TÉCNICOS (ENGENHARIA PRINECT)
# =========================================================
CONFIG_TECNICA = {
    "Onda B":           {"d": 3.0, "gl": 30},
    "Onda C":           {"d": 4.0, "gl": 30},
    "Onda BC (Dupla)":  {"d": 6.9, "gl": 40},
    "Onda E (Micro)":   {"d": 1.5, "gl": 25},
    "Onda EB (Dupla)":  {"d": 4.4, "gl": 30}
}

# =========================================================
# 2. BANCO DE DADOS FERNANDEZ (ONDA -> QUALIDADE -> COLUNA)
# =========================================================
DADOS_MATERIAIS = {
    "Onda B": {
        "FK1L-B": {"coluna": 3.5, "preco": 2.956},
        "FK2S-B": {"coluna": 4.0, "preco": 2.770},
        "FK2-B":  {"coluna": 5.0, "preco": 3.143},
        "FK2E1-B": {"coluna": 5.5, "preco": 3.473},
        "FK2E3-B": {"coluna": 6.0, "preco": 4.011},
        "FK2E4-B": {"coluna": 7.0, "preco": 4.342},
        "KMKS-B": {"coluna": 4.0, "preco": 2.948},
        "KMK-B":  {"coluna": 5.0, "preco": 3.344},
        "BMC-B":  {"coluna": 5.0, "preco": 3.793},
    },
    "Onda C": {
        "FK1L-C": {"coluna": 3.5, "preco": 3.038},
        "FK2S-C": {"coluna": 4.0, "preco": 2.853},
        "FK2-C":  {"coluna": 4.8, "preco": 3.225},
        "FK2E1-C": {"coluna": 5.0, "preco": 3.556},
        "FK2E3-C": {"coluna": 5.5, "preco": 4.094},
        "FK2E4-C": {"coluna": 6.0, "preco": 4.424},
        "KMKS-C": {"coluna": 4.0, "preco": 3.036},
        "KMK-C":  {"coluna": 5.0, "preco": 3.432},
        "BMC-C":  {"coluna": 5.0, "preco": 3.885},
    },
    "Onda BC (Dupla)": {
        "FK1L-BC": {"coluna": 7.0, "preco": 5.008},
        "FK2S-BC": {"coluna": 7.5, "preco": 4.673},
        "FK2L-BC": {"coluna": 8.0, "preco": 5.127},
        "FK2-BC":  {"coluna": 8.0, "preco": 5.458},
        "FK2E1-BC": {"coluna": 8.5, "preco": 6.120},
        "FK2E3-BC": {"coluna": 9.5, "preco": 6.699},
        "KMKS-BC": {"coluna": 8.0, "preco": 5.324},
        "KMK-BC":  {"coluna": 8.0, "preco": 5.808},
        "BMC-BC":  {"coluna": 8.0, "preco": 6.383},
    },
    "Onda E (Micro)": {
        "FK1L-E": {"coluna": 3.5, "preco": 2.961},
        "FK2L-E": {"coluna": 4.0, "preco": 3.067},
    },
    "Onda EB (Dupla)": {
        "FK1L-EB": {"coluna": 7.5, "preco": 5.034},
        "FK2L-EB": {"coluna": 8.0, "preco": 5.155},
    }
}

# =========================================================
# 3. INTERFACE E LÓGICA
# =========================================================
st.set_page_config(page_title="New Age - Orçador Técnico", layout="wide")
st.title("📦 Sistema de Orçamentos New Age Embalagens")

with st.sidebar:
    st.header("1. Seleção de Material")
    
    # PASSO 1: ONDA
    onda_selecionada = st.selectbox("Selecione a Onda", list(DADOS_MATERIAIS.keys()))
    
    # PASSO 2: PAPEL (Baseado na Onda)
    opcoes_papel = list(DADOS_MATERIAIS[onda_selecionada].keys())
    papel_selecionado = st.selectbox("Selecione o Papel/Qualidade", opcoes_papel)
    
    # PASSO 3: COLUNA (Informativo e vinculado)
    dados_final = DADOS_MATERIAIS[onda_selecionada][papel_selecionado]
    coluna_min = dados_final["coluna"]
    preco_m2 = dados_final["preco"]
    
    st.success(f"Resistência Coluna: {coluna_min} Kgf/cm")
    
    st.header("2. Modelo FEFCO")
    modelo = st.selectbox("Selecione o Modelo", [
        "0200 (Meia Maleta)", 
        "0201 (Maleta Comum)", 
        "0202 (Aba Sobreposta Parcial)", 
        "0203 (Aba Total - FOL)", 
        "0204 (Abas que se encontram no centro)",
        "0427 (Corte e Vinco - Maleta de Envio)",
        "0421 (Corte e Vinco - Tray)",
        "0300 (Telescópica - Fundo)",
        "0901 (Acessório - Almofada/Pad)"
    ])

# Parâmetros Geométricos
d = CONFIG_TECNICA[onda_selecionada]["d"]
gl = CONFIG_TECNICA[onda_selecionada]["gl"]

# --- ENTRADA DE MEDIDAS ---
st.subheader(f"Medidas Internas (mm) - {papel_selecionado}")
c1, c2, c3, c4 = st.columns(4)
L = c1.number_input("Comprimento (L)", value=300)
W = c2.number_input("Largura (W)", value=200)
H = c3.number_input("Altura (H)", value=150)
qtd = c4.number_input("Quantidade", value=500, step=100)

# =========================================================
# 4. MOTOR DE CÁLCULO AMPLIADO (FEFCO LIBRARY)
# =========================================================
if "0200" in modelo:
    bL, bW = (2*L + 2*W + gl), (H + W/2 + d)
elif "0201" in modelo:
    bL, bW = (2*L + 2*W + gl), (H + W + d)
elif "0202" in modelo:
    bL, bW = (2*L + 2*W + gl), (H + W + d + 30) # Sobreposição de 30mm
elif "0203" in modelo:
    bL, bW = (2*L + 2*W + gl), (H + 2*W + d) # Aba Total (Overlap Total)
elif "0204" in modelo:
    bL, bW = (2*L + 2*W + gl), (H + W + d)
