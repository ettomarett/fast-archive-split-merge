#!/usr/bin/env bash
# Fast Archive & Split — launch on Linux/Ubuntu
set -e
cd "$(dirname "$0")"
if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "Error: Tkinter is not installed. Install it with:"
  echo "  sudo apt install python3-tk"
  exit 1
fi
python3 -c "
import sys
sys.path.insert(0, '.')
from src.main import main
main()
"
