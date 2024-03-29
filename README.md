# bracketology

Welcome to auto-bracketology! The goal of this program is to automatically rank and seed college basketball teams based on their resumes, as the committee might. 

This program, by default, will:
1) If data has not been scraped from warrennolan.com today, scrape all ~360 men's teams and store them in data/men/\<year\>/resumes/\<team\>.json
2) Generate a score for all teams, using weighted categories in lib/men/weights.txt
3) Select the tournament field, and output a list of the selected and seeded teams in order
4) Output a 68-team bracket including those teams and their assigned tournament sites

To run: python3 scraper.py

Options:
-h: print a help message listing the options.

-w: run the projection system for the women's tournament instead of the men's. 2022-present only

-y [year]: make a bracket for given year. 2021-present only

-i [file]: use weights located in given file. See lib/weights.txt for example

-o [file]: output team data and ratings to the given csv file

-e: override scraping and use data currently stored

-s: scrape data anew regardless of whether data has been scraped today

-v: verbose. Print team resumes and bracketing procedure

-t: tracker mode. Generate weights and test their effectiveness

-r [file]: output team resumes to the given csv file.

To see all options: python3 scraper.py -h


