#!/bin/bash
# VideoAI startup script

cd "$(dirname "$0")"

# Check if virtualenv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the application
python src/main.py "$@"
