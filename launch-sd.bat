@echo off
deactivate

set PYTHON=
set GIT=
set VENV_DIR=
set SD_PATH=
set COMMANDLINE_ARGS=--xformers --medvram --api --nowebui

cd $SD_PATH
call webui.bat
