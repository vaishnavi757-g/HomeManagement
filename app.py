from flask import Flask, render_template, request, redirect, url_for,session
import sqlite3

app = Flask(__name__)
app.secret_key = "home_management_secret_key"
# Database connection
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL
        )
    """)
    try:
        conn.execute("""
            ALTER TABLE shopping
            ADD COLUMN completed INTEGER DEFAULT 0
        """)
    except sqlite3.OperationalError:
        pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
    try:
        conn.execute(
            "ALTER TABLE tasks ADD COLUMN user_id INTEGER"
        )
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE expenses ADD COLUMN user_id INTEGER"
        )
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE shopping ADD COLUMN user_id INTEGER"
        )
    except sqlite3.OperationalError:
        pass
    conn.commit()

    conn.close()

# Home page
@app.route("/")
def home():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    # Total Tasks
    tasks_count = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id = ?",
        (user["id"],)
    ).fetchone()[0]

    # Total Expenses
    expenses_total = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
        """,
        (user["id"],)
    ).fetchone()[0]

    # Shopping Items
    shopping_count = conn.execute(
        "SELECT COUNT(*) FROM shopping WHERE user_id = ?",
        (user["id"],)
    ).fetchone()[0]

    # Recent Tasks
    recent_tasks = conn.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user["id"],)
    ).fetchall()

    # Recent Expenses
    recent_expenses = conn.execute(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user["id"],)
    ).fetchall()

    # Recent Shopping
    recent_shopping = conn.execute(
        """
        SELECT * FROM shopping
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user["id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        tasks_count=tasks_count,
        expenses_total=expenses_total,
        shopping_count=shopping_count,
        recent_tasks=recent_tasks,
        recent_expenses=recent_expenses,
        recent_shopping=recent_shopping
    )
@app.route("/about")
def about():
    return render_template("about.html")
# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db()

    message = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            message = "Registration successful!"

        except sqlite3.IntegrityError:
            message = "Username already exists."

    conn.close()

    return render_template(
        "register.html",
        message=message
    )  
# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    conn = get_db()

    message = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        if user:
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            message = "Invalid username or password."

    conn.close()

    return render_template(
        "login.html",
        message=message
    )
# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))
# Manage Tasks
@app.route("/tasks", methods=["GET", "POST"])
def tasks():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    if request.method == "POST":
        task = request.form["task"]

        conn.execute(
            "INSERT INTO tasks (task, user_id) VALUES (?, ?)",
            (task, user["id"])
        )

        conn.commit()

    tasks_list = conn.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user["id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "tasks.html",
        tasks=tasks_list
    )

# Complete Task
@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    conn.execute(
        """
        UPDATE tasks
        SET completed = 1
        WHERE id = ? AND user_id = ?
        """,
        (task_id, user["id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))

# Delete Task
@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    conn.execute(
        """
        DELETE FROM tasks
        WHERE id = ? AND user_id = ?
        """,
        (task_id, user["id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))

# Manage Expenses
@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    if request.method == "POST":
        expense = request.form["expense"]
        amount = request.form["amount"]

        conn.execute(
            "INSERT INTO expenses (name, amount, user_id) VALUES (?, ?, ?)",
            (expense, amount, user["id"])
        )

        conn.commit()

    expenses_list = conn.execute(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user["id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "expenses.html",
        expenses=expenses_list
    )
# Manage Shopping
@app.route("/shopping", methods=["GET", "POST"])
def shopping():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    if request.method == "POST":
        item = request.form["item"]

        conn.execute(
            "INSERT INTO shopping (item, user_id) VALUES (?, ?)",
            (item, user["id"])
        )

        conn.commit()

    shopping_list = conn.execute(
        """
        SELECT * FROM shopping
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user["id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "shopping.html",
        shopping_list=shopping_list
    )

@app.route("/delete_shopping/<int:item_id>")
def delete_shopping(item_id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    conn.execute(
        """
        DELETE FROM shopping
        WHERE id = ? AND user_id = ?
        """,
        (item_id, user["id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("shopping"))

@app.route("/complete_shopping/<int:item_id>")
def complete_shopping(item_id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    conn.execute(
        """
        UPDATE shopping
        SET completed = 1
        WHERE id = ? AND user_id = ?
        """,
        (item_id, user["id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("shopping"))

@app.route("/delete_expense/<int:expense_id>")
def delete_expense(expense_id):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["username"],)
    ).fetchone()

    conn.execute(
        """
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (expense_id, user["id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("expenses"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)