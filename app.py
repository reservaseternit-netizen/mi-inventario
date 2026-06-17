import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# Configuración visual de la aplicación
st.set_page_config(page_title="Portal de Inventario | Eternit", page_icon="🏗️", layout="centered")

# --- ENCABEZADO PERSONALIZADO (Estilo Eternit Colombiana) ---
st.markdown(
    """
    <div style="text-align: center; padding-bottom: 10px;">
        <h1 style="color: #003366; margin-bottom: 5px; font-family: 'Segoe UI', Arial, sans-serif;">
            🏠 Consulta de Inventario y Repuestos
        </h1>
        <p style="color: #555555; font-size: 1.1rem; font-style: italic; margin-top: 0px;">
            Eternit Colombiana — Búsqueda Avanzada de Materiales, Tejas y Componentes
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)
st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>Filtro multi-criterio inteligente (Material, Medida, Código)</p>", unsafe_allow_html=True)
st.divider()

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()
        
        # --- PRE-PROCESAMIENTO INTERNO DE DATOS SUCIOS ---
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors='coerce').fillna(0).astype(int)
        
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'. Por favor verifique la ruta.")
        return None

df = cargar_datos()

if df is not None:
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Input de búsqueda explicativo para el usuario
    consulta = st.text_input("🔍 Ingrese el producto, tipo de teja, repuesto o medida:", placeholder="Ej: teja ondulada, perfil 7, niple galvanizado 1/8")

    if consulta:
        consulta_limpia = consulta.strip().lower()

        # Palabras irrelevantes que el sistema ignorará
        palabras_ignorar = ["hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo", "producto", "búscame", "buscame", "necesito", "stock", "con", "para"]
        
        # Separamos la consulta en palabras clave individuales
        palabras_clave = [p for p in consulta_limpia.split() if p not in palabras_ignorar]

        if palabras_clave:
            df_resultados = df.copy()
            
            # --- ALGORITMO DE SCORING MULTI-PALABRA ---
            def evaluar_fila(fila):
                texto_producto = f"{fila[COL_DESCRIPCION]} {fila[COL_CODIGO]}".lower()
                
                score_total = 0
                coincidencias_criticas = 0
                
                for palabra in palabras_clave:
                    if palabra in texto_producto:
                        score_total += 100
                        coincidencias_criticas += 1
                    else:
                        similitud = fuzz.partial_ratio(palabra, texto_producto)
                        if similitud >= 75:  
                            score_total += similitud
                            coincidencias_criticas += 1
                
                if coincidencias_criticas < len(palabras_clave):
                    score_total = score_total * (coincidencias_criticas / len(palabras_clave))
                
                return score_total

            # Aplicamos la evaluación a todo el inventario
            df_resultados['Score_Busqueda'] = df_resultados.apply(evaluar_fila, axis=1)
            
            # Filtramos aquellos con puntaje mínimo y ordenamos
            umbral_minimo = 60 * len(palabras_clave)
            resultados = df_resultados[df_resultados['Score_Busqueda'] >= umbral_minimo]
            resultados = resultados.sort_values(by='Score_Busqueda', ascending=False)
        else:
            resultados = pd.DataFrame()

        # --- RENDERIZADO DE
