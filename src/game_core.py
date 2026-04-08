from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MoveRecord:
    actor: str
    divisor: int
    from_number: int
    to_number: int
    human_delta: int = 0
    computer_delta: int = 0
    bank_increased: bool = False
    bank_awarded: int = 0
    terminal_reason: Optional[str] = None


@dataclass
class GameState:
    number: int
    human_score: int = 0
    computer_score: int = 0
    bank: int = 0
    is_human_turn: bool = True
    path: List[MoveRecord] = field(default_factory=list)
    last_move: Optional[MoveRecord] = None

    def clone(self) -> "GameState":
        return GameState(
            number=self.number,
            human_score=self.human_score,
            computer_score=self.computer_score,
            bank=self.bank,
            is_human_turn=self.is_human_turn,
            path=list(self.path),
            last_move=self.last_move,
        )

    def legal_moves(self) -> List[int]:
        moves: List[int] = []
        if self.number % 2 == 0:
            moves.append(2)
        if self.number % 3 == 0:
            moves.append(3)
        return moves

    def is_terminal(self) -> bool:
        return self.last_move is not None and self.last_move.terminal_reason is not None

    def winner_label(self) -> str:
        if not self.is_terminal():
            return "In progress"
        if self.human_score == self.computer_score:
            return "Draw"
        return "Human wins" if self.human_score > self.computer_score else "Computer wins"

    def apply_move(self, divisor: int) -> "GameState":
        next_state = self.clone()
        actor = "human" if self.is_human_turn else "computer"
        previous_number = self.number
        next_state.number = self.number // divisor

        human_delta = 0
        computer_delta = 0

        if divisor == 2:
            if actor == "human":
                next_state.computer_score += 2
                computer_delta = 2
            else:
                next_state.human_score += 2
                human_delta = 2
        else:
            if actor == "human":
                next_state.human_score += 3
                human_delta = 3
            else:
                next_state.computer_score += 3
                computer_delta = 3

        bank_increased = False
        if str(next_state.number).endswith(("0", "5")):
            next_state.bank += 1
            bank_increased = True

        terminal_reason: Optional[str] = None
        if next_state.number <= 10:
            terminal_reason = "threshold"
        elif not next_state.legal_moves():
            # Practical fix for undefined states above 10 with no legal moves.
            terminal_reason = "no_moves"

        bank_awarded = 0
        if terminal_reason is not None:
            bank_awarded = next_state.bank
            if actor == "human":
                next_state.human_score += bank_awarded
            else:
                next_state.computer_score += bank_awarded
            next_state.bank = 0

        move = MoveRecord(
            actor=actor,
            divisor=divisor,
            from_number=previous_number,
            to_number=next_state.number,
            human_delta=human_delta,
            computer_delta=computer_delta,
            bank_increased=bank_increased,
            bank_awarded=bank_awarded,
            terminal_reason=terminal_reason,
        )

        next_state.last_move = move
        next_state.path = [*self.path, move]
        if terminal_reason is None:
            next_state.is_human_turn = not self.is_human_turn
        else:
            next_state.is_human_turn = self.is_human_turn
        return next_state


@dataclass
class GameTreeNode:
    state: GameState
    depth: int = 0
    move: Optional[int] = None
    children: List["GameTreeNode"] = field(default_factory=list)
    value: Optional[float] = None


@dataclass
class SearchStats:
    generated: int = 0
    evaluated: int = 0
    pruned: int = 0
    time_ms: float = 0.0

    def add(self, other: "SearchStats") -> None:
        self.generated += other.generated
        self.evaluated += other.evaluated
        self.pruned += other.pruned
        self.time_ms += other.time_ms


@dataclass
class ExperimentSummary:
    algorithm: str
    games: int
    computer_wins: int
    human_wins: int
    draws: int
    generated: int
    evaluated: int
    pruned: int
    avg_move_ms: float


def terminal_score(state: GameState) -> float:
    diff = state.computer_score - state.human_score
    if diff > 0:
        return 100_000 + diff * 100
    if diff < 0:
        return -100_000 + diff * 100
    return 0.0



def evaluate_state(state: GameState) -> float:
    if state.is_terminal():
        return terminal_score(state)

    score_diff = state.computer_score - state.human_score
    is_computer_turn = not state.is_human_turn
    legal_count = len(state.legal_moves())

    bank_pressure = state.bank * (4 if is_computer_turn else -4)
    mobility_pressure = legal_count * (2 if is_computer_turn else -2)
    div3_pressure = 6 if (state.number % 3 == 0 and is_computer_turn) else 0
    div3_pressure -= 6 if (state.number % 3 == 0 and not is_computer_turn) else 0
    div2_pressure = -2 if (state.number % 2 == 0 and is_computer_turn) else 0
    div2_pressure += 2 if (state.number % 2 == 0 and not is_computer_turn) else 0
    smaller_number_bonus = 5 if (state.number <= 60 and is_computer_turn) else 0
    smaller_number_bonus -= 5 if (state.number <= 60 and not is_computer_turn) else 0

    return (
        score_diff * 12
        + bank_pressure
        + mobility_pressure
        + div3_pressure
        + div2_pressure
        + smaller_number_bonus
    )



def expand_node(node: GameTreeNode, stats: SearchStats) -> List[GameTreeNode]:
    if node.children:
        return node.children
    for move in node.state.legal_moves():
        stats.generated += 1
        node.children.append(GameTreeNode(state=node.state.apply_move(move), depth=node.depth + 1, move=move))
    return node.children



def minimax_search(
    node: GameTreeNode,
    depth: int,
    alpha: float,
    beta: float,
    use_alpha_beta: bool,
    stats: SearchStats,
) -> float:
    if depth == 0 or node.state.is_terminal():
        stats.evaluated += 1
        node.value = evaluate_state(node.state)
        return node.value

    children = expand_node(node, stats)
    if not children:
        stats.evaluated += 1
        node.value = evaluate_state(node.state)
        return node.value

    maximizing = not node.state.is_human_turn
    if use_alpha_beta:
        children = sorted(children, key=lambda child: evaluate_state(child.state), reverse=maximizing)

    if maximizing:
        best = -math.inf
        for index, child in enumerate(children):
            value = minimax_search(child, depth - 1, alpha, beta, use_alpha_beta, stats)
            best = max(best, value)
            if use_alpha_beta:
                alpha = max(alpha, best)
                if beta <= alpha:
                    stats.pruned += len(children) - index - 1
                    break
        node.value = best
        return best

    best = math.inf
    for index, child in enumerate(children):
        value = minimax_search(child, depth - 1, alpha, beta, use_alpha_beta, stats)
        best = min(best, value)
        if use_alpha_beta:
            beta = min(beta, best)
            if beta <= alpha:
                stats.pruned += len(children) - index - 1
                break
    node.value = best
    return best



def choose_computer_move(state: GameState, depth: int, algorithm: str):
    stats = SearchStats()
    root = GameTreeNode(state=state)
    use_alpha_beta = algorithm.lower() == "alpha-beta" or algorithm.lower() == "alphabeta"
    started_at = time.perf_counter()

    children = expand_node(root, stats)
    if not children:
        stats.time_ms = (time.perf_counter() - started_at) * 1000
        return None, state, evaluate_state(state), stats

    best_child: Optional[GameTreeNode] = None
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf

    for child in children:
        value = minimax_search(child, depth - 1, alpha, beta, use_alpha_beta, stats)
        if value > best_value:
            best_value = value
            best_child = child
        if use_alpha_beta:
            alpha = max(alpha, best_value)

    stats.time_ms = (time.perf_counter() - started_at) * 1000
    if best_child is None:
        return None, state, best_value, stats
    return best_child.move, best_child.state, best_value, stats



def can_reach_terminal(number: int, memo: Optional[Dict[int, bool]] = None) -> bool:
    if memo is None:
        memo = {}
    if number <= 10:
        return True
    if number in memo:
        return memo[number]

    reachable = False
    if number % 2 == 0:
        reachable = reachable or can_reach_terminal(number // 2, memo)
    if number % 3 == 0:
        reachable = reachable or can_reach_terminal(number // 3, memo)

    memo[number] = reachable
    return reachable



def make_candidate_pool() -> List[int]:
    memo: Dict[int, bool] = {}
    pool: List[int] = []
    for value in range(10_000, 20_001):
        if value % 6 == 0 and can_reach_terminal(value, memo):
            pool.append(value)
    return pool



def sample_start_numbers(pool: List[int], count: int = 5, rng: Optional[random.Random] = None) -> List[int]:
    chooser = rng or random
    if len(pool) <= count:
        return sorted(pool)
    return sorted(chooser.sample(pool, count))



def format_move(move: MoveRecord, index: int) -> str:
    actor = "Human" if move.actor == "human" else "Computer"
    extras: List[str] = []
    if move.human_delta:
        extras.append(f"human +{move.human_delta}")
    if move.computer_delta:
        extras.append(f"computer +{move.computer_delta}")
    if move.bank_increased:
        extras.append("bank +1")
    if move.bank_awarded:
        extras.append(f"{actor.lower()} collects bank +{move.bank_awarded}")
    if move.terminal_reason == "threshold":
        extras.append("game ends at <= 10")
    if move.terminal_reason == "no_moves":
        extras.append("game ends: no legal moves")
    suffix = f" ({', '.join(extras)})" if extras else ""
    return f"{index + 1}. {actor} / {move.divisor}: {move.from_number} -> {move.to_number}{suffix}"



def pick_human_simulation_move(state: GameState, policy: str, rng: Optional[random.Random] = None) -> Optional[int]:
    moves = state.legal_moves()
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    chooser = rng or random
    if policy.lower() == "random":
        return chooser.choice(moves)

    best_move = moves[0]
    best_value = math.inf
    for move in moves:
        value = evaluate_state(state.apply_move(move))
        if value < best_value:
            best_value = value
            best_move = move
    return best_move



def run_experiments(
    depth: int,
    first_player: str = "Human",
    human_policy: str = "Greedy",
    games_per_algorithm: int = 10,
    seed: int = 42,
) -> List[ExperimentSummary]:
    rng = random.Random(seed)
    pool = make_candidate_pool()
    results: List[ExperimentSummary] = []

    for algorithm in ["Minimax", "Alpha-Beta"]:
        computer_wins = 0
        human_wins = 0
        draws = 0
        aggregate = SearchStats()
        computer_move_count = 0

        for _ in range(games_per_algorithm):
            start_number = rng.choice(pool)
            state = GameState(number=start_number, is_human_turn=(first_player == "Human"))

            while not state.is_terminal():
                if state.is_human_turn:
                    move = pick_human_simulation_move(state, human_policy, rng)
                    if move is None:
                        break
                    state = state.apply_move(move)
                else:
                    _, state, _, stats = choose_computer_move(state, depth, algorithm)
                    aggregate.add(stats)
                    computer_move_count += 1

            winner = state.winner_label()
            if winner == "Computer wins":
                computer_wins += 1
            elif winner == "Human wins":
                human_wins += 1
            else:
                draws += 1

        avg_move_ms = aggregate.time_ms / computer_move_count if computer_move_count else 0.0
        results.append(
            ExperimentSummary(
                algorithm=algorithm,
                games=games_per_algorithm,
                computer_wins=computer_wins,
                human_wins=human_wins,
                draws=draws,
                generated=aggregate.generated,
                evaluated=aggregate.evaluated,
                pruned=aggregate.pruned,
                avg_move_ms=avg_move_ms,
            )
        )

    return results
