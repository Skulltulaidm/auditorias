"""
Corrector ortográfico local usando algoritmos de similitud
"""

import pandas as pd
import unicodedata
import re
from difflib import SequenceMatcher
from typing import List, Optional, Dict
import streamlit as st

class CorrectorLocal:
    def __init__(self):
        self.cache_correcciones = {}
    
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza texto removiendo acentos, espacios extra y convirtiendo a lowercase"""
        if pd.isna(texto):
            return ""
        
        texto_str = str(texto).strip()
        # Remover acentos
        texto_normalizado = unicodedata.normalize('NFD', texto_str)
        texto_sin_acentos = ''.join(char for char in texto_normalizado if unicodedata.category(char) != 'Mn')
        # Convertir a lowercase y remover espacios extra
        return re.sub(r'\s+', ' ', texto_sin_acentos.lower())
    
    def calcular_similitud(self, texto1: str, texto2: str) -> float:
        """Calcula la similitud entre dos textos usando SequenceMatcher"""
        return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()
    
    def encontrar_mejor_coincidencia(self, valor: str, opciones_validas: List[str], umbral_minimo: float = 0.6) -> Optional[str]:
        """Encuentra la mejor coincidencia usando múltiples algoritmos"""
        if pd.isna(valor):
            return None
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        # Cache para evitar recálculos
        cache_key = f"{valor_str}_{hash(tuple(opciones_validas))}"
        if cache_key in self.cache_correcciones:
            return self.cache_correcciones[cache_key]
        
        # 1. Coincidencia exacta
        if valor_str in opciones_validas:
            self.cache_correcciones[cache_key] = valor_str
            return valor_str
        
        # 2. Coincidencia case-insensitive
        for opcion in opciones_validas:
            if valor_str.lower() == opcion.lower():
                self.cache_correcciones[cache_key] = opcion
                return opcion
        
        # 3. Coincidencia sin acentos
        valor_normalizado = self.normalizar_texto(valor_str)
        for opcion in opciones_validas:
            if valor_normalizado == self.normalizar_texto(opcion):
                self.cache_correcciones[cache_key] = opcion
                return opcion
        
        # 4. Búsqueda por contención (para palabras compuestas)
        for opcion in opciones_validas:
            opcion_normalizada = self.normalizar_texto(opcion)
            if (valor_normalizado in opcion_normalizada or 
                opcion_normalizada in valor_normalizado) and len(valor_normalizado) > 3:
                self.cache_correcciones[cache_key] = opcion
                return opcion
        
        # 5. Similitud usando SequenceMatcher (más inteligente)
        mejores_coincidencias = []
        for opcion in opciones_validas:
            # Calcular similitud normal
            similitud = self.calcular_similitud(valor_str, opcion)
            
            # Calcular similitud normalizada (sin acentos)
            similitud_normalizada = self.calcular_similitud(valor_normalizado, self.normalizar_texto(opcion))
            
            # Usar la mejor similitud
            similitud_final = max(similitud, similitud_normalizada)
            
            if similitud_final >= umbral_minimo:
                mejores_coincidencias.append((opcion, similitud_final))
        
        if mejores_coincidencias:
            # Ordenar por similitud y devolver la mejor
            mejores_coincidencias.sort(key=lambda x: x[1], reverse=True)
            mejor_opcion = mejores_coincidencias[0][0]
            self.cache_correcciones[cache_key] = mejor_opcion
            return mejor_opcion
        
        # 6. Algoritmo de distancia de Levenshtein simplificado
        mejor_opcion = self.busqueda_por_distancia_editorial(valor_str, opciones_validas)
        if mejor_opcion:
            self.cache_correcciones[cache_key] = mejor_opcion
            return mejor_opcion
        
        # No se encontró coincidencia
        self.cache_correcciones[cache_key] = None
        return None
    
    def busqueda_por_distancia_editorial(self, valor: str, opciones_validas: List[str], max_distancia: int = 3) -> Optional[str]:
        """Búsqueda usando distancia de edición (Levenshtein simplificada)"""
        def distancia_levenshtein_simple(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return self.distancia_levenshtein_simple(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        valor_normalizado = self.normalizar_texto(valor)
        mejores_opciones = []
        
        for opcion in opciones_validas:
            opcion_normalizada = self.normalizar_texto(opcion)
            distancia = distancia_levenshtein_simple(valor_normalizado, opcion_normalizada)
            
            # Ajustar umbral basado en longitud de texto
            umbral_dinamico = min(max_distancia, max(1, len(valor_normalizado) // 3))
            
            if distancia <= umbral_dinamico:
                mejores_opciones.append((opcion, distancia))
        
        if mejores_opciones:
            # Ordenar por menor distancia
            mejores_opciones.sort(key=lambda x: x[1])
            return mejores_opciones[0][0]
        
        return None
    
    def distancia_levenshtein_simple(self, s1: str, s2: str) -> int:
        """Implementación simple de distancia de Levenshtein"""
        if len(s1) < len(s2):
            return self.distancia_levenshtein_simple(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def corregir_batch(self, valores_dict: Dict[str, List[str]], opciones_dict: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
        """Corrige múltiples valores en batch"""
        correcciones = {}
        
        for campo, valores in valores_dict.items():
            if campo not in opciones_dict:
                continue
                
            correcciones[campo] = {}
            opciones_validas = opciones_dict[campo]
            
            # Filtrar valores únicos
            valores_unicos = list(set([str(v).strip() for v in valores if pd.notna(v) and str(v).strip() != ""]))
            
            for valor in valores_unicos:
                if valor not in opciones_validas:
                    correccion = self.encontrar_mejor_coincidencia(valor, opciones_validas)
                    if correccion and correccion != valor:
                        correcciones[campo][valor] = correccion
        
        return correcciones
