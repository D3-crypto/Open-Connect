import subprocess
import time
import hashlib
import threading
import os
import dbus

class ClipboardMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.last_hash = ""
        self.running = False
        
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type == 'wayland':
            self.mode = 'wayland'
            print("[*] Detected Wayland display server")
        else:
            self.mode = 'x11'
            print("[*] Detected X11 display server")

    def _hash_content(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"[*] Started Linux {self.mode.upper()} Clipboard Monitor")

    def stop(self):
        self.running = False

    def get_clipboard_text_dbus(self):
        """Use the GNOME/GSConnect DBus portal to read clipboard silently"""
        try:
            bus = dbus.SessionBus()
            proxy = bus.get_object('org.gnome.Shell.Extensions.GSConnect.Clipboard', '/org/gnome/Shell/Extensions/GSConnect/Clipboard')
            interface = dbus.Interface(proxy, 'org.gnome.Shell.Extensions.GSConnect.Clipboard')
            return str(interface.GetText())
        except Exception:
            return None

    def get_clipboard_text_xclip(self):
        """Fallback for X11/XWayland"""
        try:
            result = subprocess.run(
                ['xclip', '-o', '-selection', 'clipboard'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True, 
                check=False
            )
            if result.returncode == 0:
                return result.stdout
            return ""
        except Exception:
            return ""

    def get_clipboard_text(self):
        if self.mode == 'wayland':
            text = self.get_clipboard_text_dbus()
            if text is not None:
                return text
        return self.get_clipboard_text_xclip()

    def _monitor_loop(self):
        # We need an initial delay to let the main async loop boot fully
        # before we start blasting clipboards that might exist on startup
        time.sleep(2)
        
        # Pre-hash the initial clipboard so we don't instantly broadcast 
        # whatever was already sitting on the clipboard when the app started.
        initial_text = self.get_clipboard_text()
        if initial_text:
            self.last_hash = self._hash_content(initial_text)

        while self.running:
            try:
                current_text = self.get_clipboard_text()
                
                if not current_text:
                    time.sleep(1)
                    continue
                    
                current_hash = self._hash_content(current_text)
                
                if current_hash != self.last_hash:
                    self.last_hash = current_hash
                    # We removed the `if self.last_hash != ""` check since we prepopulated it above
                    self.callback(current_text)
                        
            except Exception as e:
                pass
                
            time.sleep(0.5)

    def set_clipboard(self, text):
        try:
            self.last_hash = self._hash_content(text)
            
            # Try DBus first
            if self.mode == 'wayland':
                try:
                    bus = dbus.SessionBus()
                    proxy = bus.get_object('org.gnome.Shell.Extensions.GSConnect.Clipboard', '/org/gnome/Shell/Extensions/GSConnect/Clipboard')
                    interface = dbus.Interface(proxy, 'org.gnome.Shell.Extensions.GSConnect.Clipboard')
                    interface.SetText(text)
                    return
                except Exception:
                    pass

            # Fallback to xclip
            subprocess.run(
                ['xclip', '-selection', 'clipboard'], 
                input=text, 
                text=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass
