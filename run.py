import subprocess
import sys
import os

def run_crm():
    """Run the CRM Flask application"""
    print("Starting CRM...")
    cmd = [sys.executable, "crm-flask/app.py"] # 
    print("Running CRM command:", cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("CRM stdout:", result.stdout)
    print("CRM stderr:", result.stderr)
    print("CRM return code:", result.returncode)

def run_ai_agent():
    """Run the AI Agent"""
    print("Starting AI Agent...")
    # Use the current python executable
    cmd = [sys.executable, "ai_agent/main.py"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nAI Agent interrupted.")

def run_invoice_system():
    """Run the Invoice System"""
    print("Starting Invoice System...")
    cmd = [sys.executable, "invoice_system/run.py"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nInvoice System interrupted.")

def run_both():
    """Run CRM, Invoice System, and AI Agent together"""
    print("Starting CRM, Invoice System, and AI Agent...")
    crm_process = subprocess.Popen([sys.executable, "crm-flask/app.py"])
    print("CRM started in background on http://localhost:5000")
    invoice_process = subprocess.Popen([sys.executable, "invoice_system/run.py"])
    print("Invoice System started in background on http://localhost:5001")
    # Now run AI agent
    try:
        run_ai_agent()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # After AI agent exits, terminate background services
        if crm_process.poll() is None:  # Check if process is still running
            crm_process.terminate()
            try:
                crm_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                crm_process.kill()
        if invoice_process.poll() is None:
            invoice_process.terminate()
            try:
                invoice_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                invoice_process.kill()
        print("CRM and Invoice System servers stopped.")

if __name__ == "__main__":
    try:
        run_both()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
