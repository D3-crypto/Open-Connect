import subprocess
import time

print("Testing raw wl-paste loop...")
for i in range(5):
    print(f"Iteration {i}")
    # --no-newline is good, but let's see if we need to suppress stderr or use a different type
    result = subprocess.run(
        ['wl-paste', '--no-newline'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.DEVNULL, 
        text=True
    )
    time.sleep(0.5)
print("Done.")
