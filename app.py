import streamlit as st
import pandas as pd
import re

# Configuración de página
st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta de logística territorial. Base de datos integrada.")

# --- FUNCIÓN DE CARGA (Con Memoria Caché) ---
# Esto hace que el archivo se lea una sola vez y no cada vez que alguien busca
@st.cache_data
def cargar_datos():
    try:
        # Intenta leer el archivo 'padron.csv' que subiste a GitHub
        df = pd.read_csv("padron.csv", encoding='latin-1', sep=',')
        
        # Si falla por el separador, intenta con punto y coma
        if df.shape[1] < 2:
             df = pd.read_csv("padron.csv", encoding='latin-1', sep=';')
             
        return df
    except FileNotFoundError:
        return None

# --- FUNCIÓN DE LIMPIEZA ---
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None
    texto = texto.upper().strip()
    match = re.search(r"^([A-Z\s\.]+?)\s+(\d+)", texto)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

# --- INICIO DE LA APP ---
with st.spinner('Cargando base de datos del Padrón...'):
    df = cargar_datos()

if df is not None:
    # Verificamos columnas
    if 'Domicilio' in df.columns:
        
        # Procesamiento de direcciones (en caliente)
        if 'Calle_Limpia' not in df.columns:
            datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
            df['Calle_Limpia'] = datos_limpios[0]
            df['Altura_Limpia'] = datos_limpios[1]
            df = df.dropna(subset=['Calle_Limpia', 'Altura_Limpia'])

        st.success(f"✅ Base de Datos Conectada: {len(df)} afiliados listos para buscar.")
        st.divider()
        
        # --- BUSCADOR ---
        col1, col2 = st.columns([2, 1])
        with col1:
            busqueda = st.text_input("🔍 Buscar Afiliado (Apellido o DNI):", placeholder="Escribe aquí...")

        if busqueda:
            filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                       df['Matricula'].astype(str).str.contains(busqueda, na=False)]
            
            if not filtro.empty:
                opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Limpia']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                seleccion = st.selectbox("Resultados:", list(opciones.keys()))
                
                if seleccion:
                    idx = opciones[seleccion]
                    objetivo = df.loc[idx]
                    
                    st.info(f"📌 **CENTRO:** {objetivo['Apellido']} {objetivo['Nombre']} | {objetivo['Calle_Limpia']} {int(objetivo['Altura_Limpia'])}")
                    
                    # --- CÁLCULO VECINOS ---
                    rango = st.slider("Radio (cuadras aprox):", 100, 800, 400)
                    
                    vecinos = df[
                        (df['Calle_Limpia'] == objetivo['Calle_Limpia']) &
                        (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                        (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                        (df['Matricula'] != objetivo['Matricula'])
                    ].copy()
                    
                    vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                    vecinos = vecinos.sort_values('Distancia')
                    
                    st.write(f"**Se encontraron {len(vecinos)} afiliados en la misma calle:**")
                    st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']], use_container_width=True)
            else:
                st.warning("No se encontraron resultados.")
    else:
        st.error("Error: El archivo padron.csv no tiene la columna 'Domicilio'.")
else:
    st.error("⚠️ No encuentro el archivo 'padron.csv' en el repositorio. Asegúrate de haberlo subido a GitHub con ese nombre exacto.")
