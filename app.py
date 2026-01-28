import streamlit as st
import pandas as pd

# --- BANCO DE DADOS ATUALIZADO (Fernandez 2024) ---
BASE_MATERIAIS = [
    # ONDA B
    {"id": "FK1L-B", "onda": "B", "tipo": "Reciclado", "coluna": "3.5", "m2": 2.956, "gram": 360, "min": 250},
    {"id": "FK2S-B", "onda": "B", "tipo": "Reciclado", "coluna": "4.0", "m2": 2.770, "gram": 335, "min": 250},
    {"id": "FK2-B", "onda": "B", "tipo": "Reciclado", "coluna": "5.0", "m2": 3.143, "gram": 380, "min": 250},
    {"id": "FK2E1-B", "onda": "B", "tipo": "Reciclado", "coluna": "5.5", "m2": 3.473, "gram": 420, "min": 250},
    {"id": "FK2E3-B", "onda": "B", "tipo": "Reciclado", "coluna": "6.0", "m2": 4.011, "gram": 485, "min": 250},
    {"id": "FK2E4-B", "onda": "B", "tipo": "Reciclado", "coluna": "7.0", "m2": 4.342, "gram": 525, "min": 250},
    {"id": "KMKS-B", "onda": "B", "tipo": "Kraft", "coluna": "4.0", "m2": 2.948, "gram": 335, "min": 300},
    {"id": "KMK-B", "onda": "B", "tipo": "Kraft", "coluna": "5.0", "m2": 3.344, "gram": 380, "min": 300},
    {"id": "BMC-B", "onda": "B", "tipo": "Branco", "coluna": "4.5", "m2": 3.793, "gram": 410, "min": 300},
    
    # ONDA C
    {"id": "FK1L-C", "onda": "C", "tipo": "Reciclado", "coluna": "3.3", "m2": 3.038, "gram": 370, "min": 250},
    {"id": "FK2S-C", "onda": "C", "tipo": "Reciclado", "coluna": "3.8", "m2": 2.853, "gram": 345, "min": 250},
    {"id": "FK2-C", "onda": "C", "tipo": "Reciclado", "coluna": "4.8", "m2": 3.225, "gram": 390, "min": 250},
    {"id": "FK2E1-C", "onda": "C", "tipo": "Reciclado", "coluna": "5.3", "m2": 3.556, "gram": 430, "min": 250},
    {"id": "FK2E3-C", "onda": "C", "tipo": "Reciclado", "coluna": "6.0", "m2": 4.094, "gram": 495, "min": 250},
    {"id": "FK2E4-C", "onda": "C", "tipo": "Reciclado", "coluna": "7.0", "m2": 4.424, "gram": 535, "min": 250},
    {"id": "KMKS-C", "onda": "C", "tipo": "Kraft", "coluna": "4.0", "m2": 3.036, "gram": 345, "min": 300},
    {"id": "KMK-C", "onda": "C", "tipo": "Kraft", "coluna": "5.0", "m2": 3.432, "gram": 390, "min": 300},
    {"id": "BMC-C", "onda": "C", "tipo": "Branco", "coluna": "4.5", "m2": 3.885, "gram": 420, "min": 300},

    # ONDA BC
    {"id": "FK1L-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "6.5", "m2": 5.008, "gram": 610, "min": 250},
    {"id": "FK2S-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "6.5", "m2": 4.673, "gram": 565, "min": 250},
    {"id": "FK2L-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "7.0", "m2": 5.127, "gram": 620, "min": 250},
    {"id": "FK2-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "8.0", "m2": 5.458, "gram": 660, "min": 250},
    {"id": "FK2E1-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "9.0", "m2": 6.120, "gram": 740, "min": 250},
    {"id": "FK2E3-BC", "onda": "BC", "tipo": "Reciclado", "coluna": "10.0", "m2": 6.699, "gram": 810, "min": 250},
    {"id": "KMKS-BC", "onda": "BC", "tipo": "Kraft", "coluna": "7.0", "m2": 5.324, "gram": 605, "min": 300},
    {"id": "KMK-BC", "onda": "BC", "tipo": "Kraft", "coluna": "8.0", "m2": 5.808, "gram": 660, "min": 300},
    {"id": "BMC-BC", "onda": "BC", "tipo": "Branco", "coluna": "7.5", "m2": 6.383, "gram": 690, "min": 300},

    # ONDA E / EB
    {"id": "FK1L-E", "onda": "E (Micro)", "tipo": "Reciclado", "coluna": "4.0", "m2": 2.961, "gram": 350, "min": 250},
    {"id": "FK2L-E", "onda": "E (Micro)", "tipo": "Reciclado", "coluna": "4.5", "m2": 3.067, "gram": 360, "min": 250},
    {"id": "FK1L-EB", "onda": "EB (Dupla)", "tipo": "Reciclado", "coluna": "6.5", "m2": 5.034, "gram": 595, "min": 250},
    {"id": "FK2L-EB", "onda": "EB (Dupla)", "tipo": "Reciclado", "coluna": "7.0", "m2": 5.155, "gram": 605, "min": 250}
]

st.set_page_config(page_title="New Age - Orçamentos", layout="wide")

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("📦 Sistema de Orçamentos New Age (Tabela 2024)")

# --- INTERFACE DE CONFIGURAÇÃO ---
with st.expander("📝 Novo Item", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        modelo = st.selectbox("Modelo FEFCO", ["0201", "0200", "0427", "0426", "0424", "0901", "0903"])
        L = st.number_input("Comp. (L) mm", value=300)
        W = st.number_input("Larg. (W) mm", value=200)
        H = st.number_input("Alt. (H) mm", value=50)
        qtd = st.number_input("Quantidade", value=500, step=100)

    with col2:
        onda_sel = st.selectbox("1. Onda", sorted(list(set(m['onda'] for m in BASE_MATERIAIS))))
        tipo_sel = st.selectbox("2. Papel", sorted(list(set(m['tipo'] for m in BASE_MATERIAIS if m['onda'] == onda_sel))))
        coluna_sel = st.selectbox("3. Coluna (ECT)", sorted(list(set(m['coluna'] for m in BASE_MATERIAIS if m['onda'] == onda_sel and m['tipo'] == tipo_sel))))
        chapa = next(m for m in BASE_MATERIAIS if m['onda'] == onda_sel and m['tipo'] == tipo_sel and m['coluna'] == coluna_sel)

    with col3:
        refile = 30 if modelo.startswith("04") else 0
        d_map = {"B": 3.0, "C": 4.0, "BC": 6.5, "E (Micro)": 1.5, "EB (Dupla)": 4.5}
        d = d_map.get(onda_sel, 3.0)
        
        if modelo.startswith("02"):
            bL, bW = (2*L + 2*W + 45), (H + W + d)
        elif modelo.startswith("04"):
            bL, bW = (L + 4*H + 6*d), (2*W + 3*H + 20)
        else:
            bL, bW = L, W
            
        chapa_aberta = f"{bL + refile:.0f} x {bW + refile:.0f} mm"
        area_m2 = ((bL + refile) * (bW + refile)) / 1_000_000
        preco_venda = (area_m2 * chapa['m2']) * 2.0
        
        st.info(f"**Cód. Fernandez:** {chapa['id']}\n\n**Chapa Aberta:** {chapa_aberta}")
        st.metric("Preço Unitário", f"R$ {preco_venda:.2f}")

    if st.button("➕ Adicionar"):
        st.session_state.carrinho.append({
            "Modelo": modelo, "Medidas": f"{L}x{W}x{H}", "Chapa Aberta": chapa_aberta,
            "Material": f"{onda_sel} {tipo_sel} (Col: {coluna_sel})", "Qtd": qtd,
            "Unitário": f"R$ {preco_venda:.2f}", "Subtotal": round(preco_venda * qtd, 2),
            "Peso (kg)": round(area_m2 * chapa['gram'] * qtd / 1000, 2)
        })
        st.toast("Adicionado!")

# --- CARRINHO ---
st.divider()
if st.session_state.carrinho:
    df = pd.DataFrame(st.session_state.carrinho)
    st.table(df)
    st.metric("Total do Orçamento", f"R$ {df['Subtotal'].sum():.2f}")
    if st.button("Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()
