import tkinter as tk
from tkinter import ttk, messagebox
import random
import sqlite3
from datetime import datetime

class Game2048:
    def __init__(self):
        self.size = 4
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
    
    def add_new_tile(self):
        empty_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 0:
                    empty_cells.append((i, j))
        
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.grid[i][j] = 2 if random.random() < 0.9 else 4
    
    def move_left(self):
        moved = False
        for i in range(self.size):
            row = [x for x in self.grid[i] if x != 0]
            j = 0
            while j < len(row) - 1:
                if row[j] == row[j + 1]:
                    row[j] *= 2
                    self.score += row[j]
                    row.pop(j + 1)
                    row.append(0)
                    moved = True
                j += 1
            row = [x for x in row if x != 0]
            row.extend([0] * (self.size - len(row)))
            if self.grid[i] != row:
                moved = True
            self.grid[i] = row
        return moved
    
    def move_right(self):
        self.grid = [row[::-1] for row in self.grid]
        moved = self.move_left()
        self.grid = [row[::-1] for row in self.grid]
        return moved
    
    def move_up(self):
        self.grid = [list(x) for x in zip(*self.grid)]
        moved = self.move_left()
        self.grid = [list(x) for x in zip(*self.grid)]
        return moved
    
    def move_down(self):
        self.grid = [list(x) for x in zip(*self.grid)]
        moved = self.move_right()
        self.grid = [list(x) for x in zip(*self.grid)]
        return moved
    
    def is_game_over(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 0:
                    return False
        for i in range(self.size):
            for j in range(self.size):
                if (j < self.size - 1 and self.grid[i][j] == self.grid[i][j + 1]) or \
                   (i < self.size - 1 and self.grid[i][j] == self.grid[i + 1][j]):
                    return False
        return True

class Database:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                best_score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_user(self, username):
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create_user(self, username):
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username) VALUES (?)',
            (username,)
        )
        conn.commit()
        conn.close()
    
    def update_user_score(self, username, score):
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT best_score FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        current_best = result[0] if result else 0
        
        if score > current_best:
            cursor.execute(
                'UPDATE users SET best_score = ?, games_played = games_played + 1 WHERE username = ?',
                (score, username)
            )
        else:
            cursor.execute(
                'UPDATE users SET games_played = games_played + 1 WHERE username = ?',
                (username,)
            )
        conn.commit()
        conn.close()
        return max(score, current_best)
    
    def get_leaderboard(self, limit=10):
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT username, best_score, games_played FROM users ORDER BY best_score DESC LIMIT ?',
            (limit,)
        )
        users = cursor.fetchall()
        conn.close()
        return users

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2048 Game")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.db = Database()
        self.current_user = "Player"
        self.game = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="🎮 2048", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Информация о пользователе
        user_frame = ttk.Frame(main_frame)
        user_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(user_frame, text="Игрок:").grid(row=0, column=0, padx=5)
        self.user_entry = ttk.Entry(user_frame, width=15)
        self.user_entry.grid(row=0, column=1, padx=5)
        self.user_entry.insert(0, self.current_user)
        ttk.Button(user_frame, text="Сохранить", command=self.save_user).grid(row=0, column=2, padx=5)
        
        # Статистика
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика", padding="5")
        stats_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        self.score_label = ttk.Label(stats_frame, text="Очки: 0", font=("Arial", 12))
        self.score_label.grid(row=0, column=0, padx=10)
        
        self.best_label = ttk.Label(stats_frame, text="Лучший: 0", font=("Arial", 12))
        self.best_label.grid(row=0, column=1, padx=10)
        
        # Игровое поле
        self.game_frame = ttk.LabelFrame(main_frame, text="Игровое поле", padding="10")
        self.game_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.create_game_grid()
        
        # Кнопки управления
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(controls_frame, text="⬅️ Влево", command=self.move_left).grid(row=0, column=0, padx=5)
        ttk.Button(controls_frame, text="➡️ Вправо", command=self.move_right).grid(row=0, column=1, padx=5)
        ttk.Button(controls_frame, text="⬆️ Вверх", command=self.move_up).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(controls_frame, text="⬇️ Вниз", command=self.move_down).grid(row=1, column=1, padx=5, pady=5)
        
        # Кнопки действий
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(action_frame, text="🔄 Новая игра", command=self.new_game).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="🏆 Таблица лидеров", command=self.show_leaderboard).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="📊 Моя статистика", command=self.show_stats).grid(row=0, column=2, padx=5)
        
        # Привязка клавиш
        self.root.bind('<Left>', lambda e: self.move_left())
        self.root.bind('<Right>', lambda e: self.move_right())
        self.root.bind('<Up>', lambda e: self.move_up())
        self.root.bind('<Down>', lambda e: self.move_down())
        self.root.bind('<n>', lambda e: self.new_game())
        
        self.new_game()
    
    def create_game_grid(self):
        # Создаем сетку 4x4
        self.cells = []
        for i in range(4):
            row = []
            for j in range(4):
                cell = tk.Label(self.game_frame, text="", width=4, height=2, 
                               font=("Arial", 16, "bold"), relief="raised", borderwidth=2)
                cell.grid(row=i, column=j, padx=2, pady=2)
                row.append(cell)
            self.cells.append(row)
    
    def update_grid(self):
        # Цвета для плиток
        colors = {
            0: ("#cdc1b4", "#776e65"),
            2: ("#eee4da", "#776e65"),
            4: ("#ede0c8", "#776e65"),
            8: ("#f2b179", "#f9f6f2"),
            16: ("#f59563", "#f9f6f2"),
            32: ("#f67c5f", "#f9f6f2"),
            64: ("#f65e3b", "#f9f6f2"),
            128: ("#edcf72", "#f9f6f2"),
            256: ("#edcc61", "#f9f6f2"),
            512: ("#edc850", "#f9f6f2"),
            1024: ("#edc53f", "#f9f6f2"),
            2048: ("#edc22e", "#f9f6f2")
        }
        
        for i in range(4):
            for j in range(4):
                value = self.game.grid[i][j]
                bg_color, fg_color = colors.get(value, ("#3c3a32", "#f9f6f2"))
                
                self.cells[i][j].config(
                    text=str(value) if value != 0 else "",
                    bg=bg_color,
                    fg=fg_color
                )
        
        self.score_label.config(text=f"Очки: {self.game.score}")
    
    def new_game(self):
        self.game = Game2048()
        self.update_grid()
        self.update_stats()
    
    def move_left(self):
        if self.game and self.game.move_left():
            self.game.add_new_tile()
            self.update_grid()
            self.check_game_over()
    
    def move_right(self):
        if self.game and self.game.move_right():
            self.game.add_new_tile()
            self.update_grid()
            self.check_game_over()
    
    def move_up(self):
        if self.game and self.game.move_up():
            self.game.add_new_tile()
            self.update_grid()
            self.check_game_over()
    
    def move_down(self):
        if self.game and self.game.move_down():
            self.game.add_new_tile()
            self.update_grid()
            self.check_game_over()
    
    def check_game_over(self):
        if self.game and self.game.is_game_over():
            best_score = self.db.update_user_score(self.current_user, self.game.score)
            messagebox.showinfo("Игра окончена!", 
                              f"💀 Игра окончена!\n"
                              f"🏆 Ваш результат: {self.game.score}\n"
                              f"🎯 Лучший результат: {best_score}")
            self.update_stats()
    
    def save_user(self):
        new_user = self.user_entry.get().strip()
        if new_user:
            self.current_user = new_user
            if not self.db.get_user(new_user):
                self.db.create_user(new_user)
            self.update_stats()
            messagebox.showinfo("Успех", f"Игрок изменен на: {new_user}")
    
    def update_stats(self):
        user = self.db.get_user(self.current_user)
        if user:
            best_score = user[2]
            self.best_label.config(text=f"Лучший: {best_score}")
    
    def show_leaderboard(self):
        leaderboard_window = tk.Toplevel(self.root)
        leaderboard_window.title("Таблица лидеров")
        leaderboard_window.geometry("300x400")
        
        ttk.Label(leaderboard_window, text="🏆 Топ игроков", font=("Arial", 16, "bold")).pack(pady=10)
        
        tree = ttk.Treeview(leaderboard_window, columns=("Rank", "Name", "Score", "Games"), show="headings", height=15)
        tree.heading("Rank", text="Место")
        tree.heading("Name", text="Игрок")
        tree.heading("Score", text="Рекорд")
        tree.heading("Games", text="Игр")
        
        tree.column("Rank", width=50)
        tree.column("Name", width=100)
        tree.column("Score", width=70)
        tree.column("Games", width=50)
        
        leaderboard = self.db.get_leaderboard()
        for i, (username, score, games) in enumerate(leaderboard, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
            tree.insert("", "end", values=(medal, username, score, games))
        
        tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    def show_stats(self):
        user = self.db.get_user(self.current_user)
        if user:
            username, best_score, games_played, created_at = user[1], user[2], user[3], user[4]
            stats_text = (f"📊 Статистика игрока {username}:\n\n"
                         f"🎯 Лучший результат: {best_score}\n"
                         f"🎮 Сыграно игр: {games_played}\n"
                         f"📅 Играет с: {created_at[:10]}")
            messagebox.showinfo("Моя статистика", stats_text)
        else:
            messagebox.showinfo("Моя статистика", "Статистика не найдена!")

def main():
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()