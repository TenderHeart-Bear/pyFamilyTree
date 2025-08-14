# Family Tree Visualizer - Web Version

A modern web-based family tree visualization tool that can work offline. This web application provides an intuitive interface for visualizing and exploring family relationships through interactive diagrams.

## 🌟 Features

- **Web-based Interface**: Modern, responsive web interface accessible from any browser
- **Offline Capable**: Works without internet connection once loaded
- **File Upload**: Upload Excel files directly through the web interface
- **Interactive Visualizations**: Generate and view family tree visualizations in real-time
- **D3.js Visualization**: Beautiful, interactive tree diagrams with zoom and pan capabilities
- **Flexible Generation**: Generate complete trees or specific family branches
- **Real-time Status**: Live updates on processing status and character counts
- **Session Management**: Improved state handling with Flask sessions
- **Memory Efficient**: Optimized resource management and cleanup

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- All dependencies from `requirements.txt`

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/pyFamilyTree.git
   cd pyFamilyTree
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Web Application**:
   ```bash
   python web_app.py
   ```

4. **Access the Application**:
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The application will be ready to use!

## 📁 File Structure

```
pyFamilyTree/
├── web_app.py              # Main Flask application
├── templates/              # Web templates
│   ├── index.html         # Main web interface
│   ├── d3_tree_script.js  # D3.js visualization logic
│   └── d3_tree_template_simple.html
├── uploads/               # Temporary file upload directory
├── assets/               # Generated XML files
├── src/                  # Core application modules
│   ├── core/            # Core functionality
│   ├── data/            # Data handling
│   ├── graph/           # Graph generation
│   └── ui/              # User interface components
└── requirements.txt      # Python dependencies
```

## 🎯 Usage

### 1. Upload Family Data

1. **Select Excel File**: Choose your family data Excel file (.xlsx or .xls)
2. **Enter Sheet Name**: Specify which sheet contains your family data
3. **Upload & Process**: Click "Upload & Process" to convert Excel data to XML format

### 2. Configure Visualization

1. **Choose Generation Type**:
   - **Generate Complete Tree**: Creates visualization of all family members
   - **Specific Person**: Start from a particular family member

2. **Set Generation Limits** (if using specific person):
   - **Generations Back**: Number of ancestor generations to include
   - **Generations Forward**: Number of descendant generations to include

### 3. Generate Visualization

1. Click "Generate Visualization"
2. Wait for processing to complete
3. View the interactive family tree in the embedded viewer
4. Use mouse wheel to zoom and drag to pan around the visualization

## 🔧 Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `FLASK_DEBUG`: Set to `1` for auto-reload on code changes

### Application Settings

The web application uses Flask session management for improved state handling:
- Secure session management
- Automatic cleanup of old sessions
- Proper resource management
- Efficient file handling

## 🌐 Offline Capabilities

The web application is designed to work offline:

- **Static Assets**: All CSS and JavaScript are embedded in the HTML
- **Local Processing**: All data processing happens on the server
- **No External Dependencies**: No CDN or external API calls required
- **File-based Storage**: Uses local file system for data storage

## 📊 API Endpoints

### File Upload
- `POST /upload` - Upload and process Excel files

### Visualization
- `POST /visualize` - Generate family tree visualizations
- `GET /visualization/<filename>` - Serve generated visualization files

### Status & Data
- `GET /api/status` - Get current application status
- `GET /api/characters` - Get list of available characters

## 🛠️ Development

### Running in Development Mode

```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the application
python web_app.py
```

### Testing

The application includes test data:
- Sample Excel files for testing
- XML files in the `assets/` directory
- Test data in `assets/FamilyTree_TestData/`

## 📝 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   - Change the port in `web_app.py`: `app.run(port=5001)`

2. **File Upload Errors**:
   - Check file size (max 16MB)
   - Ensure file is Excel format (.xlsx, .xls)
   - Verify sheet name exists in Excel file

3. **Visualization Generation Fails**:
   - Check server logs for detailed error messages
   - Verify XML files were created successfully
   - Ensure proper file permissions

### Debug Mode

Enable debug mode for detailed error messages:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This web version is the primary interface for the Family Tree Visualizer, offering a modern and accessible way to explore and visualize family relationships.