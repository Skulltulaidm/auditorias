import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
import zipfile
from datetime import datetime
import chardet

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

# Configuración de validaciones por categoría
CATEGORIAS_CONFIG = {
    'Arte y Cultura': {
        'nombre_archivo_patron': r'Formato_Arte_([A-Z]{2,3})\.csv',
        'claves_validas': ['2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '2.A'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'TIPO_DE_ESPECTACULO', 'COMPAÑÍA'],
        'validaciones_especiales': ['TIPO_DE_ESPECTACULO', 'COMPAÑÍA']
    },
    'Atlético y Deportivo': {
        'nombre_archivo_patron': r'Formato_AtleticoyDeportivo_([A-Z]{2,3})\.csv',
        'claves_validas': ['1.1', '1.2', '1.3', '1.4', '1.5', '1.6'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'DISCIPLINA', 'RAMA'],
        'validaciones_especiales': ['DISCIPLINA', 'RAMA']
    },
    'CVDP': {
        'nombre_archivo_patron': r'Formato_CVDP_([A-Z]{2,3})\.csv',
        'claves_validas': ['5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9', '5.10', '5.11', '5.12', '5.13', '5.14', '5.15'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRÍCULA', 'CLAVE', 'EMPRESA'],
        'validaciones_especiales': ['EMPRESA']
    },
    'Grupos Estudiantiles': {
        'nombre_archivo_patron': r'Formato_Grupos Estudiantiles_([A-Z]{2,3})\.csv',
        'claves_validas': ['3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7'],
        'columnas_requeridas': ['EJERCICIO_ACADEMICO', 'NOMBRE', 'APELLIDO PATERNO', 'APELLIDO MATERNO', 'MATRICULA', 'CLAVE', 'NOMBRE COMPLETO  DEL GRUPO ESTUDIANTIL', 'SIGLAS DEL GRUPO ESTUDIANTIL', 'PORTAFOLIO', 'GIRO'],
        'validaciones_especiales': ['NOMBRE COMPLETO  DEL GRUPO ESTUDIANTIL', 'SIGLAS DEL GRUPO ESTUDIANTIL', 'PORTAFOLIO', 'GIRO']
    },
    'Mentoreo': {
        'nombre_archivo_patron': r'.*([A-Z]{2,3}).*\.csv',
        'claves_validas': [],
        'columnas_requeridas': ['Ejercicio Académico', 'Matrícula', 'Nombre completo', 'Email'],
        'validaciones_especiales': ['Email']
    }
}

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
    
    # Si ningún encoding funciona
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

def auditar_archivo(df, nombre_archivo, categoria, encoding_usado, es_utf8):
    """Audita un archivo CSV según la categoría"""
    errores = []
    advertencias = []
    config = CATEGORIAS_CONFIG[categoria]
    
    # Advertencia si no es UTF-8
    if not es_utf8:
        advertencias.append(f"Archivo no está en formato UTF-8 (detectado: {encoding_usado})")
    
    # Verificar nombre de archivo
    if categoria != 'Mentoreo':
        match = re.search(config['nombre_archivo_patron'], nombre_archivo)
        if not match:
            errores.append(f"Nombre de archivo incorrecto")
        else:
            campus_detectado = match.group(1)
            if campus_detectado not in CAMPUS_CODES:
                errores.append(f"Campus '{campus_detectado}' no es válido")
    
    # Verificar columnas requeridas
    columnas_faltantes = []
    for col in config['columnas_requeridas']:
        if col not in df.columns:
            # Buscar variaciones de nombres de columnas
            col_encontrada = False
            for df_col in df.columns:
                if col.lower().replace(' ', '').replace('_', '') == df_col.lower().replace(' ', '').replace('_', ''):
                    col_encontrada = True
                    break
            if not col_encontrada:
                columnas_faltantes.append(col)
    
    if columnas_faltantes:
        errores.append(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
        return errores + advertencias, len(df), 0
    
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
                errores_registros.append("Ejercicio académico incorrecto")
                registro_valido = False
        
        # Validar NOMBRE no vacío
        nombre_col = 'NOMBRE' if 'NOMBRE' in df_normalizado.columns else 'Nombre completo'
        if nombre_col in df_normalizado.columns:
            if pd.isna(row[nombre_col]) or str(row[nombre_col]).strip() == "":
                errores_registros.append("Nombre vacío")
                registro_valido = False
        
        # Validar APELLIDO PATERNO no vacío
        if 'APELLIDO PATERNO' in df_normalizado.columns:
            if pd.isna(row['APELLIDO PATERNO']) or str(row['APELLIDO PATERNO']).strip() == "":
                errores_registros.append("Apellido paterno vacío")
                registro_valido = False
        
        # Validar MATRICULA
        matricula_col = 'MATRICULA' if 'MATRICULA' in df_normalizado.columns else 'MATRÍCULA' if 'MATRÍCULA' in df_normalizado.columns else 'Matrícula'
        if matricula_col in df_normalizado.columns:
            valida, error_msg, matricula_corregida = validar_matricula(row[matricula_col])
            if not valida:
                errores_registros.append("Matrícula formato incorrecto")
                registro_valido = False
        
        # Validar CLAVE
        if 'CLAVE' in df_normalizado.columns and config['claves_validas']:
            if pd.isna(row['CLAVE']) or str(row['CLAVE']).strip() not in config['claves_validas']:
                errores_registros.append("Clave inválida")
                registro_valido = False
        
        # Validaciones especiales según categoría
        for col_especial in config['validaciones_especiales']:
            if col_especial in df_normalizado.columns:
                if col_especial == 'Email' and categoria == 'Mentoreo':
                    valida, error_msg = validar_email_mentoreo(row[col_especial], row[matricula_col])
                    if not valida:
                        errores_registros.append("Email formato incorrecto")
                        registro_valido = False
                else:
                    if pd.isna(row[col_especial]) or str(row[col_especial]).strip() == "":
                        errores_registros.append(f"{col_especial} vacío")
                        registro_valido = False
        
        if registro_valido:
            registros_validos += 1
    
    # Resumir errores de registros
    if errores_registros:
        tipos_errores = {}
        for error in errores_registros:
            if error not in tipos_errores:
                tipos_errores[error] = 1
            else:
                tipos_errores[error] += 1
        
        for tipo, count in tipos_errores.items():
            errores.append(f"{tipo} ({count} casos)")
    
    return errores + advertencias, total_registros, registros_validos

def procesar_archivos_categoria(archivos_subidos, categoria):
    """Procesa todos los archivos de una categoría"""
    resultados = []
    archivos_con_problemas = []
    
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
                # No se pudo leer el archivo
                archivos_con_problemas.append({
                    'nombre': archivo.name,
                    'problema': f"No es un CSV válido o no está en formato compatible. {error_lectura}"
                })
                continue
            
            if not es_utf8:
                archivos_con_problemas.append({
                    'nombre': archivo.name,
                    'problema': f"No está en formato UTF-8 (detectado: {encoding_usado}). Se recomienda convertir a UTF-8."
                })
            
            # Detectar campus del nombre del archivo
            campus_detectado = None
            config = CATEGORIAS_CONFIG[categoria]
            
            if categoria == 'Mentoreo':
                # Para mentoreo, buscar campus en el contenido o nombre
                for campus in CAMPUS_CODES:
                    if campus in archivo.name.upper():
                        campus_detectado = campus
                        break
            else:
                match = re.search(config['nombre_archivo_patron'], archivo.name)
                if match:
                    campus_detectado = match.group(1)
            
            # Auditar archivo
            errores, total_registros, registros_validos = auditar_archivo(
                df, archivo.name, categoria, encoding_usado, es_utf8
            )
            
            # Actualizar resultados
            for resultado in resultados:
                if resultado['Campus'] == campus_detectado:
                    resultado['En Teams'] = 'SI'
                    resultado['Total Registros'] = total_registros
                    resultado['Registros Válidos'] = registros_validos
                    
                    if errores:
                        # Resumir errores para la tabla
                        errores_filtrados = [e for e in errores if not e.startswith('Archivo no está en formato UTF-8')]
                        
                        if errores_filtrados:
                            resumen_errores = '; '.join(errores_filtrados[:3])
                            if len(resumen_errores) > 200:
                                resumen_errores = resumen_errores[:197] + "..."
                            resultado['Errores'] = resumen_errores
                            resultado['Completo'] = 'NO'
                        else:
                            # Solo advertencias de encoding
                            resultado['Errores'] = 'Solo problemas de formato UTF-8'
                            resultado['Completo'] = 'SI'
                    else:
                        resultado['Errores'] = ''
                        resultado['Completo'] = 'SI'
                    break
            
        except Exception as e:
            archivos_con_problemas.append({
                'nombre': archivo.name,
                'problema': f"Error crítico: {str(e)}"
            })
    
    # Mostrar solo archivos con problemas
    if archivos_con_problemas:
        st.error("❌ Archivos que no cumplieron los requerimientos:")
        for problema in archivos_con_problemas:
            st.error(f"📄 **{problema['nombre']}**: {problema['problema']}")
    
    return pd.DataFrame(resultados)

def crear_excel_reporte(resultados_por_categoria):
    """Crea archivo Excel con múltiples pestañas"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for categoria, df in resultados_por_categoria.items():
            # Limpiar nombre de hoja (Excel no permite ciertos caracteres)
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
    2. Sube los archivos CSV correspondientes (**preferiblemente en formato UTF-8**)
    3. Revisa los resultados de la auditoría
    4. Descarga el reporte en Excel
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
        
        st.write("**Formato de archivo requerido:**")
        st.write("- CSV UTF-8 (Comma delimited)")
        st.write("- Ejercicio académico: 202511")
        st.write("- Matrícula: A + 8 dígitos")
    
    # Subida de archivos
    archivos_subidos = st.file_uploader(
        f"Sube los archivos CSV para {categoria_seleccionada}:",
        type=['csv'],
        accept_multiple_files=True,
        help="Asegúrate de que los archivos estén en formato CSV UTF-8"
    )
    
    if archivos_subidos:
        st.success(f"Se han subido {len(archivos_subidos)} archivo(s)")
        
        # Mostrar nombres de archivos
        with st.expander("Archivos subidos"):
            for archivo in archivos_subidos:
                st.write(f"📄 {archivo.name}")
        
        # Botón para procesar
        if st.button("🔍 Procesar Auditoría", type="primary"):
            with st.spinner("Procesando archivos..."):
                
                # Procesar archivos
                resultados_df = procesar_archivos_categoria(archivos_subidos, categoria_seleccionada)
                
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
    st.markdown("Sube archivos de todas las categorías para generar un reporte completo:")
    
    # Subida de archivos para todas las categorías
    with st.expander("Subir archivos para auditoría completa"):
        archivos_completos = {}
        
        for categoria in CATEGORIAS_CONFIG.keys():
            archivos_categoria = st.file_uploader(
                f"Archivos CSV para {categoria}:",
                type=['csv'],
                accept_multiple_files=True,
                key=f"uploader_{categoria}",
                help=f"Sube todos los archivos CSV de {categoria}"
            )
            if archivos_categoria:
                archivos_completos[categoria] = archivos_categoria
        
        if archivos_completos:
            if st.button("🚀 Procesar Auditoría Completa", type="primary"):
                with st.spinner("Procesando todas las categorías..."):
                    resultados_completos = {}
                    
                    for categoria, archivos in archivos_completos.items():
                        st.markdown(f"#### {categoria}")
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
