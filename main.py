# main.py  ───────────
# pip install yt-dlp customtkinter
# FFmpeg binary must be in PATH

import os, re, threading, yt_dlp, customtkinter as ctk
from tkinter import filedialog, messagebox
from yt_dlp.utils import DownloadError

BAD = r'[<>:"/\\|?*]'
fix  = lambda s, ext: re.sub(BAD, '', s)[:180] + '.' + ext
clean = lambda u: u.strip().strip('\'" ,')

class YTApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube MP3 / MP4 Downloader"); self.geometry("580x500")
        ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")

        # URLs
        self.box = ctk.CTkTextbox(self, height=120, width=540)
        self.box.insert("0.0", "Paste one URL per line …")
        self.box.bind("<FocusIn>", lambda *_: self.box.delete("0.0","end"))
        self.box.pack(pady=(15,5))

        # Mode
        self.mode = ctk.StringVar(value="mp3")
        fr = ctk.CTkFrame(self); fr.pack(pady=5)
        ctk.CTkRadioButton(fr,text="Audio (MP3 128 kbps)",variable=self.mode,value="mp3")\
            .pack(side="left",padx=10)
        ctk.CTkRadioButton(fr,text="Video (MP4)",variable=self.mode,value="mp4")\
            .pack(side="left")

        # Resolution (only when MP4)
        self.res = ctk.StringVar(value="best")
        ctk.CTkLabel(self,text="MP4 resolution:").pack(pady=(5,0))
        res_opts = ["best","2160","1440","1080","720","480","360","240","144"]
        self.res_menu = ctk.CTkOptionMenu(self, values=res_opts, variable=self.res)
        self.res_menu.pack()

        # Path
        pf = ctk.CTkFrame(self); pf.pack(pady=5)
        self.out = ctk.StringVar(value=os.path.join(os.path.expanduser("~"),"Downloads"))
        ctk.CTkEntry(pf,textvariable=self.out,width=430).pack(side="left",padx=5)
        ctk.CTkButton(pf,text="Browse",command=lambda:
            self.out.set(filedialog.askdirectory() or self.out.get()))\
            .pack(side="left")

        # Progress + status
        self.bar=ctk.CTkProgressBar(self,width=540); self.bar.set(0); self.bar.pack(pady=(10,0))
        self.stat=ctk.CTkLabel(self,text="Idle"); self.stat.pack(pady=5)

        # Go
        self.go=ctk.CTkButton(self,text="Start Download",command=self.launch); self.go.pack()

    # ---------- helpers ----------
    def info(self,t): self.stat.configure(text=t); self.update_idletasks()

    # ---------- workflow ----------
    def launch(self):
        urls=[clean(u) for u in self.box.get("0.0","end").splitlines() if clean(u)]
        if not urls: return messagebox.showerror("Error","No URLs provided")
        self.go.configure(state="disabled")
        threading.Thread(target=self.queue,args=(urls,),daemon=True).start()

    def queue(self,urls):
        for i,u in enumerate(urls,1):
            self.info(f"{i}/{len(urls)} • analysing…")
            try: self.dl(u)
            except Exception as e: messagebox.showerror("Failed",f"{u}\n{e}")
        self.bar.set(0); self.info("All done ✅"); self.go.configure(state="normal")

    # ---------- core ----------
    def dl(self,url):
        audio = self.mode.get()=="mp3"
        if audio:
            fmt='bestaudio'
            pp=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"128"}]
        else:
            r=self.res.get();                   # "best" or height string
            if r=="best": fmt='bv*+ba/b'        # any best mp4 stream
            else:           fmt=f"bv*[height<={r}][ext=mp4]+ba[ext=m4a]/b[height<={r}][ext=mp4]"
            pp=[]                                # mp4 remux implicit

        def hook(d):
            if d["status"]=="downloading":
                tot=d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                self.bar.set(d["downloaded_bytes"]/tot)
                self.info(f"{d['_percent_str'].strip()} | {d.get('speed','?')}/s")
            elif d["status"]=="finished": self.bar.set(1); self.info("Processing…")

        opts=dict(format=fmt,outtmpl=os.path.join(self.out.get(),"%(title)s.%(ext)s"),
                  noplaylist=True,progress_hooks=[hook],quiet=True,
                  merge_output_format="mp4" if not audio else None,
                  postprocessors=pp)
        try:
            yt_dlp.YoutubeDL(opts).download([url])
        except DownloadError as e:
            raise RuntimeError(e)

# run
if __name__=="__main__": YTApp().mainloop()
