@echo off
cd /d "C:\Users\21288\Desktop\DACHUANG\dachuang"
"C:\Users\21288\AppData\Local\Programs\Python\Python312\python.exe" regression_v3/build_panel_v3.py > regression_v3/build_panel_output.log 2>&1
echo Build done: %errorlevel%
"C:\Users\21288\AppData\Local\Programs\Python\Python312\python.exe" regression_v3/make_figures.py >> regression_v3/build_panel_output.log 2>&1
echo Figures done: %errorlevel%
