"""
Funciones de validación para el auditor CSV
"""

import pandas as pd
import re
import chardet
from typing import Tuple, Optional, List, Dict
from config import CATEGORIAS_CONFIG, COLUMNAS_NO_CORREGIBLES
from gemini_corrector import GeminiCorrector

def detectar_encoding(archivo) -> Tuple[Optional[str], float]:
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

def leer_csv_con_encoding(archivo) -> Tuple[Optional[pd.DataFrame], Optional[str], bool, Optional[str]]:
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

def validar_matricula(matricula) -> Tuple[bool, Optional[str], Optional[str]]:
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

def validar_email_mentoreo(email, matricula) -> Tuple[bool, Optional[str]]:
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

def validar_valor_con_correccion(valor, lista_valores: List[str], nombre_campo: str, 
                                corrector: GeminiCorrector) -> Tuple[bool, Optional[str], Optional[str]]:
    """Valida un valor contra una lista, usando Gemini para corrección si es necesario"""
    if pd.isna(valor):
        return False, f"{nombre_campo} no puede estar vacío", None
    
    valor_str = str(valor).strip()
    if valor_str == "":
        return False, f"{nombre_campo} no puede estar vacío", None
    
    # Si ya es válido, retornar como está
    if valor_str in lista_valores:
        return True, None, valor_str
    
    # No corregir campos de nombres o ejercicio académico
    if nombre_campo in COLUMNAS_NO_CORREGIBLES:
        return False, f"{nombre_campo} '{valor_str}' no es válido", None
    
    # Intentar corrección con Gemini
    valor_corregido = corrector.corregir_valor_con_gemini(valor_str, lista_valores, nombre_campo)
    
    if valor_corregido:
        return True, None, valor_corregido
    
    # Si no se pudo corregir
    return False, f"{nombre_campo} '{valor_str}' no es válido. Opciones: {', '.join(lista_valores[:3])}{'...' if len(lista_valores) > 3 else ''}", None

def auditar_archivo(df: pd.DataFrame, nombre_archivo: str, categoria: str, 
                   encoding_usado: str, es_utf8: bool, corrector: GeminiCorrector) -> Tuple[List[str], int, int, List[str]]:
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
            from config import CAMPUS_CODES
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
                    valida, error_msg, valor_corregido = validar_valor_con_correccion(
                        row[campo], valores_permitidos, campo, corrector
                    )
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
