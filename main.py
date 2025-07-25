import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QAction,
    QTabWidget, QTextEdit, QSplitter, QVBoxLayout, QWidget,
    QMessageBox,QTreeView, QFileSystemModel,
    QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame,
    QCheckBox, QShortcut, QMenu, QInputDialog, QToolButton,QTextEdit,QStackedWidget,QTabBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject,QProcess,QThread
from PyQt5.QtGui import QKeySequence, QFont, QTextCharFormat, QTextCursor, QColor, QTextDocument,QFont,QIcon
from editor import CodeEditor
import subprocess
import psutil 
import time


def get_icon_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "resources", "cpp.ico")

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(get_icon_path()))

class OutputEmitter(QObject):
    output_signal = pyqtSignal(str)


def kill_process_using_file(file_path):
    killed = False
    for proc in psutil.process_iter(['pid', 'exe']):
        try:
            if proc.info['exe'] and proc.info['exe'].lower() == file_path.lower():
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return killed


class CppRunner(QThread):
    output_signal = pyqtSignal(str)
    process_created = pyqtSignal(str)  

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.output_signal.emit("Error: Please save the file first before running.\n")
            return

        file_ext = os.path.splitext(self.file_path)[1]
        if file_ext not in ['.c', '.cpp']:
            self.output_signal.emit("Error: Unsupported file type. Only .c and .cpp are supported.\n")
            return

        filename = os.path.basename(self.file_path)
        output_exe = self.file_path.replace(file_ext, '.exe')
        
        self.output_signal.emit(f"--- Compiling {filename} ---\n")

        if os.path.exists(output_exe):
            self.output_signal.emit("Stopping any running instances...\n")
            kill_process_using_file(output_exe)
            time.sleep(0.5)
            

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    os.remove(output_exe)
                    break
                except PermissionError:
                    if attempt < max_attempts - 1:
                        self.output_signal.emit(f"Waiting for file access... (attempt {attempt + 1})\n")
                        time.sleep(1)
                    else:
                        self.output_signal.emit(f"Warning: Could not delete old executable.\n")
                except Exception as e:
                    self.output_signal.emit(f"Error removing old executable: {e}\n")
                    break

        compiler = 'gcc' if file_ext == '.c' else 'g++'
        compile_cmd = [compiler, self.file_path, '-o', output_exe]
        
        self.output_signal.emit(f"Running: {' '.join(compile_cmd)}\n")
        self.output_signal.emit("\n")
        
        try:
            compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
            
            if compile_result.returncode != 0:
                self.output_signal.emit("--- Compilation Failed ---\n")
                self.output_signal.emit(compile_result.stderr)
                if compile_result.stdout:
                    self.output_signal.emit(compile_result.stdout)
                return
            else:
                self.output_signal.emit("--- Compilation Successful ---\n")
                self.output_signal.emit(" ")
                if compile_result.stdout:
                    self.output_signal.emit(compile_result.stdout)
                
        except subprocess.TimeoutExpired:
            self.output_signal.emit("Error: Compilation timed out.\n")
            return
        except Exception as e:
            self.output_signal.emit(f"Error during compilation: {e}\n")
            return
        if not os.path.exists(output_exe):
            self.output_signal.emit("Error: Executable was not created.\n")
            return

        self.output_signal.emit("\n")
        self.process_created.emit(output_exe)


class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                border: none;
                selection-background-color: #264f78;
            }
        """)
        font = QFont("Consolas", 12)
        self.setFont(font)
        
        self.command_buffer = ""
        self.runner = None
        self.running_program = False
        self.cpp_process = None
        
        self.setUndoRedoEnabled(False)

        self.process = QProcess(self)
        self.process.setProgram("cmd.exe")
        self.process.setWorkingDirectory(os.getcwd())
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_terminal_output)
        self.process.start()

    def start_cpp_process(self, exe_path):
        if self.cpp_process is not None:
            self.stop_cpp_process()
            
        self.cpp_process = QProcess(self)
        self.cpp_process.setProgram(exe_path)
        self.cpp_process.setWorkingDirectory(os.path.dirname(exe_path))
        self.cpp_process.setProcessChannelMode(QProcess.MergedChannels)

        self.cpp_process.readyReadStandardOutput.connect(self.read_cpp_output)
        self.cpp_process.finished.connect(self.on_cpp_finished)
        self.cpp_process.errorOccurred.connect(self.on_cpp_error)

        self.cpp_process.start()
        
        if self.cpp_process.waitForStarted(3000):
            self.append_output(" ")
        else:
            self.append_output("Error: Failed to start the executable.\n")
            self.running_program = False

    def read_cpp_output(self):
        try:
            if self.cpp_process and self.cpp_process.state() == QProcess.Running:
                output = self.cpp_process.readAllStandardOutput().data().decode("utf-8", errors='replace')
                if output:
                    self.append_output(output)
        except:
            pass

    def on_cpp_finished(self, exit_code, exit_status):
        self.running_program = False
        
        if exit_status == QProcess.NormalExit:
            if exit_code == 0:
                self.append_output("\n")
                self.append_output("\n--- Process finished successfully ---\n")
            else:
                self.append_output(f"\n--- Process finished with exit code: {exit_code} ---\n")
        else: 
            self.append_output("\n--- Process finished with exit code: {exit_code} ---\n")

    def on_cpp_error(self, error):
        self.running_program = False
        error_messages = {
            QProcess.FailedToStart: "Failed to start the executable",
            QProcess.Crashed: "Process crashed",
            QProcess.Timedout: "Process timed out",
            QProcess.WriteError: "Write error occurred",
            QProcess.ReadError: "Read error occurred",
            QProcess.UnknownError: "Unknown error occurred"
        }
        
        error_msg = error_messages.get(error, f"Process error: {error}")
        self.append_output(f"\n--- Error: {error_msg} ---\n")

    def stop_cpp_process(self):
        if self.cpp_process is not None:
            try:
                if self.cpp_process.state() == QProcess.Running:
                    self.cpp_process.write(b'\x03')

                    if not self.cpp_process.waitForFinished(500):
                        self.cpp_process.terminate()
                        if not self.cpp_process.waitForFinished(2000):
                            self.cpp_process.kill()
                            self.cpp_process.waitForFinished(1000)
                            
                self.cpp_process.deleteLater()
                self.cpp_process = None
            except Exception as e:
                print(f"Error stopping C++ process: {e}")
            finally:
                self.running_program = False

    def append_output(self, text):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def keyPressEvent(self, event):
        key = event.key()

        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.running_program and self.cpp_process:
                self.append_output("^C\n")
                self.stop_cpp_process()
                return

        if self.running_program and self.cpp_process and self.cpp_process.state() == QProcess.Running:
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                input_text = self.command_buffer
                try:
                    self.cpp_process.write((input_text + "\n").encode("utf-8"))
                    self.append_output(input_text + "\n")
                except:
                    pass
                self.command_buffer = ""
                return
            elif key in (Qt.Key_Backspace, Qt.Key_Delete):
                if self.command_buffer:
                    self.command_buffer = self.command_buffer[:-1]
                    cursor = self.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    cursor.deletePreviousChar()
                    self.setTextCursor(cursor)
                return
            else:
                text = event.text()
                if text and text.isprintable():
                    self.command_buffer += text
                    self.insertPlainText(text)
                return

        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.deletePreviousChar()
                self.setTextCursor(cursor)
            return
        
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            command = self.command_buffer.strip()
            if command:
                self.append_output("\n")
                if command.lower() in ['clear', 'cls']:
                    self.clear_terminal()
                else:
                    self.append_output("\n")
                    try:
                        self.process.write((command + "\n").encode("utf-8"))
                    except:
                        pass
            self.command_buffer = ""
            return
        
        text = event.text()
        if text and text.isprintable():
            self.command_buffer += text
            self.insertPlainText(text)

    def clear_terminal(self):
        self.clear()
        self.command_buffer = ""
        self.append_output(f"\n{os.getcwd()}> ")

    def change_working_directory(self, folder_path):
        if folder_path and os.path.exists(folder_path):
            try:
                drive = os.path.splitdrive(folder_path)[0]
                if drive:
                    self.process.write(f"{drive}\n".encode("utf-8"))
                    
                command = f'cd /d "{folder_path}"\n'
                self.process.write(command.encode("utf-8"))
                
                self.process.setWorkingDirectory(folder_path)
            except:
                pass

    def run_cpp_code(self, file_path):
        self.stop_all_processes()
            
        self.runner = CppRunner(file_path)
        self.runner.output_signal.connect(self.append_output)
        self.runner.process_created.connect(self.start_cpp_process)
        self.runner.finished.connect(self.on_runner_finished)
        self.runner.start()

    def on_runner_finished(self):
        try:
            if self.runner:
                self.runner.deleteLater()
                self.runner = None
        except:
            pass

    def stop_all_processes(self):
        if self.cpp_process is not None:
            try:
                if self.cpp_process.state() == QProcess.Running:
                    self.cpp_process.write(b'\x03') 

                    if not self.cpp_process.waitForFinished(500):
                        self.cpp_process.terminate()
                        if not self.cpp_process.waitForFinished(2000):
                            self.cpp_process.kill()
                            self.cpp_process.waitForFinished(1000)
                            
                self.cpp_process.deleteLater()
                self.cpp_process = None
            except Exception as e:
                print(f"Error stopping C++ process: {e}")
            finally:
                self.running_program = False

        if self.runner is not None:
            try:
                if self.runner.isRunning():
                    self.runner.requestInterruption()
                    self.runner.quit()

                    if not self.runner.wait(3000):
                        self.runner.terminate()
                        self.runner.wait(1000)
                        
                self.runner.deleteLater()
                self.runner = None
            except Exception as e:
                print(f"Error stopping runner thread: {e}")

    def read_terminal_output(self):
        try:
            if self.process and self.process.state() == QProcess.Running:
                output = self.process.readAllStandardOutput().data().decode("utf-8", errors='replace')
                if output:
                    self.append_output(output)
        except:
            pass

    def closeEvent(self, event):
        try:
            self.stop_all_processes()
            
            if hasattr(self, 'process') and self.process is not None:
                if self.process.state() == QProcess.Running:
                    try:
                        self.process.write(b'exit\n')
                        if not self.process.waitForFinished(1000):
                            self.process.terminate()
                            if not self.process.waitForFinished(2000):
                                self.process.kill()
                                self.process.waitForFinished(1000)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
        super().closeEvent(event)
        
    def stop_process(self):
        self.stop_all_processes() 


class FindReplaceWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ide = parent
        self.current_editor = None
        self.search_results = []
        self.current_result_index = -1
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 3px;
                font-size: 11px;
            }
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 3px 8px;
                font-size: 11px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QCheckBox {
                font-size: 11px;
            }
            QLabel {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(8, 5, 8, 5)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Find and Replace")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(23, 23)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                font-weight: bold;
                font-size: 14px;
                background-color: #ff4444;
                color: white;
            }
        """)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        find_layout = QHBoxLayout()
        find_layout.setSpacing(5)
        
        find_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.setFixedHeight(22)
        self.find_input.textChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.find_input)
        
        self.find_next_btn = QPushButton("↓")
        self.find_next_btn.setFixedSize(24, 22)
        self.find_next_btn.setToolTip("Find Next")
        self.find_next_btn.clicked.connect(self.find_next)
        find_layout.addWidget(self.find_next_btn)
        
        self.find_prev_btn = QPushButton("↑")
        self.find_prev_btn.setFixedSize(24, 22)
        self.find_prev_btn.setToolTip("Find Previous")
        self.find_prev_btn.clicked.connect(self.find_previous)
        find_layout.addWidget(self.find_prev_btn)
        
        self.match_case_cb = QCheckBox("Aa")
        self.match_case_cb.setToolTip("Match Case")
        self.match_case_cb.stateChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.match_case_cb)
        
        main_layout.addLayout(find_layout)
        
        replace_layout = QHBoxLayout()
        replace_layout.setSpacing(5)
        
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setFixedHeight(22)
        replace_layout.addWidget(self.replace_input)
        
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setFixedHeight(22)
        self.replace_btn.clicked.connect(self.replace_current)
        replace_layout.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setFixedHeight(22)
        self.replace_all_btn.clicked.connect(self.replace_all)
        replace_layout.addWidget(self.replace_all_btn)
        
        main_layout.addLayout(replace_layout)
        
        self.setLayout(main_layout)
        self.setFixedHeight(85)
        self.hide()
        
        self.find_input.returnPressed.connect(self.find_next)
        
    def show_for_editor(self, editor):
        self.current_editor = editor
        self.show()
        self.find_input.setFocus()
        
        cursor = editor.textCursor()
        if cursor.hasSelection():
            self.find_input.setText(cursor.selectedText())
        self.find_input.selectAll()
        
    def on_find_text_changed(self):
        if not self.current_editor:
            return
            
        find_text = self.find_input.text()
        if not find_text:
            self.clear_highlights()
            self.search_results = []
            return
            
        self.highlight_all_matches(find_text)
        
    def highlight_all_matches(self, find_text):
        if not self.current_editor:
            return
            
        self.clear_highlights()

        flags = QTextDocument.FindFlag(0)
        if self.match_case_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
            
        self.search_results = []
        cursor = self.current_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        extra_selections = []
        
        while True:
            cursor = self.current_editor.document().find(find_text, cursor, flags)
            if cursor.isNull():
                break

            self.search_results.append({
                'start': cursor.selectionStart(),
                'end': cursor.selectionEnd()
            })
            
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(255, 255, 0, 100)) 
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = highlight_format
            extra_selections.append(selection)
            
        self.current_editor.setExtraSelections(extra_selections)
        
        self.current_result_index = -1
            
    def clear_highlights(self):
        if self.current_editor:
            self.current_editor.setExtraSelections([])
            
    def find_next(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.move_to_result(self.current_result_index)
        
    def find_previous(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        self.move_to_result(self.current_result_index)
        
    def move_to_result(self, index):
        if not self.current_editor or index >= len(self.search_results):
            return
            
        result = self.search_results[index]
        
        cursor = self.current_editor.textCursor()
        cursor.setPosition(result['start'])
        cursor.setPosition(result['end'], QTextCursor.KeepAnchor)
        self.current_editor.setTextCursor(cursor)
        self.current_editor.ensureCursorVisible()
        
    def replace_current(self):
        if not self.current_editor:
            return
            
        cursor = self.current_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.on_find_text_changed() 
            
    def replace_all(self):
        if not self.current_editor:
            return
            
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        
        if not find_text:
            return
            
        text = self.current_editor.toPlainText()
        
        if self.match_case_cb.isChecked():
            new_text = text.replace(find_text, replace_text)
        else:
            import re
            new_text = re.sub(re.escape(find_text), replace_text, text, flags=re.IGNORECASE)
            
        self.current_editor.setPlainText(new_text)
        self.on_find_text_changed()  


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def drawBranches(self, painter, rect, index):
        pass
        
    def drawRow(self, painter, option, index):
        super().drawRow(painter, option, index)
        
        if self.model().hasChildren(index):
            branch_rect = self.visualRect(index)
            
            arrow_x = branch_rect.left() - 20
            arrow_y = branch_rect.top() + (branch_rect.height() // 2) - 6
            
            if self.isExpanded(index):
                arrow = "v"
            else:
                arrow = ">"

            painter.setPen(QColor("#666"))
            font = QFont("Consolas", 11)
            font.setBold(True) 
            painter.setFont(font) 
            painter.drawText(arrow_x, arrow_y + 11, arrow)


class FileExplorer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ide = parent
        self.terminal_widget = None 
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;")
        header.setFixedHeight(30)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 5, 8, 5)

        explorer_label = QLabel("EXPLORER")
        explorer_label.setFont(QFont("Arial", 9, QFont.Bold))
        explorer_label.setStyleSheet("color: #666; border: none;")
        header_layout.addWidget(explorer_label)
        header_layout.addStretch()

        add_file_btn = QToolButton()
        add_file_btn.setText("📄")
        add_file_btn.setToolTip("New File")
        add_file_btn.setFixedSize(20, 20)
        add_file_btn.clicked.connect(self.create_new_file)
        add_file_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        add_file_btn.setEnabled(False)  
        header_layout.addWidget(add_file_btn)

        add_folder_btn = QToolButton()
        add_folder_btn.setText("📁")
        add_folder_btn.setToolTip("New Folder")
        add_folder_btn.setFixedSize(20, 20)
        add_folder_btn.clicked.connect(self.create_new_folder)
        add_folder_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        add_folder_btn.setEnabled(False)  
        header_layout.addWidget(add_folder_btn)

        header.setLayout(header_layout)
        layout.addWidget(header)

        self.add_file_btn = add_file_btn
        self.add_folder_btn = add_folder_btn

        self.folder_name_label = QLabel()
        self.folder_name_label.setFont(QFont("Arial", 9))
        self.folder_name_label.setStyleSheet("color: #333; padding: 4px 8px; font-weight: bold;")
        self.folder_name_label.hide()  
        layout.addWidget(self.folder_name_label)

        self.stacked_widget = QStackedWidget()

        self.empty_view = QWidget()
        empty_layout = QVBoxLayout()
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_label = QLabel("No folder opened")
        empty_label.setFont(QFont("Arial", 12))
        empty_label.setStyleSheet("color: #888; font-style: italic;")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)

        instruction_text = QLabel("Use 'Select Folder' to open a folder\nto start working")
        instruction_text.setFont(QFont("Arial", 10))
        instruction_text.setStyleSheet("color: #aaa; margin-top: 8px;")
        instruction_text.setAlignment(Qt.AlignCenter)
        instruction_text.setWordWrap(True)
        empty_layout.addWidget(instruction_text)
        
        self.empty_view.setLayout(empty_layout)
        self.empty_view.setStyleSheet("background-color: #fafafa;")
        
        self.tree = CustomTreeView()
        self.model = QFileSystemModel()
        self.tree.setModel(self.model)
        
        self.tree.hideColumn(1) 
        self.tree.hideColumn(2)  
        self.tree.hideColumn(3)  
        self.tree.header().hide()  

        self.tree.setStyleSheet("""
            QTreeView {
                border: none;
                background-color: #fafafa;
                alternate-background-color: #f5f5f5;
                font-size: 18px;
            }
            QTreeView::item {
                padding: 2px 6px;
                border: none;
                height: 20px;
                padding-bottom: 4px;
            }
            QTreeView::item:selected {
                background-color: none;
                color: black;
            }
            QTreeView::item:hover {
                background-color: #e5e5e5;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings,
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
                background: transparent;
            }
        """)

        self.tree.doubleClicked.connect(self.on_file_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        self.stacked_widget.addWidget(self.empty_view)
        self.stacked_widget.addWidget(self.tree)
        
        self.stacked_widget.setCurrentWidget(self.empty_view)
        
        layout.addWidget(self.stacked_widget)

        footer = QFrame()
        footer.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #d0d0d0;")
        footer.setFixedHeight(38)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(9, 6, 9, 6)

        select_folder_btn = QPushButton("📁 Select Folder")
        select_folder_btn.setFixedHeight(24)
        select_folder_btn.clicked.connect(self.select_folder)
        select_folder_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                padding: 4px 10px;
                font-size: 15px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        footer_layout.addWidget(select_folder_btn)

        footer.setLayout(footer_layout)
        layout.addWidget(footer)

        self.setLayout(layout)
        
        self.current_folder = None

    def set_terminal_widget(self, terminal_widget):
        """Set the terminal widget reference"""
        self.terminal_widget = terminal_widget

    def update_folder_name(self, path):
        folder_name = os.path.basename(path)
        if not folder_name:
            folder_name = path 
        self.folder_name_label.setText(folder_name)

    def create_new_file(self):
        if not self.current_folder:
            return

        current_path = self.model.rootPath()
        name, ok = QInputDialog.getText(self, "New File", "Enter file name (with .c/.cpp/.h):")
        if ok and name:
            if not name.endswith(('.c', '.cpp', '.h')):
                name += '.cpp'  

            file_path = os.path.join(current_path, name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.parent_ide.open_file_by_path(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file: {str(e)}")

    def create_new_folder(self):
        if not self.current_folder:
            return
            
        current_path = self.model.rootPath()
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            folder_path = os.path.join(current_path, name)
            try:
                os.makedirs(folder_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")

    def select_folder_programmatically(self, folder):
        self.current_folder = folder
        self.model.setRootPath(folder)
        self.tree.setRootIndex(self.model.index(folder))
        self.update_folder_name(folder)
        
        self.stacked_widget.setCurrentWidget(self.tree)
        self.folder_name_label.show()
        
        self.add_file_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        
        if self.terminal_widget:
            self.terminal_widget.change_working_directory(folder)

    def show_context_menu(self, position):
        if not self.current_folder:
            return
            
        index = self.tree.indexAt(position)
        menu = QMenu()

        if index.isValid():
            file_path = self.model.filePath(index)
            if os.path.isfile(file_path):
                open_action = menu.addAction("Open")
                open_action.triggered.connect(lambda: self.parent_ide.open_file_by_path(file_path))

            menu.addSeparator()
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self.delete_item(file_path))

        menu.addAction("New File", self.create_new_file)
        menu.addAction("New Folder", self.create_new_folder)

        menu.exec_(self.tree.mapToGlobal(position))

    def delete_item(self, path):
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {os.path.basename(path)}?",
         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    import shutil
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {str(e)}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.select_folder_programmatically(folder)

    def on_file_double_click(self, index):
        if not self.current_folder:
            return
            
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.parent_ide.open_file_by_path(file_path)


class CustomTabBar(QTabBar):
    def __init__(self, tab_widget=None):
        super().__init__()
        self.tab_widget = tab_widget
    
    def tabInserted(self, index):
        super().tabInserted(index)
        close_btn = QPushButton("x")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton {
                color: red;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        if self.tab_widget:
            close_btn.clicked.connect(lambda _, i=index: self.tab_widget.tabCloseRequested.emit(i))
        self.setTabButton(index, QTabBar.RightSide, close_btn)




class PythonIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C/C++ Code Editor")
        self.setWindowIcon(QIcon(get_icon_path())) 
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()
        self.init_menu()
        self.init_shortcuts()  
        self.open_files = {}
        self.file_explorer.set_terminal_widget(self.terminal)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)   
        main_splitter = QSplitter(Qt.Horizontal)    
        self.file_explorer = FileExplorer(self)
        self.file_explorer.setFixedWidth(250)
        main_splitter.addWidget(self.file_explorer)
        
        right_splitter = QSplitter(Qt.Vertical)
  
        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        self.find_replace_widget = FindReplaceWidget(self)
        editor_layout.addWidget(self.find_replace_widget)
        
      
        tab_bar_layout = QHBoxLayout()
        tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        tab_bar_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBar(CustomTabBar(self.tab_widget)) 
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self.tab_bar = self.tab_widget.tabBar()
        font = QFont("Consolas", 9)  
        self.tab_bar.setFont(font)
                
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(40, 32)
        self.add_tab_button.clicked.connect(self.create_new_tab)
        self.add_tab_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
                font-size: 16px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

        close_icon_path = "resources/close.png"
        close_icon_style = ""
        if os.path.exists(close_icon_path):
            close_icon_style = f"image: url({close_icon_path});"
        else:
          close_icon_style = """
            color: red;
            font-size: 14px;
            font-weight: bold;
            border: none;
            background: transparent;
            qproperty-text: "×";
        """
        
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #d0d0d0;
                background-color: white;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 8px 16px;
                font-size: 16px; 
                margin-right: 0px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
            }}
            QTabBar::tab:hover {{
                background-color: #e0e0e0;
            }}
            QTabBar::close-button {{
                {close_icon_style}
                subcontrol-position: right;
                margin-left: 4px;
                width: 14px;
                height: 14px;
            }}
            QTabBar::close-button:hover {{
                background-color: #d0d0d0;
            }}
            QTabBar::close-button:pressed {{
                background-color: #c0c0c0;
            }}
        """)

        tab_header_container = QWidget()
        tab_header_layout = QHBoxLayout()
        tab_header_layout.setContentsMargins(0, 0, 0, 0)
        tab_header_layout.setSpacing(0)
        
        tab_header_layout.addWidget(self.tab_bar)
        tab_header_layout.addWidget(self.add_tab_button)
        tab_header_layout.addStretch()
        tab_header_container.setLayout(tab_header_layout)
        
        self.tab_content_widget = QStackedWidget()
        
        editor_layout.addWidget(tab_header_container)
        editor_layout.addWidget(self.tab_content_widget)

        self.tab_bar.currentChanged.connect(self.tab_content_widget.setCurrentIndex)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        editor_container.setLayout(editor_layout)
        right_splitter.addWidget(editor_container)
        
        self.terminal = TerminalWidget(self)
        right_splitter.addWidget(self.terminal)
        
        right_splitter.setSizes([600, 200])
        
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([250, 950])
        
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
        
        self.create_new_tab()
        
    def init_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.create_new_tab)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu('Edit')
        
        find_action = QAction('Find and Replace', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)
        
        run_menu = menubar.addMenu('Run')
        
        run_action = QAction('Run', self)
        run_action.setShortcut('Ctrl+R')
        run_action.triggered.connect(self.run_current_file)
        run_menu.addAction(run_action)
        
    def init_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+T"), self, self.create_new_tab)
        QShortcut(QKeySequence("Escape"), self, self.hide_find_replace)
        
    def is_untitled_empty(self, editor):
        return (not hasattr(editor, 'file_path') or editor.file_path is None) and \
               editor.toPlainText().strip() == ""
        
    def create_new_tab(self, file_path=None, content=""):
        editor = CodeEditor()
        editor.setPlainText(content)
        
        if file_path:
            tab_name = os.path.basename(file_path)
            tab_index = self.tab_bar.addTab(tab_name)
            self.open_files[file_path] = tab_index
            editor.file_path = file_path
        else:
            tab_index = self.tab_bar.addTab("*untitled")
            editor.file_path = None
        
        content_index = self.tab_content_widget.addWidget(editor)
        
        self.tab_bar.setCurrentIndex(tab_index)
        self.tab_content_widget.setCurrentIndex(content_index)
        editor.setFocus()
        
        editor.textChanged.connect(lambda: self.mark_tab_modified(editor))
        
        return editor
        
    def mark_tab_modified(self, editor):
        content_index = self.tab_content_widget.indexOf(editor)
        if content_index != -1:
            tab_index = content_index
            if tab_index < self.tab_bar.count():
                current_text = self.tab_bar.tabText(tab_index)
                if not current_text.endswith('*'):
                    self.tab_bar.setTabText(tab_index, current_text + '*')
                
    def remove_modified_indicator(self, editor):
        content_index = self.tab_content_widget.indexOf(editor)
        if content_index != -1:
            tab_index = content_index
            if tab_index < self.tab_bar.count():
                current_text = self.tab_bar.tabText(tab_index)
                if current_text.endswith('*'):
                    self.tab_bar.setTabText(tab_index, current_text[:-1])
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "C/C++ Files (*.c *.cpp *.h);;All Files (*)"
        )
        if file_path:
            self.open_file_by_path(file_path)
            
    def open_file_by_path(self, file_path):
        if file_path in self.open_files:
            tab_index = self.open_files[file_path]
            self.tab_bar.setCurrentIndex(tab_index)
            self.tab_content_widget.setCurrentIndex(tab_index)
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                current_index = self.tab_content_widget.currentIndex()
                if current_index >= 0:
                    current_editor = self.tab_content_widget.widget(current_index)
                    if current_editor and self.is_untitled_empty(current_editor):
                        current_editor.setPlainText(content)
                        current_editor.file_path = file_path
                        
                        tab_name = os.path.basename(file_path)
                        self.tab_bar.setTabText(current_index, tab_name)
                        
                        self.open_files[file_path] = current_index
                        self.remove_modified_indicator(current_editor)
                        current_editor.setFocus()
                        return
                
                editor = self.create_new_tab(file_path, content)
                self.remove_modified_indicator(editor)
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
            
    def save_file(self):
        current_index = self.tab_content_widget.currentIndex()
        if current_index >= 0:
            current_editor = self.tab_content_widget.widget(current_index)
            if current_editor:
                if hasattr(current_editor, 'file_path') and current_editor.file_path:
                    self.save_file_to_path(current_editor, current_editor.file_path)
                else:
                    self.save_file_as()
                
    def save_file_as(self):
        current_index = self.tab_content_widget.currentIndex()
        if current_index >= 0:
            current_editor = self.tab_content_widget.widget(current_index)
            if current_editor:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save File",
                    "",
                    "C/C++ Files (*.c *.cpp *.h);;All Files (*)"
                )
                if file_path:
                    self.save_file_to_path(current_editor, file_path)
                
    def save_file_to_path(self, editor, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(editor.toPlainText())
            
            content_index = self.tab_content_widget.indexOf(editor)
            if content_index != -1:
                tab_name = os.path.basename(file_path)
                self.tab_bar.setTabText(content_index, tab_name)
                
                if hasattr(editor, 'file_path') and editor.file_path in self.open_files:
                    del self.open_files[editor.file_path]
                
                editor.file_path = file_path
                self.open_files[file_path] = content_index
                
                self.remove_modified_indicator(editor)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
            
    def close_tab(self, tab_index):
        if tab_index >= self.tab_content_widget.count():
            return
            
        editor = self.tab_content_widget.widget(tab_index)
        
        tab_text = self.tab_bar.tabText(tab_index)
        if tab_text.endswith('*'):
            reply = QMessageBox.question(
                self, "Unsaved Changes", 
                f"'{tab_text[:-1]}' has unsaved changes. Do you want to save?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return

        if hasattr(editor, 'file_path') and editor.file_path in self.open_files:
            del self.open_files[editor.file_path]
        
        for file_path, index in self.open_files.items():
            if index > tab_index:
                self.open_files[file_path] = index - 1
        self.tab_bar.removeTab(tab_index)
        self.tab_content_widget.removeWidget(editor)
        editor.deleteLater()
        
        if self.tab_bar.count() == 0:
            self.create_new_tab()
            
    def close_current_tab(self):
        current_index = self.tab_bar.currentIndex()
        if current_index != -1:
            self.close_tab(current_index)
            
    def show_find_replace(self):
        current_index = self.tab_content_widget.currentIndex()
        if current_index >= 0:
            current_editor = self.tab_content_widget.widget(current_index)
            if current_editor:
                self.find_replace_widget.show_for_editor(current_editor)
            
    def hide_find_replace(self):
        self.find_replace_widget.hide()
        
    def run_current_file(self):
        current_index = self.tab_content_widget.currentIndex()
        if current_index >= 0:
            current_editor = self.tab_content_widget.widget(current_index)
            if current_editor:
                file_path = getattr(current_editor, 'file_path', None)
                if file_path and os.path.exists(file_path):
                    self.terminal.run_cpp_code(file_path)
                else:
                    self.append_output("Please save the file before running.\n")
    
    def closeEvent(self, event):
        try:
            if hasattr(self, 'terminal') and self.terminal:
                if hasattr(self.terminal, 'stop_process') and callable(self.terminal.stop_process):
                    self.terminal.stop_process()

                QApplication.processEvents()

                if hasattr(self.terminal, 'process') and self.terminal.process:
                    process = self.terminal.process

                    if process.state() == QProcess.Running:
                        try:
                            process.write(b'exit\n')

                            if not process.waitForFinished(1000):
                                print("Sending terminate signal to terminal process...")
                                process.terminate()

                                if not process.waitForFinished(3000):
                                    print("Terminal process didn't terminate gracefully, forcing kill...")
                                    process.kill()
                                    process.waitForFinished(1000)
                                else:
                                    print("Terminal process terminated gracefully")
                            else:
                                print("Terminal process exited normally")
                        
                        except Exception as write_error:
                            print(f"Could not send exit command: {write_error}, proceeding with terminate...")
                            process.terminate()
                            if not process.waitForFinished(3000):
                                print("Process didn't terminate gracefully, forcing kill...")
                                process.kill()
                                process.waitForFinished(1000)

                    try:
                        process.deleteLater()
                    except RuntimeError as e:
                        print(f"Process already deleted: {e}")

                    self.terminal.process = None

        except Exception as e:
            print(f"Error during cleanup: {e}")

            try:
                if (hasattr(self, 'terminal') and self.terminal and 
                    hasattr(self.terminal, 'process') and self.terminal.process):
                    if self.terminal.process.state() == QProcess.Running:
                        print("Emergency cleanup: force killing terminal process")
                        self.terminal.process.kill()
                        self.terminal.process.waitForFinished(500)
            except Exception as emergency_error:
                print(f"Emergency cleanup failed: {emergency_error}")
        
        finally:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ide = PythonIDE()
    ide.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()