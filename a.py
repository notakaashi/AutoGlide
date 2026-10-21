import sys
import glob
import tkinter as tk

print("Python:", sys.executable)
print("Version:", sys.version)

try:
    import PIL
    from PIL import Image, ImageTk
    print("Pillow version:", PIL.__version__)
except Exception as error:
    print("PILLOW PROBLEM:", error)
    raise SystemExit

root = tk.Tk()
files = glob.glob("pictures/login_side*")
print("Found files:", files)

try:
    img = Image.open(files[0])
    print("Opened, size:", img.size)
    photo = ImageTk.PhotoImage(img.resize((300, 380)))
    print("SUCCESS: image loads fine")
except Exception as error:
    print("LOAD PROBLEM:", error)
root.destroy()