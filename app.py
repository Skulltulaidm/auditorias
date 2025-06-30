import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
import zipfile
from datetime import datetime
import chardet
import unicodedata

# Configuración de la página
st.set_page_config(
    page_title="Auditor CSV - Actividades Estudiantiles",
    page_icon="📊",
    layout="wide"
)

# Lista de campus
CAMPUS_CODES = [
    'AGS', 'CCM', 'CDJ', 'CEM', 'CHI', 'CHS', 'CLM', 'COB', 'CSF', 'CUM',
    'CVA', 'EGL', 'EGS', 'ESM', 'GDA', 'HGO', 'IRA', 'LAG', 'LEO', 'MET',
    'MRL', 'MTY', 'NJA', 'PUE', 'QRO', 'SAL', 'SC', 'SIN', 'SLP', 'SON',
    'STA', 'TAM', 'TOL', 'VA', 'ZAC'
]

# Valores válidos para Arte y Cultura
TIPOS_ESPECTACULO_ARTE = [
    'Teatro musical',
    'Concierto (tipo ensamble)',
    'Folklore',
    'Orquesta/Coro',
    'Danza'
]

COMPANIAS_ARTE = [
    'Danza',
    'Danza Folklórica',
    'Canto/Coro',
    'Música',
    'Orquesta',
    'Staff',
    'Teatro',
    'Teatro Musical',
    'Otro'
]

# Valores válidos para Atlético y Deportivo
DISCIPLINAS_BORREGOS = [
    'Atletismo',
    'Basquetbol',
    'Futbol Americano',
    'Futbol Soccer',
    'Natación',
    'Tae Kwon Do',
    'Tenis',
    'Voleibol Sala'
]

DISCIPLINAS_RECSPORTS = [
    'Ajedrez',
    'Atletismo',
    'Basquetbol',
    'Beisbol',
    'Box',
    'Escalada',
    'E-sport',
    'Futbol Americano',
    'Futbol Rápido',
    'Futbol Soccer',
    'Gimnasia Aeróbica',
    'Golf',
    'Grupos de Animación',
    'Handball',
    'Natación',
    'Otro',
    'Rugby',
    'Softball',
    'Tae Kwon Do',
    'Tenis',
    'Tenis de Mesa',
    'Tocho',
    'Voleibol Playa',
    'Voleibol Sala'
]

# Para disciplinas generales (incluye preparatoria)
DISCIPLINAS_ATLETICO = DISCIPLINAS_BORREGOS + DISCIPLINAS_RECSPORTS + [
    'Gimnasio Preparatoria',
    'Preparatoria'
]

RAMAS_DEPORTIVAS = [
    'Femenil',
    'Varonil',
    'Mixto'
]

# Valores válidos para Grupos Estudiantiles
GIROS_GRUPOS = [
    'Ecología y Medio Ambiente',
    'Deportivos y Recreativos',
    'E-Sports',
    'Programas Académicos',
    'Arte, Cultura y Entretenimiento',
    'Medios y Publicaciones Estudiantiles',
    'Liderazgo',
    'Política y Ciudadanía',
    'Sentido Humano',
    'Desarrollo Profesional y Emprendimiento',
    'Inclusión, Diversidad y Género',
    'Lugar de Origen',
    'Religión y Filosofía',
    'Salud y Bienestar',
    'Vivencia Estudiantil',
    'FETEC'
]

PORTAFOLIOS_GRUPOS = [
    'Federación de Estudiantes',
    'Asociaciones Estudiantiles/Sociedad de Estudiantes',
    'Asociaciones Estudiantiles/Grupos de interés',
    'Liderazgo Académico / Competencia',
    'Liderazgo Académico / Posicionamiento',
    'Liderazgo Académico / Preparación',
    'Liderazgo Académico / Capítulos Estudiantiles'
]

# Configuración de validaciones por categoría
CATEGORIAS_CONFIG = {
    'Arte y Cultura': {
        'nombre_archivo_patron': r'Formato_Arte_([A-Z]{2,3})\.csv',
        'claves_validas': ['2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '2.A'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'TIPO_DE_ESPECTACULO', 'COMPAÑÍA'],
        'validaciones_especiales': {
            'TIPO_DE_ESPECTACULO': TIPOS_ESPECTACULO_ARTE,
            'COMPAÑÍA': COMPANIAS_ARTE
        }
    },
    'Atlético y Deportivo': {
        'nombre_archivo_patron': r'Formato_AtleticoyDeportivo_([A-Z]{2,3})\.csv',
        'claves_validas': ['1.1', '1.2', '1.3', '1.4', '1.5', '1.6'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'DISCIPLINA', 'RAMA'],
        'validaciones_especiales': {
            'DISCIPLINA': DISCIPLINAS_ATLETICO,
            'RAMA': RAMAS_DEPORTIVAS
        }
    },
    'CVDP': {
        'nombre_archivo_patron': r'Formato_CVDP_([A-Z]{2,3})\.csv',
        'claves_validas': ['5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9', '5.10', '5.11', '5.12', '5.13', '5.14', '5.15'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRÍCULA', 'CLAVE', 'EMPRESA'],
        'validaciones_especiales': {
            'EMPRESA': None  # EMPRESA puede ser cualquier valor, solo no puede estar vacía
        }
    },
    'Grupos Estudiantiles': {
        'nombre_archivo_patron': r'Formato_Grupos Estudiantiles_([A-Z]{2,3})\.csv',
        'claves_validas': ['3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'NOMBRE COMPLETO  DEL GRUPO ESTUDIANTIL', 'SIGLAS DEL GRUPO ESTUDIANTIL', 'PORTAFOLIO', 'GIRO'],
        'validaciones_especiales': {
            'NOMBRE COMPLETO  DEL GRUPO ESTUDIANTIL': None,  # Puede variar de mil maneras según especificación
            'SIGLAS DEL GRUPO ESTUDIANTIL': None,  # Puede variar
            'PORTAFOLIO': PORTAFOLIOS_GRUPOS,
            'GIRO': GIROS_GRUPOS
        }
    },
    'Mentoreo': {
        'nombre_archivo_patron': r'.*([A-Z]{2,3}).*\.csv',
        'claves_validas': [],
        'columnas_requeridas': ['Ejercicio Académico', 'Matrícula', 'Nombre completo', 'Email'],
        'validaciones_especiales': {
            'Email': 'validacion_email'  # Validación especial para email
        }
    }
}

def normalizar_texto(texto):
    """Normaliza texto removiendo acentos, espacios extra y convirtiendo a lowercase"""
    if pd.isna(texto):
        return ""
    
    texto_str = str(texto).strip()
    # Remover acentos
    texto_normalizado = unicodedata.normalize('NFD', texto_str)
    texto_sin_acentos = ''.join(char for char in texto_normalizado if unicodedata.category(char) != 'Mn')
    # Convertir a lowercase y remover espacios extra
    return re.sub(r'\s+', ' ', texto_sin_acentos.lower())

def encontrar_coincidencia_fuzzy(valor, lista_valores):
    """Encuentra la mejor coincidencia para un valor en una lista, corrigiendo errores menores"""
    if pd.isna(valor):
        return None, False
    
    valor_str = str(valor).strip()
    valor_normalizado = normalizar_texto(valor_str)
    
    # Búsqueda exacta primero
    for valor_valido in lista_valores:
        if valor_str == valor_valido:
            return valor_valido, True
    
    # Búsqueda case-insensitive
    for valor_valido in lista_valores:
        if valor_str.lower() == valor_valido.lower():
            return valor_valido, True
    
    # Búsqueda sin acentos y normalizada
    for valor_valido in lista_valores:
        valor_valido_normalizado = normalizar_texto(valor_valido)
        if valor_normalizado == valor_valido_normalizado:
            return valor_valido, True
    
    # Búsqueda por similitud parcial (contiene)
    for valor_valido in lista_valores:
        valor_valido_normalizado = normalizar_texto(valor_valido)
        # Si el valor ingresado está contenido en el valor válido o viceversa
        if (valor_normalizado in valor_valido_normalizado or 
            valor_valido_normalizado in valor_normalizado) and len(valor_normalizado) > 3:
            return valor_valido, True
    
    return None, False

def detectar_encoding(archivo):
    """Detecta el encoding del archivo"""
    try:
        archivo.seek(0)
        muestra = archivo.read(10000)
        archivo.seek(0)
        
        resultado = chardet.detect(muestra)
        encoding_detectado = resultado['encoding']
        confianza = resultado['confidence']
        
        return encoding_detectado, confianza
    except Exception as e:
        return None, 0

def leer_csv_con_encoding(archivo):
    """Intenta leer el CSV con diferentes encodings"""
    archivo.seek(0)
    
    # Detectar encoding primero
    encoding_detectado, confianza = detectar_encoding(archivo)
    
    # Lista de encodings a probar
    encodings_a_probar = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
    
    # Si detectamos un encoding con buena confianza, probarlo primero
    if encoding_detectado and confianza > 0.7:
        if encoding_detectado not in encodings_a_probar:
            encodings_a_probar.insert(0, encoding_detectado)
    
    for encoding in encodings_a_probar:
        try:
            archivo.seek(0)
            df = pd.read_csv(archivo, encoding=encoding)
            
            # Verificar si es UTF-8 (formato requerido)
            es_utf8 = encoding.lower() in ['utf-8', 'utf-8-sig']
            
            return df, encoding, es_utf8, None
            
        except (UnicodeDecodeError, pd.errors.EmptyDataError, Exception) as e:
            continue
    
    return None, None, False, "No se pudo leer el archivo con ningún encoding conocido"

def validar_matricula(matricula):
    """Valida y corrige formato de matrícula"""
    if pd.isna(matricula):
        return False, "Matrícula vacía", None
    
    matricula_str = str(matricula).strip().upper()
    
    # Si no empieza con A, agregar A
    if not matricula_str.startswith('A'):
        matricula_str = 'A' + matricula_str
    
    # Verificar longitud (debe ser 9 caracteres)
    if len(matricula_str) != 9:
        return False, f"Matrícula debe tener 9 caracteres, tiene {len(matricula_str)}", matricula_str
    
    # Verificar formato A + 8 dígitos
    if not re.match(r'^A\d{8}$', matricula_str):
        return False, "Matrícula debe ser A seguida de 8 dígitos", matricula_str
    
    return True, None, matricula_str

def validar_email_mentoreo(email, matricula):
    """Valida email para mentoreo"""
    if pd.isna(email) or pd.isna(matricula):
        return False, "Email o matrícula vacíos"
    
    email_str = str(email).strip()
    matricula_str = str(matricula).strip().upper()
    
    # El email debe ser matrícula@tec.mx
    email_esperado = f"{matricula_str}@tec.mx"
    
    if email_str.lower() != email_esperado.lower():
        return False, f"Email debe ser {email_esperado}"
    
    return True, None

def validar_valor_en_lista(valor, lista_valores, nombre_campo):
    """Valida que un valor esté en una lista de valores permitidos, con corrección automática"""
    if pd.isna(valor):
        return False, f"{nombre_campo} no puede estar vacío", None
    
    valor_str = str(valor).strip()
    if valor_str == "":
        return False, f"{nombre_campo} no puede estar vacío", None
    
    # Intentar encontrar coincidencia fuzzy
    valor_corregido, encontrado = encontrar_coincidencia_fuzzy(valor_str, lista_valores)
    
    if encontrado:
        return True, None, valor_corregido
    
    return False, f"{nombre_campo} '{valor_str}' no es válido. Valores permitidos: {', '.join(lista_valores[:3])}{'...' if len(lista_valores) > 3 else ''}", None

def auditar_archivo(df, nombre_archivo, categoria, encoding_usado, es_utf8):
    """Audita un archivo CSV según la categoría"""
    errores = []
    advertencias = []
    correcciones = []
    config = CATEGORIAS_CONFIG[categoria]
    
    # Advertencia si no es UTF-8
    if not es_utf8:
        advertencias.append(f"Archivo no en UTF-8 (detectado: {encoding_usado})")
    
    # Verificar nombre de archivo
    if categoria != 'Mentoreo':
        match = re.search(config['nombre_archivo_patron'], nombre_archivo)
        if not match:
            errores.append(f"Nombre de archivo incorrecto para {categoria}")
        else:
            campus_detectado = match.group(1)
            if campus_detectado not in CAMPUS_CODES:
                errores.append(f"Campus '{campus_detectado}' no es válido")
    
    # Verificar columnas requeridas
    columnas_faltantes = []
    for col in config['columnas_requeridas']:
        if col not in df.columns:
            col_encontrada = False
            for df_col in df.columns:
                if col.lower().replace(' ', '').replace('_', '') == df_col.lower().replace(' ', '').replace('_', ''):
                    col_encontrada = True
                    break
            if not col_encontrada:
                columnas_faltantes.append(col)
    
    if columnas_faltantes:
        errores.append(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
        return errores + advertencias, len(df), 0, correcciones
    
    # Normalizar nombres de columnas
    df_normalizado = df.copy()
    mapeo_columnas = {}
    for col_requerida in config['columnas_requeridas']:
        for df_col in df.columns:
            if col_requerida.lower().replace(' ', '').replace('_', '') == df_col.lower().replace(' ', '').replace('_', ''):
                mapeo_columnas[df_col] = col_requerida
                break
    
    df_normalizado = df_normalizado.rename(columns=mapeo_columnas)
    
    registros_validos = 0
    total_registros = len(df_normalizado)
    errores_registros = []
    
    for idx, row in df_normalizado.iterrows():
        registro_valido = True
        
        # Validar EJERCICIO_ACADEMICO
        ejercicio_col = 'EJERCICIO_ACADEMICO' if 'EJERCICIO_ACADEMICO' in df_normalizado.columns else 'Ejercicio Académico'
        if ejercicio_col in df_normalizado.columns:
            if pd.isna(row[ejercicio_col]) or str(row[ejercicio_col]).strip() != "202511":
                errores_registros.append(f"Fila {idx+2}: Ejercicio académico debe ser '202511'")
                registro_valido = False
        
        # Validar NOMBRE no vacío
        nombre_col = 'NOMBRE' if 'NOMBRE' in df_normalizado.columns else 'Nombre completo'
        if nombre_col in df_normalizado.columns:
            if pd.isna(row[nombre_col]) or str(row[nombre_col]).strip() == "":
                errores_registros.append(f"Fila {idx+2}: Nombre no puede estar vacío")
                registro_valido = False
        
        # Validar APELLIDO PATERNO no vacío
        if 'APELLIDO PATERNO' in df_normalizado.columns:
            if pd.isna(row['APELLIDO PATERNO']) or str(row['APELLIDO PATERNO']).strip() == "":
                errores_registros.append(f"Fila {idx+2}: Apellido paterno no puede estar vacío")
                registro_valido = False
        
        # Validar MATRICULA
        matricula_col = 'MATRICULA' if 'MATRICULA' in df_normalizado.columns else 'MATRÍCULA' if 'MATRÍCULA' in df_normalizado.columns else 'Matrícula'
        if matricula_col in df_normalizado.columns:
            valida, error_msg, matricula_corregida = validar_matricula(row[matricula_col])
            if not valida:
                errores_registros.append(f"Fila {idx+2}: {error_msg}")
                registro_valido = False
            elif matricula_corregida != str(row[matricula_col]).strip():
                correcciones.append(f"Matrícula corregida en fila {idx+2}: {row[matricula_col]} → {matricula_corregida}")
        
        # Validar CLAVE
        if 'CLAVE' in df_normalizado.columns and config['claves_validas']:
            if pd.isna(row['CLAVE']) or str(row['CLAVE']).strip() not in config['claves_validas']:
                errores_registros.append(f"Fila {idx+2}: Clave '{row['CLAVE']}' no válida")
                registro_valido = False
        
        # Validaciones especiales según categoría
        for campo, valores_permitidos in config['validaciones_especiales'].items():
            if campo in df_normalizado.columns:
                if campo == 'Email' and categoria == 'Mentoreo':
                    valida, error_msg = validar_email_mentoreo(row[campo], row[matricula_col])
                    if not valida:
                        errores_registros.append(f"Fila {idx+2}: {error_msg}")
                        registro_valido = False
                elif valores_permitidos is None:
                    if pd.isna(row[campo]) or str(row[campo]).strip() == "":
                        errores_registros.append(f"Fila {idx+2}: {campo} no puede estar vacío")
                        registro_valido = False
                elif isinstance(valores_permitidos, list):
                    valida, error_msg, valor_corregido = validar_valor_en_lista(row[campo], valores_permitidos, campo)
                    if not valida:
                        errores_registros.append(f"Fila {idx+2}: {error_msg}")
                        registro_valido = False
                    elif valor_corregido and valor_corregido != str(row[campo]).strip():
                        correcciones.append(f"{campo} corregido en fila {idx+2}: {row[campo]} → {valor_corregido}")
        
        if registro_valido:
            registros_validos += 1
    
    # Combinar errores estructurales y de registros
    todos_errores = errores + advertencias
    
    # Resumir errores de registros si hay muchos
    if len(errores_registros) > 5:
        tipos_errores = {}
        for error in errores_registros:
            if ':' in error:
                tipo = error.split(':', 2)[2].strip() if error.count(':') >= 2 else error.split(':', 1)[1].strip()
            else:
                tipo = error
            
            if tipo not in tipos_errores:
                tipos_errores[tipo] = 1
            else:
                tipos_errores[tipo] += 1
        
        for tipo, count in tipos_errores.items():
            todos_errores.append(f"{tipo}: {count} casos")
    else:
        todos_errores.extend(errores_registros)
    
    return todos_errores, total_registros, registros_validos, correcciones

def procesar_archivos_categoria(archivos_subidos, categoria):
    """Procesa todos los archivos de una categoría"""
    resultados = []
    archivos_con_problemas = []
    total_correcciones = []
    
    # Inicializar resultados para todos los campus
    for campus in CAMPUS_CODES:
        resultados.append({
            'Campus': campus,
            'En Teams': 'NO',
            'Errores': '',
            'Completo': 'NO',
            'Total Registros': 0,
            'Registros Válidos': 0
        })
    
    # Procesar archivos subidos
    for archivo in archivos_subidos:
        try:
            # Intentar leer el archivo con diferentes encodings
            df, encoding_usado, es_utf8, error_lectura = leer_csv_con_encoding(archivo)
            
            if df is None:
                # No se pudo leer el archivo - MOSTRAR ERROR
                st.error(f"❌ El archivo '{archivo.name}' no cumplió los requerimientos:")
                st.error(f"   - No es un archivo CSV válido o no está en formato compatible")
                st.error(f"   - Error: {error_lectura}")
                st.error(f"   - Este archivo no será procesado.")
                archivos_con_problemas.append(archivo.name)
                continue
            
            if not es_utf8:
                # Archivo no UTF-8 - MOSTRAR ADVERTENCIA
                st.warning(f"⚠️ El archivo '{archivo.name}' no está en formato UTF-8:")
                st.warning(f"   - Encoding detectado: {encoding_usado}")
                st.warning(f"   - Se recomienda convertir el archivo a UTF-8")
                archivos_con_problemas.append(archivo.name)
            
            # Detectar campus del nombre del archivo
            campus_detectado = None
            config = CATEGORIAS_CONFIG[categoria]
            
            if categoria == 'Mentoreo':
                for campus in CAMPUS_CODES:
                    if campus in archivo.name.upper():
                        campus_detectado = campus
                        break
            else:
                match = re.search(config['nombre_archivo_patron'], archivo.name)
                if match:
                    campus_detectado = match.group(1)
            
            # Auditar archivo
            errores, total_registros, registros_validos, correcciones = auditar_archivo(
                df, archivo.name, categoria, encoding_usado, es_utf8
            )
            
            # Acumular correcciones
            if correcciones:
                total_correcciones.extend([f"{archivo.name}: {corr}" for corr in correcciones])
            
            # Actualizar resultados
            for resultado in resultados:
                if resultado['Campus'] == campus_detectado:
                    resultado['En Teams'] = 'SI'
                    resultado['Total Registros'] = total_registros
                    resultado['Registros Válidos'] = registros_validos
                    
                    if errores:
                        errores_filtrados = [e for e in errores if not e.startswith('Archivo no en UTF-8')]
                        
                        if errores_filtrados:
                            resumen_errores = '; '.join(errores_filtrados[:2])
                            if len(resumen_errores) > 150:
                                resumen_errores = resumen_errores[:147] + "..."
                            resultado['Errores'] = resumen_errores
                            resultado['Completo'] = 'NO'
                        else:
                            resultado['Errores'] = 'Solo advertencias de formato'
                            resultado['Completo'] = 'SI'
                    else:
                        resultado['Errores'] = ''
                        resultado['Completo'] = 'SI'
                    break
            
        except Exception as e:
            # Error crítico - MOSTRAR ERROR
            st.error(f"❌ Error crítico procesando '{archivo.name}': {str(e)}")
            archivos_con_problemas.append(archivo.name)
    
    # Solo mostrar resumen si hubo problemas o correcciones
    if archivos_con_problemas:
        st.info(f"ℹ️ {len(archivos_con_problemas)} archivo(s) requirieron atención especial")
    
    if total_correcciones:
        with st.expander(f"📝 Se realizaron {len(total_correcciones)} correcciones automáticas"):
            for correccion in total_correcciones[:10]:  # Mostrar solo las primeras 10
                st.write(f"• {correccion}")
            if len(total_correcciones) > 10:
                st.write(f"... y {len(total_correcciones) - 10} correcciones más")
    
    return pd.DataFrame(resultados)

def crear_excel_reporte(resultados_por_categoria):
    """Crea archivo Excel con múltiples pestañas"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for categoria, df in resultados_por_categoria.items():
            nombre_hoja = categoria.replace('/', '_').replace('\\', '_')[:31]
            df.to_excel(writer, sheet_name=nombre_hoja, index=False)
    
    output.seek(0)
    return output

# Interfaz principal de Streamlit
def main():
    st.title("📊 Auditor de Archivos CSV - Actividades Estudiantiles")
    st.markdown("---")
    
    st.markdown("""
    ### Instrucciones de uso:
    1. Selecciona la categoría de archivos que deseas auditar
    2. Sube los archivos CSV correspondientes
    3. Revisa los resultados de la auditoría
    4. Descarga el reporte en Excel
    
    💡 **El sistema corrige automáticamente errores menores de ortografía, acentos y mayúsculas**
    """)
    
    # Selector de categoría
    categoria_seleccionada = st.selectbox(
        "Selecciona la categoría de archivos:",
        options=list(CATEGORIAS_CONFIG.keys()),
        help="Cada categoría tiene sus propias reglas de validación"
    )
    
    st.markdown(f"### Auditoría para: **{categoria_seleccionada}**")
    
    # Mostrar información de la categoría seleccionada
    config = CATEGORIAS_CONFIG[categoria_seleccionada]
    
    with st.expander("Ver configuración de validación"):
        st.write("**Columnas requeridas:**")
        for col in config['columnas_requeridas']:
            st.write(f"- {col}")
        
        if config['claves_validas']:
            st.write("**Claves válidas:**")
            for clave in config['claves_validas']:
                st.write(f"- {clave}")
        
        st.write("**Validaciones de valores específicos:**")
        for campo, valores in config['validaciones_especiales'].items():
            if isinstance(valores, list):
                st.write(f"**{campo}:**")
                for valor in valores:
                    st.write(f"  - {valor}")
            elif valores is None:
                st.write(f"**{campo}:** No puede estar vacío (cualquier valor válido)")
            else:
                st.write(f"**{campo}:** Validación especial")
    
    # Subida de archivos
    archivos_subidos = st.file_uploader(
        f"Sube los archivos CSV para {categoria_seleccionada}:",
        type=['csv'],
        accept_multiple_files=True,
        help="El sistema intentará corregir automáticamente errores menores"
    )
    
    if archivos_subidos:
        st.success(f"📁 {len(archivos_subidos)} archivo(s) cargado(s)")
        
        # Botón para procesar
        if st.button("🔍 Procesar Auditoría", type="primary"):
            with st.spinner("Procesando archivos..."):
                # Procesar archivos
                resultados_df = procesar_archivos_categoria(archivos_subidos, categoria_seleccionada)
                
                st.markdown("---")
                st.markdown("### 📊 Resultados de la Auditoría")
                
                # Métricas resumen
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    campus_con_archivos = len(resultados_df[resultados_df['En Teams'] == 'SI'])
                    st.metric("Campus con archivos", campus_con_archivos)
                
                with col2:
                    campus_completos = len(resultados_df[resultados_df['Completo'] == 'SI'])
                    st.metric("Campus completos", campus_completos)
                
                with col3:
                    total_registros = resultados_df['Total Registros'].sum()
                    st.metric("Total registros", total_registros)
                
                with col4:
                    registros_validos = resultados_df['Registros Válidos'].sum()
                    st.metric("Registros válidos", registros_validos)
                
                # Tabla de resultados
                st.dataframe(
                    resultados_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Botón de descarga
                excel_reporte = crear_excel_reporte({categoria_seleccionada: resultados_df})
                
                st.download_button(
                    label="📥 Descargar Reporte Excel",
                    data=excel_reporte,
                    file_name=f"Reporte_Auditoria_{categoria_seleccionada.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Sección de auditoría completa
    st.markdown("---")
    st.markdown("### 🎯 Auditoría Completa (Todas las Categorías)")
    
    with st.expander("Subir archivos para auditoría completa"):
        archivos_completos = {}
        
        for categoria in CATEGORIAS_CONFIG.keys():
            archivos_categoria = st.file_uploader(
                f"Archivos CSV para {categoria}:",
                type=['csv'],
                accept_multiple_files=True,
                key=f"uploader_{categoria}",
                help=f"Archivos de {categoria}"
            )
            if archivos_categoria:
                archivos_completos[categoria] = archivos_categoria
        
        if archivos_completos:
            if st.button("🚀 Procesar Auditoría Completa", type="primary"):
                with st.spinner("Procesando todas las categorías..."):
                    resultados_completos = {}
                    
                    for categoria, archivos in archivos_completos.items():
                        st.markdown(f"#### Procesando {categoria}...")
                        resultados_completos[categoria] = procesar_archivos_categoria(archivos, categoria)
                    
                    st.markdown("---")
                    st.markdown("### 📊 Resumen por Categoría")
                    
                    for categoria, df in resultados_completos.items():
                        with st.expander(f"Resultados - {categoria}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                campus_con_archivos = len(df[df['En Teams'] == 'SI'])
                                st.metric(f"Campus con archivos", campus_con_archivos)
                            with col2:
                                campus_completos = len(df[df['Completo'] == 'SI'])
                                st.metric(f"Campus completos", campus_completos)
                            
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Generar Excel completo
                    excel_completo = crear_excel_reporte(resultados_completos)
                    
                    st.download_button(
                        label="📥 Descargar Reporte Completo Excel",
                        data=excel_completo,
                        file_name=f"Reporte_Auditoria_Completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

if __name__ == "__main__":
    main()
