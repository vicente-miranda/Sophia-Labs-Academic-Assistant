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

"""
Module: Intention Classifier Loader

This module provides functionality to load a RouteLayer object from a JSON file. 
The RouteLayer is used for classifying user intentions based on predefined routing rules.

Functions:
    - load_intention_classifier: Loads and initializes a RouteLayer object from a JSON file.

Usage:
    Use `load_intention_classifier` to load the router layer for classifying user intents.
"""

import os
from semantic_router import RouteLayer

FILENAME = "layer.json"
BASE_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(BASE_DIR, FILENAME)


def load_intention_classifier() -> RouteLayer:
    """
    Load a JSON file and initialize a RouteLayer object.

    Returns:
        RouteLayer: Object used to classify user intentions.

    Raises:
        FileNotFoundError: If the specified JSON file does not exist.
        ValueError: If the file content is not compatible with RouteLayer.
    """
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"File not found: {FILE_PATH}")

    rl = RouteLayer.from_json(FILE_PATH)

    return rl