# -*- coding: utf-8 -*-
import messages
import application as app
from tkinter import simpledialog, messagebox
from tkinter import *

CLOSING_PROTOCOL = "WM_DELETE_WINDOW"
END_OF_LINE = "\n"
KEY_RETURN = "<Return>"
TEXT_STATE_DISABLED = "disabled"
TEXT_STATE_NORMAL = "normal"
FIELD_SIZE = 8
SQUARE_SIZE = 100


class TacticalFightUI(object):
    def __init__(self, application):
        self.application = application
        self.gui = None
        self.end_btn = None
        self.surrender_btn = None
        self.canvas = None
        self.color_pool = list()
        self.game_matrix = None
        self.lgray_sqr = set()
        self.white_sqr = None
        self.players_colors = dict()
        self.blocked = False
        self.username = None
        self.save_btn = None
        self.blocked_cells = set()

    def show(self):
        self.gui = Tk()
        self.gui.title(messages.TITLE)
        self.fill_canvas()
        self.end_btn = Button(self.gui, text="End turn")
        self.surrender_btn = Button(self.gui, text="Surrender and quit")
        self.save_btn = Button(self.gui, text="Save Game")
        self.save_btn.pack()
        self.surrender_btn.pack()
        self.end_btn.pack()
        self.color_pool = ["white", "orange", "blue", 'green']
        self.gui.protocol(CLOSING_PROTOCOL, self.on_closing)
        self.end_btn.bind("<Button-1>", self.end_turn)
        self.save_btn.bind("<Button-1>", self.save_game)
        self.surrender_btn.bind("<Button-1>", self.surrender)

        return self.input_dialogs()

    def loop(self):
        self.gui.mainloop()

    def save_game(self, event):
        self.application.save_game()


    def fill_canvas(self):
        self.canvas = Canvas(self.gui, width=SQUARE_SIZE * FIELD_SIZE, height=SQUARE_SIZE * FIELD_SIZE)
        self.canvas.pack()
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                self.canvas.create_rectangle(i * SQUARE_SIZE, j * SQUARE_SIZE,
                                             i * SQUARE_SIZE + SQUARE_SIZE,
                                             j * SQUARE_SIZE + SQUARE_SIZE, fill='black', outline='yellow',
                                             tag="square")
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                self.canvas.create_text(i * SQUARE_SIZE + SQUARE_SIZE / 2, j * SQUARE_SIZE + SQUARE_SIZE / 2, text="0",
                                        font="Verdana 14")
        self.canvas.tag_bind("square", "<Button-1>", self.on_square_click)

    def rewrite_text(self):
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                cell = self.game_matrix[i][j]
                if len(cell) == 1 and cell[0][1] != "none":
                    if cell[0][1] in self.players_colors.keys():
                        self.canvas.itemconfig(j * FIELD_SIZE + i + 65, fill=self.players_colors[cell[0][1]], text = cell[0][0])
                    else:
                        color = None
                        if (self.username == cell[0][1]):
                            self.players_colors[cell[0][1]] = "green"
                            self.color_pool.remove("green")
                            color = "green"
                        else:
                            color = self.color_pool.pop(0)
                            self.players_colors[cell[0][1]] = color
                        self.canvas.itemconfig(j * FIELD_SIZE + i + 65, fill=color, text = cell[0][0])
                elif len(cell) > 1:
                    texts = []
                    text = ""
                    for team in cell:
                        color = self.players_colors[team[1]]
                        texts.append(str(team[0]) + color[0])
                    if (len(texts) > 2):
                        text = texts[0] + ' ' + texts[1] + '\n'
                        for t in range(2, len(texts)):
                            text += texts[t] + ' '
                    else:
                        for t in texts:
                            text += t + ' '

                    self.canvas.itemconfig(j * FIELD_SIZE + i + 65, fill="red", text=text)
                elif cell[0][1] == "none":
                    self.canvas.itemconfig(j * FIELD_SIZE + i + 65, fill="black", text='0')

    def end_turn(self, event):
        self.blocked_cells.clear()
        self.application.end_turn()

    def begin_turn(self):
        self.unlock_ui()
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                cell = self.game_matrix[i][j]
                if len(cell) == 1 and cell[0][1] != self.username and cell[0][1]:
                    self.blocked_cells.add(j * FIELD_SIZE + i + 1)
                elif len(cell) > 1:
                    temp = False
                    for team in cell:
                        if team[1] == self.username:
                            temp = True
                    if not temp:
                        self.blocked_cells.add(j * FIELD_SIZE + i + 1)

    def surrender(self, event):
        self.application.surrender()

    def block_ui(self):
        self.end_btn['state'] = DISABLED
        self.surrender_btn['state'] = DISABLED
        self.blocked = True

    def unlock_ui(self):
        self.end_btn['state'] = NORMAL
        self.surrender_btn['state'] = NORMAL
        self.blocked = False

    def move_warriors(self, sq_from, sq_to):
        need_to_block = True
        warriors_count = simpledialog.askinteger(messages.WARRIOR_TITLE, messages.INPUT_WARRIOR_COUNT, parent=self.gui)
        if warriors_count is None:
            return False
        i_from = (sq_from - 1) % FIELD_SIZE
        j_from = int((sq_from - 1) / FIELD_SIZE)
        i_to = (sq_to - 1) % FIELD_SIZE
        j_to = int((sq_to - 1) / FIELD_SIZE)
        cell_from = self.game_matrix[i_from][j_from]
        cell_to = self.game_matrix[i_to][j_to]
        warriors_available = 0
        if len(cell_from) > 1:
            for team in cell_from:
                if team[1] == self.username:
                    warriors_available = team[0]
                    break
        else:
            warriors_available = cell_from[0][0]
        if len(cell_to) == 1:
            if (cell_to[0][1] == self.username):
                need_to_block = False

        if warriors_available < warriors_count:
            return False

        warriors_on_target = 0
        if len(cell_to) > 1:
            is_our = False
            for team in cell_to:
                if team[1] == self.username:
                    is_our = True
                    warriors_on_target = team[0]
                    team[0] = warriors_on_target + warriors_count
                    break
            if not is_our:
                cell_to.append([warriors_count, self.username])
        else:
            if cell_to[0][1] == "none":
                cell_to[0][1] = self.username
            if cell_to[0][1] != self.username:
                cell_to.append([warriors_count, self.username])
            else:
                warriors_on_target = cell_to[0][0]
                cell_to[0][0] = warriors_on_target + warriors_count

        if len(cell_from) > 1:
            for team in cell_from:
                if team[1] == self.username:
                    team[0] = warriors_available - warriors_count
                    if team[0] == 0:
                        cell_from.remove(team)
                    break
        else:
            cell_from[0][0] = warriors_available - warriors_count
            if cell_from[0][0] == 0:
                cell_from[0][1] = "none"
                self.blocked_cells.add(sq_from)

        # moving
        self.rewrite_text()
        if need_to_block:
            self.blocked_cells.add(sq_to)
        self.application.move()
        self.end_btn['state'] = NORMAL
        self.surrender_btn['state'] = NORMAL
        return True

    def on_square_click(self, event):
        if self.blocked:
            return

        ids = self.canvas.find_withtag(CURRENT)[0]  # Определяем по какой клетке кликнули
        neighbors = self.find_neighbors(ids)
        if ids in self.lgray_sqr:
            if (self.move_warriors(self.white_sqr, ids)):
                self.canvas.itemconfig(self.white_sqr, fill="black")
                neighbors_2 = self.find_neighbors(self.white_sqr)
                self.white_sqr = None
                for j in neighbors_2:
                    self.canvas.itemconfig(j, fill="black")
                    self.canvas.itemconfig(j + 64, fill="black")
                    self.lgray_sqr.remove(j)

        elif ids == self.white_sqr:
            self.white_sqr = None
            self.canvas.itemconfig(ids, fill="black")
            self.end_btn['state'] = NORMAL
            self.surrender_btn['state'] = NORMAL
            for i in neighbors:
                self.canvas.itemconfig(i, fill="black")
                self.canvas.itemconfig(i + 64, fill="black")
                self.lgray_sqr.remove(i)
        elif self.white_sqr is None and len(self.lgray_sqr) == 0 and ids not in self.blocked_cells:
            self.white_sqr = ids
            self.canvas.itemconfig(ids, fill="white")
            self.end_btn['state'] = DISABLED
            self.surrender_btn['state'] = DISABLED
            for i in neighbors:
                self.canvas.itemconfig(i, fill="light gray")
                self.canvas.itemconfig(i + 64, fill="light gray")
                self.lgray_sqr.add(i)
        self.canvas.update()

    def find_neighbors(self, square):
        """ Возвращает клетки соседствующие с square """
        # Левая верхняя клетка
        if square == 1:
            data = {FIELD_SIZE + 1, 2}
        # Правая нижняя 
        elif square == FIELD_SIZE ** 2:
            data = {square - FIELD_SIZE, square - 1}
        # Левая нижняя
        elif square == FIELD_SIZE:
            data = {FIELD_SIZE - 1, FIELD_SIZE * 2}
        # Верхняя правая
        elif square == FIELD_SIZE ** 2 - FIELD_SIZE + 1:
            data = {square + 1, square - FIELD_SIZE}
        # Клетка в левом ряду
        elif square < FIELD_SIZE:
            data = {square + 1, square - 1, square + FIELD_SIZE}
        # Клетка в правом ряду
        elif square > FIELD_SIZE ** 2 - FIELD_SIZE:
            data = {square + 1, square - 1, square - FIELD_SIZE}
        # Клетка в нижнем ряду
        elif square % FIELD_SIZE == 0:
            data = {square + FIELD_SIZE, square - FIELD_SIZE, square - 1}
        # Клетка в верхнем ряду
        elif square % FIELD_SIZE == 1:
            data = {square + FIELD_SIZE, square - FIELD_SIZE, square + 1}
        # Любая другая клетка
        else:
            data = {square - 1, square + 1, square - FIELD_SIZE, square + FIELD_SIZE}
        return data

    def input_dialogs(self):
        self.gui.lower()
        self.application.host = messages.SERVER_HOST
        if self.application.host is None:
            return False
        self.application.username = simpledialog.askstring(messages.USERNAME, messages.INPUT_USERNAME,
                                                        parent=self.gui)
        if self.application.username is None:
            return False
        self.username = self.application.username
        self.application.port = simpledialog.askinteger(messages.SERVER_PORT, messages.INPUT_SERVER_PORT,
                                                        parent=self.gui)
        if self.application.port is None:
            return False
        return True

    def alert(self, title, message):
        messagebox.showerror(title, message)

    def on_closing(self):
        self.application.exit()
        self.gui.after(2000, self.gui.destroy)
        f = True

    def show_info(self, title, msg):
        messagebox.showinfo(title, msg)


