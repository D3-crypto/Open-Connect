import subprocess
import time
import threading

def on_clipboard_change():
    print("CLIPBOARD CHANGED!")

def watch_clipboard():
    print("Starting wl-paste watch mode...")
    # `wl-paste -w` runs forever and executes the given command whenever the clipboard changes.
    # We use a dummy command like `echo` just so we can read its output to know a change happened.
    process = subprocess.Popen(['wl-paste', '-w', 'echo', 'CHANGED'], stdout=subprocess.PIPE, text=True)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        on_clipboard_change()

t = threading.Thread(target=watch_clipboard, daemon=True)
t.start()

time.sleep(10) # Let it run for a bit
print("Done watching.")
