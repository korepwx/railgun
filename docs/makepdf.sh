#!/bin/bash
sphinx-build -b latex -d _build/doctrees . _build/xetex && cd _build/xetex; xelatex *.tex
