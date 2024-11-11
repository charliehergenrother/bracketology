#!/bin/bash

./scraper.py -b index.html -r excelPath/resume2025.csv -u menresumes.html -o excelPath/presentbracketlist.csv
cp index.html men.html
./scraper.py -b menfuture.html -f -o excelPath/futurebracketlist2025.csv -g menschedule.html
./scraper.py -w -b women.html -r excelPath/resume2025w.csv -u womenresumes.html -o excelPath/presentbracketlistw.csv
./scraper.py -w -b womenfuture.html -f -o excelPath/futurebracketlist2025w.csv -g womenschedule.html
