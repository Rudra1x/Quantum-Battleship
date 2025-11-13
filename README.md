# 🚀 Quantum War Room: Project Elitzur

**A full-stack, "legendary" quantum application that uses interaction-free measurement and parallel quantum counting to find enemy ships.**

This project was built for the **Quantum Hackathon 2025**. It is a complete, deployable web application that solves the "Quantum Battleship" challenge by not only implementing the core Elitzur-Vaidman concept but by extending it into a true, multi-qubit quantum counting algorithm.

---

## 📸 Demo: The War Room Dashboard

This is our glassmorphism UI, built as a full-stack Flask application. It's fully responsive, mobile-compatible, and runs our real quantum code on the backend.

****
*<img width="1918" height="1081" alt="image" src="https://github.com/user-attachments/assets/e04fee41-ed8a-4815-9e7d-5db30b834e55" />
*
<img width="1918" height="1088" alt="image" src="https://github.com/user-attachments/assets/8d78f32b-b305-4604-afe2-4475228fa156" />
<img width="1918" height="1088" alt="image" src="https://github.com/user-attachments/assets/0d520e30-0668-456f-93a1-179b493fb02b" />



---

## ✨ Core Features

Our project is a game of two halves: a "Basic" mode that fulfills the requirements, and an "Advanced" mode that demonstrates our innovation.

* ### 1. "Basic Ping" (Single-Target Scan)
    A 4x4 grid of sectors. The user can "ping" any single sector. Using a **2-qubit Elitzur-Vaidman** circuit, this ping detects a ship's presence *without* "hitting" it (i.e., without measuring the target qubit).

* ### 2. "Advanced Counter" (Multi-Target Scan)
    The user can scan an entire row or column *at once*. This runs a **7-qubit Quantum Phase Estimation (QPE)** circuit that returns the **exact number of ships** in that line (0, 1, 2, 3, or 4) in a single quantum operation.

* ### 3.  UI
    A full-stack Flask application serves a "glass panel" UI built with Tailwind CSS. It's designed to be clean, professional, and impressive.

* ### 4. Animated "How-it-Works" Explainer
    An animated modal (the `(i)` button) that visually explains our 7-qubit QPE algorithm to the user, showing how the counting and target qubits interact.

---

## ⚛️ Core Quantum Concepts

This project isn't just a UI wrapper; it's a deep dive into core quantum algorithms.

### 1. Elitzur-Vaidman (Interaction-Free Measurement)
* **Definition:** The "quantum bomb tester" problem. It's a method to detect an object's presence in a path without ever directly interacting with it. It uses a quantum interferometer to see if a superposition was "observed" by the object (the bomb/ship).
* **Our Use:** This is the entire engine for our **"Basic Ping"** mode. The "ship" is the "bomb." By putting our probe qubit in superposition, we can detect the ship *without* collapsing the ship's own state, proving the principle of interaction-free measurement.

### 2. Quantum Phase Estimation (QPE)
* **Definition:** A cornerstone quantum algorithm used to determine the phase (or eigenvalue) of a quantum state. It's the "engine" inside algorithms like Shor's.
* **Our Use:** This is the **winning innovation** for our **"Advanced Counter."** We built a 7-qubit (3-counter, 4-target) QPE-based circuit. The number of ships in a row determines the *total phase* that gets "imprinted" onto the counting qubits.

### 3. Inverse Quantum Fourier Transform (IQFT)
* **Definition:** The quantum-mechanical version of the Inverse-Discrete Fourier Transform. Its most famous use is to translate a state's *phase* (which is unmeasurable) into a state's *amplitude* (which is measurable).
* **Our Use:** This is the **final step** of our "Advanced Counter." After the QPE "imprints" the count as a phase, our `iqft_gate(3)` function runs on the 3 counting qubits. This translates the complex phase (e.g., `3/8` of a circle) into the measurable binary string `|011>`, which we read as the integer **3**.

### 4. Controlled-Phase (CP) Gates
* **Definition:** A 2-qubit gate that applies a phase rotation to the *target* qubit, but only if the *control* qubit is in the `|1⟩` state.
* **Our Use:** These are the "links" in our QPE circuit. They are how the "ship" qubits (the targets) "add" their unit of phase to the counting qubits. Each counting qubit controls a different-sized rotation (`pi/4`, `pi/2`, `pi`), allowing us to perform the binary counting in superposition.

---

## 🛠️ Technical Architecture

We built a full-stack, three-tier application. The frontend is completely decoupled from the quantum engine, communicating via a standard JSON API.

- Rudraksh Sharma
- [[rudra1x.github.io](https://rudra1x.github.io/)](URL)
war_room.py - Main file contains all quantum code.
app.py - Flask app of main file
index.html - Frontend of our implementation
```mermaid
graph TD;
    subgraph "Browser"
        Frontend[index.html: HTML/CSS/JS]
    end

    subgraph "Server (PythonAnywhere)"
        Backend[Flask API: app.py]
    end

    subgraph "Quantum Engine"
        QEngine[Qiskit Aer Simulator]
    end

    Frontend -- "(HTTP Request)" --> Backend;
    Backend -- "(Run Circuit)" --> QEngine;
    QEngine -- "(Results)" --> Backend;
    Backend -- "(JSON)" --> Frontend;

