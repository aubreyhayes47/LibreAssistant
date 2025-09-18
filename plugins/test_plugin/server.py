import sys
import os
# Ensure project root is in sys.path for plugin_config import (if needed in future)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import time
if __name__ == "__main__":
    while True:
        time.sleep(1)
