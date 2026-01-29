import streamlit as st
import pandas as pd
import math
import sys

# =========================================================
# 1. SMARTPACK ENGINE (O CÉREBRO)
# =========================================================
class SmartPackBackend:
    def __init__(self, csv_path='formulas_smartpack.csv'):
        try:
            self.df = pd.read_csv(csv_path, delimiter=';', dtype={'Modelo': str})
            self.df['Modelo'] = self.df['Modelo'].str.lstrip('0')
        except FileNotFoundError:
            st.error("❌ Erro CRÍTICO: 'formulas_smartpack.csv' não encontrado.")
            st.stop()

    def _get_engine_variables(self, modelo, L, W, H, d):
        modelo = str(modelo).lstrip('0')
        df_model = self.df[self.df['Modelo'] == modelo]
        
        if df_model.empty: return None

        # Calibração Dinâmica (Maleta vs Montável)
        is_maleta = modelo.startswith('2')
        calib = {
            'C90': 0.5 if is_maleta else 1.0 * d,
            'HC90': (1.7 * d) if is_maleta else 1.0 * d, # Ajuste fino da 201 (H + 1.7d)
            'Glue': 0.5 if is_maleta else 1.0 * d,
            'Slot': (d + 1.0) if is_maleta else (d + 2.0)
        }

        contexto = {
            'L': float(L), 'W': float(W), 'H': float(H), 'd': lambda: float(d),
            'dtID': 1, 'dtOD': 0, 'No': 0, 'Yes': 1, 'Flat': 0, 'Round': 1, 'fd': lambda: 0,
            'sqrt': math.sqrt, 'min': min, 'max': max, 'tan': math.tan, 'atan': math.atan,
            'C90x': lambda *a: calib['C90'], 'C90y': lambda *a: calib['C90'],
            'HC90x': lambda *a: calib['HC90'], 'GlueCorr': lambda *a: calib['Glue'],
            'LPCorr': lambda *a: 1.0 * d, 'GLWidth': lambda *a: 35.0,
            'LSCf': lambda *a: 1.5 * d, 'SlotWidth': lambda *a: calib['Slot'],
            'LC': lambda d_val, dt, iln, oln: (iln if dt==1 else oln) * d,
            'switch': lambda cond, *args: args[1] if cond else args[0]
        }
        
        resolvidos = {}
        for _ in range(4):
            for _, row in df_model.iterrows():
                param = row['Parametro']
                formula = str(row['Formula'])
                if param in ['L', 'W', 'H', 'UL', 'DT']: continue
                try:
                    if formula.replace('.','',1).isdigit(): val = float(formula)
                    else: val = eval(formula.replace('^', '**'), {}, contexto)
                    contexto[param] = val
                    resolvidos[param] = val
                except: pass
        return resolvidos

    def calcular_blank(self, modelo, L, W, H, d):
        vars_eng = self._get_engine_variables(modelo, L, W, H, d)
        if not vars_eng: return 0, 0 # Modelo não achado

        # Lógica 0427 (E-commerce)
        if modelo == '427':
            Lss = vars_eng.get('Lss', L + 6*d)
            Wss = vars_eng.get('Wss', W + 2*d)
            HssY = vars_eng.get('HssY', H + 2*d)
            FH1 = HssY + (1.5 * d)
            TPH = H
            DxPI = (3 * d) + 1.0
            TIFH = TPH - DxPI
            
            Blank_X = TIFH + Wss + HssY + Wss + FH1 # Comprimento
            Ear = HssY + 14.0
            PH = HssY - (0.5 * d)
            Blank_Y = Ear + PH + Lss + PH + Ear # Largura
            return Blank_Y, Blank_X

        # Lógica 02xx (Maletas)
        elif modelo.startswith('2'):
            Lss = vars_eng.get('Lss', L + 1.0)
            Wss = vars_eng.get('Wss', W + 1.0)
            Hss = vars_eng.get('Hss', H + (1.7*d))
            GL = vars_eng.get('GL', 35.0)
            
            Blank_X = GL + 2*(Lss + Wss)
            
            Flap_Top = Wss / 2
            if modelo == '200': Flap_Top = 0 # Meia Maleta
            
            Blank_Y = Flap_Top + Hss + (Wss / 2)
            return Blank_X, Blank_Y
        
        return 0, 0

# =========================================================
# 2. CONFIGURAÇÃO E DADOS DE PREÇO
# =========================================================
st.set_page_config(page_title="SmartPack Pro", layout="wide")

# Cache para não recarregar o CSV a cada clique (Performance)
@st.cache_resource
def load_engine():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine()

CONFIG_TECNICA = {
    "Onda B":            {"d": 3.0},
    "Onda C":            {"d": 4.0},
    "Onda BC (Dupla)":   {"d": 6.9},
    "Onda E (Micro)":    {"d": 1.5},
    "Onda EB (Dupla)":   {"d": 4.4}
}

MATERIAIS = {
    "Onda B": {
        "Papel Padrão (Reciclado)": {3.5: 2.956, 4.0: 2.770, 5.0: 3.143, 6.0: 4.011, 7.0: 4.342},
        "Papel Premium (Kraft)": {4.0: 2.948, 5.0: 3.344},
        "Papel Branco": {5.0: 3.793}
    },
    "Onda C": {
        "Papel Padrão (Reciclado)": {3.5: 3.038, 4.0: 2.853, 4.8: 3.225, 5.5: 4.094, 6.0: 4.424},
        "Papel Premium (Kraft)": {4.0: 3.036, 5.0: 3.432},
        "Papel Branco": {5.0: 3.885}
    },
    "Onda BC (Dupla)": {
        "Papel Padrão (Reciclado)": {7.0: 5.008, 7.5: 4.673, 8.0: 5.458, 9.5: 6.699},
        "Papel Premium (Kraft)": {8.0: 5.808},
        "Papel Branco": {8.0: 6.383}
    }
}

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

def add_to_cart(item):
    st.session_state.carrinho.append(item)
    st.toast("Item adicionado! 🛒", icon="✅")

# =========================================================
# 3. INTERFACE DO USUÁRIO
# =========================================================
st.title("🛡️ SmartPack Pro")
st.caption(f"Sistema Conectado: {len(engine.df)} fórmulas de engenharia carregadas.")

with st.sidebar:
    st.header("1. Configuração do Material")
    onda_sel = st.selectbox("Tipo de Onda", list(MATERIAIS.keys()))
    papel_sel = st.selectbox("Tipo de Papel", list(MATERIAIS[onda_sel].keys()))
    colunas = list(MATERIAIS[onda_sel][papel_sel].keys())
    coluna_sel = st.selectbox("Resistência (Coluna)", colunas)
    
    st.divider()
    st.header("2. Modelo e Medidas")
    # Mapa: Nome Visual -> Código FEFCO
    mapa_modelos = {
        "FEFCO 0427 - E-commerce (Correio)": "427",
        "FEFCO 0201 - Maleta Padrão": "201",
        "FEFCO 0200 - Meia Maleta": "200"
    }
    modelo_visual = st.selectbox("Modelo", list(mapa_modelos.keys()))
    codigo_modelo = mapa_modelos[modelo_visual]

# Recuperação de Dados Técnicos
espessura_d = CONFIG_TECNICA[onda_sel]["d"]
preco_m2_base = MATERIAIS[onda_sel][papel_sel][coluna_sel]

# Área Principal
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Medidas (Internas)")
    L = st.number_input("Comprimento (mm)", value=300)
    W = st.number_input("Largura (mm)", value=200)
    H = st.number_input("Altura (mm)", value=100)
    qtd = st.number_input("Quantidade", value=500, step=100)

# =========================================================
# 4. CÁLCULO REAL (CHAMA O ENGINE)
# =========================================================
# Aqui acontece a mágica: O Engine calcula o blank exato
bL, bW = engine.calcular_blank(codigo_modelo, L, W, H, espessura_d)

# Cálculos Financeiros
area_m2 = (bL * bW) / 1_000_000
fator_margem = 2.0 # Margem de venda
valor_unit = (area_m2 * preco_m2_base) * fator_margem

with col2:
    st.subheader("Resultado do Orçamento")
    
    # Cartões de Resultado
    c1, c2, c3 = st.columns(3)
    c1.metric("Preço Unitário", f"R$ {valor_unit:.2f}")
    c2.metric("Total do Pedido", f"R$ {valor_unit * qtd:,.2f}")
    c3.metric("Área de Papel", f"{area_m2:.3f} m²/cx")
    
    st.markdown("### 📐 Engenharia do Blank")
    st.info(f"""
    **Tamanho da Chapa Aberta:** {bL:.1f} x {bW:.1f} mm  
    **Modelo Calculado:** FEFCO {codigo_modelo}  
    **Espessura Considerada:** {espessura_d}mm
    """)
    
    if st.button("➕ ADICIONAR AO CARRINHO", type="primary", use_container_width=True):
        add_to_cart({
            "Modelo": modelo_visual,
            "Dimensões": f"{L}x{W}x{H}",
            "Material": f"{onda_sel} ({coluna_sel}kg)",
            "Blank": f"{bL:.0f}x{bW:.0f}",
            "Qtd": qtd,
            "Unitário": f"R$ {valor_unit:.2f}",
            "Total": valor_unit * qtd
        })

# =========================================================
# 5. CARRINHO DE COMPRAS
# =========================================================
if st.session_state.carrinho:
    st.markdown("---")
    st.subheader("🛒 Carrinho de Compras")
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho, use_container_width=True, hide_index=True)
    
    total_geral = df_carrinho["Total"].sum()
    col_tot, col_btn = st.columns([3, 1])
    col_tot.markdown(f"## Total Geral: R$ {total_geral:,.2f}")
    
    if col_btn.button("Limpar"):
        st.session_state.carrinho = []
        st.rerun()
