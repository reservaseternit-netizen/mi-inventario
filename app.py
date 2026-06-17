import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# Configuración visual de la aplicación
st.set_page_config(page_title="Consulta de Inventario Pro", page_icon="📦", layout="centered")

st.markdown("<h1 style='text-align: center;'>📦 Consulta de Inventario Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Búsqueda avanzada multi-criterio (Material, Medida, Código)</p>", unsafe_allow_html=True)
st.divider()

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()
        
        # --- PRE-PROCESAMIENTO INTERNO DE DATOS SUCIOS ---
        # Reemplazamos los valores nulos (NaN) por textos vacíos o valores por defecto
        # para que las funciones de búsqueda no fallen.
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors='coerce').fillna(0).astype(int)
        
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'.")
        return None

df = cargar_datos()

if df is not None:
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Input de búsqueda explicativo para el usuario
    consulta = st.text_input(
        "🔍 Filtre por producto, material, medida o largo:", 
        placeholder="Ej: niple galvanizado 1/8 x 1"
    )

    if consulta:
        consulta_limpia = consulta.strip().lower()

        # Palabras irrelevantes que el sistema ignorará
        palabras_ignorar = ["hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo", "producto", "búscame", "buscame", "necesito", "stock", "con", "para"]
        
        # Separamos la consulta en palabras clave individuales (Ej: ['niple', 'galvanizado', '1/8', '1'])
        palabras_clave = [p for p in consulta_limpia.split() if p not in palabras_ignorar]

        if palabras_clave:
            df_resultados = df.copy()
            
            # --- ALGORITMO DE SCORING MULTI-PALABRA ---
            def evaluar_fila(fila):
                texto_producto = f"{fila[COL_DESCRIPCION]} {fila[COL_CODIGO]}".lower()
                
                score_total = 0
                coincidencias_criticas = 0
                
                for palabra in palabras_clave:
                    # 1. Intentamos coincidencia exacta de la palabra o medida dentro del texto del repuesto
                    if palabra in texto_producto:
                        score_total += 100
                        coincidencias_criticas += 1
                    else:
                        # 2. Si no es exacta (error ortográfico tipo 'visturi'), calculamos su similitud difusa
                        # Buscamos la palabra dentro del texto usando partial_ratio
                        similitud = fuzz.partial_ratio(palabra, texto_producto)
                        if similitud >= 75:  # Umbral de tolerancia ortográfica
                            score_total += similitud
                            coincidencias_criticas += 1
                
                # Penalizamos fuertemente si el artículo no contiene la mayoría de las palabras clave buscadas
                # Esto evita que al buscar 'niple galvanizado 1/8' aparezcan niples de plástico o de otras medidas
                if coincidencias_criticas < len(palabras_clave):
                    score_total = score_total * (coincidencias_criticas / len(palabras_clave))
                
                return score_total

            # Aplicamos la evaluación a todo el inventario
            df_resultados['Score_Busqueda'] = df_resultados.apply(evaluar_fila, axis=1)
            
            # Filtramos aquellos que tengan un puntaje mínimo razonable y ordenamos de mayor a menor relevancia
            umbral_minimo = 60 * len(palabras_clave)
            resultados = df_resultados[df_resultados['Score_Busqueda'] >= umbral_minimo]
            resultados = resultados.sort_values(by='Score_Busqueda', ascending=False)
        else:
            resultados = pd.DataFrame()

        # --- RENDERIZADO DE RESULTADOS ---
        if not resultados.empty:
            st.success(f"✅ Se encontraron {len(resultados)} coincidencia(s) ordenadas por relevancia:")
            
            # Mostramos un máximo de 20 para no congelar el navegador, priorizando los mejores matches
            for _, fila in resultados.head(20).iterrows():
                with st.container():
                    st.markdown(f"### 🔹 {fila[COL_DESCRIPCION]}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**🔢 Código:** `{fila[COL_CODIGO]}`")
                    with col2:
                        st.markdown(f"**📍 Ubicación:** {fila[COL_UBICACION]}")
                    with col3:
                        st.markdown(f"**📊 Stock:** {fila[COL_STOCK]} {fila[COL_UNIDAD]}")
                    
                    st.markdown("<div style='padding: 2px;'></div>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.error("❌ No se encontraron repuestos que coincidan con esos criterios combinados. Intente refinar los términos.")
            
