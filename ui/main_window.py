import tkinter as tk
import asyncio
import threading
import time
from telegram_client import send_and_receive

# 🎨 ChatGPT-like colors
BG_COLOR = "#0b0f19"
USER_COLOR = "#2563eb"
BOT_COLOR = "#1f2937"
TEXT_COLOR = "#e5e7eb"
ENTRY_BG = "#111827"

class AprilUI:
    def __init__(self, root, loop):
        self.root = root
        self.loop = loop
        self.typing_label = None
        self.typing_running = False

        root.title("April AI")
        root.geometry("520x650")
        root.configure(bg=BG_COLOR)

        # 🔥 Scrollable chat frame (ChatGPT style)
        self.canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
        self.frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.scrollbar = tk.Scrollbar(root, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))

        # 🔽 Input area
        input_frame = tk.Frame(root, bg=BG_COLOR)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.entry = tk.Entry(
            input_frame,
            bg=ENTRY_BG,
            fg="white",
            insertbackground="white",
            font=("Segoe UI", 11),
            bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))

        self.entry.bind("<Return>", lambda e: self.send())

        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send,
            bg=USER_COLOR,
            fg="white",
            bd=0,
            padx=15
        )
        send_btn.pack(side=tk.RIGHT)

    # 💬 Chat bubble
    def add_message(self, text, is_user):
        bubble = tk.Label(
            self.frame,
            text=text,
            bg=USER_COLOR if is_user else BOT_COLOR,
            fg=TEXT_COLOR,
            wraplength=350,
            justify="left",
            padx=10,
            pady=8,
            font=("Segoe UI", 10)
        )

        bubble.pack(
            anchor="e" if is_user else "w",
            pady=5,
            padx=10
        )

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # 🔥 Typing (SINGLE CLEAN LABEL)
    def show_typing(self):
        self.typing_running = True

        self.typing_label = tk.Label(
            self.frame,
            text="April is typing...",
            bg=BG_COLOR,
            fg="#9ca3af",
            font=("Segoe UI", 9, "italic")
        )
        self.typing_label.pack(anchor="w", padx=10, pady=5)

        def animate():
            dots = ["", ".", "..", "..."]
            i = 0
            while self.typing_running:
                text = "April is typing" + dots[i % 4]
                self.root.after(0, lambda t=text: self.typing_label.config(text=t))
                time.sleep(0.5)
                i += 1

        threading.Thread(target=animate, daemon=True).start()

    def remove_typing(self):
        self.typing_running = False
        if self.typing_label:
            self.typing_label.destroy()
            self.typing_label = None

    # 🚀 Send message
    def send(self):
        msg = self.entry.get().strip()
        if not msg:
            return

        self.add_message(msg, True)
        self.entry.delete(0, tk.END)

        self.show_typing()

        threading.Thread(target=self.get_reply, args=(msg,), daemon=True).start()

    # ⚡ Get reply
    def get_reply(self, msg):
        future = asyncio.run_coroutine_threadsafe(
            send_and_receive(msg), self.loop
        )
        reply = future.result()

        self.root.after(0, self.remove_typing)
        self.root.after(0, lambda: self.add_message(reply, False))