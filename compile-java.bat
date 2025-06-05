@echo off
set RUNTIME_JAVA=%~dp0.\runtime-java
set PYTHON="C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
set JAVA="C:\Users\user\.jdks\ms-11.0.27\bin\java.exe"
set JAR="C:\Users\user\.jdks\ms-11.0.27\bin\jar.exe"
set PROGUARD="%~dp0.\bin\proguard.bat"

echo DEBUG: Checking environment...
%PYTHON% --version || (echo ERROR: Python not found & pause & exit /b 1)
%JAVA% -version || (echo ERROR: Java not found & pause & exit /b 1)
if not exist %PROGUARD% (echo ERROR: proguard.bat not found at %PROGUARD% & pause & exit /b 1)
if not exist "%~dp0.\bin\.java\proguard-assembler\lib\assembler.jar" (echo ERROR: assembler.jar not found & pause & exit /b 1)

if exist "%~dp0.\bin\_props.bat" call "%~dp0.\bin\_props.bat"
if exist "%~dp0.\_props.bat" call "%~dp0.\_props.bat"

if "%~1"=="" (
  echo Usage: %~nx0 src
  pause
  exit /b 1
)
if not exist "%~1" (
  echo File "%~1" not exists
  pause
  exit /b 2
)

echo DEBUG: Cleaning up old files...
del /f /q "%~dpn1.jbc" "%~dpn1.class" "%~dpn1.jar" >NUL 2>&1

echo DEBUG: Running Python to generate .jbc...
%PYTHON% -Xutf8 "%~dp0\main.py" --jbc-only "%~dpnx1" "%~dpn1.jbc"
set STATUS=%ERRORLEVEL%
if not "%STATUS%"=="0" (
  echo ERROR: Python failed with status %STATUS%
  del /f /q "%~dpn1.jbc"
  pause
  exit /b %STATUS%
)

echo DEBUG: Extracting class name...
for /f "tokens=3" %%V in ('type "%~dpn1.jbc" ^| findstr /b "public class"') do set CLASS_NAME=%%V
if "%CLASS_NAME%"=="" (
  echo ERROR: Could not find class name in %~dpn1.jbc
  pause
  exit /b 1
)

echo DEBUG: Moving .jbc to %CLASS_NAME%.jbc...
move "%~dpn1.jbc" "%~dp1.\%CLASS_NAME%.jbc" >NUL 2>&1

echo DEBUG: Running ProGuard Assembler...
call %PROGUARD% "%~dp1.\%CLASS_NAME%.jbc" "%~dp1.\%CLASS_NAME%.class" || (echo ERROR: ProGuard Assembler failed & pause & exit /b 1)

echo DEBUG: Creating .jar...
%JAR% --create --file "%~dpn1.jar" --main-class "%CLASS_NAME%" -C "%~dp1." "%CLASS_NAME%.class" -C "%RUNTIME_JAVA%" CompilerDemo/Runtime.class || (echo ERROR: Jar creation failed & pause & exit /b 1)

echo DEBUG: Final cleanup...
move "%~dp1.\%CLASS_NAME%.jbc" "%~dpn1.jbc" >NUL 2>&1
del /f /q "%~dp1.\%CLASS_NAME%.class"

echo DEBUG: Compilation successful!
pause