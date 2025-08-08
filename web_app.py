"""
Web-based Family Tree Visualization Application
A Flask application that provides the same functionality as the desktop app
but accessible through a web browser with offline capabilities.
"""
import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile
import shutil
from pathlib import Path

# Import existing modules
from src.data.excel_converter import create_xml_from_excel_sheet
from src.graph.family import FamilyTreeGraph
from src.graph.embedded_family import EmbeddedFamilyTreeGraph
from src.data.xml_parser import FamilyTreeData
from src.core.path_manager import path_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to store current session data
current_data_dir = None
current_graph = None
session_data = {}

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    global current_data_dir, session_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    sheet_name = request.form.get('sheet_name', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload Excel files only.'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create XML directory based on Excel file and sheet names
        excel_base_name = os.path.splitext(filename)[0]
        xml_dir = os.path.join("assets", excel_base_name, sheet_name)
        
        # Create XML files from Excel
        xml_dir = create_xml_from_excel_sheet(file_path, sheet_name, xml_dir)
        
        # Store session data
        current_data_dir = xml_dir
        session_data = {
            'file_path': file_path,
            'sheet_name': sheet_name,
            'xml_dir': xml_dir,
            'filename': filename
        }
        
        # Get available characters for selection
        family_data = FamilyTreeData(xml_dir)
        characters = family_data.get_all_characters()
        character_list = [{'id': char_id, 'name': char_data.get('name', char_id)} 
                         for char_id, char_data in characters.items()]
        
        return jsonify({
            'success': True,
            'message': f'File uploaded successfully: {filename}',
            'characters': character_list,
            'total_characters': len(characters)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    """Generate family tree visualization"""
    global current_graph, current_data_dir
    
    if not current_data_dir:
        return jsonify({'error': 'No data loaded. Please upload a file first.'}), 400
    
    try:
        data = request.get_json()
        
        # Get visualization parameters
        start_person = data.get('start_person', '')
        generations_back = int(data.get('generations_back', 0))
        generations_forward = int(data.get('generations_forward', 0))
        style_choice = data.get('style', '1')
        generate_all = data.get('generate_all', False)
        
        # Create new session for this visualization
        session_dir = path_manager.create_session()
        
        # Create graph with appropriate parameters
        if generate_all:
            # Generate complete tree
            current_graph = FamilyTreeGraph(
                xml_data_dir=current_data_dir
            )
        else:
            # Generate specific view
            current_graph = FamilyTreeGraph(
                xml_data_dir=current_data_dir,
                start_person_name=start_person if start_person else None,
                generations_back=generations_back,
                generations_forward=generations_forward
            )
        
        # Generate visualization
        if current_graph and current_graph.characters:
            output_path = current_graph.generate_visualization(
                output_format='svg',
                output_dir=session_dir
            )
            
            if output_path and os.path.exists(output_path):
                # Return the path to the generated visualization
                return jsonify({
                    'success': True,
                    'visualization_path': output_path,
                    'character_count': len(current_graph.characters)
                })
            else:
                return jsonify({'error': 'Failed to generate visualization'}), 500
        else:
            return jsonify({'error': 'No characters found to graph'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error creating visualization: {str(e)}'}), 500

@app.route('/visualization/<path:filename>')
def serve_visualization(filename):
    """Serve generated visualization files"""
    try:
        # Look for the file in the sessions directory
        sessions_dir = path_manager.get_sessions_dir()
        file_path = os.path.join(sessions_dir, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'Visualization file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500

@app.route('/api/characters')
def get_characters():
    """Get list of available characters"""
    global current_data_dir
    
    if not current_data_dir:
        return jsonify({'error': 'No data loaded'}), 400
    
    try:
        family_data = FamilyTreeData(current_data_dir)
        characters = family_data.get_all_characters()
        character_list = [{'id': char_id, 'name': char_data.get('name', char_id)} 
                         for char_id, char_data in characters.items()]
        
        return jsonify({'characters': character_list})
    except Exception as e:
        return jsonify({'error': f'Error getting characters: {str(e)}'}), 500

@app.route('/api/status')
def get_status():
    """Get current application status"""
    global current_data_dir, session_data
    
    status = {
        'data_loaded': current_data_dir is not None,
        'current_file': session_data.get('filename', ''),
        'current_sheet': session_data.get('sheet_name', ''),
        'character_count': 0
    }
    
    if current_data_dir:
        try:
            family_data = FamilyTreeData(current_data_dir)
            characters = family_data.get_all_characters()
            status['character_count'] = len(characters)
        except:
            pass
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 