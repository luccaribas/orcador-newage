import streamlit as st
import pandas as pd

# --- BANCO DE DADOS FERNANDEZ 2024 (TODAS AS 31 CHAPAS) ---
# Extraído da sua planilha oficial
BASE_MATERIAIS = [
    # ONDA B
    {"id": "FK1L-B", "onda": "B", "tipo": "Reciclado", "coluna": "3.5", "m2": 2.956, "gram": 360},
    {"id": "FK2S-B", "onda": "B", "tipo": "Reciclado", "coluna": "4.0", "m2": 2.770, "gram": 335},
    {"id": "FK2-B", "onda": "B", "tipo": "Reciclado", "coluna": "5.0", "m2": 3.143, "gram": 380},
    {"id": "FK2E1-B", "onda": "B", "tipo": "Reciclado", "coluna": "5.5", "m2": 3.473, "gram": 420},
    {"id": "FK2E3-B", "onda": "B", "tipo": "Reciclado", "coluna": "6.0", "m2": 4.011, "gram": 485},
    {"id": "FK2E4-B", "onda": "B", "tipo": "Reciclado", "coluna": "7.0", "m2": 4.342, "gram": 525},
    {"id": "KMKS-B", "onda": "B", "tipo": "Kraft", "coluna": "4.0", "m2": 2.948, "gram": 335},
    {"id": "KMK-B", "onda": "B", "tipo": "Kraft", "coluna": "5.0", "m2": 3.344, "gram": 380},
    {"id": "BMC-B", "onda": "B", "tipo": "Branco", "coluna": "4.5", "m2": 3.793, "gram": 410},
    # ONDA C
    {"id": "FK1L-C", "onda": "C", "tipo": "Reciclado", "coluna": "3.3", "m2": 3.038, "gram": 370},
    {"id": "FK2S-C", "onda": "C", "tipo": "Reciclado", "coluna": "3.8", "m2": 2.853, "gram": 345},
    {"id": "FK2-C", "onda": "C", "tipo": "Reciclado", "coluna": "4.8", "m2": 3.225, "gram": 390},
    {"id": "FK2E1-C", "onda": "C", "tipo": "Reciclado", "coluna": "5.3", "m2": 3.556, "gram": 430},
    {"id": "FK2E3-C", "onda": "C", "tipo": "Reciclado", "coluna": "6.0", "m2": 4.094, "gram": 495},
    {"id": "FK2E4-C", "onda": "C", "tipo": "Reciclado", "coluna": "7.0", "m2": 4.424, "gram": 535},
    {"id": "KMKS-C", "onda": "C", "tipo": "Kraft", "coluna": "4.0", "m2": 3.036, "gram": 345},
    {"id": "KMK-C", "onda": "C", "tipo": "Kraft", "coluna": "5.0", "m2": 3.432, "gram": 390},
    {"id": "BMC-C", "onda": "C", "tipo": "Branco", "coluna": "4.5", "m2": 3.885, "gram": 420},
    # ONDA BC
    {"id": "FK1L-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "6.5", "m2": 5.008, "gram": 610},
    {"id": "FK2S-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "6.5", "m2": 4.673, "gram": 565},
    {"id": "FK2L-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "7.0", "m2": 5.127, "gram": 620},
    {"id": "FK2-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "8.0", "m2": 5.458, "gram": 660},
    {"id": "FK2E1-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "9.0", "m2": 6.120, "gram": 740},
    {"id": "FK2E3-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "10.0", "m2": 6.699, "gram": 810},
    {"id": "KMKS-BC", "onda": "BC", "tipo": "Kraft", "coluna": "7.0", "m2": 5.324, "gram": 605},
    {"id": "KMK-BC", "onda": "BC", "tipo": "Kraft", "coluna": "8.0", "m2": 5.808, "gram": 660},
    {"id": "BMC-BC", "onda": "BC", "tipo": "Branco", "coluna": "7.5", "m2": 6.383, "gram": 690},
    # MICRO E / EB
    {"id": "FK1L-E", "onda": "E (Micro)", "tipo": "Reciclado", "coluna": "4.0", "m2": 2.961, "gram": 350},
    {"id": "FK2L-E", "onda": "E (Micro)", "tipo": "Reciclado", "coluna": "4.5", "m2": 3.067, "gram": 360},
    {"id": "FK1L-EB", "onda": "EB (Dupla)", "tipo": "Reciclado", "coluna": "6.5", "m2": 5.034, "gram": 595},
    {"id": "FK2L-EB", "onda": "EB (Dupla)", "tipo": "Reciclado", "coluna": "7.0", "m2": 5.155, "gram": 605}
]

st.set_page_config(page_title="New Age - Orçador Master", layout="wide")

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("📦 Sistema de Orçamentos New Age - Tabela Fernandez 2024")

# --- CONFIGURAÇÃO ---
with st.expander("📝 Configurar Novo Item", expanded=True):
    col_dim, col_mat = st.columns(2)
    
    with col_dim:
        modelo = st.selectbox("Modelo FEFCO", ["0200", "0201", "0204", "0427", "0421", "0901", "0903"])
        L = st.number_input("Comp. Interno (L) mm", value=300)
        W = st.number_input("Larg. Interna (W) mm", value=200)
        H = st.number_input("Alt. Interna (H) mm", value=50)
        qtd = st.number_input("Quantidade", value=500, step=100)

    with col_mat:
        onda_sel = st.selectbox("Onda", sorted(list(set(m['onda'] for m in BASE_MATERIAIS))))
        tipo_sel = st.selectbox("Papel", sorted(list(set(m['tipo'] for m in BASE_MATERIAIS if m['onda'] == onda_sel))))
        coluna_sel = st.selectbox("Coluna (ECT)", sorted(list(set(m['coluna'] for m in BASE_MATERIAIS if m['onda'] == onda_sel and m['tipo'] == tipo_sel))))
        chapa = next(m for m in BASE_MATERIAIS if m['onda'] == onda_sel and m['tipo'] == tipo_sel and m['coluna'] == coluna_sel)

# --- MOTOR DE CÁLCULO INDIVIDUAL (Lógica Prinect) ---
d_map = {"B": 3.0, "C": 4.0, "BC": 6.5, "E (Micro)": 1.5, "EB (Dupla)": 4.5}
d = d_map.get(onda_sel, 3.0)

# Lógica Individualizada conforme arquivos .evr
if modelo == "0200":
    bL = (2 * L) + (2 * W) + 35
    bW = H + (W / 2) + d
elif modelo == "0201":
    bL = (2 * L) + (2 * W) + 35
    bW = H + W + d
elif modelo == "0204":
    bL = (2 * L) + (2 * W) + 35
    bW = H + (2 * W) + d
elif modelo == "0427":
    bL = L + (4 * H) + (6 * d)
    bW = (2 * W) + (3 * H) + 20
else: # Acessórios 0900
    bL, bW = L, W

# RESULTADO (Fator 100 e Sem Refile)
area_m2 = (bL * bW) / 1_000_000
preco_unit = (area_m2 * chapa['m2']) * 2.0
peso_total = (area_m2 * chapa['gram'] * qtd) / 1000

# EXIBIÇÃO
st.divider()
res1, res2, res3 = st.columns(3)
res1.metric("Preço Unitário", f"R$ {preco_unit:.2f}")
res2.info(f"**Chapa Aberta:** {bL:.0f} x {bW:.0f} mm")
if res3.button("➕ Adicionar ao Carrinho", use_container_width=True):
    st.session_state.carrinho.append({
        "Modelo": modelo, "Medidas": f"{L}x{W}x{H}", "Chapa Aberta": f"{bL:.0f}x{bW:.0f}",
        "Material": f"{onda_sel} {tipo_sel} (ECT {coluna_sel})", "Qtd": qtd,
        "Subtotal": round(preco_unit * qtd, 2), "Peso (kg)": round(peso_total, 2)
    })
    st.toast("Adicionado!")

# --- CARRINHO ---
if st.session_state.carrinho:
    st.header("🛒 Seu Orçamento")
    df = pd.DataFrame(st.session_state.carrinho)
    st.table(df)
    st.metric("Investimento Total", f"R$ {df['Subtotal'].sum():.2f}")
    if st.button("🗑️ Esvaziar"):
        st.session_state.carrinho = []
        st.rerun()
