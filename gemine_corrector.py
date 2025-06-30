"""
Corrector ortográfico usando la API de Gemini de Google
"""

import os
import pandas as pd
from google import genai
import streamlit as st
from typing import List, Dict, Optional
import time

class GeminiCorrector:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de Gemini"""
        try:
            # Intentar obtener la API key del environment o de Streamlit secrets
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key and hasattr(st, 'secrets'):
                api_key = st.secrets.get('GEMINI_API_KEY')
            
            if api_key:
                os.environ['GEMINI_API_KEY'] = api_key
                self.client = genai.Client()
                return True
            else:
                st.warning("⚠️ API Key de Gemini no configurada. Se usará corrección básica.")
                return False
        except Exception as e:
            st.warning(f"⚠️ Error al inicializar Gemini: {str(e)}. Se usará corrección básica.")
            return False
    
    def corregir_valor_con_gemini(self, valor: str, opciones_validas: List[str], campo: str) -> Optional[str]:
        """
        Usa Gemini para corregir un valor basado en una lista de opciones válidas
        """
        if not self.client or pd.isna(valor):
            return None
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        # Si ya es válido, no corregir
        if valor_str in opciones_validas:
            return valor_str
        
        try:
            prompt = f"""
            Necesito corregir un valor que tiene errores ortográficos o de formato.

            Campo: {campo}
            Valor actual: "{valor_str}"
            
            Opciones válidas:
            {chr(10).join([f"- {opcion}" for opcion in opciones_validas])}
            
            Instrucciones:
            1. Encuentra la opción válida que más se parezca al valor actual
            2. Considera errores de ortografía, acentos, mayúsculas/minúsculas, espacios
            3. Responde ÚNICAMENTE con la opción válida exacta (sin explicaciones)
            4. Si no hay ninguna coincidencia razonable, responde "NO_MATCH"
            
            Respuesta:
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            correccion = response.text.strip()
            
            # Verificar que la corrección sea válida
            if correccion in opciones_validas:
                return correccion
            elif correccion == "NO_MATCH":
                return None
            else:
                # Gemini devolvió algo no válido, usar corrección básica
                return self._correccion_basica(valor_str, opciones_validas)
                
        except Exception as e:
            st.warning(f"Error en Gemini para {campo}: {str(e)}")
            return self._correccion_basica(valor_str, opciones_validas)
    
    def _correccion_basica(self, valor: str, opciones_validas: List[str]) -> Optional[str]:
        """Corrección básica sin Gemini como respaldo"""
        import unicodedata
        import re
        
        def normalizar_texto(texto):
            # Remover acentos
            texto_normalizado = unicodedata.normalize('NFD', texto)
            texto_sin_acentos = ''.join(char for char in texto_normalizado if unicodedata.category(char) != 'Mn')
            # Convertir a lowercase y remover espacios extra
            return re.sub(r'\s+', ' ', texto_sin_acentos.lower().strip())
        
        valor_normalizado = normalizar_texto(valor)
        
        # Búsqueda case-insensitive
        for opcion in opciones_validas:
            if valor.lower() == opcion.lower():
                return opcion
        
        # Búsqueda sin acentos
        for opcion in opciones_validas:
            if valor_normalizado == normalizar_texto(opcion):
                return opcion
        
        # Búsqueda por contención
        for opcion in opciones_validas:
            opcion_normalizada = normalizar_texto(opcion)
            if (valor_normalizado in opcion_normalizada or 
                opcion_normalizada in valor_normalizado) and len(valor_normalizado) > 3:
                return opcion
        
        return None
    
    def corregir_batch(self, valores_dict: Dict[str, List[str]], opciones_dict: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
        """
        Corrige múltiples valores en batch para ser más eficiente
        """
        correcciones = {}
        
        for campo, valores in valores_dict.items():
            if campo not in opciones_dict:
                continue
                
            correcciones[campo] = {}
            opciones_validas = opciones_dict[campo]
            
            for valor in valores:
                if pd.isna(valor) or str(valor).strip() == "":
                    continue
                    
                valor_str = str(valor).strip()
                if valor_str not in opciones_validas:
                    correccion = self.corregir_valor_con_gemini(valor_str, opciones_validas, campo)
                    if correccion and correccion != valor_str:
                        correcciones[campo][valor_str] = correccion
                
                # Pequeña pausa para no saturar la API
                time.sleep(0.1)
        
        return correcciones
