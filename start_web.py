#!/usr/bin/env python3
"""
Startup script for the Family Tree Visualizer Web Application
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask',
        'werkzeug',
        'graphviz',
        'openpyxl',
        'lxml',
        'cairosvg'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_graphviz():
    """Check if Graphviz is available in the system"""
    try:
        result = subprocess.run(['dot', '-V'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Graphviz is available")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  Graphviz not found in system PATH")
    print("   This may affect visualization generation")
    print("   Install Graphviz from: https://graphviz.org/download/")
    return False

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = ['uploads', 'templates', 'assets']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created/verified")

def open_browser_safely():
    """Safely open browser with multiple fallback methods"""
    url = 'http://localhost:5000'
    
    # Try different browser opening methods
    browsers_to_try = [
        'chrome',
        'firefox',
        'safari',
        'edge',
        'opera'
    ]
    
    for browser in browsers_to_try:
        try:
            webbrowser.get(browser).open(url)
            print(f"🌍 Browser opened successfully with {browser}")
            return True
        except:
            continue
    
    # Fallback to default browser
    try:
        webbrowser.open(url)
        print("🌍 Browser opened with default browser")
        return True
    except:
        print("📝 Please manually open your browser and navigate to:")
        print(f"   {url}")
        return False

def start_web_app():
    """Start the web application"""
    print("\n🚀 Starting Family Tree Visualizer Web Application...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check Graphviz
    check_graphviz()
    
    # Create directories
    create_directories()
    
    # Import and run the web app
    try:
        from web_app import app
        
        print("\n🌐 Web application is starting...")
        print("   URL: http://localhost:5000")
        print("   Press Ctrl+C to stop the server")
        print("\n" + "=" * 50)
        
        # Open browser after a short delay
        def open_browser_delayed():
            time.sleep(3)  # Increased delay to ensure server is ready
            open_browser_safely()
        
        # Start browser in a separate thread
        import threading
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Run the Flask app with improved settings
        app.run(
            debug=True, 
            host='0.0.0.0', 
            port=5000, 
            threaded=False,  # Prevent threading issues
            use_reloader=False  # Prevent double startup
        )
        
    except ImportError as e:
        print(f"❌ Error importing web_app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error starting web application: {e}")
        return False

def main():
    """Main function"""
    print("🌳 Family Tree Visualizer - Web Version")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('web_app.py'):
        print("❌ web_app.py not found in current directory")
        print("   Please run this script from the project root directory")
        return False
    
    # Start the application
    return start_web_app()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Web application stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 