"""
Validador usando corrección local sin APIs
"""

import pandas as pd
import re
import chardet
from typing import Tuple, Optional, List, Dict
from config import CATEGORIAS_CONFIG, COLUMNAS_NO_CORREGIBLES
from corrector_local import CorrectorLocal
from corrector_reglas import CorrectorReglas

# ... (mantener las funciones existentes de detectar_encoding, leer_csv_con_encoding, etc.)

def validar_valor_con_correccion_local(valor, lista_valores: List[str], nombre_campo: str, 
                                     corrector: CorrectorLocal, corrector_reglas: CorrectorReglas) -> Tuple[bool, Optional[str], Optional[str]]:
    """Valida un valor contra una lista, usando corrección local"""
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
    
    # Intentar corrección con reglas específicas primero
    valor_corregido = corrector_reglas.aplicar_reglas_especificas(valor_str, lista_valores)
    
    # Si no funciona, usar corrector local avanzado
    if not valor_corregido:
        valor_corregido = corrector.encontrar_mejor_coincidencia(valor_str, lista_valores)
    
    if valor_corregido:
        return True, None, valor_corregido
    
    # Si no se pudo corregir
    return False, f"{nombre_campo} '{valor_str}' no es válido. Opciones: {', '.join(lista_valores[:3])}{'...' if len(lista_valores) > 3 else ''}", None

def auditar_archivo_local(df: pd.DataFrame, nombre_archivo: str, categoria: str, 
                         encoding_usado: str, es_utf8: bool) -> Tuple[List[str], int, int, List[str]]:
    """Audita un archivo CSV usando corrección local"""
    
    # Inicializar correctores
    corrector = CorrectorLocal()
    corrector_reglas = CorrectorReglas()
    
    errores = []
    advertencias = []
    correcciones = []
    config = CATEGORIAS_CONFIG[categoria]
    
    # ... (resto del código de auditoría, reemplazando la validación con corrección)
    
    # En la sección de validaciones especiales:
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
                valida, error_msg, valor_corregido = validar_valor_con_correccion_local(
                    row[campo], valores_permitidos, campo, corrector, corrector_reglas
                )
                if not valida:
                    errores_registros.append(f"Fila {idx+2}: {error_msg}")
                    registro_valido = False
                elif valor_corregido and valor_corregido != str(row[campo]).strip():
                    correcciones.append(f"{campo} corregido en fila {idx+2}: {row[campo]} → {valor_corregido}")
    
    # ... (resto del código)
    
    return todos_errores, total_registros, registros_validos, correcciones
