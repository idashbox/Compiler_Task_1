@echo off
setlocal

rem Удаляем старый mel.j, если он существует
if exist mel.j (
    echo Удаление устаревшего файла mel.j...
    del mel.j
)

rem Компилируем все .j файлы
echo Компиляция всех .j файлов...
for %%f in (Point.j Program.j) do (
    echo Компиляция %%f...
    java -jar runtime-java/jasmin.jar "%%f"
)

echo Compilation successful 