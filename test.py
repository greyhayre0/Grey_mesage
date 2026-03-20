import sqlite3

def view_users():
    try:
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Таблица users не существует")
            return
        
        # Получаем всех пользователей
        cursor.execute("SELECT id, username, role FROM users")
        rows = cursor.fetchall()
        
        if not rows:
            print("Нет пользователей в базе")
        else:
            print("ID | username | role")
            print("-" * 30)
            for row in rows:
                print(f"{row[0]} | {row[1]} | {row[2]}")
        
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    view_users()