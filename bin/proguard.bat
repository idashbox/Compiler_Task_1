@echo off
set JAVA="C:\Users\user\.jdks\ms-11.0.27\bin\java.exe"
set PROGUARD="%JAVA%" -jar "%~dp0\.java\proguard-assembler\lib\assembler.jar"

if exist "%~dp0.\_props.bat" call "%~dp0.\_props.bat"

%PROGUARD% %*