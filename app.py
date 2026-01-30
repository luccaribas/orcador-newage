import streamlit as st
import pandas as pd
import math
import os

# =========================================================
# 1. SMARTPACK V17 - HYBRID ENGINE (CALC + DATA EXTRACTION)
# =========================================================
class SmartPackBackend:
    def __init__(self, csv_path='formulas_smartpack.csv'):
        if os.path.exists(csv_path):
            try:
                self.df = pd.read_csv(csv_path, delimiter=';', dtype={'Modelo': str}, on_bad_lines='skip')
                self.df['Modelo'] = self.df['Modelo'].str.lstrip('0')
            except: self.df = pd.DataFrame()
        else: self.df = pd.DataFrame()

    def get_available_models(self):
        if self.df.empty: return []
        return sorted(self.df['Modelo'].unique())

    def _resolve_formulas(self, modelo, L, W, H, d):
        modelo = str(modelo).lstrip('0')
        if self.df.empty: return None
        df_model = self.df[self.df['Modelo'] == modelo]
        if df_model.empty: return None

        # --- TRADUTOR PRINECT COMPLETO (V16 mantido) ---
        k_d = lambda *a: float(d)
        k_h = lambda *a: 0.5 * float(d)
        k_0 = lambda *a: 0.0
        
        contexto = {
            'L': float(L), 'W': float(W), 'H': float(H), 'd': lambda: float(d),
            'sqrt': math.sqrt, 'min': min, 'max': max, 'abs': abs,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'dtID': 1, 'dtOD': 0, 'No': 0, 'Yes': 1, 'Flat': 0, 'Round': 1, 'DT': 1, 'UL': 1,
            'C90x': k_h, 'C90y': k_h, 'HC90x': k_d, 'GlueCorr': k_h, 'GLWidth': lambda *a: 35.0,
            'SlotWidth': lambda *a: float(d) + 1.0, 'Wlc': 0.0, 'LSC': 0.0, 'CLFH': 0.0, 'TIFH': 0.0, 'Ext': 0.0
        }
        
        resolvidos = {}
        for _ in range(5):
            for _, row in df_model.iterrows():
                try:
                    param = row['Parametro']
                    formula = str(row['Formula']).strip().replace('=', '')
                    if param in ['L', 'W', 'H']: continue
                    
                    if formula.replace('.','',1).isdigit(): val = float(formula)
                    else: val = eval(formula.replace('^', '**'), {}, contexto)
                    
                    contexto[param] = val
                    resolvidos[param] = val
                except: 
                    if param not in contexto: contexto[param] = 0.0
        return resolvidos

    def calcular_blank_exato(self, modelo, L, W, H, d):
        vars_eng = self._resolve_formulas(modelo, L, W, H, d)
        if not vars_eng: return 0, 0, "Modelo Inexistente"

        # === 1. TENTATIVA DIRETA (VARREDURA DE 'ONEUP' / 'SHEET') ===
        # Procura se o CSV já tem o valor final exportado pelo Prinect
        # Baseado na documentação que você enviou: $OneUp1.SheetWidth$
        
        # Lista de nomes possíveis que o Prinect usa para Blank Total
        direct_X = ['SheetWidth', 'FlatWidth', 'OneUpWidth', 'BoundingBoxX', 'Size_X', 'Blank_X']
        direct_Y = ['SheetHeight', 'FlatHeight', 'OneUpHeight', 'BoundingBoxY', 'Size_Y', 'Blank_Y']
        
        found_X = next((vars_eng[key] for key in direct_X if key in vars_eng and vars_eng[key] > 0), None)
        found_Y = next((vars_eng[key] for key in direct_Y if key in vars_eng and vars_eng[key] > 0), None)
        
        if found_X and found_Y:
            return found_X, found_Y, "Dados Prinect (100% Preciso)"

        # === 2. CÁLCULO ESTRUTURAL (FALLBACK V16) ===
        # Se não achar as colunas diretas, calcula geometricamente
        
        Lss = vars_eng.get('Lss', L + d)
        Wss = vars_eng.get('Wss', W + d)
        Hss = vars_eng.get('Hss', H + (1.7*d if modelo[0] in ['2','5','7'] else d))
        has_GL = 'GL' in vars_eng or 'GLWidth' in str(self.df[self.df['Modelo']==modelo]['Formula'].values)

        # Eixo X
        if has_GL:
            GL = vars_eng.get('GL', 35.0)
            setback = 2.0 * d if modelo.startswith('7') else 0
            Blank_X = GL + 2*(Lss + Wss) - setback
        else:
            if 'L_Blank' in vars_eng: Blank_X = vars_eng['L_Blank']
            else: Blank_X = Lss + 2*vars_eng.get('Hss', H)

        # Eixo Y
        if modelo in ['427', '426']:
            HssY = vars_eng.get('HssY', H + 2*d)
            Blank_Y = (HssY + 14.0)*2 + (HssY - 0.5*d)*2 + Lss
            # Recalcula X exato para 427
            FH1 = HssY + (1.5 * d)
            Blank_X = (H - ((3 * d) + 1.0)) + Wss + HssY + Wss + FH1
            return Blank_Y, Blank_X, "E-commerce (Calculado)"

        if modelo.startswith('7'):
            CLFH = vars_eng.get('CLFH', 0)
            Ext = vars_eng.get('Ext', 0)
            Top = vars_eng.get('FH', Wss/2)
            if CLFH > 0: Bottom = CLFH + Ext
            elif 'PH1' in vars_eng: Bottom = vars_eng['PH1'] + vars_eng['PH2']
            else: Bottom = (Wss/2) + (Wss/8)
            Blank_Y = Top + Hss + Bottom
            return Blank_X, Blank_Y, "Fundo Auto (Calculado)"

        if modelo.startswith('2'):
             Top = vars_eng.get('FH', Wss/2)
             Bottom = vars_eng.get('FH_B', Top)
             Blank_Y = Top + Hss + Bottom
             return Blank_X, Blank_Y, "Maleta (Calculada)"

        Blank_Y = Wss + 2*vars_eng.get('Hss', H)
        return Blank_X, Blank_Y, "Genérico (Calculado)"

# =========================================================
# 2. INTERFACE
# =========================================================
st.set_page_config(page_title="SmartPack V17", layout="wide")

@st.cache_resource
def load_engine_v17():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine_v17()
if 'carrinho' not in st.session_state: st.session_state.carrinho = []

@st.cache_data
def load_prices_safe():
    try:
        arquivos = [f for f in os.listdir() if 'materiais' in f.lower() and 'csv' in f.lower()]
        if arquivos:
            df = pd.read_csv(arquivos[0], sep=';')
            if len(df.columns) < 2: df = pd.read_csv(arquivos[0], sep=',')
            return df
    except: pass
    return pd.DataFrame({
        'Onda': ['B', 'C', 'BC'], 'Papel': ['Padrão', 'Reforçado', 'Duplo'],
        'Gramatura': [380, 440, 700], 'Espessura': [3.0, 4.0, 6.9],
        'Coluna': [4.0, 5.5, 8.0], 'Preco_m2': [2.77, 3.88, 5.45]
    })

df_materiais = load_prices_safe()

st.title("🏭 SmartPack V17 - Hybrid Engine")

with st.sidebar:
    st.header("1. Material")
    onda = st.selectbox("Onda", df_materiais['Onda'].unique())
    df_o = df_materiais[df_materiais['Onda'] == onda]
    papel = st.selectbox("Papel", df_o['Papel'].unique())
    df_p = df_o[df_o['Papel'] == papel]
    coluna = st.selectbox("Resistência", df_p['Coluna'].unique())
    
    mat = df_p[df_p['Coluna'] == coluna].iloc[0]
    d_real = float(mat['Espessura'])
    preco = float(mat['Preco_m2'])
    
    st.divider()
    st.header("2. Modelo")
    modelos = engine.get_available_models()
    tops = ['201', '427', '200', '711', '215']
    lista = [m for m in tops if m in modelos] + [m for m in modelos if m not in tops]
    modelo = st.selectbox("Código FEFCO", lista, format_func=lambda x: f"{x.zfill(4)}")

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Medidas (mm)")
    L = st.number_input("Comprimento", value=300)
    W = st.number_input("Largura", value=200)
    H = st.number_input("Altura", value=100)
    qtd = st.number_input("Quantidade", value=500, step=100)

bL, bW, perfil = engine.calcular_blank_exato(modelo, L, W, H, d_real)
area = (bL * bW) / 1_000_000
total = (area * preco) * 2.0 * qtd

with col2:
    st.subheader("Resultado")
    st.success(f"Fonte: **{perfil}**")
    
    c1, c2 = st.columns(2)
    c1.metric("Largura Chapa", f"{bL:.1f} mm")
    c2.metric("Compr. Chapa", f"{bW:.1f} mm")
    
    st.info(f"Consumo: {area:.4f} m² | Total: R$ {total:,.2f}")
    
    if st.button("🛒 Adicionar"):
        st.session_state.carrinho.append({"Modelo": modelo, "Total": total})
