cd /d %~dp0
sphinx-apidoc -o _content -f ../app
make.bat html
make.bat latex
cd _build\latex
pdflatex poitour.tex