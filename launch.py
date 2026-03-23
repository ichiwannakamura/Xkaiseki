"""起動スクリプト — 日本語ファイル名を Python 経由で渡す"""
import subprocess
import sys
from pathlib import Path

app = Path(__file__).parent / "\U0001f3e0_\u30db\u30fc\u30e0.py"

subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)])
