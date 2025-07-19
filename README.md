# 🧠 C/C++ IDE

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

A lightweight, modern, and customizable IDE for C and C++ development, built entirely with **Python** and **PyQt5**. Features a multi-tab editor, integrated terminal, syntax highlighting, autocompletion, and support for compiling and running C/C++ code — all in a clean and minimal interface.

![IDE Screenshot](docs/screenshot.png)

## ✨ Features

### 📝 **Editor**
- Multi-tab editor with drag-and-drop support
- Syntax highlighting for C and C++ code
- Intelligent autocompletion with Jedi integration
- Auto bracket and quote completion
- Line numbers and code folding
- Find and replace functionality

### 🔧 **Development Tools**
- One-click compile and run for C/C++ files
- Integrated terminal with full shell access
- Real-time output window with execution logs
- Smart error and warning parsing from GCC/G++

### 📁 **Project Management**
- Built-in file explorer with tree view
- Project folder support with workspace management
- File templates for quick project setup


## 📦 Installation

### Prerequisites

Before installing, make sure you have:

- **Python 3.8+** (Python 3.11+ recommended)
- **GCC/G++** compiler installed and accessible via PATH
- **Git** (optional, for version control features)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/cpp-ide.git
cd cpp-ide

# Install dependencies
pip install -r requirements.txt

# Run the IDE
python main.py
```

### Manual Installation

1. **Install PyQt5:**
   ```bash
   pip install pyqt5 pyqt5-tools
   ```

2. **Install additional dependencies:**
   ```bash
   pip install jedi pygments psutil
   ```

3. **Download and run:**
   ```bash
   python main.py
   ```

## 🚀 Quick Start

1. **Launch the IDE:**
   ```bash
   python main.py
   ```

2. **Create a new file:**
   - `Ctrl+N` for new file
   - Choose C/C++ template

3. **Write and compile:**
   ```cpp
   #include <iostream>
   using namespace std;
   
   int main() {
       cout << "Hello, World!" << endl;
       return 0;
   }
   ```

4. **Compile and run:**
   - `Ctrl+R` to compile and run

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.8+ | 3.11+ |
| **RAM** | 512MB | 2GB+ |
| **Disk Space** | 100MB | 500MB+ |
| **OS** | Windows 7+, macOS 10.12+, Linux | Latest versions |

## ⚙️ Configuration

The IDE can be configured through `config/settings.json`:

```json
{
    "editor": {
        "font_family": "Consolas",
        "font_size": 12,
        "tab_width": 4,
        "theme": "dark"
    },
    "compiler": {
        "c_compiler": "gcc",
        "cpp_compiler": "g++",
        "flags": ["-Wall", "-std=c++17"]
    }
}
```

## 🔧 Building from Source

### Development Setup

```bash
# Clone repository
git clone https://github.com/Dheerendra-123/C-CPP_IDE.git
cd cpp-ide

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
python main.py --dev
```

### Creating Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --windowed --onefile --name "CPP-IDE" main.py

# Executable will be in dist/ folder
```

## 🎯 Usage Examples

### Basic Workflow

1. **Create Project:**
   ```
   File → New Project → C++ Console Application
   ```

2. **Write Code:**
   ```cpp
   #include <vector>
   #include <algorithm>
   #include <iostream>
   
   int main() {
       std::vector<int> numbers = {3, 1, 4, 1, 5, 9};
       std::sort(numbers.begin(), numbers.end());
       
       for (int num : numbers) {
           std::cout << num << " ";
       }
       return 0;
   }
   ```

3. **Compile & Run:**
   - Use toolbar buttons or keyboard shortcuts
   - View output in integrated terminal


## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Generate coverage report
python -m pytest --cov=src tests/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Guidelines

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes** with proper tests
4. **Run the test suite:** `pytest`
5. **Commit your changes:** `git commit -m 'Add amazing feature'`
6. **Push to the branch:** `git push origin feature/amazing-feature`
7. **Open a Pull Request**



See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyQt5** - GUI framework
- **Jedi** - Code completion library
- **Pygments** - Syntax highlighting
- **GCC/G++** - Compilation toolchain

v

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/cpp-ide&type=Date)](https://star-history.com/#yourusername/cpp-ide&Date)

---

<p align="center">
  Made with ❤️ by the C/C++ IDE team
</p>

<p align="center">
  <a href="#-cc-ide">Back to top</a>
</p>