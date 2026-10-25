#!/bin/bash

./scraper.py -b index.html -r excelPath/resume2027.csv -u menresumes.html -o excelPath/presentbracketlist.csv
cp index.html men.html
./scraper.py -b menfuture.html -f -o excelPath/futurebracketlist2027.csv -g menschedule.html
./scraper.py -w -b women.html -r excelPath/resume2027w.csv -u womenresumes.html -o excelPath/presentbracketlistw.csv
./scraper.py -w -b womenfuture.html -f -o excelPath/futurebracketlist2027w.csv -g womenschedule.html
#./oddsscraper.py
./scraper.py -c 20000 -d excelPath/montecarlooutput2027.csv -p menprojections.html
