#!/bin/bash
PATH=$PATH:/c/Python27/
extract="file_$(date +%Y%m%d)"
python ./pdfminer/tools/pdf2txt.py $1 > $extract
python parser.py $extract
