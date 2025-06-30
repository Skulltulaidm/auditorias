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
        
        # Reglas de corrección específicas para casos comunes
        self.reglas_especificas = {
            # Arte y Cultura
            'musica': 'Música',
            'danza folklorica': 'Danza Folklórica',
            'danza folklorice': 'Danza Folklórica',
            'teatro musical': 'Teatro Musical',
            'orquesta coro': 'Orquesta/Coro',
            'orquesta/coro': 'Orquesta/Coro',
            'canto coro': 'Canto/Coro',
            'canto/coro': 'Canto/Coro',
            'concierto tipo ensamble': 'Concierto (tipo ensamble)',
            'concierto (tipo ensamble)': 'Concierto (tipo ensamble)',
            
            # Deportes
            'futbol americano': 'Futbol Americano',
            'futbol soccer': 'Futbol Soccer',
            'basquetbol': 'Basquetbol',
            'basquetball': 'Basquetbol',
            'basketball': 'Basquetbol',
            'voleibol sala': 'Voleibol Sala',
            'voleibol playa': 'Voleibol Playa',
            'volleyball sala': 'Voleibol Sala',
            'volleyball playa': 'Voleibol Playa',
            'tae kwon do': 'Tae Kwon Do',
            'taekwondo': 'Tae Kwon Do',
            'natacion': 'Natación',
            'atletismo': 'Atletismo',
            'gimnasia aerobica': 'Gimnasia Aeróbica',
            'tenis de mesa': 'Tenis de Mesa',
            'futbol rapido': 'Futbol Rápido',
            'e-sports': 'E-sport',
            'esports': 'E-sport',
            'grupos de animacion': 'Grupos de Animación',
            'gimnasio preparatoria': 'Gimnasio Preparatoria',
            
            # Ramas
            'femenino': 'Femenil',
            'femenina': 'Femenil',
            'masculino': 'Varonil',
            'masculina': 'Varonil',
            'hombres': 'Varonil',
            'mujeres': 'Femenil',
            'mixto': 'Mixto',
            'mixta': 'Mixto',
            
            # Giros
            'ecologia y medio ambiente': 'Ecología y Medio Ambiente',
            'ecologia': 'Ecología y Medio Ambiente',
            'medio ambiente': 'Ecología y Medio Ambiente',
            'deportivos y recreativos': 'Deportivos y Recreativos',
            'deportivos': 'Deportivos y Recreativos',
            'recreativos': 'Deportivos y Recreativos',
            'programas academicos': 'Programas Académicos',
            'arte cultura y entretenimiento': 'Arte, Cultura y Entretenimiento',
            'arte, cultura y entretenimiento': 'Arte, Cultura y Entretenimiento',
            'arte y cultura': 'Arte, Cultura y Entretenimiento',
            'medios y publicaciones estudiantiles': 'Medios y Publicaciones Estudiantiles',
            'liderazgo': 'Liderazgo',
            'politica y ciudadania': 'Política y Ciudadanía',
            'politica': 'Política y Ciudadanía',
            'ciudadania': 'Política y Ciudadanía',
            'sentido humano': 'Sentido Humano',
            'desarrollo profesional y emprendimiento': 'Desarrollo Profesional y Emprendimiento',
            'desarrollo profesional': 'Desarrollo Profesional y Emprendimiento',
            'emprendimiento': 'Desarrollo Profesional y Emprendimiento',
            'inclusion diversidad y genero': 'Inclusión, Diversidad y Género',
            'inclusion, diversidad y genero': 'Inclusión, Diversidad y Género',
            'diversidad': 'Inclusión, Diversidad y Género',
            'genero': 'Inclusión, Diversidad y Género',
            'lugar de origen': 'Lugar de Origen',
            'religion y filosofia': 'Religión y Filosofía',
            'religion': 'Religión y Filosofía',
            'filosofia': 'Religión y Filosofía',
            'salud y bienestar': 'Salud y Bienestar',
            'salud': 'Salud y Bienestar',
            'bienestar': 'Salud y Bienestar',
            'vivencia estudiantil': 'Vivencia Estudiantil',
            'fetec': 'FETEC',
            
            # Portafolios
            'federacion de estudiantes': 'Federación de Estudiantes',
            'asociaciones estudiantiles/sociedad de estudiantes': 'Asociaciones Estudiantiles/Sociedad de Estudiantes',
            'asociaciones estudiantiles sociedad de estudiantes': 'Asociaciones Estudiantiles/Sociedad de Estudiantes',
            'sociedad de estudiantes': 'Asociaciones Estudiantiles/Sociedad de Estudiantes',
            'asociaciones estudiantiles/grupos de interes': 'Asociaciones Estudiantiles/Grupos de interés',
            'asociaciones estudiantiles grupos de interes': 'Asociaciones Estudiantiles/Grupos de interés',
            'grupos de interes': 'Asociaciones Estudiantiles/Grupos de interés',
            'liderazgo academico / competencia': 'Liderazgo Académico / Competencia',
            'liderazgo academico competencia': 'Liderazgo Académico / Competencia',
            'liderazgo academico / posicionamiento': 'Liderazgo Académico / Posicionamiento',
            'liderazgo academico posicionamiento': 'Liderazgo Académico / Posicionamiento',
            'liderazgo academico / preparacion': 'Liderazgo Académico / Preparación',
            'liderazgo academico preparacion': 'Liderazgo Académico / Preparación',
            'liderazgo academico / capitulos estudiantiles': 'Liderazgo Académico / Capítulos Estudiantiles',
            'liderazgo academico capitulos estudiantiles': 'Liderazgo Académico / Capítulos Estudiantiles',
            'capitulos estudiantiles': 'Liderazgo Académico / Capítulos Estudiantiles',
        }
    
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
    
    def distancia_levenshtein(self, s1: str, s2: str) -> int:
        """Calcula la distancia de Levenshtein entre dos strings"""
        if len(s1) < len(s2):
            return self.distancia_levenshtein(s2, s1)
        
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
    
    def encontrar_mejor_coincidencia(self, valor: str, opciones_validas: List[str], umbral_minimo: float = 0.65) -> Optional[str]:
        """Encuentra la mejor coincidencia usando múltiples algoritmos"""
        if pd.isna(valor):
            return None
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        # Cache para evitar recálculos
        cache_key = f"{valor_str}_{hash(tuple(sorted(opciones_validas)))}"
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
        
        # 3. Reglas específicas
        valor_normalizado = self.normalizar_texto(valor_str)
        if valor_normalizado in self.reglas_especificas:
            candidato = self.reglas_especificas[valor_normalizado]
            if candidato in opciones_validas:
                self.cache_correcciones[cache_key] = candidato
                return candidato
        
        # 4. Coincidencia sin acentos
        for opcion in opciones_validas:
            if valor_normalizado == self.normalizar_texto(opcion):
                self.cache_correcciones[cache_key] = opcion
                return opcion
        
        # 5. Búsqueda por contención (para palabras compuestas)
        for opcion in opciones_validas:
            opcion_normalizada = self.normalizar_texto(opcion)
            if len(valor_normalizado) > 3:
                if (valor_normalizado in opcion_normalizada or 
                    opcion_normalizada in valor_normalizado):
                    self.cache_correcciones[cache_key] = opcion
                    return opcion
        
        # 6. Similitud usando SequenceMatcher
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
        
        # 7. Distancia de Levenshtein para errores menores
        mejor_opcion = self.busqueda_por_distancia_editorial(valor_str, opciones_validas)
        if mejor_opcion:
            self.cache_correcciones[cache_key] = mejor_opcion
            return mejor_opcion
        
        # No se encontró coincidencia
        self.cache_correcciones[cache_key] = None
        return None
    
    def busqueda_por_distancia_editorial(self, valor: str, opciones_validas: List[str], max_distancia: int = 3) -> Optional[str]:
        """Búsqueda usando distancia de edición para errores menores"""
        valor_normalizado = self.normalizar_texto(valor)
        mejores_opciones = []
        
        for opcion in opciones_validas:
            opcion_normalizada = self.normalizar_texto(opcion)
            distancia = self.distancia_levenshtein(valor_normalizado, opcion_normalizada)
            
            # Ajustar umbral basado en longitud de texto
            longitud_promedio = (len(valor_normalizado) + len(opcion_normalizada)) / 2
            umbral_dinamico = min(max_distancia, max(1, int(longitud_promedio * 0.3)))
            
            if distancia <= umbral_dinamico:
                mejores_opciones.append((opcion, distancia))
        
        if mejores_opciones:
            # Ordenar por menor distancia
            mejores_opciones.sort(key=lambda x: x[1])
            return mejores_opciones[0][0]
        
        return None
    
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
    
    def test_corrector(self):
        """Prueba el corrector con algunos ejemplos"""
        ejemplos_arte = [
            ('musica', COMPANIAS_ARTE),
            ('danza folklorica', COMPANIAS_ARTE),
            ('teatro musical', TIPOS_ESPECTACULO_ARTE),
            ('orquesta coro', TIPOS_ESPECTACULO_ARTE),
        ]
        
        st.info("🧪 Probando corrector local...")
        for valor, opciones in ejemplos_arte:
            resultado = self.encontrar_mejor_coincidencia(valor, opciones)
            st.write(f"'{valor}' → '{resultado}'")
