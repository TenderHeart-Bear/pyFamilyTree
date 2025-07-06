"""
Main entry point for the Family Tree GUI application.
"""
from ui.controllers.app_controller import AppController

def main():
    """Main function to run the Family Tree GUI application"""
    app = AppController()
    app.initialize()
    app.run()

if __name__ == "__main__":
    main() 