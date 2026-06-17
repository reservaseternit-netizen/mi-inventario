import streamlit as st
import pandas as pd

# Configuración visual de la aplicación
st.set_page_config(page_title="Consulta de Inventario", page_icon="📦", layout="wide")

st.markdown("<h1 style='text-align: center;'>📦 Consulta de Inventario Avanzada</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Utiliza los filtros para encontrar exactamente lo que necesitas</p>", unsafe_allow_html=True)
st.divider()

# Función para cargar la base de datos
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'.")
        return None

df = cargar_datos()

if df is not None:
    # Definición de tus columnas reales
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Convertir descripciones a texto para evitar errores
    df[COL_DESCRIPCION] = df[COL_DESCRIPCION].astype(str)

    # --- SECCIÓN DE FILTROS EN LA BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("🔍 Filtros de Búsqueda")

    # Filtro 1: Texto principal
    buscar_base = st.sidebar.text_input("1. Producto Base:", placeholder="Ej: VALVULA, VIDRIO, ESMERIL").strip().upper()

    # Filtro 2: Medidas comunes (Búsqueda por texto en la descripción)
    opciones_medida = ["Todas", "1/2", "1/4", "3/4", "1\"", "2\"", "3\"", "4\""]
    buscar_medida = st.sidebar.selectbox("2. Medida / Diámetro:", opciones_medida)

    # Filtro 3: Tipo o Diseño
    opciones_tipo = ["Todos", "BOLA", "PASO RECTO", "PORTACABLE", "CABINA", "TRAB.PESADO"]
    buscar_tipo = st.sidebar.selectbox("3. Tipo / Diseño:", opciones_tipo)

    # Filtro 4: Operación o Marca
    opciones_operacion = ["Todos", "MANUAL", "DE WALT", "BOBCAT", "NEW HOLLAND"]
    buscar_operacion = st.sidebar.selectbox("4. Características / Marca:", opciones_operacion)

    # --- LÓGICA DE FILTRADO ---
    resultados = df.copy()

    # Aplicar Filtro 1 (Producto Base)
    if buscar_base:
        resultados = resultados[resultados[COL_DESCRIPCION].str.upper().str.contains(buscar_base, na=False)]

    # Aplicar Filtro 2 (Medida)
    if buscar_medida != "Todas":
        resultados = resultados[resultados[COL_DESCRIPCION].str.upper().str.contains(buscar_medida, na=False)]

    # Aplicar Filtro 3 (Tipo)
    if buscar_tipo != "Todos":
        resultados = resultados[resultados[COL_DESCRIPCION].str.upper().str.contains(buscar_tipo, na=False)]

    # Aplicar Filtro 4 (Operación / Marca)
    if buscar_operacion != "Todos":
        resultados = resultados[resultados[COL_DESCRIPCION].str.upper().str.contains(buscar_operacion, na=False)]

    # --- MOSTRAR RESULTADOS ---
    st.subheader(f"📊 Productos Encontrados ({len(resultados)})")

    if not resultados.empty:
        # Mostrar los resultados en una tabla interactiva muy estética
        # Formateamos el stock para que no muestre decimales feos
        resultados_visibles = resultados.copy()
        resultados_visibles[COL_STOCK] = resultados_visibles[COL_STOCK].fillna(0).astype(int)
        resultados_visibles[COL_UBICACION] = resultados_visibles[COL_UBICACION].fillna("No asignada")
        
        # Seleccionamos y reordenamos las columnas para el usuario
        tabla_final = resultados_visibles[[COL_CODIGO, COL_DESCRIPCION, COL_UBICACION, COL_STOCK, COL_UNIDAD]]
        
        st.dataframe(tabla_final, use_container_width=True, hide_index=True)
    else:
        st.warning("⏳ No hay productos que coincidan con la combinación de filtros seleccionada.")
        
