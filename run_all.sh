#!/bin/bash

./scraper.py -b index.html -r excelPath/resume2024.csv
cp index.html men.html
./scraper.py -b menfuture.html -f -o excelPath/bracketlist2024.csv
./scraper.py -w -b women.html -r excelPath/resume2024w.csv
./scraper.py -w -b womenfuture.html -f -o excelPath/bracketlist2024w.csv