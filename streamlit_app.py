"""
Streamlit Cloud entry point — deploy this file as the main app.
"""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "frontend" / "app.py"), run_name="__main__")
