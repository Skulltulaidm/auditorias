"""
Corrector ortográfico usando la API de OpenAI
"""

import os
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional
import time
from openai import OpenAI

class OpenAICorrector:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de OpenAI"""
        try:
            # Obtener la API key desde las variables de entorno de Streamlit
            api_key = None
            
            # Primero intentar desde st.secrets
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                api_key = st.secrets['OPENAI_API_KEY']
            
            # Si no está en secrets, intentar desde variables de entorno
            if not api_key:
                api_key = os.getenv('OPENAI_API_KEY')
            
            if api_key:
                self.client = OpenAI(api_key=api_key)
                return True
            else:
                st.warning("⚠️ API Key de OpenAI no configurada. Se usará corrección básica.")
                return False
                
        except Exception as e:
            st.warning(f"⚠️ Error al inicializar OpenAI: {str(e)}. Se usará corrección básica.")
            return False
    
    def corregir_valor_con_openai(self, valor: str, opciones_validas: List[str], campo: str) -> Optional[str]:
        """
        Usa OpenAI para corregir un valor basado en una lista de opciones válidas
        """
        if not self.client or pd.isna(valor):
            return self._correccion_basica(valor, opciones_validas)
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        # Si ya es válido, no corregir
        if valor_str in opciones_validas:
            return valor_str
        
        try:
            # Crear el prompt para OpenAI
            opciones_texto = '\n'.join([f"- {opcion}" for opcion in opciones_validas])
            
            prompt = f"""Necesito corregir un valor que tiene errores ortográficos o de formato.

Campo: {campo}
Valor actual: "{valor_str}"

Opciones válidas:
{opciones_texto}

Instrucciones:
1. Encuentra la opción válida que más se parezca al valor actual
2. Considera errores de ortografía, acentos, mayúsculas/minúsculas, espacios
3. Responde ÚNICAMENTE con la opción válida exacta (sin explicaciones ni comillas)
4. Si no hay ninguna coincidencia razonable, responde exactamente: NO_MATCH

Respuesta:"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un corrector ortográfico especializado. Responde únicamente con la opción correcta o NO_MATCH."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            correccion = response.choices[0].message.content.strip()
            
            # Verificar que la corrección sea válida
            if correccion in opciones_validas:
                return correccion
            elif correccion == "NO_MATCH":
                return None
            else:
                # OpenAI devolvió algo no válido, usar corrección básica
                return self._correccion_basica(valor_str, opciones_validas)
                
        except Exception as e:
            st.warning(f"Error en OpenAI para {campo}: {str(e)}")
            return self._correccion_basica(valor_str, opciones_validas)
    
    def _correccion_basica(self, valor: str, opciones_validas: List[str]) -> Optional[str]:
        """Corrección básica sin OpenAI como respaldo"""
        import unicodedata
        import re
        
        if pd.isna(valor):
            return None
            
        valor_str = str(valor).strip()
        if not valor_str:
            return None
        
        def normalizar_texto(texto):
            # Remover acentos
            texto_normalizado = unicodedata.normalize('NFD', texto)
            texto_sin_acentos = ''.join(char for char in texto_normalizado if unicodedata.category(char) != 'Mn')
            # Convertir a lowercase y remover espacios extra
            return re.sub(r'\s+', ' ', texto_sin_acentos.lower().strip())
        
        valor_normalizado = normalizar_texto(valor_str)
        
        # Búsqueda case-insensitive
        for opcion in opciones_validas:
            if valor_str.lower() == opcion.lower():
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
            
            # Filtrar valores únicos para evitar correcciones duplicadas
            valores_unicos = list(set([str(v).strip() for v in valores if pd.notna(v) and str(v).strip() != ""]))
            
            for valor in valores_unicos:
                if valor not in opciones_validas:
                    correccion = self.corregir_valor_con_openai(valor, opciones_validas, campo)
                    if correccion and correccion != valor:
                        correcciones[campo][valor] = correccion
                
                # Pequeña pausa para no saturar la API
                time.sleep(0.2)
        
        return correcciones
    
    def test_connection(self) -> bool:
        """Prueba la conexión con OpenAI"""
        if not self.client:
            return False
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            st.error(f"Error de conexión con OpenAI: {str(e)}")
            return False
