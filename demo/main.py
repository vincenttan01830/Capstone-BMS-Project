import tkinter as tk
from tkinter import scrolledtext
import threading
import socket

class DeviceMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Monitor")
        self.root.geometry("800x600")

        # GUI Elements
        self.start_button = tk.Button(self.root, text="Start", command=self.start_server)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.capture_log_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=100, height=15)
        self.capture_log_text.pack(pady=10)
        self.capture_log_text.insert(tk.END, "Capture Process Output:\n")

        self.monitor_log_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=100, height=15)
        self.monitor_log_text.pack(pady=10)
        self.monitor_log_text.insert(tk.END, "Monitor Process Output:\n")

        self.server_thread = None
        self.running = False

    def start_server(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.running = True
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()

    def stop_server(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.server_thread:
            self.server_thread.join()

    def run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', 9999))
        server_socket.listen(5)

        while self.running:
            print("Server is listening for connections...")
            client_socket, _ = server_socket.accept()
            print("Connection accepted")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

        server_socket.close()

    def handle_client(self, client_socket):
        with client_socket:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if data:
                    print(f"Data received: {data}")
                    self.update_gui(data)
                else:
                    break

    def update_gui(self, data):
        if data.startswith('Capture:'):
            self.capture_log_text.insert(tk.END, data)
            self.capture_log_text.see(tk.END)
        elif data.startswith('Monitor:'):
            self.monitor_log_text.insert(tk.END, data)
            self.monitor_log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceMonitorApp(root)
    root.mainloop()
