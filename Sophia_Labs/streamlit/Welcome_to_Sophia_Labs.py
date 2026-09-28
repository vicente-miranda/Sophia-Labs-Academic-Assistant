# Proprietary License
# Effective Date: 3rd of January of 2025
#
# Copyright (c) 2025 Sophia Labs
#
# This software is the proprietary property of Sophia Labs and is provided exclusively for 
# evaluation purposes by Tiago Santos or NOVA IMS staff. Any other use, reproduction, 
# distribution, or modification without explicit written permission from the authors 
# is strictly prohibited.
#
# Consult the license for detailed terms and conditions before using this software.

import streamlit as st
from Sophia_Labs.streamlit.menu import menu
import sys
import os
from pathlib import Path

# Add the Sophia root directory to sys.path
project_root = Path(__file__).resolve().parents[2]  # Go up two levels to the root
sys.path.append(str(project_root))

menu(change=True)

