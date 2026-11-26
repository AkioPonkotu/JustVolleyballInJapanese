"""Double-clickable Windows patch application; command-line flags remain available."""
from pathlib import Path
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from patch_game import main as patch_main
from release_data import verified_payloads
from steam_game import find_game_directory
from patch_ui import ActionButton, BLUE, CREAM, INK, MUTED, WHITE, YELLOW, draw_poster, rounded


def package_directory():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'patch-data'
    return Path(__file__).resolve().parents[1] / 'dist/just-volleyball-ja'


def show_app():
    root = tk.Tk()
    root.title('Just Volleyball 日本語化パッチ')
    root.geometry('1000x710')
    root.minsize(1000, 710)
    root.configure(bg=CREAM)
    # Keep a readable poster at the minimum size; extra space stays around it.
    panel = tk.Frame(root, bg=CREAM, width=1000, height=710)
    panel.place(relx=.5, rely=.5, anchor='center')
    panel.pack_propagate(False)
    art = tk.Canvas(panel, width=1000, height=710, bg=CREAM, highlightthickness=0)
    art.place(x=0, y=0)
    draw_poster(art)
    art.create_line(44, 395, 956, 395, fill='#d9d5cb', width=1)
    art.create_text(45, 428, text='01  ゲームフォルダーを選択', anchor='w',
                    font=('Yu Gothic UI', 12, 'bold'), fill=INK)
    art.create_text(955, 428, text='volleyball.exe があるフォルダー', anchor='e',
                    font=('Yu Gothic UI', 10), fill=MUTED)
    detected_game = find_game_directory()
    path = tk.StringVar(value=str(detected_game) if detected_game else '')
    rounded(art, (44, 452, 812, 501), radius=12, fill=WHITE, outline=INK, width=2)
    entry = tk.Entry(panel, textvariable=path, font=('Yu Gothic UI', 11),
                     bg=WHITE, fg=INK, insertbackground=BLUE, relief='flat',
                     selectbackground=BLUE, selectforeground=WHITE)
    entry.place(x=58, y=464, width=738, height=26)

    def browse():
        selected = filedialog.askdirectory(parent=root, title='Just Volleyball のゲームフォルダーを選択',
                                           initialdir=path.get() or None)
        if selected:
            path.set(selected)

    browse_button = ActionButton(panel, text='参照…', command=browse, width=128)
    browse_button.place(x=830, y=451)
    status = tk.StringVar(value='Steamからゲームフォルダーを検出しました。場所を確認して適用してください。'
                          if detected_game else
                          'ゲームフォルダーを検出できませんでした。「参照…」から選択してください。')
    status_label = tk.Label(panel, textvariable=status, wraplength=900, anchor='w',
                            justify='left', font=('Yu Gothic UI', 10), bg=CREAM, fg=MUTED)
    status_label.place(x=44, y=604, width=912, height=42)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Patch.Horizontal.TProgressbar', background=BLUE,
                    troughcolor='#e5e1d7', borderwidth=0, lightcolor=BLUE, darkcolor=BLUE)
    progress = ttk.Progressbar(panel, mode='indeterminate', style='Patch.Horizontal.TProgressbar')
    art.create_line(44, 658, 956, 658, fill='#d9d5cb')
    art.create_text(44, 683, text='Windows / Steam Build 26937150 専用', anchor='w',
                    font=('Yu Gothic UI', 9), fill=MUTED)
    art.create_text(955, 683, text='非公式ファンメイド  ·  オフライン用', anchor='e',
                    font=('Yu Gothic UI', 9), fill=MUTED)
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
        progress.stop()
        progress.place_forget()
        for control in (entry, browse_button, install, restore):
            control.configure(state='normal')
        if error:
            status_label.configure(fg='#b6263c')
            status.set('処理を完了できませんでした。詳細を確認してください。')
            messagebox.showerror('処理に失敗しました', error, parent=root)
        else:
            status_label.configure(fg=BLUE)
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
        status_label.configure(fg=BLUE)
        progress.place(x=45, y=594, width=908, height=4)
        progress.start(12)

        def worker():
            error = None
            try:
                patch_main(['--game-dir', str(game), '--package', str(package_directory()), action])
            except Exception as exc:
                error = str(exc)
            events.put((action, error))

        threading.Thread(target=worker, daemon=False).start()
        root.after(100, finish)

    install = ActionButton(panel, text='日本語化を適用  →',
                           command=lambda: start('--install'), fill=YELLOW, width=256)
    install.place(x=44, y=526)
    restore = ActionButton(panel, text='元に戻す', command=lambda: start('--restore'), width=160)
    restore.place(x=316, y=526)
    tk.Button(panel, text='ライセンス', relief='flat', bg=CREAM, fg=BLUE,
              cursor='hand2', command=lambda: os.startfile(package_directory() / 'licenses')).place(x=456, y=669)
    art.create_text(955, 551, text='バックアップを作成して適用します。', anchor='e',
                    font=('Yu Gothic UI', 10), fill=MUTED)
    entry.focus_set()

    def close():
        if busy:
            messagebox.showinfo('処理中', '処理が完了してから閉じてください。', parent=root)
        else:
            root.destroy()

    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Frozen applications always use their embedded payloads by default.
        args = sys.argv[1:]
        if args == ['--verify-package']:
            verified_payloads(package_directory())
            print('Embedded patch payloads verified.')
            sys.exit(0)
        if '--package' not in args:
            args = ['--package', str(package_directory())] + args
        try:
            patch_main(args)
        except Exception as exc:
            print(f'Patch failed: {exc}', file=sys.stderr)
            sys.exit(1)
    else:
        show_app()
