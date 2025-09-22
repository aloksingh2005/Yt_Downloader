# main.py
# Requirements:
#   pip install yt-dlp customtkinter Pillow
#   FFmpeg must be installed and added to PATH

import os
import re
import threading
import yt_dlp
import customtkinter as ctk
from tkinter import filedialog, messagebox
from yt_dlp.utils import DownloadError

# Clean filename helper
BAD = r'[<>:"/\\|?*]'
fix = lambda s, ext: re.sub(BAD, '', s)[:180] + '.' + ext
clean = lambda u: u.strip().strip('\'" ,')


class SocialMediaDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Social Media Downloader (YouTube / Instagram / Facebook)")
        self.geometry("650x500")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.setup_ui()

    def setup_ui(self):
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Social Media Downloader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(15, 10))

        # Supported platforms info
        info_label = ctk.CTkLabel(
            self,
            text="Supports: YouTube, Instagram, Facebook",
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=(0, 15))

        # URLs input section
        url_frame = ctk.CTkFrame(self)
        url_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            url_frame,
            text="URLs (one per line):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        self.url_textbox = ctk.CTkTextbox(url_frame, height=120, width=580)
        self.url_textbox.insert(
            "0.0",
            "Paste URLs here (one per line)...\n\nExamples:\n"
            "https://www.instagram.com/p/xyz123/\n"
            "https://www.facebook.com/watch/?v=123456789\n"
            "https://www.youtube.com/watch?v=abc123"
        )
        self.url_textbox.bind("<FocusIn>", self.clear_placeholder)
        self.url_textbox.pack(pady=(5, 15), padx=15)

        # Download format section
        format_frame = ctk.CTkFrame(self)
        format_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            format_frame,
            text="Download Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        self.format_var = ctk.StringVar(value="mp4")
        format_radio_frame = ctk.CTkFrame(format_frame)
        format_radio_frame.pack(pady=5)

        ctk.CTkRadioButton(
            format_radio_frame,
            text="Video (MP4)",
            variable=self.format_var,
            value="mp4"
        ).pack(side="left", padx=20)

        ctk.CTkRadioButton(
            format_radio_frame,
            text="Audio (MP3)",
            variable=self.format_var,
            value="mp3"
        ).pack(side="left", padx=20)

        # Quality/Resolution section
        quality_frame = ctk.CTkFrame(format_frame)
        quality_frame.pack(pady=(10, 15))

        ctk.CTkLabel(quality_frame, text="Quality/Resolution:").pack(pady=(5, 0))

        self.quality_var = ctk.StringVar(value="best")
        quality_options = ["best", "1080p", "720p", "480p", "360p", "240p", "144p"]
        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=quality_options,
            variable=self.quality_var
        )
        self.quality_menu.pack(pady=5)

        # Output directory section
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            output_frame,
            text="Output Directory:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        dir_frame = ctk.CTkFrame(output_frame)
        dir_frame.pack(pady=(5, 15), fill="x", padx=15)

        self.output_dir = ctk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        self.dir_entry = ctk.CTkEntry(dir_frame, textvariable=self.output_dir)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            dir_frame,
            text="Browse",
            width=80,
            command=self.browse_directory
        ).pack(side="right")

        # Progress section
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=580)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5, padx=15)

        self.status_label = ctk.CTkLabel(progress_frame, text="Ready to download")
        self.status_label.pack(pady=(5, 15))

        # Download button
        self.download_button = ctk.CTkButton(
            self,
            text="Start Download",
            command=self.start_download,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        )
        self.download_button.pack(pady=20)

    def clear_placeholder(self, event):
        current_text = self.url_textbox.get("0.0", "end-1c")
        if "Paste URLs here" in current_text:
            self.url_textbox.delete("0.0", "end")

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.output_dir.set(directory)

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def start_download(self):
        urls_text = self.url_textbox.get("0.0", "end-1c")
        urls = [
            clean(url) for url in urls_text.splitlines()
            if clean(url) and "Paste URLs here" not in url
        ]

        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL")
            return

        if not os.path.exists(self.output_dir.get()):
            messagebox.showerror("Error", "Output directory does not exist")
            return

        self.download_button.configure(state="disabled", text="Downloading...")
        threading.Thread(
            target=self.download_worker,
            args=(urls,),
            daemon=True
        ).start()

    def download_worker(self, urls):
        try:
            total_urls = len(urls)
            for i, url in enumerate(urls, 1):
                self.update_status(f"Processing {i}/{total_urls}: Analyzing URL...")
                try:
                    self.download_single_url(url, i, total_urls)
                except Exception as e:
                    messagebox.showerror(
                        "Download Error",
                        f"Failed to download {i}/{total_urls}\n{url}\n\nError: {str(e)}"
                    )
                    continue
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"Unexpected error: {str(e)}")
        finally:
            self.download_button.configure(state="normal", text="Start Download")
            self.progress_bar.set(0)
            self.update_status("Ready")

    def download_single_url(self, url, current, total):
        is_audio = self.format_var.get() == "mp3"

        if is_audio:
            format_selector = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            quality = self.quality_var.get()
            if quality == "best":
                format_selector = 'best[ext=mp4]/best'
            else:
                height = quality.replace('p', '')
                format_selector = (
                    f'best[height<={height}][ext=mp4]/'
                    f'best[height<={height}]/best'
                )
            postprocessors = []

        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(self.output_dir.get(), '%(title).180s.%(ext)s'),
            'postprocessors': postprocessors,
            'progress_hooks': [lambda d: self.progress_hook(d, current, total)],
            'noplaylist': True,
            'extract_flat': False,
        }

        if 'instagram.com' in url or 'facebook.com' in url or 'fb.watch' in url:
            ydl_opts['writesubtitles'] = False
            ydl_opts['writeautomaticsub'] = False

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except DownloadError as e:
            raise Exception(f"Download failed: {str(e)}")

    def progress_hook(self, d, current_url, total_urls):
        if d['status'] == 'downloading':
            base_progress = (current_url - 1) / total_urls
            current_progress = 0
            if d.get('total_bytes'):
                current_progress = (
                    d['downloaded_bytes'] / d['total_bytes']
                ) / total_urls
            elif d.get('total_bytes_estimate'):
                current_progress = (
                    d['downloaded_bytes'] / d['total_bytes_estimate']
                ) / total_urls

            overall_progress = base_progress + current_progress
            self.progress_bar.set(overall_progress)

            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'Unknown speed')
            self.update_status(
                f"Downloading {current_url}/{total_urls}: {percent} at {speed}"
            )

        elif d['status'] == 'finished':
            self.update_status(f"Processing {current_url}/{total_urls}: Converting...")


def main():
    app = SocialMediaDownloader()
    app.mainloop()


if __name__ == "__main__":
    main()
