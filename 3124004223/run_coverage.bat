@echo off
REM 一键运行测试并生成分支覆盖率报告
python -m coverage run --branch -m unittest discover -s tests -v
python -m coverage report -m
python -m coverage html
echo.
echo 覆盖率 HTML 报告已生成在 htmlcov\index.html
pause
