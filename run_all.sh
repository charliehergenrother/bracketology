#!/bin/bash

./scraper.py -b index.html -r resume2025.csv -u menresumes.html -o presentbracketlist.csv
cp index.html men.html
./scraper.py -b menfuture.html -f -o bracketlist2025.csv -g menschedule.html
./scraper.py -w -b women.html -r resume2025w.csv -u womenresumes.html
./scraper.py -w -b womenfuture.html -f -o bracketlist2025w.csv -g womenschedule.html
