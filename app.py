"""
Aplicación principal del auditor CSV
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from config import CATEGORIAS_CONFIG, CAMPUS_CODES
from validador import leer_csv_con_encoding, auditar_archivo
from gemini_corrector import GeminiCorrector
import re

# Configuración de la página
st.set_page_config(
    page_title="Auditor CSV - Actividades Estudiantiles",
    page_icon="📊",
    layout="wide"
)

def procesar_archivos_categoria(archivos_subidos, categoria):
    """Procesa todos los archivos de una categoría"""
    resultados = []
    archivos_con_problemas = []
    total_correcciones = []
    
    # Inicializar corrector de Gemini
    corrector = GeminiCorrector()
    
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
                df, archivo.name, categoria, encoding_usado, es_utf8, corrector
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
        with st.expander(f"🤖 Gemini realizó {len(total_correcciones)} correcciones automáticas"):
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

def main():
    st.title("📊 Auditor de Archivos CSV - Actividades Estudiantiles")
    st.markdown("---")
    
    # Configurar API Key de Gemini
    with st.sidebar:
        st.header("🔧 Configuración")
        api_key = st.text_input(
            "API Key de Gemini:", 
            type="password",
            help="Opcional: Para corrección ortográfica avanzada"
        )
        if api_key:
            import os
            os.environ['GEMINI_API_KEY'] = api_key
            st.success("✅ API Key configurada")
    
    st.markdown("""
    ### Instrucciones de uso:
    1. (Opcional) Configura tu API Key de Gemini en la barra lateral para corrección ortográfica avanzada
    2. Selecciona la categoría de archivos que deseas auditar
    3. Sube los archivos CSV correspondientes
    4. Revisa los resultados de la auditoría
    5. Descarga el reporte en Excel
    
    🤖 **Con Gemini**: Corrección inteligente de errores ortográficos en campos de diccionario
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
                st.write(f"**{campo}:** (Corrección automática disponible)")
                for valor in valores[:5]:
                    st.write(f"  - {valor}")
                if len(valores) > 5:
                    st.write(f"  - ... y {len(valores) - 5} más")
            elif valores is None:
                st.write(f"**{campo}:** No puede estar vacío")
            else:
                st.write(f"**{campo}:** Validación especial")
    
    # Subida de archivos
    archivos_subidos = st.file_uploader(
        f"Sube los archivos CSV para {categoria_seleccionada}:",
        type=['csv'],
        accept_multiple_files=True,
        help="Gemini corregirá automáticamente errores ortográficos en campos de diccionario"
    )
    
    if archivos_subidos:
        st.success(f"📁 {len(archivos_subidos)} archivo(s) cargado(s)")
        
        # Botón para procesar
        if st.button("🔍 Procesar Auditoría", type="primary"):
            with st.spinner("Procesando archivos con Gemini..."):
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
                with st.spinner("Procesando todas las categorías con Gemini..."):
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
