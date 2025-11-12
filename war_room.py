import time
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random
import numpy as np  # <-- NEW IMPORT
from qiskit.compiler import transpile
from textual.widgets import Header, Footer, Button, Log, Static
from qiskit.circuit.library.standard_gates import ZGate # From our 'c4z' fix

#  PHASE 1: SINGLE PING ENGINE  
def run_quantum_sonar_ping(target_is_ship: bool):
    """
    Runs a single Elitzur-Vaidman test on ONE square.
    """
    probe_qubit = 0
    target_qubit = 1
    qc = QuantumCircuit(2, 1) 
    if target_is_ship:
        qc.x(target_qubit)
    qc.barrier()
    qc.h(probe_qubit)
    qc.h(target_qubit)
    qc.cx(probe_qubit, target_qubit)
    qc.h(target_qubit)
    qc.h(probe_qubit)
    qc.barrier()
    qc.measure(probe_qubit, 0)
    
    simulator = AerSimulator()
    transpiled_qc = transpile(qc, simulator)
    job = simulator.run(transpiled_qc, shots=1)
    result = job.result()
    counts = result.get_counts(transpiled_qc)
    measurement_outcome = int(list(counts.keys())[0])
    return measurement_outcome, transpiled_qc

#  NEW: QFT ENGINE 
def swap_qubits(qc, n):
    """Appends SWAP gates to reverse the qubit order."""
    for i in range(n // 2):
        qc.swap(i, n - i - 1)
    return qc

def iqft_gate(n_qubits):
    """
    Creates an Inverse Quantum Fourier Transform (IQFT) gate for n_qubits.
    """
    qc = QuantumCircuit(n_qubits, name="IQFT")

    # Swap the qubits first (inverse of the QFT's last step)
    swap_qubits(qc, n_qubits) # <--- MUST BE AT THE TOP

    for i in reversed(range(n_qubits)):
        for j in reversed(range(i + 1, n_qubits)):
            angle = -np.pi / (2**(j - i))
            qc.cp(angle, j, i) # cp(angle, control, target)
        qc.h(i)

    return qc
#  END QFT ENGINE 

# PHASE 4 (FINAL): THE "QUANTUM COUNTING SCANNER"
def run_quantum_counting_scan(targets: list[bool]):
    """
    Uses QPE to count the number of 'True' values (ships) in the 4-item target list.
    
    Args:
        targets: A list of 4 booleans [A, B, C, D] 
                 where True means a ship is present.
    
    Returns:
        The integer count (0, 1, 2, 3, or 4)
    """
    
    n_counting_qubits = 3  # We can count up to 2^3 - 1 = 7 (more than 4)
    n_target_qubits = 4    # Our row/column
    
    counting_register = list(range(n_counting_qubits))
    target_register = list(range(n_counting_qubits, n_counting_qubits + n_target_qubits))
    
    qc = QuantumCircuit(n_counting_qubits + n_target_qubits, n_counting_qubits)

    # 1. Prepare Target Qubits
    ship_indices = [target_register[i] for i, is_ship in enumerate(targets) if is_ship]
    for i in ship_indices:
        qc.x(i)

    # 2. Prepare Counting Qubits
    qc.h(counting_register)

    # 3. Apply the Controlled-Phase Rotations
    base_phase = np.pi / 4  
    
    for c_idx in counting_register:
        # The counter qubit index (c_idx) is in "Big Endian" order (2, 1, 0)
        # but the power (k) is in "Small Endian" order (0, 1, 2)
        # We must reverse the power.
        power = n_counting_qubits - 1 - c_idx
        angle = (2**power) * base_phase
        
        for t_idx in ship_indices:
            qc.cp(angle, c_idx, t_idx)

    qc.barrier()
    
    # 4. Apply Inverse QFT
    qc.append(iqft_gate(n_counting_qubits), counting_register)
    
    qc.barrier()

    # 5. Measure the Counting Qubits
    qc.measure(counting_register, counting_register)
    
    # 6. Run the circuit
    simulator = AerSimulator()
    transpiled_qc = transpile(qc, simulator)
    job = simulator.run(transpiled_qc, shots=1)
    result = job.result()
    counts = result.get_counts(transpiled_qc)
    
    binary_count = list(counts.keys())[0]
    
    integer_count = int(binary_count[::-1], 2)
    
    return integer_count, transpiled_qc

# GAME STATE
ROWS = "ABCD"
COLS = "1234"
SHIP_COUNT = 4
all_coords = [f"{r}{c}" for r in ROWS for c in COLS]
ship_locations = random.sample(all_coords, SHIP_COUNT)
GAME_BOARD = {
    coord: (coord in ship_locations) for coord in all_coords
}

# TEXTUAL TUI 
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal
from textual.widgets import Header, Footer, Button, Log

class QuantumWarRoomApp(App):
    """A Textual app for our Quantum Battleship game."""

    # This is our "Classic Legendary" CSS
    CSS = """
    Screen {
        background: #000020; 
        color: #00FF00;
        layout: vertical;
    }
    Header {
        background: #111111;
        color: #FFD700; 
        text-style: bold;
    }
    Footer {
        background: #111111;
    }
    
    #main-content {
        layout: horizontal;
        height: 50%;
    }
    
    #game-grid {
        width: 80%;
        height: 100%;
        border: solid #FFD700;
        layout: grid;
        grid-size: 4 4;
        grid-gutter: 1; 
        padding: 1;
    }

    #scanner-grid {
        width: 20%;
        height: 100%;
        border: solid #FFD700;
        layout: grid;
        grid-size: 1 10; /* <-- CHANGED from 1 8 to 1 10 */
        grid-gutter-vertical: 1;
        padding: 1;
    }
    
    /* NEW: Style for the scanner headers */
    .scanner-header {
        height: 100%;
        width: 100%;
        content-align: center middle;
        color: #FFD700; /* Brass color */
        text-style: bold;
    }
    
    /* UPDATED: "Advanced" Scanner Button Styling */
    .scanner-button {
        width: 100%;
        height: 100%;
        background: #440088; /* Bright Purple */
        color: #FFFFFF; /* White text */
        border: solid #FF00FF;
        text-style: bold;
    }
    .scanner-button:hover {
        background: #6600AA;
    }
    /* NEW: Style for a used scanner */
    .scanner-used {
        background: #220044;
        color: #888888;
        border: solid #440088;
    }

    Button {
        height: 100%;
        width: 100%;
        background: #000030; 
        border: solid #FFD700; 
        color: #00FF00; 
    }
    Button:hover {
        background: #000050; 
        border: solid #FFFF00; 
    }
    
    .sector-clear {
        background: #002000; 
        color: #444444;
        border: solid #004000;
    }
    .sector-ship {
        background: #FF0000;
        color: #FFFFFF;
        text-style: bold;
        border: solid #FFFFFF;
    }
    
    #command-log {
        height: 50%;
        border: solid #FFD700; 
    }
    Log {
        padding: 1;
    }
    """

    TITLE = " QUANTUM WAR ROOM // BATTLESHIP "

    def compose(self) -> ComposeResult:
        """Create the layout for our app."""
        yield Header()
        
        with Horizontal(id="main-content"):
            with Grid(id="game-grid"):
                for coord in all_coords:
                    yield Button(coord, id=coord)
            
            with Grid(id="scanner-grid"):
                # Add "ROWS" header
                yield Static("ROWS", classes="scanner-header")
                for r in ROWS:
                    yield Button(f"Scan Row {r}", id=f"scan-row-{r}", classes="scanner-button")
                
                # Add "COLS" header 
                yield Static("COLS", classes="scanner-header")
                for c in COLS:
                    yield Button(f"Scan Col {c}", id=f"scan-col-{c}", classes="scanner-button")

        yield Log(id="command-log")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is first loaded. Runs the boot check."""
        log = self.query_one(Log)
        log.write_line(" QUANTUM SONAR SYSTEM BOOT CHECK ")
        
        result_water, _ = run_quantum_sonar_ping(target_is_ship=False)
        log.write_line(f"   [TEST 1] SINGLE PING (WATER): {result_water} (EXPECT 0)")
        result_ship, _ = run_quantum_sonar_ping(target_is_ship=True)
        log.write_line(f"   [TEST 2] SINGLE PING (SHIP): {result_ship} (EXPECT 1)")
        
        # Test the new counter ---
        test_targets = [False, True, False, True] # 2 ships
        count, _ = run_quantum_counting_scan(test_targets)
        log.write_line(f"   [TEST 3] COUNTING SCAN (2 SHIPS): {count} (EXPECT 2)")
        
        test_targets_3 = [True, True, True, False] # 3 ships
        count_3, _ = run_quantum_counting_scan(test_targets_3)
        log.write_line(f"   [TEST 4] COUNTING SCAN (3 SHIPS): {count_3} (EXPECT 3)")

        log.write_line("\n ENGINE STATUS: NOMINAL (ALL SYSTEMS) ")
        log.write_line(f" {SHIP_COUNT} ENEMY SIGNATURES PLACED ON GRID ")
        log.write_line(" AWAITING COMMANDS")

    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when ANY button is pressed."""
        button_id = event.button.id
        
        if button_id.startswith("scan-row-") or button_id.startswith("scan-col-"):
            self.handle_scanner_press(event)
        elif len(button_id) == 2: # e.g., "A1"
            self.handle_single_ping(event)

    def handle_single_ping(self, event: Button.Pressed):
        """Handles a click on a single grid square."""
        log = self.query_one(Log)
        button_id = event.button.id
        
        is_ship = GAME_BOARD.get(button_id, False)
        log.write_line(f"\n>>> [SINGLE PING] COMMAND: PINGING SECTOR {button_id}...")
        
        measurement, _ = run_quantum_sonar_ping(target_is_ship=is_ship)
        
        if measurement == 1:
            log.write_line(f"    >>> ANALYSIS: **SHIP DETECTED AT {button_id}!** <<<")
            event.button.set_classes("sector-ship")
            event.button.label = "SHIP"
        else:
            log.write_line(f"    ...ANALYSIS: Sector {button_id} is clear.")
            event.button.set_classes("sector-clear")
        
        event.button.disabled = True

    # To handle the new counter
    def handle_scanner_press(self, event: Button.Pressed):
        """Handles a click on a row/column scanner button."""
        log = self.query_one(Log)
        button_id = event.button.id
        
        log.write_line(f"\n>>> [ADVANCED COUNTING SCAN] COMMAND: {event.button.label}...")
        
        # 1. Assemble the list of 4 targets
        targets_to_scan = []
        if button_id.startswith("scan-row-"):
            row = button_id[-1] 
            targets_to_scan = [GAME_BOARD[f"{row}{c}"] for c in COLS]
        elif button_id.startswith("scan-col-"):
            col = button_id[-1] 
            targets_to_scan = [GAME_BOARD[f"{r}{col}"] for r in ROWS]
        
        log.write_line(f"    ...Target list: {targets_to_scan}")

        # 2. Run the actual quantum counting function
        count, _ = run_quantum_counting_scan(targets=targets_to_scan)
        
        # 3. Report the result
        if count > 0:
            log.write_line(f"    >>> ANALYSIS: **{count} SHIP(S) DETECTED IN {event.button.label}!**")
        else:
            log.write_line(f"    ...ANALYSIS: {event.button.label} is ALL CLEAR.")
        
        # Update style and disable
        event.button.set_classes("scanner-used")
        event.button.label = f"SHIPS: {count}" # Update label to show count
        event.button.disabled = True


if __name__ == "__main__":
    app = QuantumWarRoomApp()
    app.run()