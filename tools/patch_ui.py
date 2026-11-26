"""Canvas artwork and keyboard-accessible controls for the offline installer."""
import math
import tkinter as tk

CREAM = '#f3efe4'
INK = '#18191f'
YELLOW = '#ffd63e'
BLUE = '#3067ff'
MUTED = '#666b79'
WHITE = '#fffdf8'


def rounded(canvas, box, radius=18, **options):
    x, y, right, bottom = box
    r = radius
    return canvas.create_polygon(
        x+r, y, right-r, y, right, y, right, y+r,
        right, bottom-r, right, bottom, right-r, bottom,
        x+r, bottom, x, bottom, x, bottom-r, x, y+r, x, y,
        smooth=True, splinesteps=24, **options)


class ActionButton(tk.Canvas):
    """Rounded button with hover, pressed, disabled and keyboard focus states."""
    def __init__(self, parent, text, command, fill=WHITE, width=150):
        super().__init__(parent, width=width, height=54, bg=CREAM,
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.label, self.command, self.fill = text, command, fill
        self.disabled = self.hover = self.pressed = False
        self.bind('<Configure>', lambda e: self.draw())
        self.bind('<Enter>', lambda e: self.set_hover(True))
        self.bind('<Leave>', lambda e: self.set_hover(False))
        self.bind('<ButtonPress-1>', self.press)
        self.bind('<ButtonRelease-1>', self.release)
        self.bind('<FocusIn>', lambda e: self.draw())
        self.bind('<FocusOut>', lambda e: self.draw())
        self.bind('<space>', lambda e: self.invoke())
        self.bind('<Return>', lambda e: self.invoke())

    def configure(self, cnf=None, **kwargs):
        state = kwargs.pop('state', None)
        if state is not None:
            self.disabled = state == 'disabled'
            super().configure(takefocus=not self.disabled,
                              cursor='arrow' if self.disabled else 'hand2')
            self.pressed = False
            self.draw()
        return super().configure(cnf, **kwargs)

    def set_hover(self, value):
        self.hover = value
        if not value:
            self.pressed = False
        self.draw()

    def press(self, event):
        if not self.disabled:
            self.focus_set()
            self.pressed = True
            self.draw()

    def release(self, event):
        invoke = self.pressed and 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        self.pressed = False
        self.draw()
        if invoke:
            self.invoke()

    def invoke(self):
        if not self.disabled:
            self.command()
        return 'break'

    def draw(self):
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        offset = 3 if self.pressed else 0
        color = '#dedbd2' if self.disabled else (YELLOW if self.hover else self.fill)
        rounded(self, (4, 5, w-1, h-1), fill=INK)
        rounded(self, (1+offset, 1+offset, w-5+offset, h-5+offset),
                fill=color, outline=INK, width=2)
        self.create_text(w/2-2+offset, h/2-3+offset, text=self.label,
                         font=('Yu Gothic UI', 11, 'bold'),
                         fill=MUTED if self.disabled else INK)
        if self.focus_get() == self and not self.disabled:
            rounded(self, (7, 7, w-11, h-11), radius=13,
                    fill='', outline=BLUE, width=2, dash=(3, 3))


def draw_poster(c):
    """Original vector illustration, independent of game/community assets."""
    c.create_oval(775, -230, 1190, 185, outline='#e5e1d7', width=6)
    c.create_oval(-270, 270, 65, 605, outline='#e5e1d7', width=6)
    c.create_line(0, 76, 1000, 76, fill=INK, width=2)
    rounded(c, (42, 21, 79, 58), radius=10, fill=YELLOW, outline=INK, width=2)
    c.create_text(61, 38, text='jv', font=('Segoe UI', 20, 'bold'), fill=INK)
    c.create_text(91, 38, text='JUST VOLLEYBALL', anchor='w',
                  font=('Segoe UI', 14, 'bold'), fill=INK)
    c.create_text(290, 40, text='日本語化パッチ', anchor='w',
                  font=('Yu Gothic UI', 10), fill=MUTED)
    rounded(c, (833, 24, 958, 54), radius=15, fill=WHITE, outline=INK, width=2)
    c.create_text(895, 39, text='FAN MADE  /  JA', font=('Segoe UI', 9, 'bold'), fill=INK)
    rounded(c, (44, 107, 265, 134), radius=14, fill=WHITE, outline=INK, width=2)
    c.create_text(154, 120, text='●  COMMUNITY TRANSLATION',
                  font=('Segoe UI', 9, 'bold'), fill=BLUE)
    c.create_text(41, 182, text='Just Volleyball', anchor='w',
                  font=('Segoe UI', 43, 'bold'), fill=INK)
    rounded(c, (48, 232, 343, 300), fill=INK)
    rounded(c, (44, 227, 339, 295), fill=YELLOW, outline=INK, width=2)
    c.create_text(191, 259, text='日本語で、', font=('Yu Gothic UI', 34, 'bold'), fill=INK)
    c.create_text(352, 259, text='プレイ。', anchor='w',
                  font=('Yu Gothic UI', 34, 'bold'), fill=BLUE)
    c.create_text(46, 327, text='いつものコートを、日本語で楽しもう。', anchor='w',
                  font=('Yu Gothic UI', 12), fill=MUTED)
    c.create_text(46, 355, text='ゲームを終了してから、パッチを適用してください。', anchor='w',
                  font=('Yu Gothic UI', 10), fill=MUTED)

    def card(cx, cy, angle, color, title, subtitle, ball=False):
        a = math.radians(angle)

        def points(coords):
            result = []
            for x, y in zip(coords[::2], coords[1::2]):
                result.extend((cx+x*math.cos(a)-y*math.sin(a),
                               cy+x*math.sin(a)+y*math.cos(a)))
            return result

        def poly(coords, **kwargs):
            c.create_polygon(points(coords), **kwargs)

        poly([-78, -100, 83, -100, 83, 110, -78, 110], fill=INK,
             smooth=True, splinesteps=20)
        poly([-83, -106, 78, -106, 78, 104, -83, 104], fill=color,
             outline=INK, width=2, smooth=True, splinesteps=20)
        for line in ([-80, 38, 76, 38], [-80, 68, 76, 68], [0, -103, 0, 68]):
            c.create_line(points(line), fill=WHITE, width=2)
        poly([-80, 69, 75, 69, 72, 97, -77, 97], fill=WHITE)
        tx, ty = points([-65, -78])
        c.create_text(tx, ty, text=title, anchor='w', angle=-angle,
                      font=('Segoe UI', 26, 'bold'), fill=INK)
        if ball:
            x, y = points([0, -2])
            c.create_oval(x-47, y-47, x+47, y+47, fill=WHITE, outline=INK, width=3)
            c.create_arc(x-47, y-47, x+47, y+47, start=25, extent=160,
                         style='arc', outline=BLUE, width=9)
            c.create_arc(x-47, y-47, x+47, y+47, start=205, extent=160,
                         style='arc', outline=YELLOW, width=9)
            c.create_line(x-43, y-14, x+17, y+43, fill=INK, width=2, smooth=True)
            c.create_line(x-18, y-43, x+43, y+13, fill=INK, width=2, smooth=True)
        else:
            poly([-33, -22, -15, -36, 15, -36, 33, -22, 45, -2,
                  28, 9, 21, 0, 21, 49, -21, 49, -21, 0, -28, 9, -45, -2],
                 fill=WHITE, outline=INK, width=2)
            tx, ty = points([0, 16])
            c.create_text(tx, ty, text='JA', angle=-angle,
                          font=('Segoe UI', 20, 'bold'), fill=BLUE)
        tx, ty = points([0, 83])
        c.create_text(tx, ty, text=subtitle, angle=-angle,
                      font=('Segoe UI', 10, 'bold'), fill=INK)

    card(729, 260, -12, YELLOW, '01', 'YOUR COURT')
    card(858, 259, 12, '#bda8ff', 'JA', 'YOUR LANGUAGE')
    card(794, 227, 3, YELLOW, 'PLAY', 'JUST VOLLEYBALL', ball=True)
    rounded(c, (835, 107, 949, 137), fill=INK)
    rounded(c, (832, 103, 946, 133), fill='#ed4054', outline=INK, width=2)
    c.create_text(889, 118, text='日本語で遊ぼう', font=('Yu Gothic UI', 10, 'bold'), fill=WHITE)
