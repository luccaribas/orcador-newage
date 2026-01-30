import streamlit as st
import pandas as pd
import math
import os

# =========================================================
# 1. SMARTPACK PRECISION ENGINE (DNA FEFCO)
# =========================================================
class SmartPackBackend:
    def __init__(self, csv_path='formulas_smartpack.csv'):
        # Carrega o DNA das caixas
        if os.path.exists(csv_path):
            try:
                self.df = pd.read_csv(csv_path, delimiter=';', dtype={'Modelo': str})
                self.df['Modelo'] = self.df['Modelo'].str.lstrip('0')
            except: self.df = pd.DataFrame()
        else: self.df = pd.DataFrame()

    def get_available_models(self):
        if self.df.empty: return []
        return sorted(self.df['Modelo'].unique())

    def _resolve_formulas(self, modelo, L, W, H, d):
        """
        Esta função atua como o 'Interpretador Heidelberg'.
        Ela resolve as variáveis Lss, Wss, GL, FH baseada na espessura (d).
        """
        modelo = str(modelo).lstrip('0')
        if self.df.empty: return None
        df_model = self.df[self.df['Modelo'] == modelo]
        if df_model.empty: return None

        # --- CALIBRAÇÃO DE PRECISÃO (Fatores K) ---
        # Define quanto o papel "cresce" ou "encolhe" na dobra
        fam = modelo[0]
        # Famílias 2, 5, 6, 7 (Tubulares) = Vinco Esmagado
        # Famílias 3, 4 (Tabuleiros) = Dobra Rolada
        k = {'C90': 0.5, 'HC90': 1.7*d, 'Glue': 0.5, 'Slot': d+1.0} if fam in ['2','5','6','7'] else {'C90': 1.0*d, 'HC90': 1.0*d, 'Glue': 1.0*d, 'Slot': d+2.0}
        
        contexto = {
            'L': float(L), 'W': float(W), 'H': float(H), 'd': lambda: float(d),
            'dtID': 1, 'dtOD': 0, 'No': 0, 'Yes': 1, 'Flat': 0, 'Round': 1, 'fd': lambda: 0,
            'sqrt': math.sqrt, 'min': min, 'max': max, 'tan': math.tan, 'atan': math.atan,
            # Injeção dos Fatores K nas fórmulas originais
            'C90x': lambda *a: k['C90'], 'C90y': lambda *a: k['C90'], 'HC90x': lambda *a: k['HC90'], 
            'GlueCorr': lambda *a: k['Glue'], 'LPCorr': lambda *a: 1.0*d, 'GLWidth': lambda *a: 35.0,
            'LSCf': lambda *a: 1.5*d, 'SlotWidth': lambda *a: k['Slot'],
            'LC': lambda d_val, dt, iln, oln: (iln if dt==1 else oln) * d,
            'switch': lambda cond, *args: args[1] if cond else args[0]
        }
        
        resolvidos = {}
        # Loop de resolução (5 passadas para garantir dependências complexas)
        for _ in range(5):
            for _, row in df_model.iterrows():
                try:
                    param = row['Parametro']
                    formula = str(row['Formula'])
                    if param in ['L', 'W', 'H']: continue
                    
                    # Tenta resolver a fórmula matemática
                    if formula.replace('.','',1).isdigit(): val = float(formula)
                    else: val = eval(formula.replace('^', '**'), {}, contexto)
                    
                    contexto[param] = val
                    resolvidos[param] = val
                except: pass
        return resolvidos

    def calcular_blank_exato(self, modelo, L, W, H, d):
        vars_eng = self._resolve_formulas(modelo, L, W, H, d)
        if not vars_eng: return 0, 0, "Modelo Inexistente"

        # --- ALGORITMO MESTRE DE GEOMETRIA ---
        
        # 1. Recupera as peças fundamentais (já calibradas)
        Lss = vars_eng.get('Lss', L + d)
        Wss = vars_eng.get('Wss', W + d)
        Hss = vars_eng.get('Hss', H + d)

        # 2. Verifica a Topologia Horizontal (Eixo X)
        # Se tem GL (Aba de Cola), é um Tubo Fechado.
        has_GL = 'GL' in vars_eng or 'GLWidth' in str(self.df[self.df['Modelo']==modelo]['Formula'].values)
        
        if has_GL:
            # GEOMETRIA TUBULAR (Maletas 02xx, Fundo Auto 07xx)
            GL = vars_eng.get('GL', 35.0) # Padrão industrial se a fórmula falhar
            Blank_X = GL + Lss + Wss + Lss + Wss
            
            # Para a altura (Y), somamos as abas (Flaps)
            # O CSV geralmente chama de FH (Flap Height)
            FH_Top = vars_eng.get('FH', 0)
            FH_Bottom = vars_eng.get('FH_B', FH_Top) # Se não tiver fundo, espelha o topo
            
            # Fallback Inteligente se o CSV não tiver FH explícito
            if FH_Top == 0:
                if modelo == '200': FH_Top = 0
                elif modelo == '203': FH_Top = Wss - d
                elif modelo.startswith('7'): FH_Top = Wss * 0.5; FH_Bottom = Wss * 0.8 (vars_eng.get('Lss',0) * 0.5) # Aprox Fundo Auto
                else: FH_Top = Wss * 0.5; FH_Bottom = Wss * 0.5 # Padrão RSC 0201

            Blank_Y = FH_Top + Hss + FH_Bottom
            return Blank_X, Blank_Y, "Estrutura Tubular (Exata)"

        else:
            # GEOMETRIA TABULEIRO (Corte e Vinco 04xx, 03xx)
            # Verifica se é a complexa 0427 (E-commerce)
            if modelo == '427' or modelo == '426':
                HssY = vars_eng.get('HssY', H + 2*d)
                FH1 = HssY + (1.5 * d)
                Blank_X = (H - ((3 * d) + 1.0)) + Wss + HssY + Wss + FH1
                Blank_Y = (HssY + 14.0) + (HssY - 0.5*d) + Lss + (HssY - 0.5*d) + (HssY + 14.0)
                return Blank_Y, Blank_X, "Geometria 0427 (Validada)"

            # Demais Tabuleiros (Base + Paredes)
            # Tenta achar variáveis de blank direto no CSV
            if 'L_Blank' in vars_eng and 'W_Blank' in vars_eng:
                return vars_eng['L_Blank'], vars_eng['W_Blank'], "Variável Direta CSV"
            
            # Reconstrói a cruz
            # Largura Total = Base (Wss) + 2x Paredes + 2x Travas
            # Tentamos ler a altura da parede lateral (geralmente Hss)
            Wall_H = vars_eng.get('Hss', H)
            
            # Lógica para Tampas Telescópio (03xx)
            if modelo.startswith('3'):
                return Lss + 2*Wall_H, Wss + 2*Wall_H, "Tabuleiro Telescópio"
            
            # Lógica para Envelopes (04xx genéricos)
            return Lss + 2.5*Wall_H, Wss + 3.0*Wall_H, "Corte e Vinco (Estimado)"

# =========================================================
# 2. INTERFACE COMERCIAL vs TÉCNICA
# =========================================================
st.set_page_config(page_title="SmartPack Precision", layout="wide")

# Inicializa Engine com Cache Seguro
@st.cache_resource
def load_engine_v11():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine_v11()
if 'carrinho' not in st.session_state: st.session_state.carrinho = []

# Carrega Tabela de Materiais (Auto-Diagnóstico)
@st.cache_data
def load_prices_safe():
    arquivos = [f for f in os.listdir() if 'materiais' in f.lower() and 'csv' in f.lower()]
    if arquivos:
        try:
            df = pd.read_csv(arquivos[0], sep=';')
            if len(df.columns) < 2: df = pd.read_csv(arquivos[0], sep=',')
            return df
        except: pass
    return pd.DataFrame({
        'Onda': ['B', 'C', 'BC'], 'Papel': ['Padrão', 'Padrão', 'Duplo'],
        'Gramatura': [380, 400, 700], 'Espessura': [3.0, 4.0, 6.9],
        'Coluna': [4.0, 4.5, 8.0], 'Preco_m2': [2.77, 2.85, 5.45]
    })

df_materiais = load_prices_safe()

# --- APP ---
st.title("🏭 SmartPack Precision")
st.caption("Sistema de Cálculo Estrutural FEFCO")

with st.sidebar:
    st.header("1. Material")
    onda = st.selectbox("Onda", df_materiais['Onda'].unique())
    df_o = df_materiais[df_materiais['Onda'] == onda]
    papel = st.selectbox("Papel", df_o['Papel'].unique())
    df_p = df_o[df_o['Papel'] == papel]
    coluna = st.selectbox("Resistência", df_p['Coluna'].unique())
    
    # Dados Técnicos
    mat = df_p[df_p['Coluna'] == coluna].iloc[0]
    d_real = float(mat['Espessura'])
    preco = float(mat['Preco_m2'])
    
    st.divider()
    st.header("2. Modelo FEFCO")
    modelos = engine.get_available_models()
    # Prioriza os mais comuns no topo
    tops = ['201', '427', '200', '203', '711', '215', '300']
    lista = [m for m in tops if m in modelos] + [m for m in modelos if m not in tops]
    
    modelo = st.selectbox("Código", lista, format_func=lambda x: f"FEFCO {x.zfill(4)}")
    
    # Mostra imagem ilustrativa baseada na família (Visual Aid)
    if modelo.startswith('2'):
        st.info("📦 **Tipo: Maleta (Slotted)**\n\nEstrutura tubular com abas de fechamento.")
        # 
    elif modelo.startswith('4'):
        st.info("📂 **Tipo: Corte e Vinco (Folder)**\n\nTabuleiro montável, geralmente automontável.")
        # 
    elif modelo.startswith('7'):
        st.info("⚡ **Tipo: Fundo Automático**\n\nColada na lateral e fundo pré-montado.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Medidas Internas (mm)")
    L = st.number_input("Comprimento (C)", value=300)
    W = st.number_input("Largura (L)", value=200)
    H = st.number_input("Altura (A)", value=100)
    qtd = st.number_input("Quantidade", value=500, step=100)
    
    st.markdown("---")
    st.caption(f"Espessura do Material: **{d_real} mm**")

# --- O CÁLCULO MÁGICO ---
bL, bW, logica = engine.calcular_blank_exato(modelo, L, W, H, d_real)
area = (bL * bW) / 1_000_000
total = (area * preco) * 2.0 * qtd

with col2:
    st.subheader("Análise de Engenharia")
    
    # Exibe o "Raio-X" da caixa
    st.success(f"**Topologia Detectada:** {logica}")
    
    colA, colB = st.columns(2)
    with colA:
        st.metric("Largura da Chapa (Blank X)", f"{bL:.1f} mm")
        st.metric("Comprimento da Chapa (Blank Y)", f"{bW:.1f} mm")
    with colB:
        st.metric("Consumo Unitário", f"{area:.4f} m²")
        st.metric("Valor do Pedido", f"R$ {total:,.2f}")

    # Detalhe Técnico para a Fábrica
    with st.expander("🔍 Ver Detalhes de Produção"):
        st.markdown(f"""
        **Ordem de Produção:**
        * **Modelo:** FEFCO {modelo}
        * **Dimensões Finais:** {L} x {W} x {H} mm
        * **Blank de Corte:** {bL:.1f} x {bW:.1f} mm
        * **Material:** Onda {onda} ({coluna}kg)
        * **Lógica de Vinco:** Compensação K = {1.7*d_real if modelo.startswith(('2','5','7')) else 1.0*d_real:.1f}mm
        """)
        
    if st.button("🛒 Confirmar Orçamento", type="primary", use_container_width=True):
        st.session_state.carrinho.append({
            "Modelo": f"FEFCO {modelo}",
            "Blank": f"{bL:.0f}x{bW:.0f}",
            "Total": total
        })
        st.toast("Orçamento salvo!")

if st.session_state.carrinho:
    st.divider()
    st.dataframe(pd.DataFrame(st.session_state.carrinho))
