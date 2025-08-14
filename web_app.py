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
from src.graph import D3FamilyTreeGraph
from src.data.xml_parser import FamilyTreeData
from src.core.path_manager import path_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Session
from flask_session import Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'xlsm'}

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
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    sheet_name = request.form.get('sheet_name', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload Excel files only (.xlsx, .xls, .xlsm).'}), 400
    
    if not sheet_name.strip():
        return jsonify({'error': 'Sheet name is required'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create XML directory based on Excel file and sheet names
        excel_base_name = os.path.splitext(filename)[0]
        xml_dir = os.path.join("assets", excel_base_name, sheet_name)
        
        # Create XML files from Excel
        try:
            xml_dir = create_xml_from_excel_sheet(file_path, sheet_name, xml_dir)
        except Exception as excel_error:
            return jsonify({'error': f'Error converting Excel file: {str(excel_error)}'}), 500
        
        # Store session data
        session['current_data_dir'] = xml_dir
        session['file_path'] = file_path
        session['sheet_name'] = sheet_name
        session['xml_dir'] = xml_dir
        session['filename'] = filename
        
        # Get available characters for selection
        try:
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
        except Exception as data_error:
            return jsonify({'error': f'Error loading family data: {str(data_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/load-kearnan', methods=['POST'])
def load_kearnan_data():
    """Load Kearnan Family data directly for testing"""
    global current_data_dir, session_data
    
    try:
        # Use the Kearnan Family dataset
        xml_data_dir = "assets/Family Records-MasterV2/Kearnan Family"
        
        if not os.path.exists(xml_data_dir):
            return jsonify({'error': 'Kearnan Family data not found'}), 404
        
        # Store session data
        current_data_dir = xml_data_dir
        session_data = {
            'file_path': 'Kearnan Family (pre-loaded)',
            'sheet_name': 'Kearnan Family',
            'xml_dir': xml_data_dir,
            'filename': 'Kearnan Family'
        }
        
        # Get available characters for selection
        family_data = FamilyTreeData(xml_data_dir)
        characters = family_data.get_all_characters()
        character_list = [{'id': char_id, 'name': char_data.get('name', char_id)} 
                         for char_id, char_data in characters.items()]
        
        return jsonify({
            'success': True,
            'message': f'Kearnan Family data loaded successfully with {len(characters)} characters',
            'characters': character_list
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading Kearnan Family data: {str(e)}'}), 500

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
        engine = data.get('engine', 'classic')  # New parameter for engine selection
        
        # Create new session for this visualization
        session_dir = path_manager.create_session()
        
        # Always use D3 engine
        graph_class = D3FamilyTreeGraph
        output_format = 'html'
        
        # Create graph with appropriate parameters
        if generate_all:
            # Generate complete tree
            current_graph = graph_class(
                xml_data_dir=current_data_dir,
                output_dir=session_dir,
                output_format=output_format
            )
        else:
            # Generate specific view
            current_graph = graph_class(
                xml_data_dir=current_data_dir,
                output_dir=session_dir,
                start_person_name=start_person if start_person else None,
                generations_back=generations_back,
                generations_forward=generations_forward,
                output_format=output_format
            )
        
        # Generate visualization
        if current_graph:
            output_path = current_graph.generate_visualization()
            
            if output_path and os.path.exists(output_path):
                # Return the path to the generated visualization
                return jsonify({
                    'success': True,
                    'visualization_path': output_path,
                    'character_count': len(current_graph.characters) if hasattr(current_graph, 'characters') else 0,
                    'engine': engine,
                    'format': output_format
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
        sessions_dir = path_manager.get_session_dir()
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

# Error handlers to prevent bad request errors
@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

# Handle HTTPS redirects
@app.before_request
def before_request():
    """Handle HTTPS redirects and other pre-request processing"""
    # If the request is coming over HTTPS, redirect to HTTP
    if request.headers.get('X-Forwarded-Proto') == 'https':
        return redirect(request.url.replace('https://', 'http://'), code=301)
    
    # Add security headers
    response = None
    if hasattr(request, 'endpoint') and request.endpoint:
        response = app.make_response(request.endpoint)
        if response:
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'

if __name__ == '__main__':
    # Use threaded=False to prevent issues with some browsers
    # and disable SSL context to prevent HTTPS redirects
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000, 
        threaded=False,
        ssl_context=None  # Explicitly disable SSL
    ) 