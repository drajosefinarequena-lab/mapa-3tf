import pandas as pd
import re
from difflib import SequenceMatcher

# --- CONFIGURACIÓN ---
ARCHIVO = "datos.csv"  # Tu archivo de datos
UMBRAL_SIMILITUD = 0.85 # Qué tan parecidas deben ser (0 a 1)

print("🕵️  INICIANDO DETECTIVE DE CALLES...")

# 1. Cargar Datos
try:
    df = pd.read_csv(ARCHIVO, encoding='latin-1', sep=',')
    if df.shape[1] < 2: df = pd.read_csv(ARCHIVO, encoding='latin-1', sep=';')
except:
    print("❌ No encuentro el archivo datos.csv")
    exit()

# 2. Función de Limpieza Básica (Para comparar mejor)
def limpiar_basico(texto):
    if not isinstance(texto, str): return ""
    # Quitamos números y palabras basura comunes para comparar solo el nombre clave
    texto = texto.upper().strip()
    match = re.search(r"^([A-Z\s\.]+)", texto) # Solo letras
    if match:
        calle = match.group(1).strip()
        # Quitamos prefijos comunes solo para la comparación
        for basura in ["AV ", "AV. ", "CALLE ", "DR ", "DR. ", "GRAL ", "GRAL. "]:
            calle = calle.replace(basura, "")
        return calle
    return ""

# 3. Extraer Calles Únicas
print("⏳ Analizando variantes...")
df['Calle_Analisis'] = df['Domicilio'].apply(limpiar_basico)
calles_unicas = sorted([c for c in df['Calle_Analisis'].unique() if len(c) > 3])

# 4. Buscar Similares
sospechosos = []
procesados = set()

for calle_a in calles_unicas:
    if calle_a in procesados: continue
    
    grupo = [calle_a]
    for calle_b in calles_unicas:
        if calle_a == calle_b or calle_b in procesados: continue
        
        # Calculamos similitud (0.0 a 1.0)
        ratio = SequenceMatcher(None, calle_a, calle_b).ratio()
        
        # Si son muy parecidas O si una contiene a la otra
        if ratio > UMBRAL_SIMILITUD or (len(calle_a) > 5 and calle_a in calle_b):
            grupo.append(calle_b)
            procesados.add(calle_b)
    
    if len(grupo) > 1:
        sospechosos.append(grupo)
        procesados.add(calle_a)

# 5. Imprimir Reporte
print("\n" + "="*50)
print(f"🚨 REPORTE DE CALLES DUPLICADAS ({len(sospechosos)} grupos encontrados)")
print("="*50 + "\n")

for grupo in sospechosos:
    # Mostramos solo grupos interesantes (evitamos falsos positivos obvios)
    print(f"🔎 GRUPO: {grupo[0]}")
    for variante in grupo[1:]:
        print(f"   └── {variante}")
    print("-" * 20)

print("\n💡 TIP: Copia estos nombres y agrégalos al diccionario en app.py")
