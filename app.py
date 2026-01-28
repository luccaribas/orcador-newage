import streamlit as st
import pandas as pd

# --- BANCO DE DADOS FERNANDEZ ---
PRECOS = {
    "FK1L-B": {"m2": 2.633, "gram": 360, "onda": "B", "min": 250},
    "FK2-B": {"m2": 2.801, "gram": 380, "onda": "B", "min": 250},
    "FK2-BC": {"m2": 4.864, "gram": 660, "onda": "BC", "min": 250},
    "KMK-BC": {"m2": 5.387, "gram": 660, "onda": "BC", "min": 300},
    "BMC-BC": {"m2": 6.543, "gram": 690, "onda": "BC", "min": 300}
}

st.set_page_config(page_title="New Age - Orçamentos", layout="wide")

# --- INICIALIZAÇÃO DO CARRINHO (MEMÓRIA) ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("📦 Sistema de Orçamentos New Age")
st.markdown("Configure seus itens e adicione-os ao carrinho para gerar o orçamento final.")

# --- ÁREA DE CONFIGURAÇÃO DO ITEM ---
with st.expander("1. Configurar Novo Item", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        modelo = st.selectbox("Modelo FEFCO", ["0201", "0200", "0427", "0426", "0901", "0903"])
        chapa = st.selectbox("Qualidade", list(PRECOS.keys()))
    with col2:
        L = st.number_input("Comp. (L) mm", value=300)
        W = st.number_input("Larg. (W) mm", value=200)
        H = st.number_input("Alt. (H) mm", value=50)
    with col3:
        qtd = st.number_input("Quantidade", value=500, step=100)
        
    # Lógica de Cálculo (Prinect + Refile + Fator 100)
    info = PRECOS[chapa]
    d = 3.0 if info['onda'] == "B" else 6.5
    refile = 30 if modelo.startswith("04") else 0
    
    # Fórmulas Simplificadas Prinect
    if modelo.startswith("02"):
        bL, bW = (2*L + 2*W + 50), (H + W + d)
    elif modelo.startswith("04"):
        bL, bW = (L + 4*H + 6*d), (2*W + 3*H + 20)
    else:
        bL, bW = L, W
        
    area_m2 = ((bL + refile) * (bW + refile)) / 1_000_000
    preco_unit = (area_m2 * info['m2']) * 2.0 # Fator 100
    peso_item = (area_m2 * info['gram'] * qtd) / 1000

    if st.button("➕ Adicionar ao Carrinho"):
        item = {
            "Modelo": modelo,
            "Medidas": f"{L}x{W}x{H}",
            "Chapa": chapa,
            "Qtd": qtd,
            "Unitário": round(preco_unit, 2),
            "Subtotal": round(preco_unit * qtd, 2),
            "Peso (kg)": round(peso_item, 2)
        }
        st.session_state.carrinho.append(item)
        st.toast("Item adicionado com sucesso!")

# --- VISUALIZAÇÃO DO CARRINHO ---
st.divider()
st.header("🛒 Seu Carrinho de Orçamento")

if st.session_state.carrinho:
    df = pd.DataFrame(st.session_state.carrinho)
    st.table(df)
    
    total_geral = df["Subtotal"].sum()
    peso_geral = df["Peso (kg)"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Valor Total do Orçamento", f"R$ {total_geral:.2f}")
    c2.metric("Peso Total do Pedido", f"{peso_geral:.1f} kg")
    
    with c3:
        if st.button("🗑️ Limpar Tudo"):
            st.session_state.carrinho = []
            st.rerun()

    # --- FINALIZAÇÃO ---
    st.success(f"Orçamento pronto! O valor médio por peça no total é R$ {total_geral/df['Qtd'].sum():.2f}")
    
    whatsapp_msg = f"Olá New Age! Gostaria de solicitar o orçamento para: {st.session_state.carrinho}"
    st.button("📲 Solicitar Orçamento via WhatsApp (Simulação)")
else:
    st.info("O carrinho está vazio. Adicione itens acima para ver o resumo.")
