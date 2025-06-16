# -----------------------------------------------------------------------------------------------------------------------
# Autores:
#   Isaac Abud León A01801461
#   Jaretzy Andrea Santiago Barragán A01801092
# Entrega: Etapa 3, Analizador Sintáctico
# Descripción: Analizador léxico y sintáctico básico implementado en Python usando expresiones regulares. Este programa
# utiliza Flask para crear una interfaz web que recibe código fuente, lo tokeniza y verifica su sintaxis.
# -----------------------------------------------------------------------------------------------------------------------

import os
import re
import time
from flask import Flask, render_template, request
from concurrent.futures import ThreadPoolExecutor

# -----------------------------------------------------------------------------------------------------------------------
# 1. Definición de patrones léxicos: expresiones regulares para cada tipo de token.
# Estos patrones identifican palabras clave, identificadores, operadores, números, y delimitadores.
# -----------------------------------------------------------------------------------------------------------------------

patterns = [
    # Palabras clave reservadas del lenguaje
    (r'\bvar\b', 'VAR'),
    (r'\bif\b', 'IF'),
    (r'\belse\b', 'ELSE'),
    (r'\bwhile\b', 'WHILE'),
    (r'\bfunction\b', 'FUNCTION'),
    (r'\breturn\b', 'RETURN'),
    # Identificadores: letras seguidas opcionalmente de letras o números
    (r'[a-zA-Z][a-zA-Z0-9]*', 'ID'),
    # Números: decimales y enteros
    (r'\d+\.\d+', 'DECIMAL'),
    (r'\d+', 'ENTERO'),
    # Operadores de comparación
    (r'==', 'IGUAL'),
    (r'!=', 'DIFERENTE'),
    (r'<=', 'MENOR_IGUAL'),
    (r'>=', 'MAYOR_IGUAL'),
    (r'<', 'MENOR'),
    (r'>', 'MAYOR'),
    # Operadores de asignación y aritméticos
    (r'=', 'ASIGNACION'),
    (r'\+', 'MAS'),
    (r'-', 'MENOS'),
    (r'\*', 'POR'),
    (r'/', 'DIV'),
    # Delimitadores y símbolos
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\{', 'LLAVE_IZQ'),
    (r'\}', 'LLAVE_DER'),
    (r';', 'PUNTO_COMA'),
    (r',', 'COMA'),
    # Espacios y saltos de línea (se ignoran)
    (r'\s+', None),
    (r'\n+', None)
]

# -----------------------------------------------------------------------------------------------------------------------
# 2. Clase Token: representa un token con su tipo y valor capturado del código fuente.
# -----------------------------------------------------------------------------------------------------------------------

class Token:
    def __init__(self, type, value):
        self.type = type  # Tipo de token (por ejemplo, 'ID', 'VAR', etc.)
        self.value = value  # Valor original capturado del código

# -----------------------------------------------------------------------------------------------------------------------
# 3. Lexer: función que tokeniza el código fuente. Recorre el texto e identifica tokens válidos según los patrones.
# -----------------------------------------------------------------------------------------------------------------------

def lexer(code):
    tokens = []  # Lista final de tokens
    pos = 0  # Posición actual en el texto
    while pos < len(code):
        match = None
        for pattern, token_type in patterns:
            regex = re.compile(pattern)
            match = regex.match(code, pos)
            if match:
                value = match.group(0)
                if token_type:
                    tokens.append(Token(token_type, value))
                pos = match.end()
                break
        if not match:
            raise SyntaxError(f"Carácter no reconocido en posición {pos}: {code[pos]}")
    return tokens

# -----------------------------------------------------------------------------------------------------------------------
# 4. Parser: analizador sintáctico. Verifica la estructura del código usando reglas gramaticales.
# Cada método representa una producción o regla del lenguaje.
# -----------------------------------------------------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens  # Lista de tokens que analizará
        self.current = 0      # Índice actual en la lista de tokens

    # Verifica si el token actual es del tipo esperado
    def match(self, expected):
        if self.current < len(self.tokens) and self.tokens[self.current].type == expected:
            self.current += 1
        else:
            raise SyntaxError(f"Esperado {expected} en posición {self.current}")

    # Producción inicial S -> C S | ε
    def S(self):
        if self.current < len(self.tokens):
            self.C()
            self.S()

    # Producción C: selección de tipos de instrucciones
    def C(self):
        if self.current >= len(self.tokens):
            return
        token_type = self.tokens[self.current].type
        if token_type == 'VAR':
            self.D()
        elif token_type == 'ID':
            if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == 'ASIGNACION':
                self.A()
            else:
                self.L()
        elif token_type == 'IF':
            self.I()
        elif token_type == 'WHILE':
            self.W()
        elif token_type == 'FUNCTION':
            self.F()
        elif token_type == 'RETURN':
            self.R()
        else:
            error_token_value = self.tokens[self.current].value
            raise SyntaxError(f"Sentencia o declaración inválida. Se encontró '{error_token_value}' (tipo: {token_type}) en la posición {self.current}.")

    # Declaración de variable: var ID = E;
    def D(self):
        self.match('VAR')
        self.N()
        self.match('ASIGNACION')
        self.E()
        self.match('PUNTO_COMA')

    # Asignación: ID = E;
    def A(self):
        self.N()
        self.match('ASIGNACION')
        self.E()
        self.match('PUNTO_COMA')

    # Condición: E operador E
    def COND(self):
        self.E()
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('MENOR', 'MAYOR', 'IGUAL', 'MENOR_IGUAL', 'MAYOR_IGUAL', 'DIFERENTE'):
            self.O()
            self.E()

    # Sentencia IF-ELSE
    def I(self):
        self.match('IF')
        self.match('LPAREN')
        self.COND()
        self.match('RPAREN')
        self.B()
        if self.current < len(self.tokens) and self.tokens[self.current].type == 'ELSE':
            self.match('ELSE')
            self.B()

    # Ciclo WHILE
    def W(self):
        self.match('WHILE')
        self.match('LPAREN')
        self.COND()
        self.match('RPAREN')
        self.B()

    # Bloque de código: { Z }
    def B(self):
        self.match('LLAVE_IZQ')
        self.Z()
        self.match('LLAVE_DER')

    # Declaración de función
    def F(self):
        self.match('FUNCTION')
        self.N()
        self.match('LPAREN')
        if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
            self.P()
        self.match('RPAREN')
        self.B()

    # Lista de parámetros: ID (, ID)*
    def P(self):
        self.N()
        while self.current < len(self.tokens) and self.tokens[self.current].type == 'COMA':
            self.match('COMA')
            self.N()

    # Retorno de función
    def R(self):
        self.match('RETURN')
        self.E()
        self.match('PUNTO_COMA')

    # Llamada a función
    def L(self):
        self.N()
        self.match('LPAREN')
        if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
            self.P()
        self.match('RPAREN')
        self.match('PUNTO_COMA')

    # Secuencia de sentencias dentro de un bloque
    def Z(self):
        while self.current < len(self.tokens) and self.tokens[self.current].type != 'LLAVE_DER':
            token_type = self.tokens[self.current].type
            if token_type == 'VAR':
                self.D()
            elif token_type == 'ID':
                if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == 'ASIGNACION':
                    self.A()
                else:
                    self.L()
            elif token_type == 'IF':
                self.I()
            elif token_type == 'WHILE':
                self.W()
            elif token_type == 'FUNCTION':
                self.F()
            elif token_type == 'RETURN':
                self.R()
            else:
                error_token_value = self.tokens[self.current].value
                error_token_type = self.tokens[self.current].type
                raise SyntaxError(f"Estatuto esperado en bloque, pero se encontró '{error_token_value}' (tipo: {error_token_type}) en la posición {self.current}.")

    # Identificador (ID)
    def N(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type == 'ID':
            self.match('ID')
        else:
            raise SyntaxError("Identificador esperado")

    # Operadores de comparación
    def O(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('MENOR', 'MAYOR', 'IGUAL', 'MENOR_IGUAL', 'MAYOR_IGUAL', 'DIFERENTE'):
            self.current += 1
        else:
            raise SyntaxError("Operador lógico esperado")

    # Expresiones aritméticas: suma y resta
    def E(self):
        self.T()
        while self.current < len(self.tokens) and self.tokens[self.current].type in ('MAS', 'MENOS'):
            self.current += 1
            self.T()

    # Términos: multiplicación y división
    def T(self):
        self.G()
        while self.current < len(self.tokens) and self.tokens[self.current].type in ('POR', 'DIV'):
            self.current += 1
            self.G()

    # Factores: ID, número, llamada a función, o expresión entre paréntesis
    def G(self):
        if self.current < len(self.tokens):
            if self.tokens[self.current].type == 'ID':
                self.N()
                if self.current < len(self.tokens) and self.tokens[self.current].type == 'LPAREN':
                    self.match('LPAREN')
                    if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
                        self.P()
                    self.match('RPAREN')
            elif self.tokens[self.current].type in ('ENTERO', 'DECIMAL'):
                self.Y()
            elif self.tokens[self.current].type == 'LPAREN':
                self.match('LPAREN')
                self.E()
                self.match('RPAREN')
            else:
                raise SyntaxError("Expresión esperada")
        else:
            raise SyntaxError("Expresión esperada")

    # Constantes numéricas
    def Y(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('ENTERO', 'DECIMAL'):
            self.current += 1
        else:
            raise SyntaxError("Número esperado")

# -----------------------------------------------------------------------------------------------------------------------
# 5. Procesamiento y hghliht de strings y archivos
# -----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)

# Función para generar HTML con tokens coloreados
def highlight_tokens(code, tokens):
    token_colors = {
        'VAR': 'token-var',
        'IF': 'token-if',
        'ELSE': 'token-else',
        'WHILE': 'token-while',
        'FUNCTION': 'token-function',
        'RETURN': 'token-return',
        'ID': 'token-id',
        'DECIMAL': 'token-number',
        'ENTERO': 'token-number',
        'IGUAL': 'token-operator',
        'DIFERENTE': 'token-operator',
        'MENOR_IGUAL': 'token-operator',
        'MAYOR_IGUAL': 'token-operator',
        'MENOR': 'token-operator',
        'MAYOR': 'token-operator',
        'ASIGNACION': 'token-assign',
        'MAS': 'token-operator',
        'MENOS': 'token-operator',
        'POR': 'token-operator',
        'DIV': 'token-operator',
        'LPAREN': 'token-paren',
        'RPAREN': 'token-paren',
        'LLAVE_IZQ': 'token-brace',
        'LLAVE_DER': 'token-brace',
        'PUNTO_COMA': 'token-semicolon',
        'COMA': 'token-comma'
    }
    # Para evitar reemplazar múltiples veces, se recorre el texto una vez
    result = ""
    index = 0
    for token in tokens:
        # Encuentra el token en el texto a partir de la posición actual
        start = code.find(token.value, index)
        if start == -1:
            continue  # No encontrado, lo ignora
        end = start + len(token.value)

        # Agrega el texto sin resaltar hasta el inicio del token
        result += code[index:start]

        # Resalta el token
        css_class = token_colors.get(token.type, 'token-default')
        result += f'<span class="{css_class}">{token.value}</span>'

        # Actualiza el índice para continuar
        index = end

    # Agrega lo que queda del texto sin resaltar
    result += code[index:]

    return result

def process_single_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Análisis léxico
        tokens = lexer(content)
        highlighted_code = highlight_tokens(content, tokens)
        
        return {
            'filename': os.path.basename(filepath),
            'status': 'success',
            'highlighted_code': highlighted_code,
            'token_count': len(tokens),
            'original_code': content,
            'error': None
        }
    except Exception as e:
        return {
            'filename': os.path.basename(filepath),
            'status': 'error',
            'highlighted_code': '',
            'token_count': 0,
            'original_code': '',
            'error': str(e)
        }

# obtiene los .txt de la carpeta tests
def get_test_files():
    tests_dir = os.path.join(os.getcwd(), 'tests')
    if not os.path.exists(tests_dir):
        return []
    
    files = []
    for filename in os.listdir(tests_dir):
        if filename.endswith('.txt'):
            files.append(os.path.join(tests_dir, filename))
    return files


# Funcion para procesamiento secuencial
def process_files_sequential():
    files = get_test_files()
    if not files:
        return [], 0
    
    start_time = time.time()
    results = []
    
    for filepath in files:
        result = process_single_file(filepath)
        results.append(result)
    
    execution_time = time.time() - start_time
    return results, execution_time

# Funcion para procesamiento paralelo usando ThreadPoolExecutor
def process_files_parallel():
    files = get_test_files()
    if not files:
        return [], 0
    
    start_time = time.time()
    
    # Usar ThreadPoolExecutor para procesamiento paralelo
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(process_single_file, files))
    
    execution_time = time.time() - start_time
    return results, execution_time


# -----------------------------------------------------------------------------------------------------------------------
# 6. Configuración de Flask
# -----------------------------------------------------------------------------------------------------------------------

# Ruta principal
@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    highlighted_code = ""
    original_code = ""
    
    # Información sobre archivos de prueba
    test_files = get_test_files()
    file_info = {
        'count': len(test_files),
        'files': [os.path.basename(f) for f in test_files]
    }
    
    if request.method == 'POST':
        original_code = request.form['code']
        try:
            # Procesar el código
            tokens = lexer(original_code)
            highlighted_code = highlight_tokens(original_code, tokens)
            
            # Análisis sintáctico
            parser = Parser(tokens)
            parser.S()
            
            # Verificar si se procesaron todos los tokens
            if parser.current == len(tokens):
                result = "✅ El código es sintácticamente correcto."
            else:
                remaining = ' '.join([t.value for t in tokens[parser.current:]])
                result = f"❌ Error: Código incompleto. Tokens no procesados: {remaining}"
        except SyntaxError as e:
            result = f"❌ Error sintáctico: {e}"
    else:
        original_code = ""
    
    return render_template(
        'index.html', 
        result=result,
        highlighted_code=highlighted_code,
        original_code=original_code,
        file_info=file_info
    )

# Ruta para procesamiento secuencial
@app.route('/process_sequential', methods=['POST'])
def process_sequential():

    try:
        results, execution_time = process_files_sequential()
        
        # Calcular estadísticas
        successful_files = [r for r in results if r['status'] == 'success']
        failed_files = [r for r in results if r['status'] == 'error']
        
        stats = {
            'total_files': len(results),
            'successful': len(successful_files),
            'failed': len(failed_files),
            'execution_time': round(execution_time, 4),
            'avg_time_per_file': round(execution_time / len(results), 4) if results else 0,
            'processing_type': 'Secuencial'
        }
        
        return render_template(
            'results.html',
            results=results,
            stats=stats,
            processing_type='sequential'
        )
    except Exception as e:
        return render_template(
            'error.html',
            error_message=f"Error en procesamiento secuencial: {str(e)}"
        )


# Ruta para procesamiento paralelo
@app.route('/process_parallel', methods=['POST'])

def process_parallel():

    try:
        results, execution_time = process_files_parallel()
        
        # Calcular estadísticas
        successful_files = [r for r in results if r['status'] == 'success']
        failed_files = [r for r in results if r['status'] == 'error']
        
        stats = {
            'total_files': len(results),
            'successful': len(successful_files),
            'failed': len(failed_files),
            'execution_time': round(execution_time, 4),
            'avg_time_per_file': round(execution_time / len(results), 4) if results else 0,
            'processing_type': 'Paralelo',
            'cpu_cores': os.cpu_count()
        }
        
        return render_template(
            'results.html',
            results=results,
            stats=stats,
            processing_type='parallel'
        )
    except Exception as e:
        return render_template(
            'error.html',
            error_message=f"Error en procesamiento paralelo: {str(e)}"
        )
    
if __name__ == '__main__':
    app.run(debug=True)