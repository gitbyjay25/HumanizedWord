#!/usr/bin/env bash
# Creates backend/.venv with the verified dependency stack on Linux / macOS / WSL.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo ">>> Creating virtual environment (.venv)..."
    python3 -m venv "$VENV_DIR"
fi

export PIP_DISABLE_PIP_VERSION_CHECK=1

echo ">>> Installing PyTorch (CPU wheel)..."
"$PYTHON_BIN" -m pip install --quiet --index-url https://download.pytorch.org/whl/cpu "torch==2.4.1"

echo ">>> Installing core ML / NLP stack..."
"$PYTHON_BIN" -m pip install --quiet \
    "transformers==4.45.2" \
    "peft==0.15.2" \
    "sentence-transformers==3.3.1" \
    "numpy==2.1.3" \
    "spacy==3.8.5"

echo ">>> Installing backend stack..."
"$PYTHON_BIN" -m pip install --quiet \
    "fastapi==0.115.6" \
    "uvicorn[standard]==0.32.1" \
    "pydantic==2.9.2" \
    "pydantic-settings==2.6.1" \
    "sqlalchemy[asyncio]==2.0.36" \
    "asyncpg==0.30.0" \
    "alembic==1.14.0" \
    "python-jose[cryptography]==3.3.0" \
    "passlib[bcrypt]==1.7.4" \
    "bcrypt==4.0.1" \
    "slowapi==0.1.9" \
    "python-multipart==0.0.17" \
    "aiofiles==24.1.0" \
    "httpx==0.28.1" \
    "python-dotenv==1.0.1"

echo ">>> Installing dev / test stack..."
"$PYTHON_BIN" -m pip install --quiet "pytest==8.3.3" "pytest-asyncio==0.24.0" "pytest-cov==6.0.0"

echo ">>> Downloading spaCy model..."
"$PYTHON_BIN" -m pip install --quiet "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

echo ">>> Verifying installation..."
"$PYTHON_BIN" -c "
import torch, numpy, transformers, peft, sentence_transformers, spacy, fastapi
print('torch          ', torch.__version__)
print('numpy          ', numpy.__version__)
print('transformers   ', transformers.__version__)
print('peft           ', peft.__version__)
print('spacy          ', spacy.__version__)
print('fastapi        ', fastapi.__version__)
t = torch.randn(3)
print('numpy bridge   ', 'OK' if t.numpy().shape == (3,) else 'FAIL')
"

echo ">>> Environment setup complete!"
