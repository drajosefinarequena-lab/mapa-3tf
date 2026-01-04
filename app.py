from difflib import SequenceMatcher
import streamlit as st
import pandas as pd
import re

# Configuración de página
st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta de logística territorial. (Base Normalizada y Unificada)")

# --- 1. FUNCIÓN DE CARGA ---
@st.cache_data
def cargar_datos():
    nombre_archivo = "datos.csv" 
    try:
        # Intentamos leer con coma
        df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=',')
        # Si falla, probamos punto y coma
        if df.shape[1] < 2:
             df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=';')
        return df
    except FileNotFoundError:
        return None

# --- 2. FUNCIÓN MAESTRA DE NORMALIZACIÓN ---
def normalizar_calle(texto_calle):
    if not isinstance(texto_calle, str):
        return ""
    
    # Limpieza básica
    calle = texto_calle.upper().strip()
    
    # A. DICCIONARIO DE CORRECCIONES (CASOS ESPECÍFICOS)
    correcciones = {
        # --- CASOS CRÍTICOS DE ESCRITURA ---
        # Beruti
        "BERUTI": "ANTONIO BERUTTI", "BERUTTI": "ANTONIO BERUTTI",
        "A BERUTI": "ANTONIO BERUTTI", "A BERUTTI": "ANTONIO BERUTTI",
        "A.BERUTTI": "ANTONIO BERUTTI", "ANTONIO BERUTI": "ANTONIO BERUTTI",
        "BERUTI ANTONIO": "ANTONIO BERUTTI", "BERUTTI A.": "ANTONIO BERUTTI",
        "ANTONIO BERUTTIIO": "ANTONIO BERUTTI",

        # Cafferata
        "CAFFERATA": "CAFFERATA", "CAFERATA": "CAFFERATA", "CAFERATTA": "CAFFERATA",
        "CAFERRATA": "CAFFERATA", "A CAFFERATA": "CAFFERATA", "A CAFERATTA": "CAFFERATA",
        "AGUSTIN CAFERATTA": "CAFFERATA", "ANGEL CAFERATA": "CAFFERATA",
        "C A CAFERATA": "CAFFERATA",
        
        # Pellegrini
        "PELLEGRINI": "CARLOS PELLEGRINI", "PELEGRINI": "CARLOS PELLEGRINI",
        "C PELLEGRINI": "CARLOS PELLEGRINI", "C. PELLEGRINI": "CARLOS PELLEGRINI",
        "CARLOS PELLEGRINI": "CARLOS PELLEGRINI", "PELLEGRINI CARLOS": "CARLOS PELLEGRINI",
        "C PELEGRINI": "CARLOS PELLEGRINI",

        # Yrigoyen
        "YRIGOYEN": "HIPOLITO YRIGOYEN", "IRIGOYEN": "HIPOLITO YRIGOYEN",
        "H YRIGOYEN": "HIPOLITO YRIGOYEN", "H.YRIGOYEN": "HIPOLITO YRIGOYEN",
        "HIPOLITO YRIGOYEN": "HIPOLITO YRIGOYEN",

        # --- FECHAS Y NÚMEROS ---
        # 12 de Octubre
        "12 DE OCTUBRE": "12 DE OCTUBRE", "12 OCTUBRE": "12 DE OCTUBRE",
        "12 D OCTUBRE": "12 DE OCTUBRE", "DOCE DE OCTUBRE": "12 DE OCTUBRE",
        
        # 3 de Febrero
        "3 DE FEBRERO": "3 DE FEBRERO", "TRES DE FEBRERO": "3 DE FEBRERO",
        "T DE FEBRERO": "3 DE FEBRERO", "T.DE FEBRERO": "3 DE FEBRERO",
        
        # 1 de Mayo
        "1 DE MAYO": "1 DE MAYO", "1RO DE MAYO": "1 DE MAYO",
        "1RO.DE MAYO": "1 DE MAYO", "PRIMERO DE MAYO": "1 DE MAYO",

        # --- EJES PRINCIPALES ---
        # San Martín (Protegemos Boulevard vs Avenida)
        "AV SAN MARTIN": "AV SAN MARTIN", "AV. SAN MARTIN": "AV SAN MARTIN", 
        "GRAL SAN MARTIN": "AV SAN MARTIN", "AV GRAL SAN MARTIN": "AV SAN MARTIN",
        "BOULEVARD SAN MARTIN": "BOULEVARD SAN MARTIN", "BV.SAN MARTIN": "BOULEVARD SAN MARTIN", 
        "BV SAN MARTIN": "BOULEVARD SAN MARTIN", "BVARD SAN MARTIN": "BOULEVARD SAN MARTIN",
        
        # Otros Ejes
        "AV MARQUEZ": "AV MARQUEZ", "MARQUEZ": "AV MARQUEZ", "BERNABE MARQUEZ": "AV MARQUEZ",
        "M T DE ALVEAR": "MARCELO T DE ALVEAR", "ALVEAR": "MARCELO T DE ALVEAR",
        "J J DE URQUIZA": "URQUIZA", "JUSTO JOSE DE URQUIZA": "URQUIZA", "URQUIZA": "URQUIZA",
        "J M DE ROSAS": "JUAN MANUEL DE ROSAS", "ROSAS": "JUAN MANUEL DE ROSAS",
        "AV PTE PERON": "AV PERON", "PTE PERON": "AV PERON",
        
        # Casos puntuales
        "GLADIOLO": "DE LOS GLADIOLOS", "LOS GLADIOLOS": "DE LOS GLADIOLOS",
        "E DE LOS ANDES": "EJERCITO DE LOS ANDES", "E.DE LOS ANDES": "EJERCITO DE LOS ANDES",
        "RCA ARABE SIRIA": "REPUBLICA ARABE SIRIA", "ARABE SIRIA": "REPUBLICA ARABE SIRIA",
        
        # Errores de tipeo
        "PAUSTEUR": "PASTEUR",
        "LACAUTIVA": "LA CAUTIVA",
        "ELISALDE": "PADRE ELIZALDE", "PADRE ELISALDE": "PADRE ELIZALDE",
        "RICCHIERI": "TENIENTE GENERAL RICCHIERI", "TTE GRAL RICCHIERI": "TENIENTE GENERAL RICCHIERI"
    }
    
    # Si encontramos la calle en el diccionario, devolvemos la corrección y TERMINAMOS
    if calle in correcciones:
        return correcciones[calle]
    
    # B. LIMPIEZA GENERAL (Si no estaba en el diccionario)
    palabras_basura = [
        "AV.", "AV ", "AVENIDA ", 
        "CALLE ", 
        "PJE.", "PJE ", "PASAJE ", 
        "GRL.", "GRL ", "GRAL ", "GRAL. ", "GENERAL ", 
        "DR.", "DR ", "DOC ", "DOCTOR ",
        "ING.", "ING ", "INGENIERO ",
        "ARQ.", "ARQ ", "ARQUITECTO ",
        "PROF.", "PROF ", "PROFESOR ",
        "CNEL.", "CNEL ", "CORONEL ",
        "TTE.", "TTE ", "TENIENTE ",
        "SGTO.", "SGTO ", "SARGENTO ",
        "CAP.", "CAP ", "CAPITAN ",
        "MJOR.", "MJOR ", "MAYOR ",
        "CMTE.", "CMTE ", "COMANDANTE ",
        "ALTE.", "ALTE ", "ALMIRANTE ",
        "MONS.", "MONS ", "MONSEÑOR ",
        "PBRO.", "PBRO ", "PRESBITERO ",
        "INT.", "INT ", "INTENDENTE ",
        "MAESTRA ", "MAESTRA. ",
        "BV.", "BV ", "BVARD ", "BOULEVARD ",
        # INICIALES (Para casos como C. TEJEDOR que no están en el diccionario)
        "A. ", "A ", "C. ", "C ", "J. ", "J ", 
        "H. ", "H ", "L. ", "L ", "M. ", "M ", 
        "P. ", "P ", "S. ", "S "
    ]
    
    nombre_limpio = calle
    for palabra in palabras_basura:
        if nombre_limpio.startswith(palabra):
            nombre_limpio = nombre_limpio.replace(palabra, "")
            
    return nombre_limpio.strip()

# --- 3. FUNCIÓN DE EXTRACCIÓN ---
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None, None
    texto = texto.upper().strip()
    match = re.search(r"^([A-Z\s\.\d\(\)\-]+?)\s+(\d+)", texto)
    if match:
        calle_raw = match.group(1).strip()
        altura = int(match.group(2))
        calle_norm = normalizar_calle(calle_raw) 
        return calle_raw, altura, calle_norm
    return None, None, None

# --- INICIO DE LA APP ---
with st.spinner('Procesando y unificando padrón...'):
    df = cargar_datos()

if df is not None:
    if 'Domicilio' in df.columns:
        
        # Procesamos las direcciones
        if 'Calle_Norm' not in df.columns:
            datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
            df['Calle_Original'] = datos_limpios[0]
            df['Altura_Limpia'] = datos_limpios[1]
            df['Calle_Norm'] = datos_limpios[2]
            df = df.dropna(subset=['Calle_Norm', 'Altura_Limpia'])

        st.success(f"✅ Padrón Unificado: {len(df)} afiliados listos.")
        
        # BOTÓN DE DESCARGA
        with st.expander("📥 DESCARGAR BASE UNIFICADA"):
            st.write("Descarga el archivo con las calles corregidas (Berutti, Cafferata, Fechas, etc.).")
            csv_export = df[['Apellido', 'Nombre', 'Matricula', 'Calle_Norm', 'Altura_Limpia', 'Domicilio']].to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Descargar CSV Limpio", csv_export, "padron_limpio_t3f.csv", "text/csv")

        st.divider()

        # SELECTOR
        modo_busqueda = st.radio("Modo:", ["👤 Por Persona", "🏠 Por Calle"], horizontal=True)
        st.divider()

        # MODO 1: PERSONA
        if "Persona" in modo_busqueda:
            col1, col2 = st.columns([2, 1])
            with col1:
                busqueda = st.text_input("🔍 Apellido o DNI:", placeholder="Ej: PEREZ")

            if busqueda:
                filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                           df['Matricula'].astype(str).str.contains(busqueda, na=False)]
                
                if not filtro.empty:
                    opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Original']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                    seleccion = st.selectbox("Afiliado:", list(opciones.keys()))
                    
                    if seleccion:
                        idx = opciones[seleccion]
                        objetivo = df.loc[idx]
                        
                        st.info(f"📌 OBJETIVO: {objetivo['Apellido']} {objetivo['Nombre']} | Calle Normalizada: {objetivo['Calle_Norm']} {int(objetivo['Altura_Limpia'])}")
                        
                        rango = st.slider("Radio:", 100, 1000, 500)
                        
                        # Buscamos coincidencias en la calle NORMALIZADA
                        vecinos = df[
                            (df['Calle_Norm'] == objetivo['Calle_Norm']) & 
                            (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                            (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                            (df['Matricula'] != objetivo['Matricula'])
                        ].copy()
                        
                        vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                        vecinos = vecinos.sort_values('Distancia')
                        
                        st.write(f"**Vecinos encontrados:** {len(vecinos)}")
                        st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']], use_container_width=True)
                else:
                    st.warning("No encontrado.")

        # MODO 2: CALLE
        else:
            col1, col2 = st.columns(2)
            with col1:
                # Mostramos la lista limpia de calles
                lista_calles = sorted(df['Calle_Norm'].unique())
                calle_input = st.selectbox("Selecciona Calle:", lista_calles)
            with col2:
                altura_input = st.number_input("Altura (0 = todas):", min_value=0, step=100)
            
            if calle_input:
                filtro_calle = df[df['Calle_Norm'] == calle_input].copy()
                
                if altura_input > 0:
                    rango = st.slider("Radio:", 100, 1000, 500)
                    filtro_calle = filtro_calle[
                        (filtro_calle['Altura_Limpia'] >= altura_input - rango) &
                        (filtro_calle['Altura_Limpia'] <= altura_input + rango)
                    ]
                    filtro_calle['Diferencia'] = abs(filtro_calle['Altura_Limpia'] - altura_input)
                    filtro_calle = filtro_calle.sort_values('Diferencia')
                else:
                    filtro_calle = filtro_calle.sort_values('Altura_Limpia')

                st.success(f"🏘️ Encontrados: {len(filtro_calle)}")
                st.dataframe(filtro_calle[['Apellido', 'Nombre', 'Domicilio', 'Altura_Limpia']], use_container_width=True)

    else:
        st.divider()
st.header("🕵️ Zona de Auditoría y Generación de Correcciones")

if st.checkbox("Activar Detective y Generar Archivo de Limpieza"):
    with st.spinner('Analizando y generando sugerencias automáticas...'):
        
        # 1. Función limpieza interna
        def limpiar_para_comparar(texto):
            if not isinstance(texto, str): return ""
            t = texto.upper().strip()
            for p in ["AV.", "AV ", "CALLE ", "DR.", "DR ", "GRAL.", "GRAL ", "PJE ", "PJE."]:
                t = t.replace(p, "")
            return t.strip()

        # 2. Análisis
        if 'Calle_Original' in df.columns:
            calles_unicas = sorted([c for c in df['Calle_Original'].unique() if isinstance(c, str) and len(c) > 3])
            
            sugerencias = [] # Aquí guardaremos pares [Mal, Bien]
            procesados = set()
            
            progress_bar = st.progress(0)
            total = len(calles_unicas)
            
            for i, calle_a in enumerate(calles_unicas):
                if i % 50 == 0: progress_bar.progress(i / total)
                if calle_a in procesados: continue
                
                nombre_a = limpiar_para_comparar(calle_a)
                grupo = [calle_a]
                
                for calle_b in calles_unicas:
                    if calle_a == calle_b or calle_b in procesados: continue
                    nombre_b = limpiar_para_comparar(calle_b)
                    
                    # Similitud > 85%
                    ratio = SequenceMatcher(None, nombre_a, nombre_b).ratio()
                    if ratio > 0.85:
                        grupo.append(calle_b)
                        procesados.add(calle_b)
                
                if len(grupo) > 1:
                    procesados.add(calle_a)
                    # La primera de la lista será la "Oficial" (luego tú lo revisas en Excel)
                    oficial = grupo[0]
                    for variante in grupo[1:]:
                        # Guardamos: [Nombre Malo, Nombre Sugerido]
                        sugerencias.append({"Original": variante, "Corregido": oficial})
            
            progress_bar.empty()
            
            # 3. Mostrar y Descargar
            st.warning(f"⚠️ Se encontraron {len(sugerencias)} correcciones posibles.")
            
            df_sugerencias = pd.DataFrame(sugerencias)
            st.dataframe(df_sugerencias.head())
            
            csv_sugerencias = df_sugerencias.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="⬇️ Descargar Archivo de Correcciones (correcciones.csv)",
                data=csv_sugerencias,
                file_name="correcciones.csv",
                mime="text/csv"
            )
            st.info("Paso siguiente: Descarga este archivo, revísalo en Excel, borra lo que esté mal y súbelo a GitHub.")

        else:
            st.error("No se pudo cargar la columna de calles originales.")
