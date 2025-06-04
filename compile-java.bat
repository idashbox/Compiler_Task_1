@echo off

set RUNTIME_JAVA=%~dp0.\runtime-java
set PYTHON=python

if exist "%~dp0.\_props.bat" call "%~dp0.\_props.bat"

if "%~1"=="" (
  echo Usage:
  echo   %~nx0 src
  exit /b 1
)
if not exist "%~1" (
  echo File "%~1" not exists
  exit /b 2
)

del /f /q "%~dpn1.jbc" "%~dpn1.class" "%~dpn1.jar" >NUL 2>&1
%PYTHON% "%~dp0\main.py" --jbc-only "%~dpnx1" >"%~dpn1.jbc"
set STATUS=%ERRORLEVEL%
if not "%STATUS%"=="0" (
  echo Python script failed with error code %STATUS%
  type "%~dpn1.jbc"
  del /f /q "%~dpn1.jbc"
  exit /b %STATUS%
)
set CLASS_NAME=%~n1
%JAVAC% -cp "%RUNTIME_JAVA%" "%~dpn1.jbc"
%JAR% --create --file "%~dpn1.jar" --main-class "%CLASS_NAME%" -C . "%CLASS_NAME%.class" -C "%RUNTIME_JAVA%" CompilerDemo/Runtime.class
del /f /q "%~dpn1.class"