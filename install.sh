#!/bin/sh

pyinstaller gui_components/biomod-gui.spec
mv ./dist/biomod-gui ./gui-app

pyinstaller --onefile gui_components/main.py
mv ./dist/main ./gui-app/main

rm -rf ./build
rm -rf ./dist
rm main.spec