#!/usr/bin/env python3
"""Tic-Tac-Toe engine for the GitHub profile README.

Triggered by a GitHub Action when someone opens an issue titled:
  ttt|move|<0-8>   -> player (X) plays that cell, then the bot (O) replies
  ttt|reset        -> start a fresh board

The script updates the board state, re-renders the board inside the
<!--START:ttt--> ... <!--END:ttt--> markers in README.md, and saves state.
"""
import json
import os
import re
import urllib.parse

REPO = "UsmanShahab18/UsmanShahab18"
DATA = ".github/ttt/board.json"
README = "README.md"
START = "<!--START:ttt-->"
END = "<!--END:ttt-->"
WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # cols
    (0, 4, 8), (2, 4, 6),              # diagonals
]


def load():
    try:
        with open(DATA, encoding="utf-8") as f:
            d = json.load(f)
            return d.get("board", [""] * 9), d.get("status", "playing")
    except (FileNotFoundError, ValueError):
        return [""] * 9, "playing"


def save(board, status):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump({"board": board, "status": status}, f, indent=2)


def winner(b):
    for a, c, d in WIN_LINES:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    if all(b):
        return "draw"
    return None


def bot_move(b):
    """Play O: win > block > center > corner > side."""
    # 1) Win if possible
    for i in range(9):
        if not b[i]:
            b[i] = "O"
            if winner(b) == "O":
                return
            b[i] = ""
    # 2) Block the player's winning move
    for i in range(9):
        if not b[i]:
            b[i] = "X"
            if winner(b) == "X":
                b[i] = "O"
                return
            b[i] = ""
    # 3) Center, then corners, then sides
    for i in (4, 0, 2, 6, 8, 1, 3, 5, 7):
        if not b[i]:
            b[i] = "O"
            return


def issue_url(title):
    t = urllib.parse.quote(title, safe="")
    body = urllib.parse.quote(
        "Press Submit new issue and the bot will play your move.", safe="")
    return f"https://github.com/{REPO}/issues/new?title={t}&body={body}"


def cell(b, i):
    if b[i] == "X":
        return "❌"
    if b[i] == "O":
        return "⭕"
    return f'<a href="{issue_url(f"ttt|move|{i}")}">⬜</a>'


def render(b, status):
    rows = ""
    for r in range(3):
        tds = "".join(
            f'<td align="center" width="70" height="70">{cell(b, r * 3 + c)}</td>'
            for c in range(3)
        )
        rows += f"<tr>{tds}</tr>\n"
    table = f"<table>\n{rows}</table>"

    if status == "X":
        msg = "🎉 **You won!** Click any square or New Game to play again."
    elif status == "O":
        msg = "🤖 **The bot won this round!** Click any square to try again."
    elif status == "draw":
        msg = "🤝 **It's a draw!** Start a new game below."
    else:
        msg = "🧑‍💻 **Your turn — you're ❌.** Click any ⬜ to make your move."

    reset = f'<a href="{issue_url("ttt|reset")}">🔄 New Game</a>'
    return (f"<div align=\"center\">\n\n{table}\n\n{msg}\n\n{reset}\n\n</div>")


def main():
    title = os.environ.get("ISSUE_TITLE", "").strip()
    board, status = load()

    if title == "ttt|reset":
        board, status = [""] * 9, "playing"
    elif title.startswith("ttt|move|"):
        parts = title.split("|")
        try:
            idx = int(parts[2])
        except (IndexError, ValueError):
            return
        if not (0 <= idx <= 8):
            return
        # A finished game -> start fresh before applying the click
        if status != "playing":
            board, status = [""] * 9, "playing"
        if board[idx]:
            # Cell already taken; ignore but still re-render current state
            pass
        else:
            board[idx] = "X"
            result = winner(board)
            if result == "X":
                status = "X"
            elif result == "draw":
                status = "draw"
            else:
                bot_move(board)
                result = winner(board)
                if result == "O":
                    status = "O"
                elif result == "draw":
                    status = "draw"
                else:
                    status = "playing"
    else:
        return  # Not a game command

    save(board, status)

    block = render(board, status)
    with open(README, encoding="utf-8") as f:
        content = f.read()
    pattern = re.escape(START) + r".*?" + re.escape(END)
    replacement = f"{START}\n{block}\n{END}"
    content = re.sub(pattern, replacement, content, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
