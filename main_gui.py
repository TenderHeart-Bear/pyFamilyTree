"""
Main entry point for the Family Tree GUI application.
"""
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.ui.controllers.app_controller import AppController

def main():
    """Main function to run the Family Tree GUI application"""
    app = AppController()
    app.initialize()
    app.run()

if __name__ == "__main__":
    main() 