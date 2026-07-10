import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from downloader import HitomiDownloader

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("HitoLa PDF/CBZ Downloader & Converter")
        self.root.geometry("680x620")
        self.root.minsize(600, 500)
        
        self.active_downloader = None
        self.download_thread = None
        self.is_running = False

        # Apply dark modern flat theme
        self.setup_theme()
        self.create_widgets()

    def setup_theme(self):
        self.bg_color = "#1e1e1e"      # main background
        self.frame_bg = "#2d2d2d"      # container frame background
        self.fg_color = "#ffffff"      # primary text
        self.accent_color = "#007acc"  # blue accent buttons
        self.accent_hover = "#005999"
        self.cancel_color = "#d9534f"  # red cancel button
        self.cancel_hover = "#c9302c"
        self.input_bg = "#3c3f41"      # input background
        self.input_fg = "#ffffff"
        self.border_color = "#555555"

        self.root.configure(bg=self.bg_color)

        # Style ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure progress bar
        self.style.configure(
            "Dark.Horizontal.TProgressbar",
            thickness=18,
            troughcolor="#3c3f41",
            background=self.accent_color,
            bordercolor=self.bg_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color
        )

    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title / Header
        header_lbl = tk.Label(
            main_container, 
            text="HitoLa Converter", 
            font=("Segoe UI", 20, "bold"), 
            bg=self.bg_color, 
            fg=self.fg_color
        )
        header_lbl.pack(anchor="w", pady=(0, 5))

        subheader_lbl = tk.Label(
            main_container, 
            text="Download comics from Hitomi.la and convert them to PDF or CBZ", 
            font=("Segoe UI", 10, "italic"), 
            bg=self.bg_color, 
            fg="#aaaaaa"
        )
        subheader_lbl.pack(anchor="w", pady=(0, 20))

        # --- Configuration Frame ---
        config_frame = tk.LabelFrame(
            main_container, 
            text=" Configuration ", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.frame_bg, 
            fg=self.fg_color, 
            bd=1, 
            relief=tk.SOLID, 
            padx=15, 
            pady=15
        )
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # Mode Selection (Single vs Multiple URLs)
        self.multi_mode_var = tk.BooleanVar(value=False)
        mode_cb = tk.Checkbutton(
            config_frame,
            text="Download Multiple URLs (One-at-a-time)",
            variable=self.multi_mode_var,
            command=self.toggle_mode,
            bg=self.frame_bg,
            fg=self.fg_color,
            selectcolor=self.frame_bg,
            activebackground=self.frame_bg,
            activeforeground=self.fg_color,
            font=("Segoe UI", 10)
        )
        mode_cb.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # URL Input Label
        self.url_lbl = tk.Label(
            config_frame, 
            text="Doujin URL / ID:", 
            font=("Segoe UI", 10), 
            bg=self.frame_bg, 
            fg=self.fg_color
        )
        self.url_lbl.grid(row=1, column=0, sticky="w", pady=(0, 5))

        # Single URL Input
        self.url_entry = tk.Entry(
            config_frame,
            width=50,
            bg=self.input_bg,
            fg=self.input_fg,
            insertbackground=self.fg_color,
            bd=1,
            relief=tk.SOLID,
            font=("Segoe UI", 10)
        )
        self.url_entry.grid(row=2, column=0, columnspan=3, sticky="we", pady=(0, 15))

        # Multiple URLs Text Area (hidden initially)
        self.url_text = ScrolledText(
            config_frame,
            height=6,
            bg=self.input_bg,
            fg=self.input_fg,
            insertbackground=self.fg_color,
            bd=1,
            relief=tk.SOLID,
            font=("Segoe UI", 10)
        )

        # Output Directory
        dir_lbl = tk.Label(
            config_frame, 
            text="Output Directory:", 
            font=("Segoe UI", 10), 
            bg=self.frame_bg, 
            fg=self.fg_color
        )
        dir_lbl.grid(row=3, column=0, sticky="w", pady=(0, 5))

        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dir_entry = tk.Entry(
            config_frame,
            textvariable=self.dir_var,
            width=40,
            bg=self.input_bg,
            fg=self.input_fg,
            insertbackground=self.fg_color,
            bd=1,
            relief=tk.SOLID,
            font=("Segoe UI", 10)
        )
        self.dir_entry.grid(row=4, column=0, columnspan=2, sticky="we", pady=(0, 15))

        browse_btn = tk.Button(
            config_frame,
            text="Browse...",
            command=self.browse_directory,
            bg=self.input_bg,
            fg=self.fg_color,
            activebackground=self.accent_color,
            activeforeground=self.fg_color,
            bd=0,
            padx=10,
            font=("Segoe UI", 9, "bold")
        )
        browse_btn.grid(row=4, column=2, sticky="e", padx=(10, 0), pady=(0, 15))

        # Format Selection
        format_lbl = tk.Label(
            config_frame,
            text="Output Format:",
            font=("Segoe UI", 10),
            bg=self.frame_bg,
            fg=self.fg_color
        )
        format_lbl.grid(row=5, column=0, sticky="w")

        self.format_var = tk.StringVar(value="pdf")
        pdf_rb = tk.Radiobutton(
            config_frame,
            text="PDF File (.pdf)",
            variable=self.format_var,
            value="pdf",
            bg=self.frame_bg,
            fg=self.fg_color,
            selectcolor=self.frame_bg,
            activebackground=self.frame_bg,
            activeforeground=self.fg_color,
            font=("Segoe UI", 10)
        )
        pdf_rb.grid(row=5, column=1, sticky="w")

        cbz_rb = tk.Radiobutton(
            config_frame,
            text="Comic Book Zip (.cbz)",
            variable=self.format_var,
            value="cbz",
            bg=self.frame_bg,
            fg=self.fg_color,
            selectcolor=self.frame_bg,
            activebackground=self.frame_bg,
            activeforeground=self.fg_color,
            font=("Segoe UI", 10)
        )
        cbz_rb.grid(row=5, column=2, sticky="w")

        # Configure columns inside frame
        config_frame.columnconfigure(0, weight=1)
        config_frame.columnconfigure(1, weight=1)

        # --- Progress Frame ---
        progress_frame = tk.Frame(main_container, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, pady=(5, 10))

        self.status_lbl = tk.Label(
            progress_frame,
            text="Ready",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#dddddd"
        )
        self.status_lbl.pack(anchor="w", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            style="Dark.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # Controls (Start / Cancel)
        controls_frame = tk.Frame(main_container, bg=self.bg_color)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        self.start_btn = tk.Button(
            controls_frame,
            text="Start Download",
            command=self.toggle_download,
            bg=self.accent_color,
            fg=self.fg_color,
            activebackground=self.accent_hover,
            activeforeground=self.fg_color,
            bd=0,
            pady=8,
            font=("Segoe UI", 10, "bold")
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.warning_lbl = tk.Label(
            main_container,
            text="⚠️ DDoS Protection Safety: Image downloads are throttled (1-second delay) to avoid IP bans.",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="#e0a800"
        )
        self.warning_lbl.pack(pady=(0, 10))

        # --- Console Log Frame ---
        console_frame = tk.LabelFrame(
            main_container,
            text=" Activity Log ",
            font=("Segoe UI", 10, "bold"),
            bg=self.frame_bg,
            fg=self.fg_color,
            bd=1,
            relief=tk.SOLID,
            padx=10,
            pady=10
        )
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = ScrolledText(
            console_frame,
            bg="#121212",
            fg="#33ff33",
            insertbackground="#33ff33",
            bd=0,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def toggle_mode(self):
        if self.multi_mode_var.get():
            self.url_lbl.config(text="Doujin URLs (one per line):")
            self.url_entry.grid_remove()
            self.url_text.grid(row=2, column=0, columnspan=3, sticky="we", pady=(0, 15))
        else:
            self.url_lbl.config(text="Doujin URL / ID:")
            self.url_text.grid_remove()
            self.url_entry.grid(row=2, column=0, columnspan=3, sticky="we", pady=(0, 15))

    def browse_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.dir_var.get())
        if selected_dir:
            self.dir_var.set(selected_dir)

    def toggle_download(self):
        if self.is_running:
            self.cancel_download()
        else:
            self.start_download()

    def start_download(self):
        output_dir = self.dir_var.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output directory.")
            return

        urls = []
        if self.multi_mode_var.get():
            lines = self.url_text.get("1.0", tk.END).split("\n")
            urls = [line.strip() for line in lines if line.strip()]
        else:
            single_url = self.url_entry.get().strip()
            if single_url:
                urls = [single_url]

        if not urls:
            messagebox.showerror("Error", "Please enter at least one valid Hitomi.la URL or ID.")
            return

        self.is_running = True
        self.start_btn.config(text="Cancel / Stop", bg=self.cancel_color, activebackground=self.cancel_hover)
        
        # Run download logic in separate thread
        self.download_thread = threading.Thread(target=self.run_download_queue, args=(urls, output_dir))
        self.download_thread.daemon = True
        self.download_thread.start()

    def cancel_download(self):
        if self.active_downloader:
            self.log("[System] Sending cancel signal to active download...")
            self.active_downloader.cancel()
        self.is_running = False
        self.start_btn.config(text="Start Download", bg=self.accent_color, activebackground=self.accent_hover)

    def run_download_queue(self, urls, output_dir):
        format_type = self.format_var.get()
        total_urls = len(urls)
        self.log(f"[System] Starting download queue for {total_urls} galleries...")

        for idx, url in enumerate(urls):
            if not self.is_running:
                break

            self.log(f"\n[Queue] Processing gallery {idx+1}/{total_urls}: {url}")
            
            def progress_cb(msg, progress):
                self.root.after(0, lambda: self.status_lbl.config(text=f"[{idx+1}/{total_urls}] {msg}"))
                self.root.after(0, lambda: self.progress_bar.config(value=progress * 100))
                # Log system level updates (not individual page updates to avoid log spam)
                if "page" not in msg.lower() or progress == 1.0:
                    self.root.after(0, lambda: self.log(f" -> {msg}"))

            self.active_downloader = HitomiDownloader(
                url=url,
                output_dir=output_dir,
                format_type=format_type,
                progress_callback=progress_cb,
                throttle_seconds=1.0
            )

            success = self.active_downloader.download()
            
            if not success:
                if self.active_downloader.is_cancelled:
                    self.log("[System] Queue processing stopped by user.")
                    break
                else:
                    self.log(f"[Error] Failed to process URL: {url}")
            else:
                self.log(f"[Completed] Gallery {idx+1}/{total_urls} finished successfully.")

        self.root.after(0, self.finish_download_queue)

    def finish_download_queue(self):
        self.is_running = False
        self.active_downloader = None
        self.start_btn.config(text="Start Download", bg=self.accent_color, activebackground=self.accent_hover)
        self.status_lbl.config(text="Finished")
        self.progress_bar.config(value=0)
        self.log("\n[System] All operations completed.")
        messagebox.showinfo("Done", "Download and conversion queue completed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
