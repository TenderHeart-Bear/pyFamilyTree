# pyFamilyTree

A Python-based family tree visualization tool with a modern GUI that generates beautiful, interactive family tree diagrams from Excel/XML data.

## Features

- **Modern GUI Interface**: User-friendly interface built with CustomTkinter
- **Excel Data Import**: Load family data directly from Excel files
- **Flexible Visualization**: Generate complete family trees or focused views
- **Diamond Union Structure**: Clean family tree layout with diamond nodes for marriages and circle nodes for children groups
- **Interactive Nodes**: Clickable family members with detailed information
- **Multiple Generations**: Support for ancestors and descendants with customizable depth
- **Zoom & Pan**: Full zoom and pan capabilities for large family trees
- **Export Options**: SVG, PNG, and PDF export formats
- **Smart Person Search**: Partial name matching for easy person lookup
- **Session Management**: Reload last dataset functionality

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/pyFamilyTree.git
cd pyFamilyTree
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Graphviz:
   - **Windows**: Download from [Graphviz's official website](https://graphviz.org/download/)
   - **Linux**: `sudo apt-get install graphviz`
   - **macOS**: `brew install graphviz`

## Usage

### GUI Mode (Recommended)
```bash
python main_gui.py
```

### Command Line Mode
```bash
python main.py
```

### Using the Application

1. **Load Data**: Click "Load Data" and select your Excel file and sheet
2. **Generate Tree**: Click "Generate Tree" to create visualizations
3. **Choose Options**:
   - **Complete Tree**: Generate entire family tree
   - **Focused View**: Specify a starting person and generation limits
4. **Navigate**: Use zoom and pan controls to explore large trees
5. **Export**: Save your trees in various formats

## Data Structure

### Excel Data Format
Your Excel file should contain columns for:
- **ID**: Unique identifier for each person
- **Name**: Full name
- **Birthday**: Birth date
- **Marriage_Date**: Wedding date (if applicable)
- **Died**: Death status or date
- **Father_ID**: Reference to father's ID
- **Mother_ID**: Reference to mother's ID
- **Spouse_ID**: Reference to spouse's ID

### XML Data Format
The tool converts Excel data to XML format with the following structure:
```xml
<character>
    <id>K001</id>
    <name>John Doe</name>
    <middle_name>William</middle_name>
    <birthday>Jan 15 1950</birthday>
    <marriage_date>Jun 20 1975</marriage_date>
    <spouse_id>K002</spouse_id>
    <father_id>K003</father_id>
    <mother_id>K004</mother_id>
</character>
```

## Project Structure
```
pyFamilyTree/
├── src/                      # Source code
│   ├── core/                 # Core functionality
│   │   ├── models/          # Data models
│   │   ├── interfaces/      # Interface definitions
│   │   └── path_manager.py  # Path management
│   ├── data/                # Data handling
│   │   ├── excel_converter.py
│   │   ├── xml_handler.py
│   │   └── xml_parser.py
│   ├── graph/               # Graph generation
│   │   ├── base.py
│   │   ├── family.py
│   │   └── embedded_family.py
│   └── ui/                  # User interface
│       ├── controllers/     # Application controllers
│       ├── views/          # GUI views
│       └── widgets/        # Custom widgets
├── assets/                  # Sample data files
├── tests/                   # Test files
├── config/                  # Configuration files
├── main.py                  # Main GUI entry point
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Configuration

Settings are stored in `config/settings.json` and include:
- **Appearance**: Theme and UI preferences
- **Graph**: Default generation limits
- **Export**: Format preferences and auto-export settings

## Sample Data

The project includes sample family data in the `assets/` directory:
- `FamilyTree_TestData/`: Generic test data
- Sample Excel files for testing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.

