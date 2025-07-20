from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QCompleter, QWidget,QAction
from PyQt5.QtGui import QTextCursor, QFont, QPainter, QColor, QTextFormat,QKeySequence
from PyQt5.QtCore import Qt, QStringListModel, QRect, QSize
import re


from cpp_highlighter import CppHighlighter  


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.codeEditor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFont(QFont("Consolas", 12))
        self.highlighter = CppHighlighter(self.document())

        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        self.completer = QCompleter()
        self.completer.setModel(QStringListModel())
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)
        self.setup_completer_style()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        run_action = QAction("▶ Compile and Run", self)
        run_action.setShortcut(QKeySequence("Ctrl+R")) 
        font = QFont()
        font.setPointSize(10)  
        run_action.setFont(font)
        main_win = self.window()
        if hasattr(main_win, 'run_current_file'):
            run_action.triggered.connect(main_win.run_current_file)
        menu.insertAction(menu.actions()[0], run_action)
        menu.exec_(event.globalPos())

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.darkGray)
                painter.drawText(0, top, self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlight_current_line(self):
        if self.isReadOnly():
            return
        selection = QTextEdit.ExtraSelection()
        lineColor = QColor("#e0f7fa")
        selection.format.setBackground(lineColor)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def setup_completer_style(self):
        popup = self.completer.popup()
        popup.setStyleSheet("""
            QListView {
                border: 1px solid #3e3e42;
                color: black;
                selection-background-color: #289CFA;
                selection-color: #ffffff;
                outline: none;
                font-family: Consolas;
                font-size: 16px;
                padding: 1px;
            }
            QListView::item {
                padding: 4px 10px;
                border: none;
                border-radius: 2px;
                margin: 1px;
            }
            QListView::item:hover:!selected {
                background-color: wheat;
                color: black;
            }
            QListView::item:selected {
                background-color: #289CFA;
                color: white;
            }
            QListView::item:selected:hover {
                background-color: #1177bb;
                color: white;
            }
            QScrollBar:vertical {
                background-color: #2d2d30;
                border: none;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        popup.setMaximumHeight(200)
        popup.setMinimumWidth(150)

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, extra)
        tc.insertText(completion)
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def update_completions(self):
        code = self.toPlainText()
        
        # C/C++ keywords and common functions
        cpp_keywords = [
            # C keywords
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while',
            
            # C++ keywords
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'bitand', 'bitor', 'bool',
            'catch', 'class', 'compl', 'const_cast', 'constexpr', 'decltype', 'delete',
            'dynamic_cast', 'explicit', 'export', 'false', 'friend', 'inline', 'mutable',
            'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or',
            'or_eq', 'private', 'protected', 'public', 'reinterpret_cast', 'static_assert',
            'static_cast', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
            'typeid', 'typename', 'using', 'virtual', 'wchar_t', 'xor', 'xor_eq',
            
            # Standard library functions
            'printf', 'scanf', 'malloc', 'free', 'strlen', 'strcpy', 'strcmp', 'strcat',
            'memcpy', 'memset', 'fopen', 'fclose', 'fread', 'fwrite', 'fprintf', 'fscanf',
            'cout', 'cin', 'endl', 'std', 'vector', 'string', 'map', 'set', 'list',
            'queue', 'stack', 'pair', 'make_pair', 'sort', 'find', 'push_back', 'size',
            'empty', 'begin', 'end', 'insert', 'erase', 'clear'
        ]
        
        suggestions = set(cpp_keywords)
        
        # Extract variable names (simple heuristic)
        suggestions.update(re.findall(r'\b(?:int|float|double|char|bool|string|auto)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code))
        
        # Extract function names
        suggestions.update(re.findall(r'\b(?:int|float|double|char|bool|void|string|auto)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code))
        
        # Extract class names
        suggestions.update(re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', code))
        
        # Extract struct names
        suggestions.update(re.findall(r'struct\s+([a-zA-Z_][a-zA-Z0-9_]*)', code))
        
        # Extract namespace names
        suggestions.update(re.findall(r'namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)', code))
        
        # Extract #include headers (without angle brackets or quotes)
        suggestions.update(re.findall(r'#include\s*[<"]\s*([a-zA-Z0-9_\.]+)\s*[>"]', code))
        
        # Extract #define macros
        suggestions.update(re.findall(r'#define\s+([a-zA-Z_][a-zA-Z0-9_]*)', code))
        
        # Extract enum values
        enum_matches = re.findall(r'enum\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?\s*\{([^}]+)\}', code)
        for enum_body in enum_matches:
            enum_values = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', enum_body)
            suggestions.update(enum_values)
        
        suggestions = sorted([s for s in suggestions if s and len(s) > 1])
        self.completer.model().setStringList(suggestions)


    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                event.ignore()
                return
            elif event.key() == Qt.Key_Escape:
                self.completer.popup().hide()
                return
            elif event.key() in (Qt.Key_Up, Qt.Key_Down):
                event.ignore()
                return

        char = event.text()
        pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
        if char in pairs:
            cursor = self.textCursor()
            cursor.insertText(char + pairs[char])
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        super().keyPressEvent(event)

        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        completion_prefix = tc.selectedText()

        if len(completion_prefix) >= 1 and (completion_prefix.isalnum() or '_' in completion_prefix):
            self.update_completions()
            self.completer.setCompletionPrefix(completion_prefix)
            rect = self.cursorRect()
            rect.setWidth(
                self.completer.popup().sizeHintForColumn(0) +
                self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)
        else:
            self.completer.popup().hide()