# Divisor Game

A Python GUI application implementing the Divisor Game with AI opponents using Minimax and Alpha-Beta pruning algorithms.

## About the Game

The Divisor Game is a two-player mathematical game where players alternate dividing a number by 2 or 3. The game features:

- **Interactive GUI** built with CustomTkinter
- **Multiple AI algorithms**: Minimax and Alpha-Beta pruning
- **Configurable search depth** for AI difficulty levels
- **Move history** panel to track all game moves
- **Separate windows** for game tree visualization and experiment running
- **Experiment runner** for automated game testing and statistics

## Features

- Starting player selection (Human or Computer)
- Configurable algorithm (Minimax or Alpha-Beta pruning)
- Adjustable search depth for AI difficulty
- Real-time game state display with scores and current number
- Visual game tree representation
- Move history tracking
- Batch experiment runner for testing strategies

## Requirements

- Python 3.8+
- CustomTkinter 5.2.2
- darkdetect 0.8.0
- packaging >= 23.0

## Installation

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python src\app.py
```

Or if `python` is not available:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
py src\app.py
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/app.py
```

## Quick Start

1. Clone the repository
2. Create and activate a virtual environment (see Installation section above)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python src/app.py`

## Project Structure

```
.
├── src/
│   ├── app.py           # Main GUI application
│   └── game_core.py     # Game logic, AI algorithms, experiments
├── requirements.txt     # Python dependencies
├── run_windows.bat      # Quick Windows launcher script
├── LICENSE              # MIT License
└── README.md            # This file
```

## Key Modules

### src/app.py
- Main CustomTkinter GUI application
- Game board interface with move buttons
- Real-time game state updates
- Move history panel
- Game tree viewer window
- Experiment runner window

### src/game_core.py
- Game state and rules implementation
- Minimax algorithm implementation
- Alpha-Beta pruning optimization
- Search statistics tracking
- Experiment runner for batch testing
- AI move selection logic

## Usage

### Playing a Game

1. Select starting player (Human or Computer)
2. Choose AI algorithm and search depth
3. Select a starting number from the candidates
4. Use the numbered buttons to make moves (divide by 2 or 3)
5. Computer automatically makes its move when selected as the current player

### Running Experiments

Use the "Experiment Runner" window to:
- Test different algorithms against each other
- Evaluate performance at various search depths
- Generate statistics and performance data
- Save experiment results

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created as a practical assignment for studying game AI algorithms (Minimax, Alpha-Beta pruning).