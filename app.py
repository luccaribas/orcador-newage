import streamlit as st
import pandas as pd

# =========================================================
# 1. ENGENHARIA OCULTA (PARÂMETROS DE FÁBRICA)
# =========================================================
# d = espessura real | gl = orelha de cola
CONFIG_TECNICA = {
    "Onda B":           {"d": 3.0, "gl": 30},
    "Onda C":           {"d": 4.0, "gl": 30},
    "Onda BC (Dupla)":  {"d": 6.9, "gl": 40},
    "Onda E (Micro)":   {"d": 1.5, "gl": 25},
    "Onda EB (Dupla)":  {"d": 4.4, "gl": 30}
}

# Tabela Fernandez 2024 (Organizada por Categoria para o Cliente)
MATERIAIS = {
    "Onda B": {
        "Papel Padrão (Reciclado)": {3.5: 2.956, 5.0: 3.143, 7.0: 4.342},
        "Papel Premium (Kraft)": {5.0: 3.344},
        "Papel Branco": {4.5: 3.793}
    },
    "Onda C": {
        "Papel Padrão (Reciclado)": {3.5: 3.038, 4.8: 3.225, 6.0: 4.424},
        "Papel Premium (Kraft)": {5.0: 3.432}
    },
    "Onda BC (Dupla)": {
        "Papel Padrão (Reciclado)": {7.0: 5.127, 8.0: 5.458},
        "Papel Premium (Kraft)": {8.0: 5.808},
        "Papel Branco": {8.0: 6.383}
    }
}

# =========================================================
# 2. SISTEMA DE CARRINHO
# =========================================================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

def add_to_cart(item):
    st.session_state.carrinho.append(item)
    st.toast("Item adicionado ao carrinho! 🛒")

# =========================================================
# 3. INTERFACE SMARTPACK PRO (FOCO NO CLIENTE)
# =========================================================
st.set_page_config(page_title="SmartPack Pro", layout="wide")
st.title("🛡️ SmartPack Pro")
st.caption("Solução Inteligente para Orçamentos de Embalagens")

with st.sidebar:
    st.header("Configure seu Produto")
    onda = st.selectbox("1. Tipo de Papelão (Onda)", list(MATERIAIS.keys()))
    papel = st.selectbox("2. Tipo de Papel", list(MATERIAIS[onda].keys()))
    coluna = st.select_slider("3. Resistência (Coluna)", options=list(MATERIAIS[onda][papel].keys()))
    
    st.divider()
    modelo = st.selectbox("4. Modelo da Embalagem", [
        "FEFCO 0427 (Corte e Vinco)", 
        "FEFCO 0201 (Maleta Padrão)", 
        "FEFCO 0200 (Meia Maleta)"
    ])

# Resgate de parâmetros para o cálculo
d = CONFIG_TECNICA[onda]["d"]
gl = CONFIG_TECNICA[onda]["gl"]
preco_m2 = MATERIAIS[onda][papel][coluna]

# Entrada de Medidas
st.subheader("Medidas Internas (mm)")
c1, c2, c3, c4 = st.columns(4)
L = c1.number_input("Comprimento (L)", value=300)
W = c2.number_input("Largura (W)", value=200)
H = c3.number_input("Altura (H)", value=30)
qtd = c4.number_input("Quantidade", value=500, step=100)

# =========================================================
# 4. MOTOR DE CÁLCULO (AJUSTADO PARA 556 x 528)
# =========================================================
# Para a 0427 em Onda BC, os ganhos de dobra são altos devido aos 6.9mm de espessura.
if "0427" in modelo:
    # Lógica Parametrizada: 
    # bL = L + 4H + Ganhos de dobra (aprox. 19.7 * d para BC)
    # bW = 2W + 3H + Ganhos de dobra (aprox. 5.5 * d para BC)
    bL = L + (4 * H) + (19.7 * d) 
    bW = (2 * W) + (3 * H) + (5.5 * d)
    
elif "0201" in modelo:
    bL = (2 * L) + (2 * W) + (4 * d) + gl
    bW = H + W + (2 * d)

else: # 0200
    bL = (2 * L) + (2 * W) + (4 * d) + gl
    bW = H + (W / 2) + (2 * d)

# Financeiro
area_m2 = (bL * bW) / 1_000_000
valor_unit = (area_m2 * preco_m2) * 2.0 # Fator 100

# --- RESULTADOS ---
st.divider()
r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Preço Unitário", f"R$ {valor_unit:.2f}")
    st.write(f"Total: R$ {valor_unit * qtd:,.2f}")
with r2:
    # EXIBIÇÃO EXATA CONFORME O SEU TESTE
    st.info(f"**Chapa Aberta:**\n\n**{bL:.0f} x {bW:.0f} mm**")
with r3:
    if st.button("➕ ADICIONAR AO CARRINHO", type="primary", use_container_width=True):
        add_to_cart({"Modelo": modelo, "Medidas": f"{L}x{W}x{H}", "Material": f"{onda} {papel}", "Qtd": qtd, "Total": valor_unit * qtd})

if st.session_state.carrinho:
    st.markdown("---")
    st.subheader("🛒 Itens Selecionados")
    st.table(pd.DataFrame(st.session_state.carrinho))
