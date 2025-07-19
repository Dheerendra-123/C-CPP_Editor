from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import keyword
import re

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.python_keywords = keyword.kwlist

        self.builtin_functions = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print',
            'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
            'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        ]

        self.builtin_constants = ['True', 'False', 'None', 'Ellipsis', 'NotImplemented']

        self.builtin_exceptions = [
            'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
            'BlockingIOError', 'BrokenPipeError', 'BufferError', 'BytesWarning',
            'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError',
            'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
            'EOFError', 'Exception', 'FileExistsError', 'FileNotFoundError',
            'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'ImportError',
            'ImportWarning', 'IndentationError', 'IndexError', 'InterruptedError',
            'IsADirectoryError', 'KeyError', 'KeyboardInterrupt', 'LookupError',
            'MemoryError', 'ModuleNotFoundError', 'NameError', 'NotADirectoryError',
            'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning',
            'PermissionError', 'ProcessLookupError', 'RecursionError', 'ReferenceError',
            'RuntimeError', 'RuntimeWarning', 'StopAsyncIteration', 'StopIteration',
            'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError',
            'TimeoutError', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError',
            'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning',
            'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError'
        ]

        self.magic_methods = [
            '__init__', '__del__', '__repr__', '__str__', '__bytes__', '__format__',
            '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__hash__',
            '__bool__', '__getattr__', '__getattribute__', '__setattr__', '__delattr__',
            '__dir__', '__get__', '__set__', '__delete__', '__set_name__', '__init_subclass__',
            '__prepare__', '__instancecheck__', '__subclasscheck__', '__call__', '__len__',
            '__length_hint__', '__getitem__', '__setitem__', '__delitem__', '__missing__',
            '__iter__', '__reversed__', '__contains__', '__add__', '__sub__', '__mul__',
            '__matmul__', '__truediv__', '__floordiv__', '__mod__', '__divmod__', '__pow__',
            '__lshift__', '__rshift__', '__and__', '__xor__', '__or__', '__radd__',
            '__rsub__', '__rmul__', '__rmatmul__', '__rtruediv__', '__rfloordiv__',
            '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__',
            '__rand__', '__rxor__', '__ror__', '__iadd__', '__isub__', '__imul__',
            '__imatmul__', '__itruediv__', '__ifloordiv__', '__imod__', '__ipow__',
            '__ilshift__', '__irshift__', '__iand__', '__ixor__', '__ior__', '__neg__',
            '__pos__', '__abs__', '__invert__', '__complex__', '__int__', '__float__',
            '__index__', '__round__', '__trunc__', '__floor__', '__ceil__', '__enter__',
            '__exit__', '__await__', '__aiter__', '__anext__', '__aenter__', '__aexit__'
        ]

        self.formats = {
            'keyword': self._create_format(QColor("#DD34CF"), True),
            'builtin': self._create_format(QColor("#CB4A05")),
            'constant': self._create_format(QColor("#289CFA"), True),
            'exception': self._create_format(QColor("#1FA9F4")),
            'magic': self._create_format(QColor("#ADAD0E")),
            'string': self._create_format(QColor("#528839")),
            'comment': self._create_format(QColor("#A1A09E")),
            'number': self._create_format(QColor("#1E72E7")),
            'decorator': self._create_format(QColor("#F0CC02")),
            'operator': self._create_format(QColor("#C45F5F")),
            'bracket_round': self._create_format(QColor("#B9BABB"), True),
            'bracket_curly': self._create_format(QColor("#877903"), True),
            'bracket_square': self._create_format(QColor("#700276"), True),
            'class_name': self._create_format(QColor("#1DC5A3"), True),
            'function_name': self._create_format(QColor("#C8C839")),
            'self': self._create_format(QColor("#2FAAED")),
            'docstring': self._create_format(QColor("#62A443")),
            'f_string': self._create_format(QColor("#528839")),
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
        self._highlight_strings(text)
        self._highlight_comments(text)
        self._highlight_numbers(text)
        self._highlight_decorators(text)
        self._highlight_keywords(text)
        self._highlight_operators(text)
        self._highlight_brackets(text)
        self._highlight_class_names(text)
        self._highlight_function_names(text)
        self._highlight_self_cls(text)

    def _is_excluded(self, start):
        return any(a <= start < b for a, b in self._excluded_ranges)

    def _highlight_keywords(self, text):
        for keyword_list, fmt in [
            (self.python_keywords, 'keyword'),
            (self.builtin_functions, 'builtin'),
            (self.builtin_constants, 'constant'),
            (self.builtin_exceptions, 'exception'),
            (self.magic_methods, 'magic')
        ]:
            for word in keyword_list:
                pattern = rf'\b{re.escape(word)}\b'
                for match in re.finditer(pattern, text):
                    if not self._is_excluded(match.start()):
                        self.setFormat(match.start(), match.end() - match.start(), self.formats[fmt])

    def _highlight_strings(self, text):
        self.setCurrentBlockState(0)
        triple_single, triple_double = "'''", '"""'

        if self.previousBlockState() == 1:
            end = text.find(triple_single)
            if end == -1:
                end = text.find(triple_double)
            if end == -1:
                self.setFormat(0, len(text), self.formats['docstring'])
                self.setCurrentBlockState(1)
                self._excluded_ranges.append((0, len(text)))
                return
            else:
                self.setFormat(0, end + 3, self.formats['docstring'])
                self._excluded_ranges.append((0, end + 3))
                return

        for delim in [triple_single, triple_double]:
            start = text.find(delim)
            while start >= 0:
                end = text.find(delim, start + 3)
                if end == -1:
                    self.setFormat(start, len(text) - start, self.formats['docstring'])
                    self.setCurrentBlockState(1)
                    self._excluded_ranges.append((start, len(text)))
                    return
                else:
                    self.setFormat(start, end - start + 3, self.formats['docstring'])
                    self._excluded_ranges.append((start, end + 3))
                    start = text.find(delim, end + 3)

        f_patterns = [
            r'f"(?:[^"\\]|\\.)*"', r"f'(?:[^'\\]|\\.)*'",
            r'rf"(?:[^"\\]|\\.)*"', r"rf'(?:[^'\\]|\\.)*'",
            r'fr"(?:[^"\\]|\\.)*"', r"fr'(?:[^'\\]|\\.)*'"
        ]
        patterns = [
            r'r"(?:[^"\\]|\\.)*"', r"r'(?:[^'\\]|\\.)*'",
            r'"(?:[^"\\]|\\.)*"', r"'(?:[^'\\]|\\.)*'"
        ]

        for p in f_patterns:
            for match in re.finditer(p, text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['f_string'])
                self._excluded_ranges.append((match.start(), match.end()))

        for p in patterns:
            for match in re.finditer(p, text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['string'])
                self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_comments(self, text):
        for match in re.finditer(r'#.*', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['comment'])
            self._excluded_ranges.append((match.start(), match.end()))

    def _highlight_numbers(self, text):
        patterns = [
            r'\b0[xX][0-9a-fA-F]+\b', r'\b0[bB][01]+\b', r'\b0[oO][0-7]+\b',
            r'\b\d+\.\d*([eE][+-]?\d+)?\b', r'\b\d*\.\d+([eE][+-]?\d+)?\b',
            r'\b\d+[eE][+-]?\d+\b', r'\b\d+[jJ]\b', r'\b\d+\b'
        ]
        for p in patterns:
            for match in re.finditer(p, text):
                if not self._is_excluded(match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])

    def _highlight_decorators(self, text):
        for match in re.finditer(r'@\w+(\.\w+)*', text):
            if not self._is_excluded(match.start()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['decorator'])

    def _highlight_operators(self, text):
        patterns = [r'\+\+|--|==|!=|<=|>=|<<|>>|\*\*|//|->', r'[+\-*/%=<>!&|^~]']
        for p in patterns:
            for match in re.finditer(p, text):
                if not self._is_excluded(match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['operator'])

    def _highlight_brackets(self, text):
        for match in re.finditer(r'[\[\]{}()]', text):
            if not self._is_excluded(match.start()):
                char = match.group()
                fmt = None
                if char in '()':
                    fmt = self.formats['bracket_round']
                elif char in '{}':
                    fmt = self.formats['bracket_curly']
                elif char in '[]':
                    fmt = self.formats['bracket_square']
                if fmt:
                    self.setFormat(match.start(), 1, fmt)

    def _highlight_class_names(self, text):
        for match in re.finditer(r'\bclass\s+([A-Z][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['class_name'])

    def _highlight_function_names(self, text):
        for match in re.finditer(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)', text):
            if not self._is_excluded(match.start(1)):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['function_name'])

    def _highlight_self_cls(self, text):
        for match in re.finditer(r'\b(self|cls)\b', text):
            if not self._is_excluded(match.start()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['self'])
