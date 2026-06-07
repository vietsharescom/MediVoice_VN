@echo off
:: overnight_run.bat — MediVoice VN overnight pipeline
:: Run before sleep. Estimated: 5-8h total (i5-12400F, 32GB RAM, no GPU)
:: Step 1 (~1-2h):  Download VietMed dataset (~2.5GB audio)
:: Step 2 (~3-5h):  Train PhoBERT NER (3 epochs, 7994 samples, CPU)
::
:: Usage: double-click or run in terminal:
::   cd D:\MediVoice_VN
::   scripts\overnight_run.bat > logs\overnight_run.log 2>&1
::
:: Logs:
::   logs\overnight_run.log       <- combined stdout
::   logs\download_vietmed.log    <- VietMed download detail
::   logs\train_ner_phobert.log   <- NER training detail
::   models\ner_phobert\best\     <- trained model output

setlocal
set ROOT=D:\MediVoice_VN
set PYTHON=python

echo ================================================================
echo  MediVoice VN — Overnight Pipeline
echo  Started: %date% %time%
echo ================================================================

:: Create logs dir
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

:: ----------------------------------------------------------------
:: STEP 1 — Download VietMed dataset
:: ----------------------------------------------------------------
echo.
echo [STEP 1] Downloading VietMed (doof-ferb/VietMed) ...
echo          Output: %ROOT%\data\vietmed\
echo          Est. time: 1-2h depending on internet speed
echo.
%PYTHON% -u "%ROOT%\scripts\download_vietmed.py" --split all
if errorlevel 1 (
    echo [STEP 1] FAILED — check logs\download_vietmed.log
    echo          Continuing to NER training anyway...
) else (
    echo [STEP 1] VietMed download complete.
)

:: ----------------------------------------------------------------
:: STEP 2 — Train PhoBERT NER
:: ----------------------------------------------------------------
echo.
echo [STEP 2] Training PhoBERT NER (3 epochs, 7994 samples, CPU)...
echo          Output: %ROOT%\models\ner_phobert\best\
echo          Est. time: 3-5h on CPU
echo.
%PYTHON% -u "%ROOT%\scripts\train_ner_phobert.py" --epochs 3 --batch 8
if errorlevel 1 (
    echo [STEP 2] FAILED — check logs\train_ner_phobert.log
) else (
    echo [STEP 2] NER training complete.
)

:: ----------------------------------------------------------------
:: DONE
:: ----------------------------------------------------------------
echo.
echo ================================================================
echo  Overnight pipeline finished: %date% %time%
echo  Results:
echo    VietMed audio  → %ROOT%\data\vietmed\
echo    NER model      → %ROOT%\models\ner_phobert\best\
echo    Training log   → %ROOT%\logs\train_ner_phobert.log
echo ================================================================
endlocal
