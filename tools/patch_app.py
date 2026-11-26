"""Double-clickable Windows patch application; command-line flags remain available."""
import ctypes
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from patch_game import main as patch_main


def package_directory():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1] / 'dist/just-volleyball-ja'


def show_app():
    # Keep CLI output available for scripts, but hide the console on double-click.
    if os.name == 'nt' and getattr(sys, 'frozen', False):
        console = ctypes.windll.kernel32.GetConsoleWindow()
        if console:
            ctypes.windll.user32.ShowWindow(console, 0)
    root = tk.Tk()
    root.title('Just Volleyball 日本語化パッチ')
    root.geometry('650x320')
    root.minsize(650, 320)
    panel = ttk.Frame(root, padding=24)
    panel.pack(fill='both', expand=True)
    ttk.Label(panel, text='Just Volleyball 日本語化パッチ', font=('Yu Gothic UI', 16, 'bold')).pack(anchor='w')
    ttk.Label(panel, text='Windows / Steam Build ID 26937150 専用・オフライン用\nゲームを終了してから操作してください。').pack(anchor='w', pady=(8, 18))
    ttk.Label(panel, text='ゲームフォルダー（volleyball.exe がある場所）').pack(anchor='w')
    path = tk.StringVar()
    row = ttk.Frame(panel)
    row.pack(fill='x', pady=(4, 14))
    entry = ttk.Entry(row, textvariable=path)
    entry.pack(side='left', fill='x', expand=True)

    def browse():
        selected = filedialog.askdirectory(parent=root, title='Just Volleyball のゲームフォルダーを選択')
        if selected:
            path.set(selected)

    browse_button = ttk.Button(row, text='参照…', command=browse)
    browse_button.pack(side='left', padx=(8, 0))
    buttons = ttk.Frame(panel)
    buttons.pack(anchor='w')
    status = tk.StringVar(value='Steamの「管理 → ローカルファイルを閲覧」で場所を確認できます。')
    ttk.Label(panel, textvariable=status, wraplength=595).pack(anchor='w', pady=(16, 0))
    events = queue.Queue()
    busy = False

    def finish():
        nonlocal busy
        try:
            action, error = events.get_nowait()
        except queue.Empty:
            root.after(100, finish)
            return
        busy = False
        for control in (entry, browse_button, install, restore):
            control.configure(state='normal')
        if error:
            status.set('処理を完了できませんでした。詳細を確認してください。')
            messagebox.showerror('処理に失敗しました', error, parent=root)
        else:
            text = '日本語化パッチを適用しました。' if action == '--install' else '元のゲームファイルへ戻しました。'
            status.set(text)
            messagebox.showinfo('完了', text, parent=root)

    def start(action):
        nonlocal busy
        if busy:
            return
        game = Path(path.get().strip())
        if not path.get().strip() or not all((game / name).is_file() for name in ('volleyball.exe', 'volleyball.pck')):
            messagebox.showerror('フォルダーを確認してください', 'volleyball.exe と volleyball.pck があるフォルダーを選択してください。', parent=root)
            return
        busy = True
        for control in (entry, browse_button, install, restore):
            control.configure(state='disabled')
        status.set('処理中です。完了するまでお待ちください…')

        def worker():
            error = None
            try:
                patch_main(['--game-dir', str(game), '--package', str(package_directory()), action])
            except Exception as exc:
                error = str(exc)
            events.put((action, error))

        threading.Thread(target=worker, daemon=False).start()
        root.after(100, finish)

    install = ttk.Button(buttons, text='適用', command=lambda: start('--install'), width=16)
    install.pack(side='left')
    restore = ttk.Button(buttons, text='解除', command=lambda: start('--restore'), width=16)
    restore.pack(side='left', padx=8)

    def close():
        if busy:
            messagebox.showinfo('処理中', '処理が完了してから閉じてください。', parent=root)
        else:
            root.destroy()

    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # External payloads live beside the EXE, not in PyInstaller's temp folder.
        args = sys.argv[1:]
        if '--package' not in args:
            args = ['--package', str(package_directory())] + args
        try:
            patch_main(args)
        except Exception as exc:
            print(f'Patch failed: {exc}', file=sys.stderr)
            sys.exit(1)
    else:
        show_app()
