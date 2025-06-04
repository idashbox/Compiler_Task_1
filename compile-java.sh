#!/bin/bash

CD=$(dirname "$(readlink -f "$0")")
RUNTIME_JAVA="$CD/runtime-java"
PYTHON=python

[[ -e "$CD/bin/_props.sh" ]] && . "$CD/bin/_props.sh"
[[ -e "$CD/_props.sh" ]] && . "$CD/_props.sh"

FILENAME="$1"
if [[ -z $FILENAME ]]; then
  echo 'Usage:'
  echo "  $0 src"
  exit 1
fi
if [[ ! -e $FILENAME ]]; then
  echo "File \"$FILENAME\" not exists"
  exit 2
fi

rm -f "${FILENAME%.*}.java" "${FILENAME%.*}.class" "${FILENAME%.*}.jar"
"$PYTHON" "$CD/main.py" --jbc-only "$FILENAME" >"${FILENAME%.*}.java"
STATUS=$?
if [[ $STATUS -ne 0 ]]; then
  rm -f "${FILENAME%.*}.java"
  exit $STATUS
fi
CLASS_NAME=$(basename "${FILENAME%.*}")
javac -cp "$RUNTIME_JAVA" "${FILENAME%.*}.java"
jar --create --file "${FILENAME%.*}.jar" --main-class "$CLASS_NAME" -C . "$CLASS_NAME.class" -C "$RUNTIME_JAVA" CompilerDemo/Runtime.class
rm -f "${FILENAME%.*}.class"