@echo off
cd /d %~dp0
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
python -m app.ml.train_model
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
