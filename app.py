import streamlit as st
import pandas as pd
import re

# Configuración de página
st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta de logística territorial. Base de datos integrada.")

# --- FUNCIÓN DE CARGA ---
@st.cache_data
def cargar_datos():
    # AHORA BUSCAMOS EL NOMBRE SIMPLE
    nombre_archivo = "datos.csv"
    
    try:
        # Intentamos leer como CSV estándar
        df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=',')
        
        # Si falló la separación, probamos con punto y coma
        if df.shape[1] < 2:
             df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=';')
             
        return df
    except FileNotFoundError:
        return None

# --- FUNCIÓN LIMPIEZA ---
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None
    texto = texto.upper().strip()
    match = re.search(r"^([A-Z\s\.]+?)\s+(\d+)", texto)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

# --- APP ---
with st.spinner('Cargando padrón...'):
    df = cargar_datos()

if df is not None:
    if 'Domicilio' in df.columns:
        
        if 'Calle_Limpia' not in df.columns:
            datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
            df['Calle_Limpia'] = datos_limpios[0]
            df['Altura_Limpia'] = datos_limpios[1]
            df = df.dropna(subset=['Calle_Limpia', 'Altura_Limpia'])

        st.success(f"✅ Base cargada: {len(df)} afiliados.")
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            busqueda = st.text_input("🔍 Buscar (Apellido o DNI):", placeholder="Ej: PEREZ")

        if busqueda:
            filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                       df['Matricula'].astype(str).str.contains(busqueda, na=False)]
            
            if not filtro.empty:
                opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Limpia']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                seleccion = st.selectbox("Resultados:", list(opciones.keys()))
                
                if seleccion:
                    idx = opciones[seleccion]
                    objetivo = df.loc[idx]
                    
                    st.info(f"📌 CENTRO: {objetivo['Apellido']} {objetivo['Nombre']} | {objetivo['Calle_Limpia']} {int(objetivo['Altura_Limpia'])}")
                    
                    rango = st.slider("Radio (numeración):", 100, 800, 400)
                    
                    vecinos = df[
                        (df['Calle_Limpia'] == objetivo['Calle_Limpia']) &
                        (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                        (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                        (df['Matricula'] != objetivo['Matricula'])
                    ].copy()
                    
                    vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                    vecinos = vecinos.sort_values('Distancia')
                    
                    st.write(f"**Vecinos encontrados en la misma calle:** {len(vecinos)}")
                    st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']], use_container_width=True)
            else:
                st.warning("No encontrado.")
    else:
        st.error("Error: El archivo datos.csv no tiene columna 'Domicilio'.")
else:
    st.error("⚠️ ERROR: No encuentro el archivo 'datos.csv'. Asegúrate de haberlo subido a GitHub con ese nombre exacto (todo minúscula).")
