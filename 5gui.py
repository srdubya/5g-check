#!/usr/bin/env python3
import os.path
import sys
import tkinter as tk
from tkinter import font
from tkinter import ttk

from gateway import Gateway


class UI:
    GREEN = '#00FF00'
    RED = '#FF0000'

    def __init__(self):
        self._root = tk.Tk()
        self._root.title(f"{os.path.basename(sys.argv[0])}")
        # root.geometry('300x200')

        self._main_frame = tk.Frame(self._root)
        self._main_frame.pack(expand=True, fill=tk.BOTH, pady=5, padx=5)

        self._space_frame = tk.Frame(self._main_frame)
        self._space_frame.pack(side=tk.TOP, fill=tk.X)

        self._progress = ttk.Progressbar(self._space_frame,
                                         orient=tk.HORIZONTAL, mode='determinate', length=10, maximum=10)
        self._progress.pack(side=tk.TOP, fill=tk.X)

        self._button_frame = tk.Frame(self._main_frame)
        self._button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._label_font = font.Font(size=24, weight='bold')
        self._band_label = tk.Label(self._button_frame, text='5G', foreground=self.GREEN, font=self._label_font)
        self._band_label.pack(side=tk.LEFT)

        self._exit_button = tk.Button(self._button_frame, text='Exit', command=self._root.destroy)
        self._exit_button.pack(side=tk.RIGHT)

        self.ticker = 0
        self._callback = None

    def every_sec(self):
        if self.ticker >= 10:
            self._progress['value'] = 0
            self.ticker = 0
            self._callback()
        else:
            self._progress['value'] += 1
            self.ticker += 1
        self._root.after(1_000, self.every_sec)

    def run_loop(self, callback):
        self._callback = callback
        self._root.after(1_000, self.every_sec)
        self._root.mainloop()

    def set_band(self, value):
        if '5G' in value:
            self._band_label['text'] = '5G'
            self._band_label.config(foreground=self.GREEN)
        else:
            self._band_label['text'] = value
            self._band_label.config(foreground=self.RED)


auth_header = Gateway.sign_in()
ui = UI()


def main():
    global auth_header, ui
    if not auth_header:
        if len(sys.argv) < 2:
            print("Please add the authentication cookie, or set up `~/.5g-secret`.", file=sys.stderr)
            print(f"Usage:  {os.path.basename(sys.argv[0])} <authorization cookie>", file=sys.stderr)
            exit(1)
        else:
            auth_header = sys.argv[1]
    ui.run_loop(update)


def update():
    global auth_header, ui
    auth_header, resp = Gateway.get_status(auth_header)
    ui.set_band(resp['modemtype'])


if __name__ == '__main__':
    main()
