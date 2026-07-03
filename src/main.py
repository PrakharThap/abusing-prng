import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import main as gui_main


def main():
    gui_main()


if __name__ == "__main__":
    main()
