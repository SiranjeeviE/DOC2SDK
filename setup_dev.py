import subprocess
import sys
import os

def run_command(command, cwd=None):
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        cwd=cwd,
        text=True
    )
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
    process.stdout.close()
    return process.wait()

def setup():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("🚀 Setting up AntiGravity Development Environment...")
    
    # Root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Backend Setup
    print("\n--- Backend Setup ---")
    backend_dir = os.path.join(root_dir, "backend")
    
    # Create venv if not exists
    if not os.path.exists(os.path.join(backend_dir, "venv")):
        run_command("python -m venv venv", cwd=backend_dir)
    
    # Install requirements
    pip_path = os.path.join(backend_dir, "venv", "Scripts", "pip") if os.name == "nt" else os.path.join(backend_dir, "venv", "bin", "pip")
    run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir)
    
    # 2. Frontend Setup
    print("\n--- Frontend Setup ---")
    frontend_dir = os.path.join(root_dir, "frontend")
    run_command("npm install", cwd=frontend_dir)
    
    print("\n✅ Setup Complete!")
    print("\nTo start the project:")
    print("1. Backend: cd backend && venv\\Scripts\\activate && uvicorn app.main:app --reload")
    print("2. Frontend: cd frontend && npm run dev")
    print("\nor use docker-compose up --build")

if __name__ == "__main__":
    setup()
