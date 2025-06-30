"""
Configuración y diccionarios de valores válidos para el auditor CSV
"""

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

# Columnas que NO se pueden corregir automáticamente
COLUMNAS_NO_CORREGIBLES = [
    'NOMBRE',
    'APELLIDO PATERNO', 
    'APELLIDO MATERNO',
    'Nombre completo',
    'EJERCICIO_ACADEMICO',
    'Ejercicio Académico'
]
