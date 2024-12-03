import sys
import os
import subprocess

def check_environment():
    print("\n=== Python Environment Diagnostic ===\n")
    
    # Print Python version and location
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Path: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Print current working directory
    print(f"\nCurrent Directory: {os.getcwd()}")
    
    # List installed packages
    print("\nInstalled Packages:")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error listing packages: {e}")
    
    # Try importing required packages
    packages = ['moviepy', 'numpy', 'cv2']
    print("\nPackage Import Test:")
    for package in packages:
        try:
            __import__(package)
            print(f"[OK] {package} successfully imported")
        except ImportError as e:
            print(f"[ERROR] {package} import failed: {e}")

if __name__ == "__main__":
    check_environment()

