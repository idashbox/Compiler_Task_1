@echo off
setlocal

rem Проверяем, передан ли файл в качестве аргумента
if "%~1"=="" (
    echo Usage: %0 ^<file.j^>
    exit /b 1
)

rem Проверяем существование файла
if not exist "%~1" (
    echo Error: File %~1 not found
    exit /b 1
)

rem Компилируем .j файл в .class файл с помощью Jasmin
java -jar runtime-java/jasmin.jar "%~1"

rem Проверяем успешность компиляции
if errorlevel 1 (
    echo Error: Compilation failed
    exit /b 1
)

echo Compilation successful 