import os
import subprocess
import sys

def main():
    # Project configuration
    project_name = "tic_tac_toe_website"
    base_dir = os.path.expanduser(f"~/Desktop/Work/{project_name}")
    logs_dir = os.path.join(base_dir, "logs")
    venv_dir = os.path.join(base_dir, "venv")
    app_file = os.path.join(base_dir, "app.py")

    # Step 1: Project setup - Create project and logs folders
    os.makedirs(logs_dir, exist_ok=True)

    # Step 2: Set up Python virtual environment
    subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Step 3: Install Flask in the virtual environment
    if os.name == "nt":
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_executable = os.path.join(venv_dir, "bin", "pip")
        python_executable = os.path.join(venv_dir, "bin", "python")
    subprocess.run([pip_executable, "install", "flask"], check=True)

    # Step 4: Feature implementation - Write the tic tac toe Flask app
    app_code = '''from flask import Flask, render_template_string, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")

TEMPLATE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Tic Tac Toe</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; margin: 20px 0; }
        td {
            width: 60px; height: 60px; text-align: center; font-size: 2em;
            border: 2px solid #444; cursor: pointer;
        }
        .winner { color: green; }
        .draw { color: orange; }
        .reset-btn { margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Tic Tac Toe</h1>
    <form method="post">
        <table>
            {% for i in range(3) %}
            <tr>
                {% for j in range(3) %}
                <td>
                    {% if board[i][j] == '' and not winner %}
                        <button type="submit" name="move" value="{{i}}-{{j}}" style="width:100%;height:100%;font-size:2em;background:none;border:none;">&nbsp;</button>
                    {% else %}
                        {{ board[i][j] }}
                    {% endif %}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
    </form>
    {% if winner %}
        <div class="winner">{{ winner }} wins!</div>
    {% elif draw %}
        <div class="draw">It's a draw!</div>
    {% endif %}
    <form method="post">
        <button type="submit" name="reset" class="reset-btn">Reset Game</button>
    </form>
</body>
</html>
"""

def check_winner(board):
    # Rows, columns, diagonals
    lines = board + [list(col) for col in zip(*board)]
    lines.append([board[i][i] for i in range(3)])
    lines.append([board[i][2-i] for i in range(3)])
    for line in lines:
        if line[0] and line.count(line[0]) == 3:
            return line[0]
    return None

def is_draw(board):
    return all(cell for row in board for cell in row)

def log_game(board, winner):
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    with open(os.path.join(LOGS_DIR, "games.log"), "a") as f:
        f.write(f"Board: {board}, Winner: {winner}\\n")

@app.route("/", methods=["GET", "POST"])
def index():
    if "board" not in session:
        session["board"] = [["" for _ in range(3)] for _ in range(3)]
        session["turn"] = "X"
    board = session["board"]
    turn = session["turn"]
    winner = check_winner(board)
    draw = is_draw(board) and not winner

    if request.method == "POST":
        if "reset" in request.form:
            session.pop("board", None)
            session.pop("turn", None)
            return redirect(url_for("index"))
        if not winner and not draw and "move" in request.form:
            move = request.form["move"]
            i, j = map(int, move.split("-"))
            if board[i][j] == "":
                board[i][j] = turn
                session["turn"] = "O" if turn == "X" else "X"
                winner = check_winner(board)
                draw = is_draw(board) and not winner
                session["board"] = board
                if winner or draw:
                    log_game(board, winner if winner else "Draw")
            return redirect(url_for("index"))

    return render_template_string(TEMPLATE, board=board, winner=winner, draw=draw)

if __name__ == "__main__":
    app.run(debug=True)
'''
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(app_code)

if __name__ == "__main__":
    main()