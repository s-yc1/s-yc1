@echo off
REM 一键运行全部单元测试
python -m unittest discover -s tests -v
pause
