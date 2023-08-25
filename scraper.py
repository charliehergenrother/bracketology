#!/usr/bin/env python3

from datetime import date
from team import Team, SELECTION_SUNDAYS
from game import Game
from builder import Builder
from itertools import permutations
import os
import sys
import json
import requests
import math
import random

SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_COORDINATES_FILE = "lib/team_locations.txt"

reverse_team_dict = dict()
AUTO_MAXES = {"2021": 31, "2022": 32, "2023": 32}

#class to turn the Team and Game objects into jsonifyable strings
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

#class to scrape and store data about college basketball teams
class Scraper:

    def __init__(self):
        self.teams = dict()
        return

    #load in team and site coordinates, compute every team's site preferences (closest as the crow flies)
    def load_coordinates(self):
        first_sites = dict()
        regional_sites = dict()
        first_weekend_sites = list()
        first_weekend_rankings = dict()
        region_rankings = dict()
        SITE_COORDINATES_FILE = "lib/site_locations_" + self.year + ".txt"
        f = open(SITE_COORDINATES_FILE, "r")
        for count, line in enumerate(f):
            site_name = line[:line.find("[")]
            latitude = float(line[line.find("[")+1:line.find(" N, ")-1])
            longitude = float(line[line.find(" N, ")+4:line.find(" W]")-1])
            if count < 8:
                first_sites[site_name] = [latitude, longitude]
                #two pods at each site, so append each site twice
                first_weekend_sites.append(site_name)
                first_weekend_sites.append(site_name)
            else:
                regional_sites[site_name] = [latitude, longitude]
        f.close()
        f = open(TEAM_COORDINATES_FILE, "r")
        for line in f:
            team = line[:line.find("[")]
            latitude = float(line[line.find("[")+1:line.find(" N, ")-1])
            longitude = float(line[line.find(" N, ")+4:line.find(" W]")-1])
            try:
                self.teams[team].latitude = latitude
            except KeyError:    #this team didn't exist this year
                continue
            self.teams[team].longitude = longitude
            first_distances = dict()
            regional_distances = dict()
            for site in first_sites:
                distance = math.sqrt((latitude - first_sites[site][0])**2 + (longitude - first_sites[site][1])**2)
                first_distances[site] = distance
            for site in regional_sites:
                distance = math.sqrt((latitude - regional_sites[site][0])**2 + (longitude - regional_sites[site][1])**2)
                regional_distances[site] = distance
            first_order = list()
            regional_order = list()
            for site in sorted(first_distances, key=lambda x: first_distances[x]):
                first_order.append(site)
            for site in sorted(regional_distances, key=lambda x: regional_distances[x]):
                regional_order.append(site)
            first_weekend_rankings[team] = first_order
            region_rankings[team] = regional_order
        f.close()
        return first_weekend_sites, first_weekend_rankings, region_rankings

    def load_special_teams(self):
        SPECIAL_TEAMS_FILE = "lib/special_teams_" + self.year + ".json"
        with open(SPECIAL_TEAMS_FILE, "r") as f:
            special_teams = json.loads(f.read())
        eliminated_teams = special_teams["eliminated_teams"]
        ineligible_teams = special_teams["ineligible_teams"]
        conference_winners = special_teams["conference_winners"]
        return eliminated_teams, ineligible_teams, conference_winners

    #grab the data from where it's stored on disk or scrape it if necessary
    #param datadir: directory where the data is stored
    #param should_scrape: If true, scrape the data from the web if we haven't yet today
    #param force_scrape: If true, scrape the data from the web regardless of if we have or haven't
    def load_data(self, datadir, should_scrape, force_scrape):
        if not os.path.exists(datadir):
            print("creating datadir", datadir)
            os.makedirs(datadir)
        if not os.path.exists(datadir + SCRAPE_DATE_FILE):
            f = open(datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(datadir + SCRAPE_DATE_FILE, "r+")
        today = date.today()
        today_date = today.strftime("%m-%d")    #format: mm-dd
        saved_date = f.read().strip()
        f.close()
        if force_scrape or (should_scrape and today_date != saved_date):
            self.do_scrape(datadir, today_date)
        else:
            self.do_load(datadir)
        first_weekend_sites, first_weekend_rankings, region_rankings = self.load_coordinates()
        eliminated_teams, ineligible_teams, conference_winners = self.load_special_teams()
        return first_weekend_sites, first_weekend_rankings, region_rankings, eliminated_teams, ineligible_teams, conference_winners

    #load the data that has previously been scraped
    #param datadir: directory where the data is stored
    def do_load(self, datadir):
        #loop through datadir
        for root, dirs, files in os.walk(datadir):
            for filename in files:
                if ('.json') not in filename:
                    continue
                if self.verbose:
                    print("Loading", filename)
                with open(os.path.join(root, filename), "r") as f:
                    team_obj = json.loads(f.read())
                games = set()
                for game_obj in team_obj["games"]:
                    games.add(Game(game_obj["opponent"], game_obj["location"], game_obj["opp_NET"], \
                        game_obj["team_score"], game_obj["opp_score"], game_obj["date"]))
                curr_team = Team()
                curr_team.fill_data(team_obj["conference"], team_obj["NET"], team_obj["KenPom"], team_obj["BPI"],
                        team_obj["Sagarin"], team_obj["KPI"], team_obj["SOR"], team_obj["NET_SOS"], \
                        team_obj["noncon_SOS"], games, team_obj["team_out"])
                self.teams[filename[:filename.find(".json")]] = curr_team
                team = filename[:filename.find(".json")]
                reverse_team_dict[curr_team.team_out] = team
    
    #scrape one team's data
    def scrape_team_data(self, team, datadir):
        TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketball/" + self.year + "/team-net-sheet?team="
        team_url = TEAM_NITTY_URL_START + team
        self.teams[team] = Team()
        self.teams[team].scrape_data(team_url, self.year)
        f = open(datadir + team + ".json", "w+")
        f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
        f.close()
        reverse_team_dict[self.teams[team].team_out] = team

    #scrape college basketball data from the web
    #param datadir: directory where the data should be stored
    #param today_date: MM-DD representation of today's date. written to file to record that scraping took place
    def do_scrape(self, datadir, today_date):
        net_url = "https://www.warrennolan.com/basketball/" + self.year + "/net"
        net_page = requests.get(net_url)
        if net_page.status_code != 200:
            print('scraper problem!')
            sys.exit()
        print("NET page obtained!")
        table_start = False
        for line in net_page.text.split("\n"):
            if not table_start:
                if "tbody" in line:
                    table_start = True
                continue
            if "blue-black" in line:
                team_start_index = line.find("schedule/")+9
                team = line[team_start_index:line.find('">', team_start_index)]
                self.scrape_team_data(team, datadir)
                print("scraped", team + "!")

        f = open(datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

    #write all team scores for each category to specified file
    def output_scores(self, outputfile):
        with open(outputfile, "w") as f:
            f.write("Team," + \
                    "Losses(" + str(round(LOSS_WEIGHT, 5)) + \
                    "), NET(" + str(round(NET_WEIGHT, 5)) + \
                    "), Power(" + str(round(POWER_WEIGHT, 5)) + \
                    "), Q1(" + str(round(Q1_WEIGHT, 5)) + \
                    "), Q2(" + str(round(Q2_WEIGHT, 5)) + \
                    "), Q3(" + str(round(Q3_WEIGHT, 5)) + \
                    "), Q4(" + str(round(Q4_WEIGHT, 5)) + \
                    "), Road(" + str(round(ROAD_WEIGHT, 5)) + \
                    "), Neutral(" + str(round(NEUTRAL_WEIGHT, 5)) + \
                    "), Top 10(" + str(round(TOP_10_WEIGHT, 5)) + \
                    "), Top 25(" + str(round(TOP_25_WEIGHT, 5)) + \
                    "), SOS(" + str(round(SOS_WEIGHT, 5)) + \
                    "), Noncon SOS(" + str(round(NONCON_SOS_WEIGHT, 5)) + \
                    "), Awful losses(" + str(round(AWFUL_LOSS_WEIGHT, 5)) + \
                    "), Bad losses(" + str(round(BAD_LOSS_WEIGHT, 5)) + \
                    "), Total Score\n")
            for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
                line = self.teams[team].team_out + "," + \
                        str(round(self.teams[team].loss_score, 5)) + "," + \
                        str(round(self.teams[team].NET_score, 5)) + "," + \
                        str(round(self.teams[team].power_score, 5)) + "," + \
                        str(round(self.teams[team].Q1_score, 5)) + "," + \
                        str(round(self.teams[team].Q2_score, 5)) + "," + \
                        str(round(self.teams[team].Q3_score, 5)) + "," + \
                        str(round(self.teams[team].Q4_score, 5)) + "," + \
                        str(round(self.teams[team].road_score, 5)) + "," + \
                        str(round(self.teams[team].neutral_score, 5)) + "," + \
                        str(round(self.teams[team].top10_score, 5)) + "," + \
                        str(round(self.teams[team].top25_score, 5)) + "," + \
                        str(round(self.teams[team].SOS_score, 5)) + "," + \
                        str(round(self.teams[team].NCSOS_score, 5)) + "," + \
                        str(round(self.teams[team].awful_loss_score, 5)) + "," + \
                        str(round(self.teams[team].bad_loss_score, 5)) + "," + \
                        str(round(self.teams[team].score, 5)) + "\n"
                f.write(line)

#accept command line arguments
def process_args():
    year = "2023"
    argindex = 1
    outputfile = ""
    should_scrape = True
    force_scrape = False
    verbose = False
    weightfile = "lib/weights.txt"
    tracker = False

    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-y year] [-w weightfile] [-o outputfile] [-e|-s] [-v]")
            print("     -h: print this help message")
            print("     -y: make a bracket for this year. 2021-present only")
            print("     -w: use weights located in this file")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -s: scrape data anew regardless of whether data has been scraped today")
            print("     -v: verbose. Print team resumes and bracketing procedure")
            print("     -t: tracker mode. Generate weights and test their effectiveness")
            sys.exit()
        elif sys.argv[argindex] == '-o':
            outputfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-e':
            should_scrape = False
        elif sys.argv[argindex] == '-t':
            tracker = True
        elif sys.argv[argindex] == '-v':
            verbose = True
        elif sys.argv[argindex] == '-s':
            force_scrape = True
        elif sys.argv[argindex] == '-w':
            weightfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-y':
            if int(sys.argv[argindex + 1]) < 2021:
                print("year not supported, sorry. Try 2021-present.")
                sys.exit()
            year = sys.argv[argindex + 1]
            argindex += 1
        argindex += 1
    datadir = "data/" + year + "/"
    return year, outputfile, datadir, should_scrape, force_scrape, verbose, tracker, weightfile

def main():
    scraper = Scraper()
    scraper.year, outputfile, datadir, should_scrape, force_scrape, scraper.verbose, \
            scraper.tracker, weightfile = process_args()
    first_weekend_sites, first_weekend_rankings, region_rankings, eliminated_teams, ineligible_teams, conference_winners = \
            scraper.load_data(datadir, should_scrape, force_scrape)
    builder = Builder(scraper.year, scraper.teams, scraper.verbose, \
            first_weekend_sites, first_weekend_rankings, region_rankings, \
            eliminated_teams, ineligible_teams, conference_winners,
            reverse_team_dict)
    if scraper.tracker:
        builder.actual_results = builder.load_results()
        builder.weight_results = dict()
        builder.run_tracker(tuple())
        counter = 0
        for weights in sorted(builder.weight_results, key=lambda x: builder.weight_results[x]):
            print([str(x).rjust(2) for x in weights], builder.weight_results[weights])
            counter += 1
            if counter > 50:
                break
    else:
        builder.build_scores(weightfile)
        builder.select_seed_and_print_field(True)
        builder.build_bracket()
        if outputfile:
            scraper.output_scores(outputfile)

if __name__ == '__main__':
    main()

