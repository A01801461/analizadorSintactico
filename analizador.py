import re
from flask import Flask, render_template, request

# -----------------------------------------------------------------------------------------------------------------------
# 1. Definición de patrones léxicos: expresiones para cada tipo de token
# -----------------------------------------------------------------------------------------------------------------------

# Patrones Lexicos
patterns = [
    # palabras clave reservadas
    (r'\bvar\b', 'VAR'),
    (r'\bif\b', 'IF'),
    (r'\belse\b', 'ELSE'),
    (r'\bwhile\b', 'WHILE'),
    (r'\bfunction\b', 'FUNCTION'),
    (r'\breturn\b', 'RETURN'),
    # Identificadores (nombres var y fun)
    (r'[a-zA-Z][a-zA-Z0-9]*', 'ID'),
    # numeros
    (r'\d+\.\d+', 'DECIMAL'),
    (r'\d+', 'ENTERO'),
    # operadores de comparación
    (r'==', 'IGUAL'),
    (r'!=', 'DIFERENTE'),
    (r'<=', 'MENOR_IGUAL'),
    (r'>=', 'MAYOR_IGUAL'),
    (r'<', 'MENOR'),
    (r'>', 'MAYOR'),
    # operadores de asignación y aritmeticos
    (r'=', 'ASIGNACION'),
    (r'\+', 'MAS'),
    (r'-', 'MENOS'),
    (r'\*', 'POR'),
    (r'/', 'DIV'),
    # delimitadores y símbolos
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\{', 'LLAVE_IZQ'),
    (r'\}', 'LLAVE_DER'),
    (r';', 'PUNTO_COMA'),
    (r',', 'COMA'),
    # espacios y saltos de linea
    (r'\s+', None),
    (r'\n+', None)
]
# -----------------------------------------------------------------------------------------------------------------------
# 2. Clase Token: le da un tipo y un valor a cada token
# -----------------------------------------------------------------------------------------------------------------------
# Clase para los tokens
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

# -----------------------------------------------------------------------------------------------------------------------
# 3. Lexer: Tokeniza el codigo (rompe el string en lista de tokens)
# -----------------------------------------------------------------------------------------------------------------------

# Función del lexer
def lexer(code):
    tokens = []
    pos = 0
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
# 4. Parser: verifica la sintaxis aplicando reglas gramaticales
# -----------------------------------------------------------------------------------------------------------------------
# Cada función de la clase parser, es "una regla gramatical"
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def match(self, expected):
        if self.current < len(self.tokens) and self.tokens[self.current].type == expected:
            self.current += 1
        else:
            raise SyntaxError(f"Esperado {expected} en posición {self.current}")

    def S(self):
        if self.current < len(self.tokens):
            self.C()
            self.S()  # Recursión para C S
        # Si no hay más tokens, se asume que S puede terminar

    def C(self):
        if self.current >= len(self.tokens):
            # Si se llama S y no hay mas tokens (parte vacia de S -> C S)
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
            # Si el token no es ninguno de los admitidos por C
            error_token_value = self.tokens[self.current].value
            raise SyntaxError(f"Sentencia o declaración inválida. Se encontró '{error_token_value}' (tipo: {token_type}) en la posición {self.current}.")

    def D(self):
        self.match('VAR')
        self.N()
        self.match('ASIGNACION')
        self.E()
        self.match('PUNTO_COMA')

    def A(self):
        self.N()
        self.match('ASIGNACION')
        self.E()
        self.match('PUNTO_COMA')

    def COND(self):
        self.E()
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('MENOR', 'MAYOR', 'IGUAL', 'MENOR_IGUAL', 'MAYOR_IGUAL', 'DIFERENTE'):
            self.O()
            self.E()

    def I(self):
        self.match('IF')
        self.match('LPAREN')
        self.COND()
        self.match('RPAREN')
        self.B()
        if self.current < len(self.tokens) and self.tokens[self.current].type == 'ELSE':
            self.match('ELSE')
            self.B()

    def W(self):
        self.match('WHILE')
        self.match('LPAREN')
        self.COND()
        self.match('RPAREN')
        self.B()

    def B(self):
        self.match('LLAVE_IZQ')
        self.Z()
        self.match('LLAVE_DER')

    def F(self):
        self.match('FUNCTION')
        self.N()
        self.match('LPAREN')
        if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
            self.P()
        self.match('RPAREN')
        self.B()
    
    def P(self):
        self.N()  # Primer parámetro
        while self.current < len(self.tokens) and self.tokens[self.current].type == 'COMA':
            self.match('COMA')
            self.N()  # Parámetros adicionales separados por comas

    def R(self):
        self.match('RETURN')
        self.E()
        self.match('PUNTO_COMA')

    def L(self):
        self.N()
        self.match('LPAREN')
        if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
            self.P()
        self.match('RPAREN')
        self.match('PUNTO_COMA')

    def Z(self):
        while self.current < len(self.tokens) and self.tokens[self.current].type != 'LLAVE_DER':
            token_type = self.tokens[self.current].type  # Get current token type

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
            elif token_type == 'FUNCTION':  # <<< Agregue este caso
                self.F()                    # Ahora Z tambien acepta llamadas a funciones
            elif token_type == 'RETURN':
                self.R()
            else:
                # Error (el token no es ninguno de los aceptados por Z)
                error_token_value = self.tokens[self.current].value
                error_token_type = self.tokens[self.current].type
                raise SyntaxError(f"Estatuto esperado en bloque, pero se encontró '{error_token_value}' (tipo: {error_token_type}) en la posición {self.current}.")

    def N(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type == 'ID':
            self.match('ID')
        else:
            raise SyntaxError("Identificador esperado")

    def O(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('MENOR', 'MAYOR', 'IGUAL', 'MENOR_IGUAL', 'MAYOR_IGUAL', 'DIFERENTE'):
            self.current += 1
        else:
            raise SyntaxError("Operador lógico esperado")

    def E(self):
        self.T()
        while self.current < len(self.tokens) and self.tokens[self.current].type in ('MAS', 'MENOS'):
            self.current += 1
            self.T()

    def T(self):
        self.G()
        while self.current < len(self.tokens) and self.tokens[self.current].type in ('POR', 'DIV'):
            self.current += 1
            self.G()

    def G(self):
        if self.current < len(self.tokens):
            if self.tokens[self.current].type == 'ID':
                self.N()  # Parsea el identificador
                # Si viene un paréntesis, es una llamada a función
                if self.current < len(self.tokens) and self.tokens[self.current].type == 'LPAREN':
                    self.match('LPAREN')
                    # Si no hay parámetros, se espera solo ')'
                    if self.current < len(self.tokens) and self.tokens[self.current].type != 'RPAREN':
                        self.P()  # Parsea la lista de parámetros (N)
                    self.match('RPAREN')
                # Si no hay '(', entonces es solo un identificador (N)
            elif self.tokens[self.current].type in ('ENTERO', 'DECIMAL'):
                self.Y()  # Parsea un número
            elif self.tokens[self.current].type == 'LPAREN':
                self.match('LPAREN')
                self.E()  # Parsea una expresión entre paréntesis
                self.match('RPAREN')
            else:
                raise SyntaxError("Expresión esperada")
        else:
            raise SyntaxError("Expresión esperada")
    
    def Y(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('ENTERO', 'DECIMAL'):
            self.current += 1
        else:
            raise SyntaxError("Número esperado")

# -----------------------------------------------------------------------------------------------------------------------
# 5. Configuración de Flask
# -----------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)

# Función para generar HTML con tokens coloreados
def highlight_tokens(tokens):
    # Mapeo  para cada tipo de token
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
    
    highlighted = []
    for token in tokens:
        css_class = token_colors.get(token.type, 'token-default')
        # Escapar caracteres especiales para HTML
        value = token.value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        highlighted.append(f'<span class="{css_class}">{value}</span>')
    
    return ''.join(highlighted)

# Ruta principal
@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    highlighted_code = ""
    original_code = ""
    
    if request.method == 'POST':
        original_code = request.form['code']
        try:
            # Procesar el código
            tokens = lexer(original_code)
            highlighted_code = highlight_tokens(tokens)
            
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
        original_code = ""  # Para GET requests
    
    return render_template(
        'index.html', 
        result=result,
        highlighted_code=highlighted_code,
        original_code=original_code
    )

if __name__ == '__main__':
    app.run(debug=True)