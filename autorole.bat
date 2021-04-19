@echo off
rem Folder path of your both
cd /d "E:\O2Jam"
start "" "%localappdata%/Programs/Python/Python39/python.exe" "giverole.py" %1
echo %1 >> autorolelog.txt
exit