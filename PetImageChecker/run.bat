@echo off
echo Running Python backend for Pet Verification...
echo Setting up virtual environment if it doesn't exist...
IF NOT EXIST venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

IF "%POSTGRES_DSN%"=="" (
    IF "%POSTGRES_PASSWORD%"=="" (
        echo WARNING: POSTGRES_PASSWORD is not set. PostgreSQL-backed tips/history will be skipped.
    ) ELSE (
        set POSTGRES_DSN=dbname=pethub user=postgres password=%POSTGRES_PASSWORD% host=localhost port=5432
        echo POSTGRES_DSN has been auto-configured from POSTGRES_PASSWORD.
    )
)

echo Installing requirements...
pip install -r requirements.txt
echo Starting FastAPI application...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
