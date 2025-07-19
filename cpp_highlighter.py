from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # C keywords
        self.c_keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
        ]

        # C++ keywords
        self.cpp_keywords = [
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'bitand', 'bitor', 'bool',
            'catch', 'class', 'compl', 'const_cast', 'constexpr', 'decltype', 'delete',
            'dynamic_cast', 'explicit', 'export', 'false', 'friend', 'inline', 'mutable',
            'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or',
            'or_eq', 'private', 'protected', 'public', 'reinterpret_cast', 'static_assert',
            'static_cast', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
            'typeid', 'typename', 'using', 'virtual', 'wchar_t', 'xor', 'xor_eq', 'concept',
            'requires', 'co_await', 'co_return', 'co_yield', 'consteval', 'constinit'
        ]

        # Control flow keywords (special highlighting)
        self.control_keywords = [
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break',
            'continue', 'return', 'goto', 'try', 'catch', 'throw', 'co_return', 'co_yield'
        ]

        # Built-in functions
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
            'cout', 'cin', 'cerr', 'clog', 'endl', 'flush', 'getline', 'push_back',
            'size', 'empty', 'clear', 'begin', 'end', 'find', 'insert', 'erase'
        ]

        # Built-in types
        self.builtin_types = [
            'size_t', 'ptrdiff_t', 'time_t', 'clock_t', 'FILE', 'wchar_t',
            'string', 'vector', 'list', 'deque', 'set', 'multiset', 'map', 'multimap',
            'unordered_set', 'unordered_multiset', 'unordered_map', 'unordered_multimap',
            'stack', 'queue', 'priority_queue', 'pair', 'tuple', 'array', 'bitset',
            'shared_ptr', 'unique_ptr', 'weak_ptr', 'auto_ptr', 'optional', 'variant',
            'iostream', 'istream', 'ostream', 'ifstream', 'ofstream', 'stringstream',
            'istringstream', 'ostringstream', 'iterator', 'const_iterator', 'reverse_iterator'
        ]

        # Primitive types
        self.primitive_types = [
            'bool', 'char', 'int', 'float', 'double', 'void', 'short', 'long',
            'signed', 'unsigned', 'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t'
        ]

        # Constants
        self.builtin_constants = [
            'true', 'false', 'nullptr', 'NULL', 'EOF', 'SEEK_SET', 'SEEK_CUR', 'SEEK_END',
            'EXIT_SUCCESS', 'EXIT_FAILURE', 'RAND_MAX', 'INT_MAX', 'INT_MIN',
            'CHAR_MAX', 'CHAR_MIN', 'UCHAR_MAX', 'SHRT_MAX', 'SHRT_MIN', 'USHRT_MAX',
            'LONG_MAX', 'LONG_MIN', 'ULONG_MAX', 'FLT_MAX', 'FLT_MIN', 'DBL_MAX', 'DBL_MIN'
        ]

        self.namespaces = ['std', 'boost', 'chrono', 'filesystem', 'ranges']
        self.formats = {
            'keyword': self._create_format(QColor("#5C2D91"), True),        # Deep Purple
            'control_keyword': self._create_format(QColor("#5C2D91"), True),
            'primitive_type': self._create_format(QColor("#005FB8"), True), # Dark Blue
            'builtin_type': self._create_format(QColor("#007C79")),         # Dark Teal
            'builtin_function': self._create_format(QColor("#C18401")),     # Dark Gold
            'constant': self._create_format(QColor("#0078D7")),             # Blue
            'namespace': self._create_format(QColor("#007C79")),            # Teal
            'string': self._create_format(QColor("#007000")),               # Dark Green
            'char': self._create_format(QColor("#007000")),
            'raw_string': self._create_format(QColor("#886600")),
            'comment': self._create_format(QColor("#008000"), italic=True),
            'comment_block': self._create_format(QColor("#008000"), italic=True),
            'comment_doc': self._create_format(QColor("#006400"), italic=True),
            'number': self._create_format(QColor("#175E54")),
            'preprocessor': self._create_format(QColor("#000080")),         # Navy
            'preprocessor_keyword': self._create_format(QColor("#8A2BE2")), # Blue Violet
            'operator': self._create_format(QColor("#333333")),
            'punctuation': self._create_format(QColor("#333333")),
            'bracket_round': self._create_format(QColor("#AA7700")),
            'bracket_curly': self._create_format(QColor("#8B008B")),
            'bracket_square': self._create_format(QColor("#1E90FF")),
            'bracket_angle': self._create_format(QColor("#2E8B57")),
            'class_name': self._create_format(QColor("#007C79"), True),
            'function_name': self._create_format(QColor("#C18401")),
            'function_call': self._create_format(QColor("#C18401")),
            'member_access': self._create_format(QColor("#0078D7")),
            'escape_sequence': self._create_format(QColor("#886600"), True),
            'macro': self._create_format(QColor("#800080")),
            'label': self._create_format(QColor("#5C2D91")),
            'attribute': self._create_format(QColor("#4169E1")),
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
        self._highlight_operators_and_punctuation(text)
        self._highlight_brackets(text)
        self._highlight_class_names(text)
        self._highlight_function_names(text)
        self._highlight_member_access(text)
        self._highlight_namespaces(text)
        self._highlight_labels(text)
        self._highlight_attributes(text)

    def _is_excluded(self, start, end=None):
        if end is None:
            end = start + 1
        return any(a <= start < b or a < end <= b or (start <= a and b <= end) 
                  for a, b in self._excluded_ranges)

    def _highlight_keywords(self, text):
        keyword_groups = [
            (self.control_keywords, 'control_keyword'),
            (self.c_keywords + self.cpp_keywords, 'keyword'),
            (self.primitive_types, 'primitive_type'),
            (self.builtin_types, 'builtin_type'),
            (self.builtin_functions, 'builtin_function'),
            (self.builtin_constants, 'constant')
        ]
        
        for keyword_list, fmt in keyword_groups:
            for word in keyword_list:
                pattern = rf'\b{re.escape(word)}\b'
                for match in re.finditer(pattern, text):
                    if not self._is_excluded(match.start(), match.end()):
                        self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])

    def _highlight_strings_and_chars(self, text):
        for match in re.finditer(r'R"([^(]*)\(.*?\)\1"', text, re.DOTALL):
            if not self._is_excluded(match.start(), match.end()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['raw_string'])
                self._excluded_ranges.append((match.start(), match.end()))

        # Regular strings and characters
        string_patterns = [
            (r'"(?:[^"\\]|\\.)*"', 'string'),  # Double quoted strings
            (r"'(?:[^'\\]|\\.)+'", 'char'),    # Single quoted characters (including multi-char)
            (r"'(?:[^'\\]|\\.)'", 'char')      # Single quoted single characters
        ]

        for pattern, fmt in string_patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start(), match.end()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])
                    self._excluded_ranges.append((match.start(), match.end()))
                    self._highlight_escape_sequences(text, match.start(), match.end())

    def _highlight_escape_sequences(self, text, start, end):

        escape_patterns = [
            r'\\[abfnrtv\\\'\"?]',  # Simple escapes
            r'\\[0-7]{1,3}',        # Octal escapes
            r'\\x[0-9a-fA-F]{1,2}', # Hex escapes
            r'\\u[0-9a-fA-F]{4}',   # Unicode escapes
            r'\\U[0-9a-fA-F]{8}',   # Extended Unicode escapes
            r'\\N\{[^}]+\}'         # Named Unicode escapes
        ]
        
        substring = text[start:end]
        for pattern in escape_patterns:
            for match in re.finditer(pattern, substring):
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
                is_doc_comment = start + 2 < len(text) and text[start + 2] in ['*', '!']
                fmt = 'comment_doc' if is_doc_comment else 'comment_block'
                
                end = text.find('*/', start + 2)
                if end == -1:
                    self.setFormat(start, len(text) - start, self.formats[fmt])
                    self.setCurrentBlockState(1)
                    self._excluded_ranges.append((start, len(text)))
                    return
                else:
                    self.setFormat(start, end - start + 2, self.formats[fmt])
                    self._excluded_ranges.append((start, end + 2))
                    start = text.find('/*', end + 2)
            else:
                start = text.find('/*', start + 1)

    def _highlight_line_comments(self, text):
        for match in re.finditer(r'//.*', text):
            if not self._is_excluded(match.start(), match.end()):

                comment_text = match.group()
                is_doc_comment = comment_text.startswith('///') or comment_text.startswith('//!')
                fmt = 'comment_doc' if is_doc_comment else 'comment'
                
                self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])
                self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_preprocessor(self, text):
        for match in re.finditer(r'^\s*#\s*(\w+)(.*)$', text, re.MULTILINE):
            if not self._is_excluded(match.start(), match.end()):

                directive_end = match.start(1) + len(match.group(1))
                self.setFormat(match.start(), directive_end - match.start(), self.formats['preprocessor_keyword'])

                if match.group(2):
                    self.setFormat(directive_end, len(match.group(2)), self.formats['preprocessor'])
                
                self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_numbers(self, text):
        number_patterns = [
            # Hexadecimal with suffixes
            r'\b0[xX][0-9a-fA-F]+(?:[uUlL]|[uU][lL]|[lL][uU])*\b',
            # Binary (C++14) with suffixes
            r'\b0[bB][01]+(?:[uUlL]|[uU][lL]|[lL][uU])*\b',
            # Octal with suffixes
            r'\b0[0-7]+(?:[uUlL]|[uU][lL]|[lL][uU])*\b',
            # Floating point with various formats
            r'\b\d+\.\d*(?:[eE][+-]?\d+)?[fFlL]?\b',
            r'\b\d*\.\d+(?:[eE][+-]?\d+)?[fFlL]?\b',
            r'\b\d+[eE][+-]?\d+[fFlL]?\b',
            # Decimal integers with suffixes
            r'\b\d+(?:[uUlL]|[uU][lL]|[lL][uU])*\b'
        ]
        
        for pattern in number_patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start(), match.end()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])

    def _highlight_operators_and_punctuation(self, text):
        # Operators
        operator_patterns = [
            r'<<|>>|<=|>=|==|!=|&&|\|\||[+\-*/]=|\+\+|--|->|\*=|/=|%=|&=|\|=|\^=|<<=|>>=',
            r'::|.*|<=>|and|or|not|bitand|bitor|xor|not_eq|and_eq|or_eq|xor_eq',
            r'[+\-*/%=<>!&|^~?]'
        ]
        
        for pattern in operator_patterns:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start(), match.end()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['operator'])

        for match in re.finditer(r'[;,.]', text):
            if not self._is_excluded(match.start(), match.end()):
                self.setFormat(match.start(), 1, self.formats['punctuation'])

    def _highlight_brackets(self, text):
        bracket_pairs = [
            (r'[()]', 'bracket_round'),
            (r'[{}]', 'bracket_curly'),
            (r'[\[\]]', 'bracket_square'),
        ]
        
        for pattern, fmt_name in bracket_pairs:
            for match in re.finditer(pattern, text):
                if not self._is_excluded(match.start(), match.end()):
                    self.setFormat(match.start(), 1, self.formats[fmt_name])
        
        for match in re.finditer(r'[<>]', text):
            if not self._is_excluded(match.start(), match.end()):
                before = text[:match.start()]
                after = text[match.end():]
                
                if (re.search(r'\btemplate\s*$', before) or 
                    re.search(r'\b\w+\s*$', before) and re.search(r'^\s*\w+', after) or
                    re.search(r'^\s*[,>]', after)):
                    self.setFormat(match.start(), 1, self.formats['bracket_angle'])

    def _highlight_class_names(self, text):
        for match in re.finditer(r'\b(?:class|struct|enum(?:\s+class)?)\s+([A-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['class_name'])

        for match in re.finditer(r'\b([A-Z][a-zA-Z0-9_]*)\s*(?:<|::)', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['class_name'])

    def _highlight_function_names(self, text):
        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                func_name = match.group(1)
                all_keywords = (self.c_keywords + self.cpp_keywords + self.control_keywords + 
                               self.primitive_types + self.builtin_types)
                if func_name not in all_keywords:
                    before = text[:match.start()].strip()
                    operator_chars = '=!<>+-*/&|^%'
                    if (
                        before.endswith(('return', 'if', 'while', 'for', '(', ',', '{', ';', '=', '!', '&&', '||')) or
                        not before or
                        before[-1] in operator_chars
                    ):
                        fmt = 'function_call'
                    else:
                        fmt = 'function_name'
                    self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats[fmt])

    def _highlight_member_access(self, text):
        for match in re.finditer(r'\.([a-zA-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['member_access'])
        
        for match in re.finditer(r'->([a-zA-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['member_access'])

    def _highlight_namespaces(self, text):
        for match in re.finditer(r'\bnamespace\s+([a-zA-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['namespace'])
        

        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)::', text):
            if not self._is_excluded(match.start(1), match.end(1)):
                namespace = match.group(1)
                if namespace in self.namespaces:
                    self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['namespace'])

    def _highlight_labels(self, text):
        for match in re.finditer(r'^([a-zA-Z_][a-zA-Z0-9_]*):(?!=)', text, re.MULTILINE):
            if not self._is_excluded(match.start(1), match.end(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['label'])

    def _highlight_attributes(self, text):
        for match in re.finditer(r'\[\[([^]]+)\]\]', text):
            if not self._is_excluded(match.start(), match.end()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['attribute'])
                self._excluded_ranges.append((match.start(), match.end()))