import streamlit as st
import pandas as pd
import math
import os
import re

# =========================================================
# SMARTPACK BACKEND ROBUSTO (Dependency Solver)
# =========================================================
class SmartPackBackend:
    """
    Backend Profissional:
    - Resolução Topológica (não usa loop burro de 5x)
    - Contexto Seguro (sem eval solto perigoso)
    - Auditoria de Falhas (retorna lista de erros)
    """

    def __init__(self, csv_path='formulas_smartpack.csv'):
        self.csv_path = csv_path
        self.df = pd.DataFrame()
        if os.path.exists(csv_path):
            try:
                self.df = pd.read_csv(csv_path, delimiter=';', dtype={'Modelo': str}, on_bad_lines='skip')
                # Limpeza agressiva para garantir leitura
                self.df['Modelo'] = self.df['Modelo'].astype(str).str.replace(r"\D", "", regex=True).str.lstrip('0')
                self.df['Parametro'] = self.df['Parametro'].astype(str).str.strip()
                self.df['Formula'] = self.df['Formula'].astype(str).str.strip()
            except Exception:
                self.df = pd.DataFrame()

    def get_available_models(self):
        if self.df.empty: return []
        return sorted(self.df['Modelo'].dropna().unique(), key=lambda x: (len(x), x))

    # ---------- UTILITÁRIOS ----------
    @staticmethod
    def _is_number(s: str) -> bool:
        s = str(s).strip()
        return bool(re.fullmatch(r"[-+]?\d+(\.\d+)?", s))

    @staticmethod
    def _deps(expr: str):
        """Extrai variáveis de uma fórmula para checar dependências."""
        tokens = set(re.findall(r"\b[A-Za-z_]\w*\b", expr))
        # Blacklist de palavras que NÃO são variáveis do CSV
        blacklist = {
            "min","max","abs","sqrt","sin","cos","tan","asin","atan","floor","ceil","round",
            "switch","if","if1","if2", "pow", "pi",
            "Yes","No","Flat","Round",
            "dtID","dtOD","dtSS","DT",
            "d","fd", "C90x", "GlueCorr", "SlotWidth" # Funções do contexto
        }
        return {t for t in tokens if t not in blacklist}

    # ---------- CONTEXTO MATEMÁTICO (O Mapeamento Prinect) ----------
    def _make_context(self, L, W, H, d, base_dim="ID", UL=1):
        t = float(d)

        # Definição Sólida de Tipo de Dimensão
        dtID, dtOD, dtSS = "dtID", "dtOD", "dtSS"
        base_dim = str(base_dim).upper().strip()
        DT = dtID if base_dim == "ID" else (dtOD if base_dim == "OD" else dtSS)

        # Funções Auxiliares Seguras
        def switch(x, a, aval, b, bval, c=None, cval=None):
            if x == a: return aval
            if x == b: return bval
            if c is not None and x == c: return cval
            return bval

        # --- AQUI ESTÁ A INTEGRAÇÃO COM SEU CSV ---
        # Mapeamos as funções do Prinect para valores físicos baseados na espessura (t)
        k_d = lambda *a: t
        k_h = lambda *a: 0.5 * t
        
        ctx = {
            # Dimensões e Estado
            "L": float(L), "W": float(W), "H": float(H),
            "dtID": dtID, "dtOD": dtOD, "dtSS": dtSS, "DT": DT,
            "Yes": 1, "No": 0, "Flat": 0, "Round": 1, "UL": int(UL),

            # Matemática
            "sqrt": math.sqrt, "min": min, "max": max, "abs": abs,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "atan": math.atan, "pow": math.pow, "pi": math.pi,
            "switch": switch,

            # Funções Prinect (Fundamentais para não gerar erro de dependência)
            "d": lambda: t, "fd": lambda: 0.5 * t,
            
            # Correções de Vinco (Mapeadas dos arquivos .htm que analisamos)
            "C90x": k_h, "C90y": k_h, "C90X": k_h, "C90Y": k_h,
            "HC90x": k_d, "HC90X": k_d, "HC90y": k_d,
            "GlueCorr": k_h, "GLWidth": lambda *a: 35.0,
            "SlotWidth": lambda *a: max(6.0, t + 1.0),
            "LPCorr": lambda *a: 0.0,
            
            # Tratamento de Funções "Missing" (Evita travamento)
            "O90y": k_d, "I90y": k_h, "DC0y": lambda *a: 0.0,
            "BCDC1x": k_d, "HWDC1x": k_d,
            
            # Inicialização de Variáveis Comuns (Para quebrar ciclo se necessário)
            "Wlc": 0.0, "Llc": 0.0, "Hlc": 0.0, "LSC": 0.0,
            "CLFH": 0.0, "TIFH": 0.0, "Ext": 0.0, "PH": 0.0
        }
        return ctx

    # ---------- RESOLUÇÃO TOPOLÓGICA (O Coração do Código) ----------
    def _resolve_formulas(self, modelo, L, W, H, d, base_dim="ID", UL=1, max_iter=500):
        modelo = str(modelo).lstrip('0')
        if self.df.empty: return None, ["CSV Vazio"]

        df_model = self.df[self.df['Modelo'] == modelo]
        if df_model.empty: return None, [f"Modelo {modelo} não encontrado"]

        # Carrega fórmulas brutas
        formulas = {row["Parametro"]: str(row["Formula"]).strip().lstrip("=") for _, row in df_model.iterrows()}
        ctx = self._make_context(L, W, H, d, base_dim=base_dim, UL=UL)
        
        pending = dict(formulas)
        resolved = {}
        warnings = []

        # Loop de Resolução Topológica
        for _ in range(max_iter):
            if not pending: break
            progressed = False
            
            for param, expr in list(pending.items()):
                # Ignora inputs base
                if param in ("L", "W", "H"): 
                    pending.pop(param, None)
                    continue

                expr_py = expr.replace("^", "**")
                
                # Caso 1: É número direto
                if self._is_number(expr_py):
                    val = float(expr_py)
                    ctx[param] = val
                    resolved[param] = val
                    pending.pop(param, None)
                    progressed = True
                    continue

                # Caso 2: Checa dependências
                deps = self._deps(expr_py)
                if not deps.issubset(ctx.keys()):
                    continue # Ainda falta informação, pula

                # Caso 3: Tenta calcular
                try:
                    val = eval(expr_py, {"__builtins__": {}}, ctx)
                    if isinstance(val, (int, float)): val = float(val)
                    ctx[param] = val
                    resolved[param] = val
                    pending.pop(param, None)
                    progressed = True
                except Exception:
                    continue # Erro de cálculo (ex: divisão por zero), tenta depois

            if not progressed: break

        # Relatório de Pendências
        if pending:
            sample = list(pending.items())[:5]
            missing_map = []
            for p, ex in sample:
                missing = sorted([x for x in self._deps(ex) if x not in ctx])
                missing_map.append(f"Param '{p}': Faltando {missing}")
            warnings.append(f"Pendências não resolvidas ({len(pending)}): " + "; ".join(missing_map))

        return ctx, warnings

    # ---------- API PÚBLICA ----------
    def calcular_blank_exato(self, modelo, L, W, H, d, base_dim="ID", UL=1):
        ctx, warns = self._resolve_formulas(modelo, L, W, H, d, base_dim=base_dim, UL=UL)
        if ctx is None: return 0.0, 0.0, "Erro Modelo", warns

        # 1. Tenta a Verdade Absoluta (Se você exportou SheetWidth do Prinect)
        if 'SheetWidth' in ctx and ctx['SheetWidth'] > 0:
            return ctx['SheetWidth'], ctx.get('SheetHeight', 0), "Prinect Sheet Data", warns
        
        if 'FlatWidth' in ctx and ctx['FlatWidth'] > 0:
            return ctx['FlatWidth'], ctx.get('FlatHeight', 0), "Prinect Flat Data", warns

        # 2. Usa os componentes resolvidos (Lss/Wss)
        Lss = ctx.get("Lss") or ctx.get("Lss1")
        Wss = ctx.get("Wss") or ctx.get("Wss1")
        
        # IMPORTANTE: Para caixas tubulares (02xx, 07xx), Lss é apenas UM PAINEL.
        # Se usarmos só Lss, o preço fica errado. Precisamos somar (Layout).
        # Se o CSV já calculou o Blank total na variável 'L_Blank', usamos ela.
        if 'L_Blank' in ctx: Lss = ctx['L_Blank']
        
        # Verificação de Segurança para Tubulares
        # Se achou GL (Aba de Cola), sabemos que precisamos multiplicar os paineis
        if 'GL' in ctx and Lss < (2*L + 2*W): 
            # Reconstrução Segura usando variáveis resolvidas
            GL = ctx.get('GL', 35.0)
            Wss_Calc = ctx.get('Wss', W)
            # Layout Tubular: GL + Frente + Lateral + Fundo + Lateral
            # (Aqui usamos as variáveis resolvidas Lss e Wss, não o L bruto)
            Lss = GL + 2*Lss + 2*Wss_Calc 
            
            # Altura Tubular
            Top = ctx.get('FH', 0)
            Bottom = ctx.get('FH_B', ctx.get('Bottom', Top)) # Tenta achar fundo específico
            Wss = Top + ctx.get('Hss', H) + Bottom

        if isinstance(Lss, (int, float)) and isinstance(Wss, (int, float)) and Lss > 0 and Wss > 0:
            return float(Lss), float(Wss), "Cálculo Robusto V18", warns

        return 0.0, 0.0, "Falha de Resolução", warns

# =========================================================
# APP STREAMLIT (INTERFACE)
# =========================================================
st.set_page_config(page_title="SmartPack V18 Pro", layout="wide")

@st.cache_resource
def load_engine():
    return SmartPackBackend('formulas_smartpack.csv')

engine = load_engine()

# Leitura segura de materiais
@st.cache_data
def load_prices_safe():
    try:
        files = [f for f in os.listdir() if 'materiais' in f.lower() and 'csv' in f.lower()]
        if files: return pd.read_csv(files[0], sep=';' if ';' in open(files[0]).read() else ',')
    except: pass
    return pd.DataFrame({'Onda': ['B'], 'Papel': ['Padrão'], 'Coluna': ['4.0'], 'Preco_m2': [3.0], 'Espessura': [3.0]})

df_materiais = load_prices_safe()

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Material")
    if not df_materiais.empty:
        onda = st.selectbox("Onda", df_materiais['Onda'].unique())
        row = df_materiais[df_materiais['Onda'] == onda].iloc[0]
        d_real = float(row.get('Espessura', 3.0))
        preco_base = float(row.get('Preco_m2', 3.0))
    else:
        d_real = st.number_input("Espessura (mm)", 3.0)
        preco_base = st.number_input("Preço Base (R$/m²)", 3.0)

    st.divider()
    st.header("2. Definição Comercial")
    # AQUI ESTÁ A CORREÇÃO DO FATOR 2.0
    perda = st.number_input("Markup / Perda (Ex: 1.10 = +10%)", value=1.50, step=0.05)
    
    st.divider()
    modelos = engine.get_available_models()
    if modelos:
        modelo = st.selectbox("Modelo FEFCO", modelos, format_func=lambda x: f"{x.zfill(4)}")
    else:
        st.error("Nenhum modelo carregado. Verifique o CSV.")
        st.stop()

# --- ÁREA PRINCIPAL ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Dimensões Internas")
    L = st.number_input("Comprimento (L)", value=300)
    W = st.number_input("Largura (W)", value=200)
    H = st.number_input("Altura (H)", value=100)
    qtd = st.number_input("Quantidade", value=1000, step=100)

# CÁLCULO
bL, bW, perfil, warns = engine.calcular_blank_exato(modelo, L, W, H, d_real)

with col2:
    st.subheader("Resultado de Engenharia")
    
    # Validação de Segurança
    if bL <= 0 or bW <= 0:
        st.error(f"❌ Falha no Cálculo ({perfil})")
        if warns:
            with st.expander("Ver Logs de Erro"):
                for w in warns: st.code(w)
    else:
        area_unit = (bL * bW) / 1_000_000
        custo_total = (area_unit * preco_base) * perda * qtd
        
        st.success(f"Motor: **{perfil}**")
        c1, c2 = st.columns(2)
        c1.metric("Largura Chapa", f"{bL:.1f} mm")
        c2.metric("Compr. Chapa", f"{bW:.1f} mm")
        
        st.info(f"Consumo Unitário: {area_unit:.4f} m²")
        st.metric(f"Valor Total (Fator {perda:.2f})", f"R$ {custo_total:,.2f}")
        
        # Mostra avisos não fatais
        if warns:
            with st.expander("⚠️ Avisos de Resolução (Parâmetros Faltantes)"):
                for w in warns: st.text(w)
