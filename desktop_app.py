import os
import sys
import time
import socket
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(BASE_DIR))

# Ensure working directory is BASE_DIR
os.chdir(str(BASE_DIR))

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_in_use(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_uvicorn_server():
    try:
        import uvicorn
        from app.main import app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            reload=False
        )
    except Exception as e:
        with open("server_error.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Server startup error: {e}\n")

class DesktopAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yahoo Mail Order Manager")
        self.root.geometry("460x350")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8fafc")

        self.lan_ip = get_lan_ip()
        self.local_url = "http://localhost:8000"
        self.mobile_url = f"http://{self.lan_ip}:8000"

        self.setup_ui()
        self.start_backend_process()

    def setup_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#6001d2", height=70)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="Yahoo Mail Order Manager",
            font=("Segoe UI", 15, "bold"),
            fg="white",
            bg="#6001d2"
        )
        title_label.pack(pady=(12, 2))

        subtitle_label = tk.Label(
            header_frame,
            text="Production Web & Mobile Server Engine",
            font=("Segoe UI", 8),
            fg="#e9d5ff",
            bg="#6001d2"
        )
        subtitle_label.pack(pady=(0, 10))

        # Main content card
        content_frame = tk.Frame(self.root, bg="#f8fafc", padx=20, pady=12)
        content_frame.pack(fill="both", expand=True)

        # Status row
        self.status_box = tk.Frame(content_frame, bg="#fef3c7", highlightbackground="#fcd34d", highlightthickness=1, padx=10, pady=8)
        self.status_box.pack(fill="x", pady=(0, 12))

        self.status_icon = tk.Label(self.status_box, text="🟡", font=("Segoe UI", 12), bg="#fef3c7")
        self.status_icon.pack(side="left", padx=(0, 6))

        self.status_text = tk.Label(
            self.status_box,
            text="Starting Server (Please wait a moment...)",
            font=("Segoe UI", 9, "bold"),
            fg="#92400e",
            bg="#fef3c7"
        )
        self.status_text.pack(side="left")

        # URLs info
        info_frame = tk.Frame(content_frame, bg="white", highlightbackground="#e2e8f0", highlightthickness=1, padx=12, pady=10)
        info_frame.pack(fill="x", pady=(0, 12))

        tk.Label(info_frame, text="💻 PC Dashboard:", font=("Segoe UI", 8, "bold"), fg="#64748b", bg="white").grid(row=0, column=0, sticky="w")
        tk.Label(info_frame, text=self.local_url, font=("Segoe UI", 9, "bold"), fg="#1e293b", bg="white").grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(info_frame, text="📱 Mobile / WiFi:", font=("Segoe UI", 8, "bold"), fg="#64748b", bg="white").grid(row=1, column=0, sticky="w", pady=(6, 0))
        tk.Label(info_frame, text=self.mobile_url, font=("Segoe UI", 9, "bold"), fg="#6001d2", bg="white").grid(row=1, column=1, sticky="w", padx=8, pady=(6, 0))

        # Buttons
        btn_frame = tk.Frame(content_frame, bg="#f8fafc")
        btn_frame.pack(fill="x")

        self.open_btn = tk.Button(
            btn_frame,
            text="🌐 Open Dashboard in Browser",
            font=("Segoe UI", 10, "bold"),
            bg="#6001d2",
            fg="white",
            activebackground="#4c01a8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.open_browser
        )
        self.open_btn.pack(fill="x", pady=(0, 8))

        row_btns = tk.Frame(btn_frame, bg="#f8fafc")
        row_btns.pack(fill="x")

        copy_btn = tk.Button(
            row_btns,
            text="📋 Copy Mobile Link",
            font=("Segoe UI", 8, "bold"),
            bg="#ffffff",
            fg="#334155",
            relief="groove",
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.copy_mobile_link
        )
        copy_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        exit_btn = tk.Button(
            row_btns,
            text="🛑 Close Server",
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#dc2626",
            relief="groove",
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.on_close
        )
        exit_btn.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_backend_process(self):
        if is_port_in_use(8000):
            self.mark_server_ready()
            return

        # Start uvicorn thread
        t = threading.Thread(target=run_uvicorn_server, daemon=True)
        t.start()

        # Check port status repeatedly
        self.check_port_attempts = 0
        self.poll_port_status()

    def poll_port_status(self):
        if is_port_in_use(8000):
            self.mark_server_ready()
            self.open_browser()
        else:
            self.check_port_attempts += 1
            if self.check_port_attempts < 20:  # Wait up to 10 seconds
                self.root.after(500, self.poll_port_status)
            else:
                self.status_box.config(bg="#fee2e2", highlightbackground="#fca5a5")
                self.status_icon.config(text="🔴", bg="#fee2e2")
                self.status_text.config(text="Server Failed to Start (Port 8000)", fg="#991b1b", bg="#fee2e2")

    def mark_server_ready(self):
        self.status_box.config(bg="#ecfdf5", highlightbackground="#a7f3d0")
        self.status_icon.config(text="🟢", bg="#ecfdf5")
        self.status_text.config(text="Server is ACTIVE and serving PC & Mobile Web App", fg="#065f46", bg="#ecfdf5")

    def open_browser(self):
        webbrowser.open(self.local_url)

    def copy_mobile_link(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.mobile_url)
        messagebox.showinfo("Copied!", f"Mobile Link copied:\n{self.mobile_url}\n\nOpen this link in Chrome or Safari on your phone!")

    def on_close(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopAppGUI(root)
    root.mainloop()
