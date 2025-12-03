"""Run backend API and Streamlit frontend together.

This Python launcher starts both processes and opens the frontend URL in the default browser.

Usage:
    python run_all.py

Requirements:
 - Python on PATH
 - `streamlit` package installed
 - `backend/.env` configured
"""
import subprocess
import webbrowser
import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def start_backend():
    cmd = [sys.executable, os.path.join('backend', 'data_api.py'), '--host', '127.0.0.1', '--port', '5001']
    return subprocess.Popen(cmd, cwd=PROJECT_ROOT)

def start_frontend():
    cmd = ['streamlit', 'run', os.path.join('frontend', 'app.py'), '--server.port', '8501']
    return subprocess.Popen(cmd, cwd=PROJECT_ROOT)

def main():
    print('Running ETL pipeline (backend/main.py)')
    etl = subprocess.run([sys.executable, os.path.join('backend', 'main.py'), '--year', '2025'], cwd=PROJECT_ROOT)
    if etl.returncode != 0:
        print(f'ETL failed with exit code {etl.returncode}. Aborting launcher.')
        sys.exit(etl.returncode)

    print('Starting backend...')
    backend_proc = start_backend()
    time.sleep(2)
    print('Starting frontend...')
    frontend_proc = start_frontend()

    # open browser to Streamlit
    url = 'http://localhost:8501'
    print(f'Opening {url} in your browser...')
    webbrowser.open(url)

    try:
        # Wait for processes; if one exits, we exit
        while True:
            if backend_proc.poll() is not None:
                print('Backend process exited. Shutting down frontend.')
                frontend_proc.terminate()
                break
            if frontend_proc.poll() is not None:
                print('Frontend process exited. Shutting down backend.')
                backend_proc.terminate()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interrupted, terminating processes...')
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == '__main__':
    main()
