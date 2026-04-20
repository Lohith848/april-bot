import asyncio
import threading
import tkinter as tk
from telegram_client import start_client
from ui.main_window import AprilUI

# Create global async loop
loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Run loop in background thread
threading.Thread(target=start_loop, daemon=True).start()

# Start Telegram client
asyncio.run_coroutine_threadsafe(start_client(), loop)

# Start UI
root = tk.Tk()
app = AprilUI(root, loop)
root.mainloop()