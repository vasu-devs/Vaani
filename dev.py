import subprocess
import time
import os
import signal
import sys

def run_process(command, cwd=None, title=None):
    print(f"Starting {title}...")
    return subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    processes = []

    try:
        # 1. Start API Server
        api_proc = run_process(
            f'"{sys.executable}" run_server.py', 
            cwd=backend_dir, 
            title="API Server"
        )
        processes.append(api_proc)
        time.sleep(2) # Give API time to start

        # 2. Start Agent Worker
        agent_proc = run_process(
            f'"{sys.executable}" run_agent.py dev', 
            cwd=backend_dir, 
            title="Voice Agent Worker"
        )
        processes.append(agent_proc)

        # 3. Start Frontend
        frontend_proc = run_process(
            "npm run dev", 
            cwd=frontend_dir, 
            title="Frontend Vite"
        )
        processes.append(frontend_proc)

        print("\nAll services started. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping services...")
        for p in processes:
            p.terminate()
        sys.exit(0)
