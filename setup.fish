#!/usr/bin/env fish

echo "--- Setting up Delivery Robot Environment ---"

if not test -d venv
    echo "[SETUP] Creating Python Virtual Environment (venv)..."
    python3 -m venv venv
else
    echo "[SETUP] venv already exists."
end

echo "[SETUP] Activating venv..."
source venv/bin/activate.fish

echo "[SETUP] Installing dependencies..."
pip install -r requirements.txt

echo "--- Setup Complete ---"
echo "To run the robot: python brain/main.py"
echo "To run tests:     python -m unittest discover tests"
