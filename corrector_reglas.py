"""
Corrector con reglas específicas para los campos más comunes
"""

import pandas as pd
import re
from typing import Dict, List, Optional

class CorrectorReglas:
    def __init__(self):
        # Reglas de corrección específicas
        self.reglas_generales = {
            # Correcciones comunes de acentos
            'musica': 'Música',
            'danza folklorica': 'Danza Folklórica',
            'teatro musical': 'Teatro Musical',
            'orquesta coro': 'Orquesta/Coro',
            
            # Deportes comunes
            'futbol americano': 'Futbol Americano',
            'futbol soccer': 'Futbol Soccer',
            'basquetbol': 'Basquetbol',
            'voleibol sala': 'Voleibol Sala',
            'voleibol playa': 'Voleibol Playa',
            
            # Ramas
            'femenino': 'Femenil',
            'masculino': 'Varonil',
            'femenil': 'Femenil',
            'varonil': 'Varonil',
            'mixto': 'Mixto',
            
            # Giros comunes
            'ecologia': 'Ecología y Medio Ambiente',
            'medio ambiente': 'Ecología y Medio Ambiente',
            'arte cultura': 'Arte, Cultura y Entretenimiento',
            'liderazgo': 'Liderazgo',
        }
        
        # Patrones de reemplazo
        self.patrones = [
            (r'\s+', ' '),  # Múltiples espacios a uno
            (r'^(.+)$', lambda m: m.group(1).strip()),  # Quitar espacios al inicio/final
        ]
    
    def aplicar_reglas_especificas(self, valor: str, opciones_validas: List[str]) -> Optional[str]:
        """Aplica reglas específicas de corrección"""
        if pd.isna(valor):
            return None
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        # Aplicar patrones de limpieza
        valor_limpio = valor_str
        for patron, reemplazo in self.patrones:
            if callable(reemplazo):
                valor_limpio = re.sub(patron, reemplazo, valor_limpio)
            else:
                valor_limpio = re.sub(patron, reemplazo, valor_limpio)
        
        # Buscar en reglas generales
        valor_lower = valor_limpio.lower()
        if valor_lower in self.reglas_generales:
            candidato = self.reglas_generales[valor_lower]
            if candidato in opciones_validas:
                return candidato
        
        # Buscar coincidencias parciales en reglas
        for regla, correccion in self.reglas_generales.items():
            if regla in valor_lower and correccion in opciones_validas:
                return correccion
        
        return None
