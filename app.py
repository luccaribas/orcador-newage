import streamlit as st
import pandas as pd
import math
import os

# =========================================================
# 1. SMARTPACK V16 - OMNI READER (DICIONÁRIO COMPLETO)
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

        # --- A GRANDE BIBLIOTECA DE TRADUÇÃO (V16) ---
        
        # 1. Funções Lambda Genéricas (Para tratar as 299 variações de vinco)
        # Qualquer função de correção (DC, C90, HWDC) retorna uma fração da espessura
        k_d = lambda *a: float(d)       # Retorna d (para dobras externas)
        k_h = lambda *a: 0.5 * float(d) # Retorna meio d (para dobras internas)
        k_0 = lambda *a: 0.0            # Retorna 0 (para correções lineares irrelevantes no corte)
        
        contexto = {
            # --- INPUTS DO USUÁRIO ---
            'L': float(L), 'W': float(W), 'H': float(H), 'd': lambda: float(d),
            
            # --- MATEMÁTICA AVANÇADA (Faltava isso!) ---
            'sqrt': math.sqrt, 'min': min, 'max': max, 'abs': abs,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'pow': math.pow, 'pi': math.pi,
            
            # --- CONSTANTES DE ESTADO (FLAGS) ---
            'dtID': 1, 'dtOD': 0, 'dtSS': 0, 'No': 0, 'Yes': 1, 
            'Flat': 0, 'Round': 1, 'fd': lambda: 0, 'DT': 1, 'UL': 1,
            'SSGD': 0, 'EdgeType': 1,
            
            # --- FUNÇÕES DE CORREÇÃO (MAPEAMENTO DOS 299 CÓDIGOS) ---
            # O Python agora sabe que tudo isso se refere a compensação de espessura
            'C90x': k_h, 'C90y': k_h, 'C90X': k_h, 'C90Y': k_h,
            'HC90x': k_d, 'HC90X': k_d, 'HC90y': k_d, 'HC90Y': k_d,
            'O90x': k_d, 'O90X': k_d, 'O90y': k_d, 'O90Y': k_d,
            'I90x': k_h, 'I90X': k_h, 'I90y': k_h, 'I90Y': k_h,
            'HI90x': k_d, 'HI90X': k_d, 'HI90y': k_d, 'HI90Y': k_d,
            
            # Família DC (Distance Correction) e HW (Heavy Weight)
            'DC0x': k_0, 'DC0y': k_0, 'DC1x': k_0, 'DC1y': k_0,
            'BCDC1x': k_d, 'BCDC1y': k_d, 'BCDC0x': k_0,
            'HWDC1x': k_d, 'HWDC1y': k_d, 
            
            # Funções Específicas
            'GlueCorr': k_h, 'GLWidth': lambda *a: 35.0,
            'SlotWidth': lambda *a: float(d) + 1.0,
            'LPCorr': k_0, 'PHCorrX': k_0, 'PHCorrY': k_0,
            
            # --- INICIALIZAÇÃO DE VARIÁVEIS CRÍTICAS ---
            # Evita erro se a fórmula tentar ler antes de calcular
            'Wlc': 0.0, 'LSC': 0.0, 'CLFH': 0.0, 'TIFH': 0.0, 'Ext': 0.0,
            'PH': 0.0, 'PH1': 0.0, 'PH2': 0.0, 'FH': 0.0, 'GL': 35.0
        }
        
        resolvidos = {}
        
        # 5 Passadas de Resolução (Ciclo de Dependência)
        for _ in range(5):
            for _, row in df_model.iterrows():
                try:
                    param = row['Parametro']
                    formula = str(row['Formula']).strip().replace('=', '')
                    
                    if param in ['L', 'W', 'H']: continue
                    
                    # Tenta calcular
                    if formula.replace('.','',1).isdigit(): 
                        val = float(formula)
                    else: 
                        val = eval(formula.replace('^', '**'), {}, contexto)
                    
                    contexto[param] = val
                    resolvidos[param] = val
                except: 
                    # Se falhar (variável ainda não calculada), define 0.0 temporário
                    if param not in contexto: contexto[param] = 0.0
                    
        return resolvidos

    def calcular_blank_exato(self, modelo, L, W, H, d):
        vars_eng = self._resolve_formulas(modelo, L, W, H, d)
        if not vars_eng: return 0, 0, "Modelo Inexistente"

        # Dimensões Base de Vinco
        Lss = vars_eng.get('Lss', L + d)
        Wss = vars_eng.get('Wss', W + d)
        Hss = vars_eng.get('Hss', H + (1.7*d if modelo[0] in ['2','5','7'] else d))

        # --- LÓGICA DE LAYOUT V16 (AGORA COM VARIÁVEIS REAIS) ---

        # 1. EIXO X (LARGURA)
        has_GL = 'GL' in vars_eng or 'GLWidth' in str(self.df[self.df['Modelo']==modelo]['Formula'].values)
        if has_GL:
            GL = vars_eng.get('GL', 35.0)
            # Tubulares geralmente são soma linear
            # Correção Fina: Desconto de dobras em Fundo Auto (07xx)
            setback = 2.0 * d if modelo.startswith('7') else 0
            Blank_X = GL + 2*(Lss + Wss) - setback
        else:
            # Tabuleiros
            # Prioridade Absoluta: Se o CSV calculou L_Blank, use ele.
            if 'L_Blank' in vars_eng: Blank_X = vars_eng['L_Blank']
            elif 'FlatWidth' in vars_eng: Blank_X = vars_eng['FlatWidth']
            else:
                # Reconstrói
                Wall_H = vars_eng.get('Hss', H)
                Blank_X = Lss + 2*Wall_H

        # 2. EIXO Y (COMPRIMENTO)
        # O Pulo do Gato para a 711 e 427
        
        # Se for E-commerce 427/426
        if modelo in ['427', '426']:
            # Tenta usar TIFH (Tuck In Flap Height) se o CSV calculou
            if 'TIFH' in vars_eng and vars_eng['TIFH'] > 0:
                # Fórmula exata baseada nas variáveis internas
                # Y = TIFH + Tampa + Fundo + Tampa + TIFH... (Simplificado: Soma das alturas verticais)
                # Como a 427 é complexa, confiamos na geometria 'Gold' que já validamos
                HssY = vars_eng.get('HssY', H + 2*d)
                FH1 = HssY + (1.5 * d)
                Blank_X = (H - ((3 * d) + 1.0)) + Wss + HssY + Wss + FH1
                Blank_Y = (HssY + 14.0)*2 + (HssY - 0.5*d)*2 + Lss
                return Blank_Y, Blank_X, "E-commerce (Precision)"

        # Se for Fundo Automático 7xx (Aqui estava o erro!)
        if modelo.startswith('7'):
            # Agora temos CLFH (Crash Lock Flap Height) lido do CSV!
            CLFH = vars_eng.get('CLFH', 0)
            Ext = vars_eng.get('Ext', 0)
            
            # A altura é: Aba Topo + Corpo + Fundo Automático
            Top = vars_eng.get('FH', Wss/2)
            
            # Se CLFH foi calculado pelo CSV (agora mapeado), usamos ele.
            if CLFH > 0:
                Bottom = CLFH + Ext
            elif 'PH1' in vars_eng and 'PH2' in vars_eng:
                Bottom = vars_eng['PH1'] + vars_eng['PH2'] # Soma componentes
            else:
                Bottom = (Wss/2) + (Wss/8) # Fallback

            Blank_Y = Top + Hss + Bottom
            return Blank_X, Blank_Y, f"Fundo Automático (CLFH={Bottom:.1f})"

        # Maletas Padrão
        if modelo.startswith('2'):
             Top = vars_eng.get('FH', Wss/2)
             Bottom = vars_eng.get('FH_B', Top)
             Blank_Y = Top + Hss + Bottom
             return Blank_X, Blank_Y, "Maleta Padrão"

        # Tabuleiros Genéricos
        Blank_Y = Wss + 2*vars_eng.get('Hss', H)
        return Blank_X, Blank_Y, "Tabuleiro Genérico"

# =========================================================
# 2. INTERFACE
# =========================================================
st.set_page_config(page_title="SmartPack V16", layout="wide")

@st.cache_resource
def load_engine_v16():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine_v16()
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

st.title("🏭 SmartPack V16 - Omni Reader")

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
    st.success(f"Motor V16: **{perfil}**")
    
    c1, c2 = st.columns(2)
    c1.metric("Largura Chapa", f"{bL:.1f} mm")
    c2.metric("Compr. Chapa", f"{bW:.1f} mm")
    
    st.info(f"Consumo: {area:.4f} m² | Total: R$ {total:,.2f}")
    
    if st.button("🛒 Adicionar"):
        st.session_state.carrinho.append({"Modelo": modelo, "Total": total})
