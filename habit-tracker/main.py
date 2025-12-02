from __future__ import annotations
import json
import datetime
import math
import os
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any
from pathlib import Path

# Config
DEFAULT_FILE = "habits.json"

DEFAULT_HABITS = [
    "Drink Water",
    "Read 20 minutes",
    "Exercise 10 minutes",
    "Meditate",
    "Journal",
    "Sleep Early",
    "Coding practice"
]

# UI colors (gradient light -> ocean)
GRAD_TOP = (243, 251, 255)   # #F3FBFF
GRAD_BOTTOM = (45, 156, 219) # #2D9CDB
CARD_TOP = (255, 255, 255)
CARD_BOTTOM = (235, 248, 255)

TEXT = "#083047"
MUTED = "#5F7A89"
ICON_SIZE = 28
CARD_WIDTH = 260
CARD_HEIGHT = 100  # option B: medium cards

# Core functions (testable)
def load_habits(filename: str = DEFAULT_FILE) -> Dict[str, Dict[str, Any]]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_habits(habits: Dict[str, Dict[str, Any]], filename: str = DEFAULT_FILE) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)

def add_habit(habits: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Dict[str, Any]]:
    name = name.strip()
    if not name:
        raise ValueError("Habit name cannot be empty")
    if name in habits:
        raise ValueError("Habit already exists")
    habits[name] = {"done": False, "streak": 0, "last_done": None}
    return habits

def mark_done(habits: Dict[str, Dict[str, Any]], name: str, today: str | None = None) -> Dict[str, Dict[str, Any]]:
    if name not in habits:
        raise KeyError("Habit not found")
    if today is None:
        today = datetime.date.today().isoformat()
    info = habits[name]
    last = info.get("last_done")
    # update streak only if last was yesterday
    if last:
        last_date = datetime.date.fromisoformat(last)
        if last_date == datetime.date.fromisoformat(today) - datetime.timedelta(days=1):
            info["streak"] = info.get("streak", 0) + 1
        elif last_date == datetime.date.fromisoformat(today):
            # already marked today — no change
            pass
        else:
            info["streak"] = 1
    else:
        info["streak"] = 1
    info["done"] = True
    info["last_done"] = today
    habits[name] = info
    return habits

def unmark_habit(habits: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Dict[str, Any]]:
    if name not in habits:
        raise KeyError("Habit not found")
    habits[name]["done"] = False
    return habits

def delete_habit(habits: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Dict[str, Any]]:
    if name not in habits:
        raise KeyError("Habit not found")
    del habits[name]
    return habits

def reset_daily(habits: Dict[str, Dict[str, Any]], today: str | None = None) -> Dict[str, Dict[str, Any]]:

    if today is None:
        today = datetime.date.today().isoformat()
    meta = habits.get("_meta", {})
    last_reset = meta.get("last_reset")
    if last_reset == today:
        return habits  # already reset today
    # perform reset
    for k, v in list(habits.items()):
        if k == "_meta":
            continue
        if isinstance(v, dict):
            v["done"] = False
    habits["_meta"] = {"last_reset": today}
    return habits

# Utility
def ensure_defaults(habits: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    # if no user habits (only meta missing), populate defaults
    names = [k for k in habits.keys() if not k.startswith("_")]
    if not names:
        for h in DEFAULT_HABITS:
            try:
                add_habit(habits, h)
            except ValueError:
                pass
        # set initial meta
        habits["_meta"] = {"last_reset": datetime.date.today().isoformat()}
        save_habits(habits)
    return habits

# UI helpers
def rgb_to_hex(rgb: tuple[int,int,int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def interp(a: tuple[int,int,int], b: tuple[int,int,int], t: float) -> tuple[int,int,int]:
    return (int(a[0] + (b[0]-a[0])*t),
            int(a[1] + (b[1]-a[1])*t),
            int(a[2] + (b[2]-a[2])*t))

# draw rounded rectangle on canvas
def create_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=12, **kwargs):
    # corner ovals
    points = [
        (x1+r, y1, x2-r, y2),
    ]
    # create shape using polygon with arcs approximation
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", **kwargs)
    # center rectangle + sides
    canvas.create_rectangle(x1+r/2, y1, x2-r/2, y2, **kwargs)
    canvas.create_rectangle(x1, y1+r/2, x2, y2-r/2, **kwargs)

# Main GUI
class Card:
    def __init__(self, parent_canvas: tk.Canvas, x, y, w, h, name, info, icon_img, on_mark, on_unmark, on_delete):
        self.canvas = parent_canvas
        self.x = x; self.y = y; self.w = w; self.h = h
        self.name = name
        self.info = info
        self.icon_img = icon_img
        self.on_mark = on_mark
        self.on_unmark = on_unmark
        self.on_delete = on_delete
        self._build()

    def _build(self):
        # shadow
        shadow = self.canvas.create_rectangle(self.x+4, self.y+6, self.x+self.w+4, self.y+self.h+6, fill="#d6eaf8", outline="", tags="shadow")
        # card background (rounded) — draw on a separate small canvas area by using rectangle & arcs
        # we will draw a rounded rect by calling create_rounded_rect with a fill color
        card_fill = rgb_to_hex(interp(CARD_TOP, CARD_BOTTOM, 0.1))
        create_rounded_rect(self.canvas, self.x, self.y, self.x+self.w, self.y+self.h, r=14, fill=card_fill, outline="")
        # icon or emoji
        icon_x = self.x + 18
        icon_y = self.y + self.h/2
        if self.icon_img:
            # create image
            self.canvas.create_image(icon_x, icon_y, image=self.icon_img, anchor="center")
        else:
            self.canvas.create_text(icon_x, icon_y, text="🌊", font=("Segoe UI", 14))
        # name
        name_x = self.x + 18 + ICON_SIZE + 8
        self.canvas.create_text(name_x, self.y+20, text=self.name, anchor="w", font=("Segoe UI", 12, "bold"), fill=TEXT)
        # streak and status
        status = "✅" if self.info.get("done") else "❌"
        streak = self.info.get("streak", 0)
        self.canvas.create_text(name_x, self.y+44, text=f"{status}   Streak: {streak}", anchor="w", font=("Segoe UI", 10), fill=MUTED)
        # action buttons (small) — we will use real Tk buttons placed over canvas via create_window
        btn_w = 60; btn_h = 28
        bx = self.x + self.w - btn_w - 12
        by = self.y + 14
        # Mark / Undo button label depends on state
        if self.info.get("done"):
            text = "Undo"
            cmd = lambda n=self.name: self.on_unmark(n)
        else:
            text = "Done"
            cmd = lambda n=self.name: self.on_mark(n)
        mark_btn = tk.Button(self.canvas.master, text=text, width=6, command=cmd, bg="#E6F7FF", bd=0)
        self.canvas.create_window(bx, by, anchor="nw", window=mark_btn, width=btn_w, height=btn_h)
        # Delete button
        del_btn = tk.Button(self.canvas.master, text="Delete", width=6, command=lambda n=self.name: self.on_delete(n), bg="#FFE9E9", bd=0)
        self.canvas.create_window(bx, by+36, anchor="nw", window=del_btn, width=btn_w, height=btn_h)

class OceanTrackerApp:
    def __init__(self, root):
        self.root = root
        root.title("Ocean Tracker")
        root.geometry("820x680")
        root.resizable(False, False)

        # data
        self.habits = load_habits()
        ensure_defaults(self.habits)
        # reset daily if needed
        reset_daily(self.habits)
        save_habits(self.habits)

        # assets
        self.assets = {}
        self._load_icons()

        # UI root canvas for gradient and wave
        self.bg_canvas = tk.Canvas(root, width=820, height=680, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        # draw gradient
        self._draw_gradient(self.bg_canvas, 820, 680)
        # main card area (white rounded panel)
        card_w, card_h = 760, 600
        cx = (820 - card_w)//2
        cy = 40
        # draw panel rounded rect
        create_rounded_rect(self.bg_canvas, cx, cy, cx+card_w, cy+card_h, r=18, fill="#FFFFFF", outline="")
        # title + wave small icon
        title_x = cx + 24
        title_y = cy + 18
        # small wave icon left of title
        if self.assets.get("wave"):
            self.bg_canvas.create_image(title_x, title_y+6, image=self.assets["wave"], anchor="w")
            self.bg_canvas.create_text(title_x+36, title_y+8, text="Ocean Tracker", anchor="w", font=("Segoe UI", 18, "bold"), fill=TEXT)
        else:
            self.bg_canvas.create_text(title_x+10, title_y+8, text="🌊 Ocean Tracker PRO", anchor="w", font=("Segoe UI", 18, "bold"), fill=TEXT)
        self.bg_canvas.create_text(title_x+10, title_y+36, text="Track your habits — steady like the tide", anchor="w", font=("Segoe UI", 10), fill=MUTED)
        # area for cards (we will use a canvas for cards so we can easily place them and support scrolling)
        cards_x = cx + 20
        cards_y = cy + 80
        cards_w = card_w - 40
        cards_h = card_h - 140
        # cards canvas (with inner frame for scrolling)
        self.cards_canvas = tk.Canvas(self.bg_canvas, width=cards_w, height=cards_h, bg="#FFFFFF", highlightthickness=0)
        self.cards_canvas.place(x=cards_x, y=cards_y)
        # create internal canvas where we draw cards
        self.card_draw_canvas = tk.Canvas(self.cards_canvas, width=cards_w, height=cards_h, bg="#FFFFFF", highlightthickness=0)
        self.card_draw_canvas.pack()
        # simple manual scrolling with wheel
        self.card_draw_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # add controls on right bottom
        self._build_controls(cx+card_w-220, cy+card_h-140)

        # draw cards
        self._draw_cards()

        # wave animation area at bottom inside panel
        self.wave_offset = 0.0
        self._animate_wave(cx, cy+card_h-60, card_w, 60)

    def _load_icons(self):
        assets_folder = Path("assets")
        names = ["wave", "spiral", "seashell", "dolphin"]
        for nm in names:
            p = assets_folder / f"{nm}.png"
            if p.exists():
                try:
                    img = tk.PhotoImage(file=str(p))
                    self.assets[nm] = img
                except Exception:
                    self.assets[nm] = None
            else:
                self.assets[nm] = None

    def _draw_gradient(self, canvas: tk.Canvas, w: int, h: int):
        # vertical gradient by drawing many narrow rectangles
        steps = 80
        for i in range(steps):
            t = i / (steps-1)
            c = interp(GRAD_TOP, GRAD_BOTTOM, t)
            canvas.create_rectangle(0, int(i*(h/steps)), w, int((i+1)*(h/steps)), outline="", fill=rgb_to_hex(c))

    def _on_mousewheel(self, event):
        # simple scroll by moving the inner canvas content (we can move all items)
        delta = int(-1*(event.delta/120)*20)
        # move all items in card_draw_canvas
        self.card_draw_canvas.yview_scroll(delta, "units")
        # move by shifting the canvas (simulate)
        self.card_draw_canvas.move("all", 0, delta)

    def _build_controls(self, x, y):
        # Add Habit entry + buttons
        # use simple Tk widgets placed onto bg_canvas
        entry = tk.Entry(self.bg_canvas.master, width=22, font=("Segoe UI", 11))
        self.bg_canvas.create_window(x, y, anchor="nw", window=entry)
        add_btn = tk.Button(self.bg_canvas.master, text="Add Habit", command=lambda: self._on_add(entry), bg="#2D9CDB", fg="white", bd=0)
        self.bg_canvas.create_window(x+0, y+36, anchor="nw", window=add_btn)
        reset_btn = tk.Button(self.bg_canvas.master, text="Reset Daily", command=self._on_reset_daily, bg="#8FD1FF", bd=0)
        self.bg_canvas.create_window(x+90, y+36, anchor="nw", window=reset_btn)
        save_btn = tk.Button(self.bg_canvas.master, text="Save & Exit", command=self._on_save_exit, bg="#2D9CDB", fg="white", bd=0)
        self.bg_canvas.create_window(x, y+76, anchor="nw", window=save_btn)

    def _on_add(self, entry):
        name = entry.get().strip()
        if not name:
            messagebox.showinfo("Invalid", "Please enter a habit name.")
            return
        try:
            add_habit(self.habits, name)
            save_habits(self.habits)
            entry.delete(0, tk.END)
            self._draw_cards()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_reset_daily(self):
        reset_daily(self.habits)
        save_habits(self.habits)
        self._draw_cards()
        messagebox.showinfo("Reset", "Daily done flags have been reset (streaks preserved).")

    def _on_save_exit(self):
        save_habits(self.habits)
        self.root.destroy()

    def _draw_cards(self):
        # clear canvas
        self.card_draw_canvas.delete("all")
        # layout two columns
        padding = 12
        col_gap = 20
        col_w = (CARD_WIDTH)
        x0 = padding
        y0 = padding
        items = [k for k in self.habits.keys() if not k.startswith("_")]
        # sort to have stable order
        items.sort()
        col = 0
        row = 0
        # ensure card_draw_canvas is tall enough
        per_row = 2
        count = len(items)
        rows_needed = math.ceil(count / per_row)
        total_height = rows_needed * (CARD_HEIGHT + padding) + padding
        self.card_draw_canvas.config(scrollregion=(0,0, self.card_draw_canvas.winfo_reqwidth(), total_height))
        for idx, name in enumerate(items):
            info = self.habits[name]
            col = idx % 2
            row = idx // 2
            x = x0 + col * (col_w + col_gap)
            y = y0 + row * (CARD_HEIGHT + padding)
            # draw card using Card class
            icon = self.assets.get("wave")
            Card(self.card_draw_canvas, x, y, CARD_WIDTH, CARD_HEIGHT, name, info, icon,
                 on_mark=self._handle_mark_done, on_unmark=self._handle_unmark, on_delete=self._handle_delete)
        # draw final area filler if needed

    # handlers used by Card
    def _handle_mark_done(self, name):
        try:
            mark_done(self.habits, name)
            save_habits(self.habits)
            self._draw_cards()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _handle_unmark(self, name):
        try:
            unmark_habit(self.habits, name)
            save_habits(self.habits)
            self._draw_cards()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _handle_delete(self, name):
        if not messagebox.askyesno("Confirm", f"Delete habit '{name}'?"):
            return
        try:
            delete_habit(self.habits, name)
            save_habits(self.habits)
            self._draw_cards()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # wave animation bottom
    def _animate_wave(self, x, y, w, h):
        # draw a smooth sine wave polygon and animate vertical offset
        self.wave_canvas = tk.Canvas(self.bg_canvas, width=w, height=h, bg="#FFFFFF", highlightthickness=0)
        self.bg_canvas.create_window(x, y, anchor="nw", window=self.wave_canvas)
        self.wave_w = w
        self.wave_h = h
        self._wave_phase = 0.0
        self._wave_id = None
        self._update_wave()
    
    def _update_wave(self):
        c = self.wave_canvas
        c.delete("all")
        # parameters
        points = []
        amp = 8
        freq = 2.0
        phase = self._wave_phase
        steps = 100
        for i in range(steps+1):
            t = i / steps
            px = t * self.wave_w
            py = self.wave_h/2 + math.sin(t * freq * 2*math.pi + phase) * amp
            points.append((px, py))
        # create polygon by connecting bottom corners
        poly = [(0, self.wave_h)] + points + [(self.wave_w, self.wave_h)]
        # flatten
        flat = [coord for p in poly for coord in p]
        c.create_polygon(flat, fill=rgb_to_hex(interp(GRAD_BOTTOM, GRAD_TOP, 0.15)), outline="")
        self._wave_phase += 0.12
        self.root.after(60, self._update_wave)

# Run
def main():
    root = tk.Tk()
    app = OceanTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
