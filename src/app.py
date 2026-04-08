from __future__ import annotations

import tkinter as tk
from typing import Dict, List

import customtkinter as ctk

from game_core import (
    GameState,
    SearchStats,
    choose_computer_move,
    format_move,
    make_candidate_pool,
    run_experiments,
    sample_start_numbers,
)


class DivisorGameApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Divide-by-2-or-3 Game")
        self.geometry("1460x920")
        self.minsize(1240, 780)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.candidate_pool = make_candidate_pool()
        self.candidate_numbers = sample_start_numbers(self.candidate_pool)
        self.selected_number: int | None = None
        self.game: GameState | None = None
        self.computer_thinking = False
        self.pending_computer_turn_id: str | None = None
        self.last_search_stats = SearchStats()

        self.first_player_var = ctk.StringVar(value="Human")
        self.algorithm_var = ctk.StringVar(value="Alpha-Beta")
        self.depth_var = ctk.IntVar(value=5)
        self.visual_depth_var = ctk.StringVar(value="3")
        self.human_policy_var = ctk.StringVar(value="Greedy")
        self.experiment_depth_var = ctk.StringVar(value=f"Current: {self.depth_var.get()}")

        self.status_var = ctk.StringVar(value="No game started")
        self.turn_var = ctk.StringVar(value="-")
        self.current_number_var = ctk.StringVar(value="-")
        self.human_score_var = ctk.StringVar(value="0")
        self.computer_score_var = ctk.StringVar(value="0")
        self.bank_var = ctk.StringVar(value="0")
        self.tree_context_var = ctk.StringVar(value="Possible future moves from current state")
        self.tree_depth_var = ctk.StringVar(value="Shown tree depth: 3")
        self.search_stats_var = ctk.StringVar(value="No computer search yet")

        self.number_buttons: List[ctk.CTkButton] = []
        self.tree_window: ctk.CTkToplevel | None = None
        self.tree_canvas: tk.Canvas | None = None
        self.tree_context_label: ctk.CTkLabel | None = None
        self.tree_stats_label: ctk.CTkLabel | None = None
        self.experiments_window: ctk.CTkToplevel | None = None
        self.experiment_box: ctk.CTkTextbox | None = None
        self.run_experiments_button: ctk.CTkButton | None = None

        self._build_ui()
        self._render_candidate_buttons()
        self._refresh_view()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=16)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Divide-by-2-or-3 game", font=ctk.CTkFont(size=30, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 4)
        )
        ctk.CTkLabel(
            header,
            text=(
                "Team 2 Game"
            ),
            justify="left",
            wraplength=1100,
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))

        setup = ctk.CTkFrame(self, corner_radius=16)
        setup.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        setup.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(setup, text="Who starts", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 4)
        )
        ctk.CTkOptionMenu(setup, values=["Human", "Computer"], variable=self.first_player_var).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 14)
        )

        ctk.CTkLabel(setup, text="Computer algorithm", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=16, pady=(16, 4)
        )
        ctk.CTkOptionMenu(setup, values=["Minimax", "Alpha-Beta"], variable=self.algorithm_var).grid(
            row=1, column=1, sticky="ew", padx=16, pady=(0, 14)
        )

        ctk.CTkLabel(setup, text="Search depth (N-ply)", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=2, sticky="w", padx=16, pady=(16, 4)
        )
        self.depth_label = ctk.CTkLabel(setup, text=f"{self.depth_var.get()}", font=ctk.CTkFont(size=15, weight="bold"))
        self.depth_label.grid(row=0, column=3, sticky="e", padx=16, pady=(16, 4))
        ctk.CTkSlider(
            setup,
            from_=2,
            to=8,
            number_of_steps=6,
            variable=self.depth_var,
            command=self._on_depth_changed,
        ).grid(row=1, column=2, columnspan=2, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            setup,
            text="Choose one of the 5 generated start numbers",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=16, pady=(2, 10))

        self.number_buttons_frame = ctk.CTkFrame(setup, fg_color="transparent")
        self.number_buttons_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10)
        self.number_buttons_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkButton(setup, text="Generate new numbers", command=self.generate_new_numbers).grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(12, 16)
        )
        ctk.CTkButton(setup, text="Start game", command=self.start_game).grid(
            row=4, column=2, columnspan=2, sticky="ew", padx=(8, 16), pady=(12, 16)
        )

        middle = ctk.CTkFrame(self, corner_radius=16)
        middle.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        middle.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for idx, (title, variable) in enumerate(
            [
                ("Current number", self.current_number_var),
                ("Human score", self.human_score_var),
                ("Computer score", self.computer_score_var),
                ("Bank", self.bank_var),
            ]
        ):
            card = ctk.CTkFrame(middle, corner_radius=12)
            card.grid(row=0, column=idx, sticky="ew", padx=8, pady=(14, 8))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(card, textvariable=variable, font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkLabel(middle, text="Status", font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=1, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        ctk.CTkLabel(middle, textvariable=self.status_var, font=ctk.CTkFont(size=15)).grid(
            row=1, column=1, columnspan=3, sticky="w", padx=12, pady=(10, 4)
        )
        ctk.CTkLabel(middle, text="Turn", font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=2, column=0, sticky="w", padx=12, pady=(0, 10)
        )
        ctk.CTkLabel(middle, textvariable=self.turn_var, font=ctk.CTkFont(size=15)).grid(
            row=2, column=1, columnspan=3, sticky="w", padx=12, pady=(0, 10)
        )

        actions = ctk.CTkFrame(middle, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 14))
        actions.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.divide2_button = ctk.CTkButton(actions, text="Divide by 2", command=lambda: self.human_move(2))
        self.divide2_button.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.divide3_button = ctk.CTkButton(actions, text="Divide by 3", command=lambda: self.human_move(3))
        self.divide3_button.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        self.restart_button = ctk.CTkButton(actions, text="Restart current match", command=self.restart_match)
        self.restart_button.grid(row=0, column=2, sticky="ew", padx=6, pady=6)
        ctk.CTkButton(actions, text="Open game tree", command=self._open_tree_window).grid(
            row=0, column=3, sticky="ew", padx=6, pady=6
        )
        ctk.CTkButton(actions, text="Open experiments", command=self._open_experiments_window).grid(
            row=0, column=4, sticky="ew", padx=6, pady=6
        )

        history_frame = ctk.CTkFrame(self, corner_radius=16)
        history_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8, 16))
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(history_frame, text="Move history", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 8)
        )
        ctk.CTkLabel(
            history_frame,
            text="The game tree and experiment tools were moved out of the main screen to keep gameplay simpler.",
            justify="left",
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="e", padx=14, pady=(14, 8))
        self.history_text = ctk.CTkTextbox(history_frame, wrap="word")
        self.history_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.history_text.configure(font=("Consolas", 13))

    def _on_depth_changed(self, value: float) -> None:
        depth_value = str(int(round(value)))
        self.depth_label.configure(text=depth_value)
        self.experiment_depth_var.set(f"Current: {depth_value}")
        self._render_tree_window()

    def _render_candidate_buttons(self) -> None:
        for widget in self.number_buttons_frame.winfo_children():
            widget.destroy()
        self.number_buttons.clear()
        for index, number in enumerate(self.candidate_numbers):
            button = ctk.CTkButton(
                self.number_buttons_frame,
                text=str(number),
                command=lambda n=number: self.select_number(n),
            )
            button.grid(row=0, column=index, sticky="ew", padx=6, pady=6)
            self.number_buttons.append(button)
        self._refresh_number_buttons()

    def _refresh_number_buttons(self) -> None:
        has_selection = self.selected_number is not None
        for button, number in zip(self.number_buttons, self.candidate_numbers):
            if self.selected_number == number:
                button.configure(
                    fg_color=("#1F6AA5", "#144870"),
                    hover_color=("#1A5A8A", "#103A58"),
                    state="disabled",
                    text_color_disabled=("#F9FAFB", "#F9FAFB"),
                )
            elif has_selection:
                button.configure(
                    fg_color=("#C5CDD8", "#4B5563"),
                    hover_color=("#C5CDD8", "#4B5563"),
                    state="disabled",
                    text_color_disabled=("#6B7280", "#D1D5DB"),
                )
            else:
                button.configure(
                    fg_color=("#3B8ED0", "#1F6AA5"),
                    hover_color=("#36719F", "#144870"),
                    state="normal",
                )

    def select_number(self, number: int) -> None:
        if self.selected_number is not None:
            return
        self.selected_number = number
        self._refresh_number_buttons()

    def generate_new_numbers(self) -> None:
        self._cancel_pending_computer_turn()
        self.candidate_numbers = sample_start_numbers(self.candidate_pool)
        self.selected_number = None
        self.game = None
        self.computer_thinking = False
        self.last_search_stats = SearchStats()
        self._render_candidate_buttons()
        self._refresh_view()

    def start_game(self) -> None:
        if self.selected_number is None:
            self.status_var.set("Select one of the generated numbers first")
            return
        self._cancel_pending_computer_turn()
        self.computer_thinking = False
        self.game = GameState(
            number=self.selected_number,
            human_score=0,
            computer_score=0,
            bank=0,
            is_human_turn=(self.first_player_var.get() == "Human"),
        )
        self.last_search_stats = SearchStats()
        self._refresh_view()
        self._maybe_run_computer_turn()

    def restart_match(self) -> None:
        self._cancel_pending_computer_turn()
        self.selected_number = None
        self.game = None
        self.computer_thinking = False
        self.last_search_stats = SearchStats()
        self._refresh_view()

    def human_move(self, divisor: int) -> None:
        if self.game is None or self.computer_thinking:
            return
        if self.game.is_terminal() or not self.game.is_human_turn:
            return
        if divisor not in self.game.legal_moves():
            return
        self.game = self.game.apply_move(divisor)
        self._refresh_view()
        self._maybe_run_computer_turn()

    def _cancel_pending_computer_turn(self) -> None:
        if self.pending_computer_turn_id is not None:
            try:
                self.after_cancel(self.pending_computer_turn_id)
            except Exception:
                pass
            self.pending_computer_turn_id = None

    def _maybe_run_computer_turn(self) -> None:
        if self.game is None:
            return
        if self.game.is_terminal() or self.game.is_human_turn or self.computer_thinking:
            return
        self.computer_thinking = True
        self.status_var.set("Computer is thinking...")
        self._refresh_buttons()
        self.pending_computer_turn_id = self.after(150, self._run_computer_turn)

    def _run_computer_turn(self) -> None:
        self.pending_computer_turn_id = None
        if self.game is None:
            self.computer_thinking = False
            return
        move, next_state, _, stats = choose_computer_move(self.game, int(self.depth_var.get()), self.algorithm_var.get())
        self.last_search_stats = stats
        if move is not None:
            self.game = next_state
        self.computer_thinking = False
        self._refresh_view()

    def _refresh_view(self) -> None:
        if self.game is None:
            self.current_number_var.set("-")
            self.human_score_var.set("0")
            self.computer_score_var.set("0")
            self.bank_var.set("0")
            self.turn_var.set("-")
            self.status_var.set("No game started" if self.selected_number is None else "Ready to start")
            self.history_text.configure(state="normal")
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", "Start a match to see the move history.\n\nOpen the Game Tree window when you want to inspect possible future moves.")
            self.history_text.configure(state="disabled")
        else:
            self.current_number_var.set(str(self.game.number))
            self.human_score_var.set(str(self.game.human_score))
            self.computer_score_var.set(str(self.game.computer_score))
            self.bank_var.set(str(self.game.bank))
            if self.game.is_terminal():
                self.turn_var.set("Game finished")
                self.status_var.set(
                    f"{self.game.winner_label()} | Final score: Human {self.game.human_score}, Computer {self.game.computer_score}"
                )
            else:
                self.turn_var.set("Human" if self.game.is_human_turn else "Computer")
                if not self.computer_thinking:
                    self.status_var.set("Human turn" if self.game.is_human_turn else "Computer turn")
            self._render_history_text()

        if self.last_search_stats.generated == 0 and self.last_search_stats.evaluated == 0:
            self.search_stats_var.set("No computer search yet")
        else:
            self.search_stats_var.set(
                f"Generated {self.last_search_stats.generated} | Evaluated {self.last_search_stats.evaluated} | "
                f"Pruned {self.last_search_stats.pruned} | Time {self.last_search_stats.time_ms:.2f} ms"
            )

        self._refresh_buttons()
        self._refresh_number_buttons()
        self._apply_tree_context_colors()
        self._render_tree_window()

    def _render_history_text(self) -> None:
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if self.game is None:
            self.history_text.insert("1.0", "Start a match to see the move history.")
        elif not self.game.path:
            self.history_text.insert(
                "1.0",
                "No move has been played yet.\n\nOpen the Game Tree window to inspect the possible future moves from the current state.",
            )
        else:
            text = "\n\n".join(format_move(move, index) for index, move in enumerate(self.game.path))
            self.history_text.insert("1.0", text)
            self.history_text.see("end")
        self.history_text.configure(state="disabled")

    def _refresh_buttons(self) -> None:
        legal_moves = self.game.legal_moves() if self.game is not None else []
        can_human_act = (
            self.game is not None and not self.computer_thinking and not self.game.is_terminal() and self.game.is_human_turn
        )
        self.divide2_button.configure(state="normal" if can_human_act and 2 in legal_moves else "disabled")
        self.divide3_button.configure(state="normal" if can_human_act and 3 in legal_moves else "disabled")
        self.restart_button.configure(state="normal" if self.selected_number is not None else "disabled")

    def _state_line(self, state: GameState) -> str:
        turn = "H" if state.is_human_turn else "C"
        suffix = " terminal" if state.is_terminal() else ""
        return f"N={state.number} | H={state.human_score} C={state.computer_score} B={state.bank} | turn={turn}{suffix}"

    def _tree_context_info(self) -> Dict[str, str]:
        if self.game is None or len(self.game.path) == 0:
            return {
                "text": "Possible future moves from current state",
                "fg": "#7a4b00",
                "bg": "#ffe8b3",
                "node_fill": "#fff0cc",
                "node_outline": "#c77d00",
                "edge": "#a86b00",
            }
        return {
            "text": f"Future moves after {len(self.game.path)} move(s) already played",
            "fg": "#0f5132",
            "bg": "#cfead6",
            "node_fill": "#dff1ff",
            "node_outline": "#1f6aa5",
            "edge": "#667a8a",
        }

    def _apply_tree_context_colors(self) -> None:
        context = self._tree_context_info()
        self.tree_context_var.set(context["text"])
        if self.tree_context_label is not None and self.tree_context_label.winfo_exists():
            self.tree_context_label.configure(fg_color=context["bg"], text_color=context["fg"])

    def _build_tree_layout(self, state: GameState, depth: int):
        levels: List[List[GameState]] = [[state]]
        current_level = [state]
        for _ in range(depth):
            next_level: List[GameState] = []
            for node in current_level:
                if node.is_terminal():
                    continue
                for move in node.legal_moves():
                    next_level.append(node.apply_move(move))
            if not next_level:
                break
            levels.append(next_level)
            current_level = next_level
        return levels

    def _render_tree_graphic(self, canvas: tk.Canvas) -> None:
        canvas.delete("all")
        width = max(canvas.winfo_width(), 800)
        height = max(canvas.winfo_height(), 560)

        if self.game is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Start a game, then open this window to inspect the current game tree.",
                font=("Segoe UI", 16, "bold"),
                width=width - 80,
                fill="#334155",
            )
            return

        depth = int(self.visual_depth_var.get())
        levels = self._build_tree_layout(self.game, depth)
        context = self._tree_context_info()
        top_margin = 80
        side_margin = 100
        vertical_step = max(110, min(160, (height - top_margin - 80) / max(1, len(levels) - 1 or 1)))
        box_w = 116
        box_h = 52
        positions: Dict[tuple[int, int], tuple[float, float]] = {}

        for level_index, level in enumerate(levels):
            count = len(level)
            if count == 1:
                xs = [width / 2]
            else:
                usable_width = max(200, width - 2 * side_margin)
                spacing = usable_width / (count - 1)
                xs = [side_margin + spacing * i for i in range(count)]
            y = top_margin + level_index * vertical_step
            for item_index, x in enumerate(xs):
                positions[(level_index, item_index)] = (x, y)

        for level_index in range(len(levels) - 1):
            parent_index = 0
            child_index = 0
            for parent in levels[level_index]:
                parent_pos = positions[(level_index, parent_index)]
                children = []
                if not parent.is_terminal():
                    for move in parent.legal_moves():
                        children.append((move, parent.apply_move(move)))
                for move, _child in children:
                    child_pos = positions[(level_index + 1, child_index)]
                    canvas.create_line(
                        parent_pos[0],
                        parent_pos[1] + box_h / 2,
                        child_pos[0],
                        child_pos[1] - box_h / 2,
                        fill=context["edge"],
                        width=2,
                    )
                    label_x = (parent_pos[0] + child_pos[0]) / 2
                    label_y = (parent_pos[1] + child_pos[1]) / 2 - 10
                    canvas.create_text(label_x, label_y, text=f"÷{move}", font=("Segoe UI", 9, "bold"), fill=context["edge"])
                    child_index += 1
                parent_index += 1

        for level_index, level in enumerate(levels):
            for item_index, node in enumerate(level):
                x, y = positions[(level_index, item_index)]
                canvas.create_rectangle(
                    x - box_w / 2,
                    y - box_h / 2,
                    x + box_w / 2,
                    y + box_h / 2,
                    fill=context["node_fill"],
                    outline=context["node_outline"],
                    width=2,
                )
                turn = "H" if node.is_human_turn else "C"
                canvas.create_text(x, y - 12, text=str(node.number), font=("Segoe UI", 10, "bold"), fill="#1f2937")
                canvas.create_text(
                    x,
                    y + 2,
                    text=f"H:{node.human_score} C:{node.computer_score} B:{node.bank}",
                    font=("Segoe UI", 8),
                    fill="#1f2937",
                )
                canvas.create_text(x, y + 16, text=turn, font=("Segoe UI", 9, "bold"), fill="#1f2937")

    def _open_tree_window(self) -> None:
        if self.tree_window is not None and self.tree_window.winfo_exists():
            self.tree_window.focus()
            self._render_tree_window()
            return

        self.tree_window = ctk.CTkToplevel(self)
        self.tree_window.title("Game Tree")
        self.tree_window.geometry("1120x820")
        self.tree_window.minsize(900, 700)
        self.tree_window.grid_columnconfigure(0, weight=1)
        self.tree_window.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.tree_window, text="Game tree", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        ctk.CTkLabel(
            self.tree_window,
            text="This window shows possible future states from the current live position. It updates after every move.",
            justify="left",
            wraplength=900,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        topbar = ctk.CTkFrame(self.tree_window, corner_radius=12)
        topbar.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        topbar.grid_columnconfigure(3, weight=1)
        self.tree_context_label = ctk.CTkLabel(
            topbar,
            textvariable=self.tree_context_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            padx=10,
            pady=5,
        )
        self.tree_context_label.grid(row=0, column=0, sticky="w", padx=12, pady=12)
        ctk.CTkLabel(topbar, text="Shown depth", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=(8, 8), pady=12
        )
        ctk.CTkOptionMenu(
            topbar,
            values=["2", "3", "4", "5"],
            variable=self.visual_depth_var,
            width=90,
            command=self._on_visual_depth_changed,
        ).grid(row=0, column=2, sticky="w", pady=12)
        ctk.CTkLabel(topbar, textvariable=self.tree_depth_var, font=ctk.CTkFont(size=12)).grid(
            row=0, column=3, sticky="w", padx=(12, 10), pady=12
        )
        self.tree_stats_label = ctk.CTkLabel(topbar, textvariable=self.search_stats_var, font=ctk.CTkFont(size=12))
        self.tree_stats_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 12))

        holder = tk.Frame(self.tree_window, bg="#d9d9d9")
        holder.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)
        self.tree_canvas = tk.Canvas(holder, bg="white", highlightthickness=0)
        self.tree_canvas.grid(row=0, column=0, sticky="nsew")
        self.tree_canvas.bind("<Configure>", lambda _event: self._render_tree_window())

        self._render_tree_window()

    def _on_visual_depth_changed(self, value: str) -> None:
        self.tree_depth_var.set(f"Shown tree depth: {value}")
        self._render_tree_window()

    def _render_tree_window(self) -> None:
        if self.tree_window is None or not self.tree_window.winfo_exists() or self.tree_canvas is None:
            return
        self._apply_tree_context_colors()
        self._render_tree_graphic(self.tree_canvas)

    def _open_experiments_window(self) -> None:
        if self.experiments_window is not None and self.experiments_window.winfo_exists():
            self.experiments_window.focus()
            return

        self.experiments_window = ctk.CTkToplevel(self)
        self.experiments_window.title("Experiment Runner")
        self.experiments_window.geometry("900x720")
        self.experiments_window.minsize(760, 620)
        self.experiments_window.grid_columnconfigure(0, weight=1)
        self.experiments_window.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.experiments_window, text="Experiment runner", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )
        ctk.CTkLabel(
            self.experiments_window,
            text="Runs 10 games with Minimax and 10 games with Alpha-Beta using the current search depth.",
            justify="left",
            wraplength=760,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        controls = ctk.CTkFrame(self.experiments_window, corner_radius=12)
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        controls.grid_columnconfigure((1, 3), weight=1)
        ctk.CTkLabel(controls, text="Simulated human policy", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=12
        )
        ctk.CTkOptionMenu(controls, values=["Greedy", "Random"], variable=self.human_policy_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 12), pady=12
        )
        ctk.CTkLabel(controls, text="Depth used", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=2, sticky="w", padx=(12, 8), pady=12
        )
        ctk.CTkLabel(controls, textvariable=self.experiment_depth_var, font=ctk.CTkFont(size=13)).grid(
            row=0, column=3, sticky="w", padx=(0, 12), pady=12
        )
        self.run_experiments_button = ctk.CTkButton(controls, text="Run 10 + 10 experiments", command=self.run_experiments)
        self.run_experiments_button.grid(row=1, column=0, columnspan=4, sticky="ew", padx=12, pady=(0, 12))

        self.experiment_box = ctk.CTkTextbox(self.experiments_window, wrap="word")
        self.experiment_box.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.experiment_box.configure(font=("Consolas", 13))
        self.experiment_box.insert(
            "1.0",
            "Open this window only when you want benchmark results.\n\n"
            "The main gameplay screen stays focused on playing the match.",
        )

    def run_experiments(self) -> None:
        if self.experiment_box is None or self.run_experiments_button is None:
            return
        self.run_experiments_button.configure(state="disabled", text="Running...")
        self.experiment_box.delete("1.0", "end")
        self.update_idletasks()
        summaries = run_experiments(
            depth=int(self.depth_var.get()),
            first_player=self.first_player_var.get(),
            human_policy=self.human_policy_var.get(),
            games_per_algorithm=10,
            seed=42,
        )
        output_lines: List[str] = []
        for summary in summaries:
            output_lines.extend(
                [
                    f"Algorithm: {summary.algorithm}",
                    f"  Games: {summary.games}",
                    f"  Computer wins: {summary.computer_wins}",
                    f"  Human wins: {summary.human_wins}",
                    f"  Draws: {summary.draws}",
                    f"  Nodes generated: {summary.generated}",
                    f"  Nodes evaluated: {summary.evaluated}",
                    f"  Pruned branches: {summary.pruned}",
                    f"  Avg. computer move time: {summary.avg_move_ms:.2f} ms",
                    "",
                ]
            )
        self.experiment_box.insert("1.0", "\n".join(output_lines).strip())
        self.run_experiments_button.configure(state="normal", text="Run 10 + 10 experiments")


if __name__ == "__main__":
    app = DivisorGameApp()
    app.mainloop()
