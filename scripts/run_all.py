"""
Master script to run both uvicorn (FastAPI) and streamlit.
Terminates both cleanly on Ctrl+C or when either exits.
"""

import os
import signal
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

processes: list[subprocess.Popen] = []


def shutdown(signum=None, frame=None):
    for p in processes:
        if p.poll() is None:
            p.terminate()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    python = sys.executable
    api_cmd = [
        python, "-m", "uvicorn", "src.main:app",
        "--reload", "--host", "0.0.0.0", "--port", "8000",
    ]
    streamlit_cmd = [
        python, "-m", "streamlit", "run", "src/streamlit_app.py",
        "--server.port", "8501", "--server.headless", "true",
    ]

    p1 = subprocess.Popen(api_cmd, cwd=PROJECT_ROOT)
    p2 = subprocess.Popen(streamlit_cmd, cwd=PROJECT_ROOT)
    processes.extend([p1, p2])

    print("API: http://127.0.0.1:8000 | Dashboard: http://localhost:8501")
    print("Press Ctrl+C to stop both.")

    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"Process exited (code {p.poll()}), shutting down...")
                    shutdown()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
