import time
import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile
from qiskit.circuit.library.standard_gates import ZGate
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# --- INITIALIZE FLASK APP ---
app = Flask(__name__)
# This allows our web frontend to make requests
CORS(app)
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

# --- 4. GAME STATE (Global variable) ---
ROWS = "ABCD"
COLS = "1234"
SHIP_COUNT = 4
all_coords = [f"{r}{c}" for r in ROWS for c in COLS]
ship_locations = random.sample(all_coords, SHIP_COUNT)
GAME_BOARD = {
    coord: (coord in ship_locations) for coord in all_coords
}
print("--- GAME BOARD INITIALIZED ---")
print(GAME_BOARD)


# --- 5. FLASK API ENDPOINTS ---

@app.route('/')
def index():
    """Serves the main HTML page (which we will build next)."""
    # We will create this 'index.html' file in the next step
    return "Quantum Battleship Server is Running. Ready for frontend."

@app.route('/ping', methods=['POST'])
def handle_ping():
    """Handles a single-ping request from the frontend."""
    data = request.json
    button_id = data.get('id') # e.g., "A1"
    
    if not button_id:
        return jsonify({"error": "No ID provided"}), 400
        
    is_ship = GAME_BOARD.get(button_id, False)
    measurement, _ = run_quantum_sonar_ping(target_is_ship=is_ship)
    
    # Return the result as JSON
    return jsonify({
        "id": button_id,
        "result": measurement # 0 (clear) or 1 (ship)
    })

@app.route('/scan', methods=['POST'])
def handle_scan():
    """Handles an advanced-scan request from the frontend."""
    data = request.json
    scan_id = data.get('id') # e.g., "scan-row-A"
    
    targets_to_scan = []
    if scan_id.startswith("scan-row-"):
        row = scan_id[-1] 
        targets_to_scan = [GAME_BOARD[f"{row}{c}"] for c in COLS]
    elif scan_id.startswith("scan-col-"):
        col = scan_id[-1] 
        targets_to_scan = [GAME_BOARD[f"{r}{col}"] for r in ROWS]
    else:
        return jsonify({"error": "Invalid scan ID"}), 400

    count, _ = run_quantum_counting_scan(targets=targets_to_scan)
    
    # Return the result as JSON
    return jsonify({
        "id": scan_id,
        "count": count # 0, 1, 2, 3, or 4
    })

# --- RUN THE SERVER ---
if __name__ == '__main__':
    # This will run the server on http://127.0.0.1:5000
    app.run(debug=True, port=5000)