from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.c_keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
        ]

        self.cpp_keywords = [
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'bitand', 'bitor', 'bool',
            'catch', 'class', 'compl', 'const_cast', 'constexpr', 'decltype', 'delete',
            'dynamic_cast', 'explicit', 'export', 'false', 'friend', 'inline', 'mutable',
            'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or',
            'or_eq', 'private', 'protected', 'public', 'reinterpret_cast', 'static_assert',
            'static_cast', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
            'typeid', 'typename', 'using', 'virtual', 'wchar_t', 'xor', 'xor_eq'
        ]

        self.builtin_functions = [
            'printf', 'scanf', 'sprintf', 'sscanf', 'fprintf', 'fscanf', 'fgets', 'fputs',
            'malloc', 'calloc', 'realloc', 'free', 'strlen', 'strcpy', 'strncpy', 'strcmp',
            'strncmp', 'strcat', 'strncat', 'strchr', 'strrchr', 'strstr', 'strtok',
            'memcpy', 'memmove', 'memset', 'memcmp', 'memchr', 'fopen', 'fclose', 'fread',
            'fwrite', 'fseek', 'ftell', 'rewind', 'fflush', 'getc', 'putc', 'getchar',
            'putchar', 'puts', 'gets', 'atoi', 'atof', 'atol', 'strtol', 'strtod',
            'rand', 'srand', 'exit', 'abort', 'atexit', 'system', 'getenv',
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh',
            'exp', 'log', 'log10', 'pow', 'sqrt', 'ceil', 'floor', 'fabs', 'fmod',
            'cout', 'cin', 'cerr', 'clog', 'endl', 'flush', 'getline'
        ]

        self.builtin_types = [
            'size_t', 'ptrdiff_t', 'time_t', 'clock_t', 'FILE', 'NULL',
            'string', 'vector', 'list', 'deque', 'set', 'multiset', 'map', 'multimap',
            'unordered_set', 'unordered_multiset', 'unordered_map', 'unordered_multimap',
            'stack', 'queue', 'priority_queue', 'pair', 'tuple', 'array',
            'shared_ptr', 'unique_ptr', 'weak_ptr', 'auto_ptr',
            'iostream', 'istream', 'ostream', 'ifstream', 'ofstream', 'stringstream',
            'istringstream', 'ostringstream', 'iterator', 'const_iterator'
        ]

        self.builtin_constants = [
            'true', 'false', 'nullptr', 'NULL', 'EOF', 'SEEK_SET', 'SEEK_CUR', 'SEEK_END',
            'EXIT_SUCCESS', 'EXIT_FAILURE', 'RAND_MAX', 'INT_MAX', 'INT_MIN',
            'CHAR_MAX', 'CHAR_MIN', 'UCHAR_MAX', 'SHRT_MAX', 'SHRT_MIN', 'USHRT_MAX',
            'LONG_MAX', 'LONG_MIN', 'ULONG_MAX', 'FLT_MAX', 'FLT_MIN', 'DBL_MAX', 'DBL_MIN'
        ]

        self.namespaces = ['std', 'boost']

        self.formats = {
            'keyword': self._create_format(QColor("#569CD6"), True),  # Blue
            'builtin': self._create_format(QColor("#4EC9B0")),  # Teal
            'type': self._create_format(QColor("#4EC9B0"), True),  # Teal bold
            'constant': self._create_format(QColor("#B5CEA8")),  # Light green
            'namespace': self._create_format(QColor("#4EC9B0")),  # Teal
            'string': self._create_format(QColor("#CE9178")),  # Orange
            'char': self._create_format(QColor("#CE9178")),  # Orange
            'comment': self._create_format(QColor("#6A9955")),  # Green
            'comment_block': self._create_format(QColor("#6A9955")),  # Green
            'number': self._create_format(QColor("#B5CEA8")),  # Light green
            'preprocessor': self._create_format(QColor("#9B9B9B")),  # Gray
            'operator': self._create_format(QColor("#D4D4D4")),  # Light gray
            'bracket_round': self._create_format(QColor("#FFD700"), True),  # Gold
            'bracket_curly': self._create_format(QColor("#DA70D6"), True),  # Orchid
            'bracket_square': self._create_format(QColor("#87CEEB"), True),  # Sky blue
            'bracket_angle': self._create_format(QColor("#FFA500"), True),  # Orange
            'class_name': self._create_format(QColor("#4EC9B0"), True),  # Teal bold
            'function_name': self._create_format(QColor("#DCDCAA")),  # Light yellow
            'escape_sequence': self._create_format(QColor("#D7BA7D")),  # Light orange
        }

        self._excluded_ranges = []

    def _create_format(self, color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(self, text):
        self.setFormat(0, len(text), QTextCharFormat())
        self._excluded_ranges = []
        self._highlight_block_comments(text)
        self._highlight_strings_and_chars(text)
        self._highlight_line_comments(text)
        self._highlight_preprocessor(text)
        self._highlight_numbers(text)
        self._highlight_keywords(text)
        self._highlight_operators(text)
        self._highlight_brackets(text)
        self._highlight_class_names(text)
        self._highlight_function_names(text)
        self._highlight_namespaces(text)

    def _is_excluded(self, start):
        return any(a <= start < b for a, b in self._excluded_ranges)

    def _highlight_keywords(self, text):
        all_keywords = self.c_keywords + self.cpp_keywords
        for keyword_list, fmt in [
            (all_keywords, 'keyword'),
            (self.builtin_functions, 'builtin'),
            (self.builtin_types, 'type'),
            (self.builtin_constants, 'constant')
        ]:
            for word in keyword_list:
                pattern = rf'\b{re.escape(word)}\b'
                for match in re.finditer(pattern, text):
                    if not self._is_excluded(match.start()):
                        self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])

    def _highlight_strings_and_chars(self, text):
        for match in re.finditer(r'R"([^(]*)\(.*?\)\1"', text, re.DOTALL):
            if not self._is_excluded(match.start()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['string'])
                self._excluded_ranges.append((match.start(), match.end()))

        patterns = [
            r'"(?:[^"\\]|\\.)*"',  # Double quoted strings
            r"'(?:[^'\\]|\\.)'"    # Single quoted characters
        ]

        for i, pattern in enumerate(patterns):
            fmt = 'string' if i == 0 else 'char'
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])
                    self._excluded_ranges.append((match.start(), match.end()))
                    self._highlight_escape_sequences(text, match.start(), match.end())

    def _highlight_escape_sequences(self, text, start, end):
        escape_pattern = r'\\(?:[abfnrtv\\\'\"?]|[0-7]{1,3}|x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})'
        substring = text[start:end]
        for match in re.finditer(escape_pattern, substring):
            abs_start = start + match.start()
            self.setFormat(abs_start, match.end() - match.start(), self.formats['escape_sequence'])

    def _highlight_block_comments(self, text):
        self.setCurrentBlockState(0)
        
        if self.previousBlockState() == 1:
            end = text.find('*/')
            if end == -1:
                self.setFormat(0, len(text), self.formats['comment_block'])
                self.setCurrentBlockState(1)
                self._excluded_ranges.append((0, len(text)))
                return
            else:
                self.setFormat(0, end + 2, self.formats['comment_block'])
                self._excluded_ranges.append((0, end + 2))

        start = text.find('/*')
        while start >= 0:
            if not self._is_excluded(start):
                end = text.find('*/', start + 2)
                if end == -1:
                    self.setFormat(start, len(text) - start, self.formats['comment_block'])
                    self.setCurrentBlockState(1)
                    self._excluded_ranges.append((start, len(text)))
                    return
                else:
                    self.setFormat(start, end - start + 2, self.formats['comment_block'])
                    self._excluded_ranges.append((start, end + 2))
                    start = text.find('/*', end + 2)
            else:
                start = text.find('/*', start + 1)

    def _highlight_line_comments(self, text):
        for match in re.finditer(r'//.*', text):
            if not self._is_excluded(match.start()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['comment'])
                self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_preprocessor(self, text):
        for match in re.finditer(r'^\s*#.*', text, re.MULTILINE):
            if not self._is_excluded(match.start()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['preprocessor'])
                self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_numbers(self, text):
        patterns = [
            # Hexadecimal
            r'\b0[xX][0-9a-fA-F]+[uUlL]*\b',
            # Binary (C++14)
            r'\b0[bB][01]+[uUlL]*\b',
            # Octal
            r'\b0[0-7]+[uUlL]*\b',
            # Floating point
            r'\b\d+\.\d*(?:[eE][+-]?\d+)?[fFlL]?\b',
            r'\b\d*\.\d+(?:[eE][+-]?\d+)?[fFlL]?\b',
            r'\b\d+[eE][+-]?\d+[fFlL]?\b',
            # Decimal integers
            r'\b\d+[uUlL]*\b'
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])

    def _highlight_operators(self, text):
        patterns = [
            r'<<|>>|<=|>=|==|!=|&&|\|\||[+\-*/]=|\+\+|--|->'
            r'|::|.*|\[\]',
            r'[+\-*/%=<>!&|^~?:;,.]'
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['operator'])

    def _highlight_brackets(self, text):
        bracket_patterns = [
            (r'[()]', 'bracket_round'),
            (r'[{}]', 'bracket_curly'),
            (r'[\[\]]', 'bracket_square'),
            (r'[<>]', 'bracket_angle')
        ]
        
        for pattern, fmt_name in bracket_patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start()):
                    if fmt_name == 'bracket_angle':
                        context = text[max(0, match.start()-10):match.end()+10]
                        if not re.search(r'template\s*<|<\s*\w+\s*>', context):
                            continue
                    self.setFormat(match.start(), 1, self.formats[fmt_name])

    def _highlight_class_names(self, text):
        for match in re.finditer(r'\b(?:class|struct)\s+([A-Z][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['class_name'])
        
        for match in re.finditer(r'\b([A-Z][a-zA-Z0-9_]*)\s*<', text):
            if not self._is_excluded(match.start(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['class_name'])

    def _highlight_function_names(self, text):
        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', text):
            if not self._is_excluded(match.start(1)):
                func_name = match.group(1)
                if func_name not in (self.c_keywords + self.cpp_keywords + self.builtin_types):
                    self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['function_name'])

    def _highlight_namespaces(self, text):
        for match in re.finditer(r'\bnamespace\s+([a-zA-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['namespace'])
        
        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)::', text):
            if not self._is_excluded(match.start(1)):
                namespace = match.group(1)
                if namespace in self.namespaces or namespace in ['std', 'boost']:
                    self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['namespace'])