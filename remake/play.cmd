@echo off
rem Start CS2 on the Povo map with the F6 marker. Usage: play [lit|unlit]  (default: lit)
rem Marks from the previous session are collected first, into
rem data\labeled_pictures\PROBLEMS_TO_SOLVE\marks.
set MAP=povo_site_lit
if /I "%1"=="unlit" set MAP=povo_site
python "%~dp0tools\cs2_launch.py" %MAP%
