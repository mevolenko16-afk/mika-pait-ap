import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import os, json, math

CONFIG_FILE = "paint_config.json"


class Paint:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Рисовалка")
        self.root.geometry("1200x720")
        self.root.minsize(900, 600)
        self.root.configure(bg="#2b2b3d")

        # Настройки
        self.color = "#000000"
        self.bg_color = "#ffffff"
        self.brush_size = 5
        self.tool = "brush"        # brush, line, rect, oval, eraser, fill
        self.last_x = None
        self.last_y = None
        self.start_x = None
        self.start_y = None
        self.temp_id = None
        self.drawing = False

        self.build_ui()
        self.new_canvas()

    # ============================================================
    #  ИНТЕРФЕЙС
    # ============================================================
    def build_ui(self):
        # Верхняя панель инструментов
        toolbar = tk.Frame(self.root, bg="#1e1e2e", height=60)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        # Логотип
        tk.Label(toolbar, text="🎨", bg="#1e1e2e", fg="#ff6ec7",
                 font=("Segoe UI Emoji", 20)).pack(side="left", padx=(14, 4))
        tk.Label(toolbar, text="Рисовалка", bg="#1e1e2e", fg="#ffffff",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 20))

        # Кнопки инструментов
        self.tool_btns = {}
        tools = [
            ("brush",  "🖌", "Кисть"),
            ("line",   "📏", "Линия"),
            ("rect",   "▭",  "Прямоугольник"),
            ("oval",   "◯",  "Овал"),
            ("eraser", "🧽", "Ластик"),
            ("fill",   "🪣", "Заливка"),
        ]
        for key, icon, tip in tools:
            b = tk.Button(toolbar, text=icon, bg="#2b2b3d", fg="#ffffff",
                          activebackground="#4c1d95", activeforeground="#ffffff",
                          relief="flat", bd=0, cursor="hand2",
                          font=("Segoe UI Emoji", 14),
                          width=3, height=1,
                          command=lambda k=key: self.set_tool(k))
            b.pack(side="left", padx=2, pady=8)
            self.tool_btns[key] = b

        # Разделитель
        tk.Frame(toolbar, bg="#3a3a55", width=1).pack(side="left", fill="y", padx=8, pady=8)

        # Размер кисти
        tk.Label(toolbar, text="Толщина:", bg="#1e1e2e", fg="#c4b5fd",
                 font=("Segoe UI", 10)).pack(side="left", padx=(4, 4))
        self.size_var = tk.IntVar(value=self.brush_size)
        size_slider = tk.Scale(toolbar, from_=1, to=50, orient="horizontal",
                               variable=self.size_var, length=120,
                               bg="#1e1e2e", fg="#ffffff", troughcolor="#2b2b3d",
                               activebackground="#ff6ec7", highlightthickness=0, bd=0,
                               sliderrelief="flat", showvalue=True, width=12,
                               command=self._set_size)
        size_slider.pack(side="left", padx=4)

        tk.Frame(toolbar, bg="#3a3a55", width=1).pack(side="left", fill="y", padx=8, pady=8)

        # Кнопки действий
        self._tb_btn(toolbar, "🆕 Новый", self.new_canvas).pack(side="left", padx=2)
        self._tb_btn(toolbar, "🎨 Раскраска", self.open_coloring).pack(side="left", padx=2)
        self._tb_btn(toolbar, "💾 Сохранить", self.save_image).pack(side="left", padx=2)
        self._tb_btn(toolbar, "📂 Открыть", self.load_image).pack(side="left", padx=2)
        self._tb_btn(toolbar, "↩ Очистить", self.clear_canvas).pack(side="left", padx=2)

        # Основная область
        main = tk.Frame(self.root, bg="#2b2b3d")
        main.pack(fill="both", expand=True)

        # Левая панель — палитра
        palette_panel = tk.Frame(main, bg="#1e1e2e", width=140)
        palette_panel.pack(side="left", fill="y")
        palette_panel.pack_propagate(False)

        tk.Label(palette_panel, text="🎨", bg="#1e1e2e", fg="#ff6ec7",
                 font=("Segoe UI Emoji", 24)).pack(pady=(14, 4))
        tk.Label(palette_panel, text="Палитра", bg="#1e1e2e", fg="#c4b5fd",
                 font=("Segoe UI", 10, "bold")).pack()

        # Текущий цвет
        self.color_preview = tk.Label(palette_panel, text="", bg=self.color,
                                      width=8, height=2, relief="flat", bd=2)
        self.color_preview.pack(pady=8)

        self._tb_btn(palette_panel, "Выбрать цвет", self.pick_color,
                     width=14).pack(pady=4)

        # Сетка цветов
        colors = [
            "#000000", "#ffffff", "#ff0000", "#00ff00", "#0000ff", "#ffff00",
            "#ff00ff", "#00ffff", "#ff8000", "#8000ff", "#800000", "#008000",
            "#ff6ec7", "#c084fc", "#22d3ee", "#4ade80", "#f87171", "#facc15",
            "#8b5cf6", "#ec4899", "#0891b2", "#16a34a", "#dc2626", "#ca8a04",
        ]
        grid = tk.Frame(palette_panel, bg="#1e1e2e")
        grid.pack(pady=6)
        for i, c in enumerate(colors):
            r, cc = divmod(i, 3)
            sw = tk.Frame(grid, bg=c, width=26, height=26,
                          highlightbackground="#444", highlightthickness=1,
                          cursor="hand2")
            sw.grid(row=r, column=cc, padx=2, pady=2)
            sw.bind("<Button-1>", lambda e, col=c: self.set_color(col))

        # Фон
        tk.Label(palette_panel, text="Фон:", bg="#1e1e2e", fg="#c4b5fd",
                 font=("Segoe UI", 9)).pack(pady=(14, 2))
        self._tb_btn(palette_panel, "Сменить фон", self.pick_bg_color,
                     width=14).pack(pady=2)

        # Холст
        canvas_frame = tk.Frame(main, bg="#2b2b3d")
        canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color,
                                highlightthickness=2,
                                highlightbackground="#3a3a55",
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        # Обработчики
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Статус-бар
        self.status = tk.Label(self.root, text="Готово. Рисуй мышкой 🎨",
                               bg="#1e1e2e", fg="#c4b5fd", anchor="w",
                               font=("Segoe UI", 9), padx=10)
        self.status.pack(fill="x", side="bottom")

        self.set_tool("brush")

    def _tb_btn(self, parent, text, cmd, width=None):
        b = tk.Button(parent, text=text, bg="#2b2b3d", fg="#ffffff",
                      activebackground="#4c1d95", activeforeground="#ffffff",
                      relief="flat", bd=0, cursor="hand2",
                      font=("Segoe UI", 9), padx=8, pady=6,
                      command=cmd)
        if width:
            b.config(width=width)
        b.bind("<Enter>", lambda e: b.config(bg="#4c1d95"))
        b.bind("<Leave>", lambda e: b.config(bg="#2b2b3d"))
        return b

    # ============================================================
    #  ИНСТРУМЕНТЫ
    # ============================================================
    def set_tool(self, tool):
        self.tool = tool
        for k, b in self.tool_btns.items():
            if k == tool:
                b.config(bg="#4c1d95", fg="#ffffff")
            else:
                b.config(bg="#2b2b3d", fg="#ffffff")
        names = {
            "brush": "Кисть", "line": "Линия", "rect": "Прямоугольник",
            "oval": "Овал", "eraser": "Ластик", "fill": "Заливка",
        }
        self.status.config(text=f"Инструмент: {names.get(tool, tool)}")

    def _set_size(self, val):
        self.brush_size = int(float(val))

    def set_color(self, color):
        if self.tool == "eraser":
            self.set_tool("brush")
        self.color = color
        self.color_preview.config(bg=color)

    def pick_color(self):
        c = colorchooser.askcolor(color=self.color, title="Выбери цвет")[1]
        if c:
            self.set_color(c)

    def pick_bg_color(self):
        c = colorchooser.askcolor(color=self.bg_color, title="Цвет фона")[1]
        if c:
            self.bg_color = c
            self.canvas.config(bg=c)

    # ============================================================
    #  РИСОВАНИЕ
    # ============================================================
    def on_press(self, e):
        self.drawing = True
        self.start_x, self.start_y = e.x, e.y
        self.last_x, self.last_y = e.x, e.y

        if self.tool == "fill":
            try:
                self.canvas.create_rectangle(0, 0, 5000, 5000,
                                             fill=self.color, outline="",
                                             tags="fillbg")
                self.canvas.tag_lower("fillbg")
            except Exception:
                pass
            self.drawing = False
            return

        if self.tool == "brush":
            self.canvas.create_oval(
                e.x - self.brush_size//2, e.y - self.brush_size//2,
                e.x + self.brush_size//2, e.y + self.brush_size//2,
                fill=self.color, outline=self.color, tags="draw")
        elif self.tool == "eraser":
            r = self.brush_size * 2
            self.canvas.create_oval(
                e.x - r, e.y - r, e.x + r, e.y + r,
                fill=self.bg_color, outline=self.bg_color, tags="draw")

    def on_drag(self, e):
        if not self.drawing:
            return

        if self.tool in ("brush", "eraser"):
            color = self.color if self.tool == "brush" else self.bg_color
            size = self.brush_size if self.tool == "brush" else self.brush_size * 4
            self.canvas.create_line(
                self.last_x, self.last_y, e.x, e.y,
                fill=color, width=size,
                capstyle="round", smooth=True, tags="draw")
            self.last_x, self.last_y = e.x, e.y

        elif self.tool in ("line", "rect", "oval"):
            if self.temp_id:
                self.canvas.delete(self.temp_id)
            x0, y0, x1, y1 = self.start_x, self.start_y, e.x, e.y
            if self.tool == "line":
                self.temp_id = self.canvas.create_line(
                    x0, y0, x1, y1, fill=self.color, width=self.brush_size,
                    capstyle="round", tags="draw")
            elif self.tool == "rect":
                self.temp_id = self.canvas.create_rectangle(
                    x0, y0, x1, y1, outline=self.color, width=self.brush_size,
                    tags="draw")
            elif self.tool == "oval":
                self.temp_id = self.canvas.create_oval(
                    x0, y0, x1, y1, outline=self.color, width=self.brush_size,
                    tags="draw")

    def on_release(self, e):
        self.drawing = False
        self.temp_id = None

    # ============================================================
    #  ДЕЙСТВИЯ
    # ============================================================
    def new_canvas(self):
        self.canvas.delete("all")
        self.status.config(text="Новый холст создан ✨")

    def clear_canvas(self):
        if messagebox.askyesno("Очистить", "Стереть всё?"):
            self.canvas.delete("all")
            self.status.config(text="Холст очищен")

    def save_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".ps",
            filetypes=[("PostScript", "*.ps"), ("Все файлы", "*.*")])
        if path:
            try:
                self.canvas.postscript(file=path, colormode="color")
                messagebox.showinfo("💾", f"Сохранено:\n{path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def load_image(self):
        messagebox.showinfo("📂",
            "Загрузка картинки без библиотек недоступна.\n"
            "Используй раскраски — они встроены.")

    # ============================================================
    #  РАСКРАСКИ (контуры, которые можно раскрашивать)
    # ============================================================
    def open_coloring(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("🎨 Раскраски")
        dlg.geometry("560x420")
        dlg.configure(bg="#1e1e2e")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="🎨 Выбери раскраску",
                 bg="#1e1e2e", fg="#ffffff",
                 font=("Segoe UI", 15, "bold")).pack(pady=(16, 4))

        tk.Label(dlg, text="Кликни — и контур появится на холсте.\n"
                            "Раскрашивай инструментом 🪣 Заливка или кистью.",
                 bg="#1e1e2e", fg="#c4b5fd",
                 font=("Segoe UI", 10), justify="center").pack(pady=(0, 12))

        grid = tk.Frame(dlg, bg="#1e1e2e")
        grid.pack(pady=8)

        drawings = [
            ("🐱", "Котик",      self.draw_cat),
            ("🌸", "Цветок",     self.draw_flower),
            ("🏠", "Домик",      self.draw_house),
            ("⭐", "Звезда",     self.draw_star),
            ("🐟", "Рыбка",      self.draw_fish),
            ("🌳", "Дерево",     self.draw_tree),
            ("❤️", "Сердце",     self.draw_heart),
            ("🚗", "Машинка",    self.draw_car),
            ("🦋", "Бабочка",    self.draw_butterfly),
            ("🌈", "Радуга",     self.draw_rainbow),
            ("🍎", "Яблоко",     self.draw_apple),
            ("😺", "Смайлик",    self.draw_smiley),
        ]

        for i, (emoji, name, fn) in enumerate(drawings):
            r, c = divmod(i, 3)
            cell = tk.Frame(grid, bg="#2b2b3d", cursor="hand2",
                            highlightbackground="#4c1d95", highlightthickness=2)
            cell.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            tk.Label(cell, text=emoji, bg="#2b2b3d", fg="#ff6ec7",
                     font=("Segoe UI Emoji", 36)).pack(padx=20, pady=(10, 2))
            tk.Label(cell, text=name, bg="#2b2b3d", fg="#ffffff",
                     font=("Segoe UI", 10)).pack(pady=(0, 10))

            def click(e, f=fn, d=dlg):
                self.canvas.delete("all")
                f()
                d.destroy()
                self.status.config(text="Раскраска готова! Раскрашивай 🎨")

            for w in [cell, *cell.winfo_children()]:
                w.bind("<Button-1>", click)

    # ============================================================
    #  ОТРИСОВКА КОНТУРОВ (по центру холста)
    # ============================================================
    def _center(self):
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 500
        return w // 2, h // 2

    def draw_cat(self):
        cx, cy = self._center()
        # Голова
        self.canvas.create_oval(cx-120, cy-120, cx+120, cy+120,
                                outline="#000000", width=4)
        # Уши
        self.canvas.create_polygon(cx-110, cy-90, cx-70, cy-170, cx-30, cy-100,
                                   outline="#000000", width=4, fill="")
        self.canvas.create_polygon(cx+110, cy-90, cx+70, cy-170, cx+30, cy-100,
                                   outline="#000000", width=4, fill="")
        # Глаза
        self.canvas.create_oval(cx-60, cy-40, cx-20, cy, outline="#000000", width=3)
        self.canvas.create_oval(cx+20, cy-40, cx+60, cy, outline="#000000", width=3)
        # Нос
        self.canvas.create_polygon(cx-10, cy+20, cx+10, cy+20, cx, cy+40,
                                   outline="#000000", width=3, fill="")
        # Рот
        self.canvas.create_arc(cx-30, cy+20, cx, cy+70, start=180, extent=90,
                               style="arc", outline="#000000", width=3)
        self.canvas.create_arc(cx, cy+20, cx+30, cy+70, start=270, extent=90,
                               style="arc", outline="#000000", width=3)
        # Усы
        for dx, dy in [(-90, 30), (-90, 50), (-90, 70), (90, 30), (90, 50), (90, 70)]:
            x2 = cx + dx + (-30 if dx < 0 else 30)
            self.canvas.create_line(cx+dx, cy+dy, x2, cy+dy,
                                    fill="#000000", width=2)

    def draw_flower(self):
        cx, cy = self._center()
        # Лепестки
        for angle in range(0, 360, 60):
            r = 100
            x = cx + int(r * math.cos(math.radians(angle)))
            y = cy + int(r * math.sin(math.radians(angle)))
            self.canvas.create_oval(x-60, y-60, x+60, y+60,
                                    outline="#000000", width=4)
        # Серединка
        self.canvas.create_oval(cx-45, cy-45, cx+45, cy+45,
                                outline="#000000", width=4)

    def draw_house(self):
        cx, cy = self._center()
        # Стены
        self.canvas.create_rectangle(cx-120, cy-40, cx+120, cy+130,
                                     outline="#000000", width=4)
        # Крыша
        self.canvas.create_polygon(cx-140, cy-40, cx+140, cy-40, cx, cy-150,
                                   outline="#000000", width=4, fill="")
        # Дверь
        self.canvas.create_rectangle(cx-30, cy+50, cx+30, cy+130,
                                     outline="#000000", width=3)
        # Окно
        self.canvas.create_rectangle(cx-90, cy-10, cx-30, cy+40,
                                     outline="#000000", width=3)
        self.canvas.create_rectangle(cx+30, cy-10, cx+90, cy+40,
                                     outline="#000000", width=3)
        # Перекрестие окна
        self.canvas.create_line(cx-60, cy-10, cx-60, cy+40, fill="#000000", width=2)
        self.canvas.create_line(cx-90, cy+15, cx-30, cy+15, fill="#000000", width=2)

    def draw_star(self):
        cx, cy = self._center()
        R, r = 140, 60
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            rad = R if i % 2 == 0 else r
            points.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
        flat = [coord for pt in points for coord in pt]
        self.canvas.create_polygon(flat, outline="#000000", width=4, fill="")

    def draw_fish(self):
        cx, cy = self._center()
        # Тело
        self.canvas.create_oval(cx-130, cy-60, cx+80, cy+60,
                                outline="#000000", width=4)
        # Хвост
        self.canvas.create_polygon(cx+80, cy, cx+160, cy-60, cx+160, cy+60,
                                   outline="#000000", width=4, fill="")
        # Глаз
        self.canvas.create_oval(cx-90, cy-20, cx-60, cy+10,
                                outline="#000000", width=3)
        self.canvas.create_oval(cx-80, cy-12, cx-72, cy-4,
                                fill="#000000")
        # Плавники
        self.canvas.create_polygon(cx-30, cy-60, cx+10, cy-90, cx+30, cy-60,
                                   outline="#000000", width=3, fill="")

    def draw_tree(self):
        cx, cy = self._center()
        # Ствол
        self.canvas.create_rectangle(cx-25, cy+40, cx+25, cy+160,
                                     outline="#000000", width=4)
        # Крона
        self.canvas.create_oval(cx-110, cy-140, cx+110, cy+60,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx-90, cy-100, cx-10, cy-20,
                                outline="#000000", width=2)
        self.canvas.create_oval(cx+10, cy-100, cx+90, cy-20,
                                outline="#000000", width=2)

    def draw_heart(self):
        cx, cy = self._center()
        points = []
        for t in range(0, 360, 5):
            rad = math.radians(t)
            x = 16 * math.sin(rad) ** 3
            y = -(13 * math.cos(rad) - 5 * math.cos(2*rad)
                  - 2 * math.cos(3*rad) - math.cos(4*rad))
            points.append((cx + x * 8, cy + y * 8))
        flat = [c for pt in points for c in pt]
        self.canvas.create_polygon(flat, outline="#000000", width=4, fill="")

    def draw_car(self):
        cx, cy = self._center()
        # Кузов
        self.canvas.create_rectangle(cx-150, cy-30, cx+150, cy+60,
                                     outline="#000000", width=4)
        # Крыша
        self.canvas.create_polygon(cx-80, cy-30, cx-50, cy-90, cx+50, cy-90,
                                   cx+80, cy-30, outline="#000000", width=4, fill="")
        # Окна
        self.canvas.create_rectangle(cx-70, cy-80, cx-10, cy-35,
                                     outline="#000000", width=2)
        self.canvas.create_rectangle(cx+10, cy-80, cx+70, cy-35,
                                     outline="#000000", width=2)
        # Колёса
        self.canvas.create_oval(cx-110, cy+30, cx-50, cy+90,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx+50, cy+30, cx+110, cy+90,
                                outline="#000000", width=4)

    def draw_butterfly(self):
        cx, cy = self._center()
        # Тело
        self.canvas.create_oval(cx-10, cy-100, cx+10, cy+100,
                                outline="#000000", width=3)
        # Крылья верхние
        self.canvas.create_oval(cx-130, cy-90, cx-10, cy+10,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx+10, cy-90, cx+130, cy+10,
                                outline="#000000", width=4)
        # Крылья нижние
        self.canvas.create_oval(cx-110, cy, cx-10, cy+90,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx+10, cy, cx+110, cy+90,
                                outline="#000000", width=4)
        # Усики
        self.canvas.create_line(cx, cy-100, cx-20, cy-140, fill="#000000", width=2)
        self.canvas.create_line(cx, cy-100, cx+20, cy-140, fill="#000000", width=2)

    def draw_rainbow(self):
        cx, cy = self._center()
        colors_width = 4
        R = 160
        for i, r in enumerate([R, R-25, R-50, R-75, R-100, R-125]):
            self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                                   start=0, extent=180, style="arc",
                                   outline="#000000", width=colors_width)

    def draw_apple(self):
        cx, cy = self._center()
        # Яблоко
        self.canvas.create_oval(cx-110, cy-80, cx+110, cy+120,
                                outline="#000000", width=4)
        # Вмятина сверху
        self.canvas.create_arc(cx-30, cy-100, cx+30, cy-60,
                               start=0, extent=-180, style="arc",
                               outline="#000000", width=4)
        # Черенок
        self.canvas.create_line(cx, cy-90, cx+10, cy-140,
                                fill="#000000", width=4)
        # Листик
        self.canvas.create_oval(cx+5, cy-140, cx+60, cy-110,
                                outline="#000000", width=3)

    def draw_smiley(self):
        cx, cy = self._center()
        # Лицо
        self.canvas.create_oval(cx-140, cy-140, cx+140, cy+140,
                                outline="#000000", width=5)
        # Глаза
        self.canvas.create_oval(cx-70, cy-60, cx-30, cy-20,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx+30, cy-60, cx+70, cy-20,
                                outline="#000000", width=4)
        self.canvas.create_oval(cx-55, cy-45, cx-40, cy-30, fill="#000000")
        self.canvas.create_oval(cx+40, cy-45, cx+55, cy-30, fill="#000000")
        # Улыбка
        self.canvas.create_arc(cx-80, cy+10, cx+80, cy+100,
                               start=0, extent=-180, style="arc",
                               outline="#000000", width=5)

    # ============================================================
    #  СОХРАНЕНИЕ НАСТРОЕК
    # ============================================================
    def _load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "color": self.color,
                    "bg_color": self.bg_color,
                    "brush_size": self.brush_size,
                }, f)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = Paint(root)
    root.mainloop()
