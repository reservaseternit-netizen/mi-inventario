import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# Configuración visual de la aplicación
st.set_page_config(page_title="Consulta de Inventario Pro", page_icon="📦", layout="wide")

st.markdown("<h1 style='text-align: center;'>📦 Consulta de Inventario Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Búsqueda ultra-rápida inteligente (Material, Medida, Código)</p>", unsafe_allow_html=True)
st.divider()

# --- CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def cargar_y_limpiar_datos(archivo):
    try:
        # openpyxl es requerido para leer archivos modernos de Excel
        df = pd.read_excel(archivo, engine='openpyxl')
        df.columns = df.columns.astype(str).str.strip()
        
        # Mapeo de columnas requeridas para validar que existan
        columnas_criticas = ["Material", "Texto breve de material", "Ubic.", "UMB", "Cantidad stock valorado"]
        for col in columnas_criticas:
            if col not in df.columns:
                st.error(f"⚠️ Falta la columna obligatoria: '{col}' en el Excel.")
                return None

        # Preprocesamiento optimizado (Vectorizado)
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors='coerce').fillna(0).astype(int)
        
        # Creamos el string de búsqueda indexado para acelerar la comparación
        df["Texto_Busqueda"] = (df["Texto breve de material"] + " " + df["Material"]).str.lower()
        
        return df
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
        return None

# Selector de archivos: Dinámico si se sube uno, o busca el local por defecto
archivo_excel = st.sidebar.file_uploader("Actualizar Base de Datos (Excel)", type=["xlsx"])
if not archivo_excel:
    archivo_excel = "mi inventario.xlsx" # Carga por defecto local

df = cargar_y_limpiar_datos(archivo_excel)

# --- LÓGICA DE NEGOCIO ---
if df is not None:
    # Input del usuario
    consulta = st.text_input(
        "🔍 Filtre por producto, material, medida o largo:", 
        placeholder="Ej: niple galvanizado 1/8 x 1"
    )

    if consulta:
        consulta_limpia = consulta.strip().lower()
        palabras_ignorar = {"hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo", "producto", "búscame", "buscame", "necesito", "stock", "con", "para"}
        palabras_clave = [p for p in consulta_limpia.split() if p not in palabras_ignorar]

        if palabras_clave:
            # --- MOTOR DE BÚSQUEDA OPTIMIZADO (Sin .apply) ---
            # Filtro 1: Buscamos filas que tengan coincidencias exactas de al menos una palabra clave (Filtro rápido)
            mascara_interseccion = df["Texto_Busqueda"].apply(lambda x: any(p in x for p in palabras_clave))
            df_filtrado = df[mascara_interseccion].copy()

            if not df_filtrado.empty:
                # Calculamos el scoring aprovechando la velocidad de RapidFuzz en lote
                def calcular_score_rapido(texto_fila):
                    score_total = 0
                    coincidencias = 0
                    for palabra in palabras_clave:
                        if palabra in texto_fila:
                            score_total += 100
                            coincidencias += 1
                        else:
                            # partial_ratio directo y veloz
                            similitud = fuzz.partial_ratio(palabra, texto_fila)
                            if similitud >= 75:
                                score_total += similitud
                                coincidencias += 1
                    
                    # Penalización por palabras faltantes
                    if coincidencias < len(palabras_clave):
                        score_total *= (coincidencias / len(palabras_clave))
                    return score_total

                df_filtrado['Score'] = df_filtrado["Texto_Busqueda"].apply(calcular_score_rapido)
                
                # Umbral y ordenamiento
                umbral_minimo = 60 * len(palabras_clave)
                resultados = df_filtrado[df_filtrado['Score'] >= umbral_minimo].sort_values(by='Score', ascending=False)
            else:
