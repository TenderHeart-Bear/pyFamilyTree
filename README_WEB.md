# Family Tree Visualizer - Web Version

A modern web-based family tree visualization tool that can work offline. This web application provides the same functionality as the desktop version but accessible through any web browser.

## 🌟 Features

- **Web-based Interface**: Modern, responsive web interface accessible from any browser
- **Offline Capable**: Works without internet connection once loaded
- **File Upload**: Upload Excel files directly through the web interface
- **Interactive Visualizations**: Generate and view family tree visualizations in real-time
- **Multiple Styles**: Choose between Classic and Embedded visualization styles
- **Flexible Generation**: Generate complete trees or specific family branches
- **Real-time Status**: Live updates on processing status and character counts

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- All dependencies from `requirements.txt`

### Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Application**:
   ```bash
   python web_app.py
   ```

3. **Access the Application**:
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The application will be ready to use!

## 📁 File Structure

```
pyFamilyTree/
├── web_app.py              # Main Flask application
├── templates/
│   └── index.html          # Main web interface
├── uploads/                # Temporary file upload directory
├── assets/                 # Generated XML files
├── src/                    # Core application modules
└── requirements.txt        # Python dependencies
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

3. **Select Style**:
   - **Classic Style**: Traditional family tree with dotted lines between spouses
   - **Embedded Style**: Modern style with diamond nodes connecting spouses

### 3. Generate Visualization

1. Click "Generate Visualization"
2. Wait for processing to complete
3. View the interactive family tree in the embedded viewer

## 🔧 Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `FLASK_DEBUG`: Set to `1` for auto-reload on code changes

### Application Settings

The web application uses the same configuration as the desktop version:
- Session management through `path_manager`
- XML data processing through existing modules
- Graph generation using existing `FamilyTreeGraph` classes

## 🌐 Offline Capabilities

The web application is designed to work offline:

- **Static Assets**: All CSS and JavaScript are embedded in the HTML
- **Local Processing**: All data processing happens on the server
- **No External Dependencies**: No CDN or external API calls required
- **File-based Storage**: Uses local file system for data storage

## 🔒 Security Features

- **File Type Validation**: Only accepts Excel files (.xlsx, .xls)
- **Secure Filename Handling**: Uses `secure_filename` for uploaded files
- **File Size Limits**: Configurable maximum file size (default: 16MB)
- **Session Management**: Isolated processing sessions

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

The web application uses the same test data as the desktop version:
- Excel files in the root directory
- XML files in the `assets/` directory
- Test data in `assets/FamilyTree_TestData/`

## 🔄 Integration with Desktop Version

The web version shares the same core modules as the desktop version:
- `src/data/excel_converter.py` - Excel to XML conversion
- `src/graph/family.py` - Family tree graph generation
- `src/data/xml_parser.py` - XML data processing
- `src/core/path_manager.py` - Session and path management

## 🚀 Deployment

### Local Development
```bash
python web_app.py
```

### Production Deployment
```bash
# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "web_app.py"]
```

## 📝 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   - Change the port in `web_app.py`: `app.run(port=5001)`

2. **File Upload Errors**:
   - Check file size (max 16MB)
   - Ensure file is Excel format (.xlsx, .xls)
   - Verify sheet name exists in Excel file

3. **Visualization Generation Fails**:
   - Check that Graphviz is installed
   - Verify XML files were created successfully
   - Check server logs for detailed error messages

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

This project is licensed under the same terms as the main family tree application.

---

**Note**: This web version maintains full compatibility with the existing desktop application while providing a modern web interface for easier access and sharing. 