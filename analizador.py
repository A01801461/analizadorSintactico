import re
from flask import Flask, request, render_template_string

# Patrones para el lexer
patterns = [
    (r'\bvar\b', 'VAR'),
    (r'\bif\b', 'IF'),
    (r'\belse\b', 'ELSE'),
    (r'\bwhile\b', 'WHILE'),
    (r'\bfunction\b', 'FUNCTION'),
    (r'\breturn\b', 'RETURN'),
    (r'[a-zA-Z][a-zA-Z0-9]*', 'ID'),
    (r'\d+\.\d+', 'DECIMAL'),
    (r'\d+', 'ENTERO'),
    (r'==', 'IGUAL'),
    (r'!=', 'DIFERENTE'),
    (r'<=', 'MENOR_IGUAL'),
    (r'>=', 'MAYOR_IGUAL'),
    (r'<', 'MENOR'),
    (r'>', 'MAYOR'),
    (r'=', 'ASIGNACION'),
    (r'\+', 'MAS'),
    (r'-', 'MENOS'),
    (r'\*', 'POR'),
    (r'/', 'DIV'),
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r'\{', 'LLAVE_IZQ'),
    (r'\}', 'LLAVE_DER'),
    (r';', 'PUNTO_COMA'),
    (r',', 'COMA'),
    (r'\s+', None),  # Ignorar espacios
    (r'\n+', None) # ignorar saltos de linea
]

# Clase para los tokens
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

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

# Clase del parser
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
            return  # λ (vacío)
        if self.tokens[self.current].type == 'VAR':
            self.D()
        elif self.tokens[self.current].type == 'ID':
            if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == 'ASIGNACION':
                self.A()
            else:
                self.L()
        elif self.tokens[self.current].type == 'IF':
            self.I()
        elif self.tokens[self.current].type == 'WHILE':
            self.W()
        elif self.tokens[self.current].type == 'FUNCTION':
            self.F()
        elif self.tokens[self.current].type == 'RETURN':
            self.R()
        else:
            return  # λ (vacío)

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

    def I(self):
        self.match('IF')
        self.match('LPAREN')
        self.E()
        self.O()
        self.E()
        self.match('RPAREN')
        self.B()
        if self.current < len(self.tokens) and self.tokens[self.current].type == 'ELSE':
            self.match('ELSE')
            self.B()

    def W(self):
        self.match('WHILE')
        self.match('LPAREN')
        self.E()
        self.O()
        self.E()
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
        self.N()
        while self.current < len(self.tokens) and self.tokens[self.current].type == 'COMA':
            self.match('COMA')
            self.N()

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
            if self.tokens[self.current].type == 'VAR':
                self.D()
            elif self.tokens[self.current].type == 'ID':
                if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == 'ASIGNACION':
                    self.A()
                else:
                    self.L()
            elif self.tokens[self.current].type == 'IF':
                self.I()
            elif self.tokens[self.current].type == 'WHILE':
                self.W()
            elif self.tokens[self.current].type == 'RETURN':
                self.R()
            else:
                raise SyntaxError("Estatuto esperado en bloque")

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
                self.N()
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

    def Y(self):
        if self.current < len(self.tokens) and self.tokens[self.current].type in ('ENTERO', 'DECIMAL'):
            self.current += 1
        else:
            raise SyntaxError("Número esperado")

from flask import Flask, render_template, request

# Configuración de Flask
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        code = request.form['code']
        try:
            tokens = lexer(code)
            parser = Parser(tokens)
            parser.S()
            if parser.current == len(tokens):
                result = "El código es sintácticamente correcto."
            else:
                result = "Error: Código incompleto o tokens sobrantes."
        except SyntaxError as e:
            result = f"Error sintáctico: {e}"
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)