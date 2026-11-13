#!/usr/bin/env python3
"""Run the MetaTrader news-filter source as C++ against a stand-in runtime.

Offline logic check only: it does not prove the source compiles in MetaEditor.
Skips (exit 0) when no C++ compiler is installed.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
META = HERE.parents[1] / 'metatrader'


def to_cpp(source: str) -> str:
    out = []
    for line in source.splitlines():
        if line.startswith('#property') or line.startswith('#include'):
            continue
        # MQL dynamic array declarations: `type name[];`
        line = re.sub(r'^(\s*)(\w+)\s+(\w+)\[\];', r'\1Array<\2> \3;', line)
        out.append(line)
    return '\n'.join(out) + '\n'


def main() -> int:
    compiler = shutil.which('c++') or shutil.which('g++') or shutil.which('clang++')
    if not compiler:
        print('skipped: no C++ compiler')
        return 0
    four = (META / 'FinanceCalendarNewsFilter.mq4').read_text()
    five = (META / 'FinanceCalendarNewsFilter.mq5').read_text()
    assert four == five, 'MT4 and MT5 example sources differ'
    fixtures = ''.join(f'static const char *FX_{path.stem.upper().replace("-", "_")} = R"FXJSON({path.read_text()})FXJSON";\n'
                       for path in sorted((HERE / 'fixtures').glob('*.json')))
    program = ('#include "mql_shim.h"\n' + to_cpp((META / 'FinanceCalendarNews.mqh').read_text())
               + to_cpp(five) + fixtures + (HERE / 'cases.inc').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'news.cpp'
        src.write_text(program)
        exe = Path(tmp) / 'news'
        subprocess.run([compiler, '-std=c++17', '-Wall', '-Wno-unused-function', '-Wno-unused-variable', '-Wno-sign-compare',
                        '-I', str(HERE), str(src), '-o', str(exe)], check=True)
        return subprocess.run([str(exe)]).returncode


if __name__ == '__main__':
    sys.exit(main())
