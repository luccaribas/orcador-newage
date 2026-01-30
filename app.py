import streamlit as st
import pandas as pd
import math
import os # Biblioteca para ver arquivos do sistema

# =========================================================
# 1. ENGINE & CALIBRAÇÃO (V9 - MANTIDO)
# =========================================================
class CalibrationEngine:
    @staticmethod
    def get_factors(modelo, d):
        fam = str(modelo)[0]
        if fam in ['2', '5', '6', '7']: return {'C90': 0.5, 'C180': 1.0*d, 'HC90': 1.7*d, 'Glue': 0.5, 'Slot': d+1.0, 'Profile': 'Tubular'}
        elif fam in ['3', '4']: return {'C90': 1.0*d, 'C180': 2.0*d, 'HC90': 1.0*d, 'Glue': 1.0*d, 'Slot': d+2.0, 'Profile': 'Tabuleiro'}
        else: return {'C90': 0.5*d, 'C180': d, 'HC90': d, 'Glue': 0, 'Slot': d, 'Profile': 'Generico'}

class SmartPackBackend:
    def __init__(self, csv_path='formulas_smartpack.csv'):
        # Tenta ler o arquivo de fórmulas
        if os.path.exists(csv_path):
            try:
                self.df = pd.read_csv(csv_path, delimiter=';', dtype={'Modelo': str})
                self.df['Modelo'] = self.df['Modelo'].str.lstrip('0')
            except: pass
        else:
            self.df = pd.DataFrame() # Cria vazio se falhar

    def get_available_models(self):
        if self.df.empty: return []
        return sorted(self.df['Modelo'].unique())

    def _get_engine_variables(self, modelo, L, W, H, d):
        modelo = str(modelo).lstrip('0')
        if self.df.empty: return None
        df_model = self.df[self.df['Modelo'] == modelo]
        if df_model.empty: return None

        k = CalibrationEngine.get_factors(modelo, d)
        contexto = {
            'L': float(L), 'W': float(W), 'H': float(H), 'd': lambda: float(d),
            'dtID': 1, 'dtOD': 0, 'No': 0, 'Yes': 1, 'Flat': 0, 'Round': 1, 'fd': lambda: 0,
            'sqrt': math.sqrt, 'min': min, 'max': max, 'tan': math.tan, 'atan': math.atan,
            'C90x': lambda *a: k['C90'], 'C90y': lambda *a: k['C90'],
            'HC90x': lambda *a: k['HC90'], 'GlueCorr': lambda *a: k['Glue'],
            'LPCorr': lambda *a: 1.0 * d, 'GLWidth': lambda *a: 35.0,
            'LSCf': lambda *a: 1.5 * d, 'SlotWidth': lambda *a: k['Slot'],
            'LC': lambda d_val, dt, iln, oln: (iln if dt==1 else oln) * d,
            'switch': lambda cond, *args: args[1] if cond else args[0]
        }
        
        resolvidos = {}
        for _ in range(5):
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
        resolvidos['_Profile'] = k['Profile']
        return resolvidos

    def calcular_blank(self, modelo, L, W, H, d):
        vars_eng = self._get_engine_variables(modelo, L, W, H, d)
        if not vars_eng: return 0, 0, "Erro"

        k = CalibrationEngine.get_factors(modelo, d)
        Lss = vars_eng.get('Lss', L + k['C90']*2)
        Wss = vars_eng.get('Wss', W + k['C90']*2)
        Hss = vars_eng.get('Hss', H + k['HC90'])
        
        has_GL = 'GL' in vars_eng or 'GLWidth' in str(self.df[self.df['Modelo']==modelo]['Formula'].values)
        
        if has_GL or modelo.startswith(('2', '5', '6', '7')):
            GL = vars_eng.get('GL', 35.0)
            Blank_X = GL + Lss + Wss + Lss + Wss
            Flap_Top = vars_eng.get('FH', Wss / 2)
            if modelo == '200': Flap_Top = 0
            elif modelo == '203': Flap_Top = Wss - d
            Blank_Y = Flap_Top + Hss + vars_eng.get('FH_B', Flap_Top)
            return Blank_X, Blank_Y, k['Profile']
        elif modelo == '427':
            HssY = vars_eng.get('HssY', H + 2*d)
            FH1 = HssY + (1.5 * d)
            TIFH = H - ((3 * d) + 1.0)
            Blank_X = TIFH + Wss + HssY + Wss + FH1
            PH = HssY - (0.5 * d)
            Ear = HssY + 14.0
            Blank_Y = Ear + PH + Lss + PH + Ear
            return Blank_Y, Blank_X, "0427 Gold"
        else:
            Wall_H = vars_eng.get('Hss', H + d)
            if modelo.startswith('3'): return Lss + (2 * Wall_H), Wss + (2 * Wall_H), k['Profile']
            else: return Lss + (2 * Wall_H), Wss + (3 * Wall_H), "Estimado"

# =========================================================
# 2. CONFIGURAÇÃO E CARGA SEGURA (V9)
# =========================================================
st.set_page_config(page_title="SmartPack Enterprise", layout="wide")

@st.cache_resource
def load_engine_v9():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine_v9()

if 'carrinho' not in st.session_state: st.session_state.carrinho = []

st.title("🏭 SmartPack Enterprise")

# --- FUNÇÃO DE DIAGNÓSTICO E LEITURA ---
@st.cache_data
def load_prices_safe():
    # Procura arquivos com nomes parecidos para evitar erro de .txt oculto
    arquivos_pasta = os.listdir()
    
    arquivo_encontrado = None
    for f in arquivos_pasta:
        if 'materiais' in f.lower() and 'csv' in f.lower():
            arquivo_encontrado = f
            break
            
    if arquivo_encontrado:
        try:
            df = pd.read_csv(arquivo_encontrado, sep=';')
            if len(df.columns) < 2: df = pd.read_csv(arquivo_encontrado, sep=',')
            return df, arquivo_encontrado
        except:
            return None, "Erro Leitura"
    
    # Se não achou nada, retorna None
    return None, "Não Encontrado"

df_materiais, status_arquivo = load_prices_safe()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuração")
    
    # FERRAMENTA DE DIAGNÓSTICO (Vai aparecer na sua tela!)
    if df_materiais is None:
        st.error(f"⚠️ Status: {status_arquivo}")
        st.warning("Usando Tabela PADRÃO (Modo Segurança)")
        
        # Mostra o que o Python está vendo na pasta
        st.markdown("---")
        st.caption("🕵️‍♂️ Diagnóstico de Arquivos:")
        arquivos = os.listdir()
        for f in arquivos:
            if 'csv' in f or 'py' in f:
                st.code(f) # Lista os arquivos reais
        st.markdown("---")
        
        # Tabela Padrão (Fallback)
        dados_padrao = {
            'Onda': ['B', 'C', 'BC'],
            'Papel': ['Reciclado', 'Kraft', 'Duplo'],
            'Gramatura': [380, 400, 700],
            'Espessura': [3.0, 4.0, 6.9],
            'Coluna': [4.0, 4.5, 8.0],
            'Preco_m2': [2.77, 2.85, 5.45]
        }
        df_materiais = pd.DataFrame(dados_padrao)
    else:
        st.success(f"✅ Tabela Carregada: `{status_arquivo}`")

    # Filtros em Cascata
    ondas = df_materiais['Onda'].unique()
    onda_sel = st.selectbox("1. Onda", ondas)
    
    df_onda = df_materiais[df_materiais['Onda'] == onda_sel]
    papeis = df_onda['Papel'].unique()
    papel_sel = st.selectbox("2. Papel", papeis)
    
    df_final = df_onda[df_onda['Papel'] == papel_sel]
    colunas = df_final['Coluna'].unique()
    coluna_sel = st.selectbox("3. Resistência", colunas)
    
    material = df_final[df_final['Coluna'] == coluna_sel].iloc[0]
    espessura_real = float(material['Espessura'])
    preco_base = float(material['Preco_m2'])
    gramatura = material['Gramatura']
    
    st.divider()
    modelos = engine.get_available_models()
    populares = ['201', '427', '200', '203', '711']
    lista = [m for m in populares if m in modelos] + [m for m in modelos if m not in populares]
    modelo_visual = st.selectbox("Modelo", lista, format_func=lambda x: f"FEFCO {x.zfill(4)}")

# --- AREA PRINCIPAL ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Medidas")
    L = st.number_input("Comprimento (mm)", value=300)
    W = st.number_input("Largura (mm)", value=200)
    H = st.number_input("Altura (mm)", value=100)
    qtd = st.number_input("Quantidade", value=1000, step=100)
    st.caption(f"Material: {onda_sel} | {gramatura}g | {coluna_sel}kg")

bL, bW, perfil = engine.calcular_blank(modelo_visual, L, W, H, espessura_real)
area_m2 = (bL * bW) / 1_000_000
preco_venda = (area_m2 * preco_base) * 2.0 

with col2:
    tab_cli, tab_fab = st.tabs(["Orçamento", "Fábrica"])
    
    with tab_cli:
        c1, c2 = st.columns(2)
        c1.metric("Unitário", f"R$ {preco_venda:.2f}")
        c2.metric("Total", f"R$ {preco_venda * qtd:,.2f}")
        if st.button("🛒 Comprar"):
            st.session_state.carrinho.append({"Modelo": modelo_visual, "Total": preco_venda*qtd})
            st.toast("Sucesso!")

    with tab_fab:
        st.markdown(f"""
        **Ordem de Produção:**
        - Modelo: FEFCO {modelo_visual} ({perfil})
        - Blank: **{bL:.1f} x {bW:.1f} mm**
        - Material: Onda {onda_sel} (Esp: {espessura_real}mm)
        """)

if st.session_state.carrinho:
    st.dataframe(pd.DataFrame(st.session_state.carrinho))
