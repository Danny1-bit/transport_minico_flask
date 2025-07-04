import sys
import os

# Ajouter le répertoire transport_minico_flask au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'transport_minico_flask'))

from app import app

if __name__ == "__main__":
    app.run() 