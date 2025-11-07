#!/bin/bash

./scraper.py -b index.html -r excelPath/resume2026.csv -u menresumes.html -o excelPath/presentbracketlist.csv
cp index.html men.html
./scraper.py -b menfuture.html -f -o excelPath/futurebracketlist2026.csv -g menschedule.html
./scraper.py -w -b women.html -r excelPath/resume2026w.csv -u womenresumes.html -o excelPath/presentbracketlistw.csv
./scraper.py -w -b womenfuture.html -f -o excelPath/futurebracketlist2026w.csv -g womenschedule.html
./scraper.py -c 15000 -d excelPath/montecarlooutput2026.csv
