import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# Configuración visual de la aplicación
st.set_page_config(page_title="Consulta de Inventario", page_icon="📦", layout="centered")

st.markdown("<h1 style='text-align: center;'>📦 Consulta de Inventario</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Busca códigos, descripciones o ubicaciones al instante</p>", unsafe_allow_html=True)
st.divider()

# Función optimizada para cargar la base de datos
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        # Limpiamos posibles espacios invisibles en los títulos de las columnas
        df.columns = df.columns.astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx' en el repositorio.")
        return None

df = cargar_datos()

if df is not None:
    # Definición exacta de tus columnas reales
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Caja de texto limpia para el usuario
    consulta = st.text_input("🔍 Escriba el producto, descripción o código a buscar:", placeholder="Ej: trapero, de walt, 1170371...")

    if consulta:
        consulta_limpia = consulta.strip().lower()

        # Palabras comunes a ignorar si el usuario escribe una frase conversacional
        palabras_ignorar = ["hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo", "producto", "búscame", "buscame", "necesito", "stock"]
        palabras_clave = " ".join([p for p in consulta_limpia.split() if p not in palabras_ignorar])

        if palabras_clave:
            # --- NUEVA LÓGICA DE BÚSQUEDA DIFUSA ---
            # 1. Intentar búsqueda exacta primero por rendimiento
            mascara_exacta = df[COL_DESCRIPCION].astype(str).str.lower().str.contains(palabras_clave, na=False) | \
                             df[COL_CODIGO].astype(str).str.lower().str.contains(palabras_clave, na=False)
            
            resultados_exactos = df[mascara_exacta]

            if not resultados_exactos.empty:
                resultados = resultados_exactos.copy()
            else:
                # 2. Si no hay coincidencia exacta, aplicamos RapidFuzz fila por fila
                # Creamos una función que evalúa qué tan parecida es la consulta con la descripción de tu inventario
                def calcular_similitud(fila):
                    desc = str(fila[COL_DESCRIPCION]).lower()
                    cod = str(fila[COL_CODIGO]).lower()
                    
                    # Comparamos la consulta con la descripción (usamos WRatio que es excelente para textos cortos)
                    score_desc = fuzz.WRatio(palabras_clave, desc)
                    # Comparamos con el código por si el usuario metió un número similar
                    score_cod = fuzz.token_set_ratio(palabras_clave, cod) 
                    
                    return max(score_desc, score_cod)

                # Copiamos el dataframe temporalmente para no alterar el original
                df_busqueda = df.copy()
                df_busqueda['coincidencia'] = df_busqueda.apply(calcular_similitud, axis=1)
                
                # Filtramos las filas que tengan más del 65% de similitud y ordenamos de mayor a menor
                resultados = df_busqueda[df_busqueda['coincidencia'] >= 65].sort_values(by='coincidencia', ascending=False)
        else:
            resultados = pd.DataFrame()

        # Mostrar resultados de forma estética
        if not resultados.empty:
            st.success(f"✅ Se encontraron {len(resultados)} coincidencia(s):")
            
            # Limitamos a los mejores 10 resultados para no saturar la pantalla si hay demasiadas opciones difusas
            for _, fila in resultados.head(10).iterrows():
                # Tarjeta limpia para cada producto
                with st.container():
                    st.markdown(f"### 🔹 {fila[COL_DESCRIPCION]}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**🔢 Código:** `{fila[COL_CODIGO]}`")
                    with col2:
                        ub = fila[COL_UBICACION] if pd.notna(fila[COL_UBICACION]) else "No asignada"
                        st.markdown(f"**📍 Ubicación:** {ub}")
                    with col3:
                        stock_val = fila[COL_STOCK] if pd.notna(fila[COL_STOCK]) else 0
                        unidad_val = fila[COL_UNIDAD] if pd.notna(fila[COL_UNIDAD]) else "UN"
                        st.markdown(f"**📊 Stock:** {int(stock_val)} {unidad_val}")
                    
                    st.markdown("<div style='padding: 2px;'></div>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.error("❌ No se encontraron resultados ni sugerencias aproximadas para tu búsqueda.")
