import os, sys
from pathlib import Path

src_path = os.path.join(Path(__file__).resolve().parent.parent, 'src')
sys.path.append(src_path)