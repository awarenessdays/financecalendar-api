"""Execute real MQL parser/state code through the local C++ stand-in."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

class MetaTraderLogic(unittest.TestCase):
    @unittest.skipUnless(shutil.which("c++") or shutil.which("g++") or shutil.which("clang++"), "C++ compiler unavailable")
    def test_parser_decisions_transport_and_chart_timer(self):
        subprocess.run([sys.executable, str(Path(__file__).parent / "metatrader" / "run_mql_tests.py")], check=True)

if __name__ == "__main__": unittest.main()
