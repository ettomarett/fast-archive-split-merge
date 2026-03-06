"""
Fast Archive & Split — entry point.
"""
import sys

# Ensure src is on path when run as script
if __name__ == "__main__":
    import os
    top = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if top not in sys.path:
        sys.path.insert(0, top)

import customtkinter as ctk
from src.ui.main_window import MainWindow


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.minsize(500, 400)
    root.title("Fast Archive & Split")
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
