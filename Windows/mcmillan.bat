@echo off
mkdir Build
mkdir ..\dist
mkdir ..\dist\ttx
C:\Python23\Installer\Configure.py
C:\Python23\Installer\Makespec.py --upx --onefile --paths "C:\Python23\Lib\encodings;C:\Python23\Lib\site-packages\FontTools\fontTools\encodings;C:\Python23\Lib\site-packages\FontTools\fontTools\misc;C:\Python23\Lib\site-packages\FontTools\fontTools\pens;C:\Python23\Lib\site-packages\FontTools\fontTools\ttLib;" --icon ttx.ico --out Build C:\Python23\Lib\site-packages\FontTools\fontTools\ttx.py
C:\Python23\Installer\Build.py Build\ttx.spec
move Build\ttx.exe ..\dist\ttx

