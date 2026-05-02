"""Configuration pytest commune — charge les variables d'env depuis .env."""

import sys
import os
from dotenv import load_dotenv

# Charger .env depuis la racine du projet
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
