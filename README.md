Analizador Léxico y Sintáctico:

    Descripción:
        Este proyecto implementa un analizador léxico y sintáctico básico en Python, utilizando expresiones regulares para tokenizar el código fuente y un conjunto de reglas gramaticales para validar su estructura. Además, cuenta con una interfaz web sencilla desarrollada con Flask, que permite al usuario ingresar código y recibir retroalimentación sobre su validez sintáctica.

    Autores:
        Isaac Abud León – A01801461
        Jaretzy Andrea Santiago Barragán – A01801092

    Entrega correspondiente a la Etapa 2: Analizador Sintáctico.

    Características del programa:
        Análisis léxico: reconoce palabras clave (var, if, while, etc.), identificadores, operadores, números, delimitadores, etc.
        Análisis sintáctico: valida que el código cumpla con reglas estructurales de un lenguaje imperativo básico.
        Soporte para estructuras comunes:
            Declaración de variables
            Asignaciones
            Condicionales (if, else)
            Ciclos (while)
            Funciones (definiciones, llamadas y return)
        Interfaz web: el usuario puede ingresar su código en un formulario y ver si es válido o no.

    ¿Cómo funciona?:
        Lexer: convierte el código fuente en una lista de tokens usando expresiones regulares.
        Parser: consume la lista de tokens e intenta validar la estructura usando una gramática definida en Python.
        Si el código es válido, se muestra un mensaje de éxito. Si hay errores, se especifica el tipo y posición del primer error.

    Tecnologías:
        Python 
        Flask (para la interfaz web)
        Expresiones regulares (re)
        HTML

    Ejemplo de uso:
        Código de entrada:
            var x = 10;
            function suma(a, b) {
                return a + b;
            }
            x = suma(2, 3);
        Resultado:
            ✅ El código es sintácticamente correcto.

    Errores comunes que detecta:
        Palabras mal escritas (retun en lugar de return)
        Estructura incorrecta (if sin paréntesis)
        Falta de punto y coma al final de una instrucción
        Uso incorrecto de operadores o delimitadores
        Llamadas a funciones sin paréntesis

    Estructura del proyecto:
        ├── analizador.py     # Contiene el programa completo
        ├── templates/
        │   └── index.html    # Interfaz web para el usuario
        └── README.md         # Documentación del proyecto
    
    Instrucciones para ejecutar
        1. Ir a la carpeta donde se tenga todo el proyecto
        2. Instala Flask:
            pip install flask
        3. Ejecuta la aplicación:
            python analizador.py
        4. Abre tu navegador y entra a:
            http://localhost:5000
        5. Ingresa tu código en el recuadro donde dice "Ingresa tu código aquí..."
        6. Da clic en el botón "Analizar"
        7. Observa tu código coloreado
        9. Al final observa el resultado del análisis 

    Notas adicionales: 
        Actualmente, los errores se muestran como excepciones con mensajes específicos que indican el token problemático.
        El diseño del parser está basado en un enfoque recursivo descendente.
        Este proyecto puede servir como base para implementar compiladores más avanzados o analizadores semánticos.