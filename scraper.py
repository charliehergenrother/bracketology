#!/usr/bin/env python3

from datetime import date
from team import Team
from game import Game
from builder import Builder
from tracker import Tracker
from scorer import Scorer
import os
import sys
import json
import requests
import math

SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_COORDINATES_FILE = "lib/team_locations.txt"

reverse_team_dict = dict()

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

    #get the order of sites closest to a given set of coordinates (corresponding to a school)
    #param sites: dict containing names of sites and their coordinates
    #param latitude: latitude of school
    #param longitude: longitude of school
    def get_site_order(self, sites, latitude, longitude):
        site_distances = dict()
        for site in sites:
            distance = math.sqrt((latitude - sites[site][0])**2 + (longitude - sites[site][1])**2)
            site_distances[site] = distance
        site_order = list()
        for site in sorted(site_distances, key=lambda x: site_distances[x]):
            site_order.append(site)
        return site_order

    #load in team and site coordinates, compute every team's site preferences (closest as the crow flies)
    def load_coordinates(self):
        first_sites = dict()
        regional_sites = dict()
        first_weekend_sites = list()
        first_weekend_rankings = dict()
        region_rankings = dict()
        
        SITE_COORDINATES_FILE = "lib/" + self.year + "/site_locations.txt"
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

            first_weekend_rankings[team] = self.get_site_order(first_sites, latitude, longitude)
            region_rankings[team] = self.get_site_order(regional_sites, latitude, longitude)
        f.close()
        return first_weekend_sites, first_weekend_rankings, region_rankings

    #load ineligible teams, eliminated teams, and conference winners for a specific year
    def load_special_teams(self):
        SPECIAL_TEAMS_FILE = "lib/" + self.year + "/special_teams.json"
        with open(SPECIAL_TEAMS_FILE, "r") as f:
            special_teams = json.loads(f.read())
        eliminated_teams = special_teams["eliminated_teams"]
        ineligible_teams = special_teams["ineligible_teams"]
        conference_winners = special_teams["conference_winners"]
        return eliminated_teams, ineligible_teams, conference_winners

    #grab the data from where it's stored on disk or scrape it if necessary
    #param should_scrape: If true, scrape the data from the web if we haven't yet today
    #param force_scrape: If true, scrape the data from the web regardless of if we have or haven't
    def load_data(self, should_scrape, force_scrape):
        if not os.path.exists(self.datadir):
            print("creating datadir", self.datadir)
            os.makedirs(self.datadir)
        if not os.path.exists(self.datadir + SCRAPE_DATE_FILE):
            f = open(self.datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(self.datadir + SCRAPE_DATE_FILE, "r+")
        today = date.today()
        today_date = today.strftime("%m-%d")    #format: mm-dd
        saved_date = f.read().strip()
        f.close()
        if force_scrape or (should_scrape and today_date != saved_date):
            self.do_scrape(today_date)
        else:
            self.do_load()
        first_weekend_sites, first_weekend_rankings, region_rankings = self.load_coordinates()
        eliminated_teams, ineligible_teams, conference_winners = self.load_special_teams()
        return Builder(self.year, self.teams, self.verbose, self.outputfile, first_weekend_sites, \
                first_weekend_rankings, region_rankings, eliminated_teams, \
                ineligible_teams, conference_winners, reverse_team_dict)

    #load the data that has previously been scraped
    def do_load(self):
        #loop through datadir
        for root, dirs, files in os.walk(self.datadir):
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
    #team: string indicating which team's data should be scraped
    def scrape_team_data(self, team):
        TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketball/" + self.year + "/team-net-sheet?team="
        team_url = TEAM_NITTY_URL_START + team
        self.teams[team] = Team()
        self.teams[team].scrape_data(team_url, self.year)
        f = open(self.datadir + team + ".json", "w+")
        f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
        f.close()
        reverse_team_dict[self.teams[team].team_out] = team

    #scrape college basketball data from the web
    #param today_date: MM-DD representation of today's date. written to file to record that scraping took place
    def do_scrape(self, today_date):
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
                self.scrape_team_data(team)
                print("scraped", team + "!")

        f = open(self.datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

#accept command line arguments
def process_args():
    year = "2024"
    argindex = 1
    outputfile = ""
    webfile = ""
    should_scrape = True
    force_scrape = False
    verbose = False
    weightfile = "lib/weights.txt"
    tracker = False

    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-y year] [-w weightfile] [-o outputfile] [-b webfile] [-e|-s] [-v]")
            print("     -h: print this help message")
            print("     -y: make a bracket for given year. 2021-present only")
            print("     -w: use weights located in given file")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -b: set an html filename where the displayed bracket will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -s: scrape data anew regardless of whether data has been scraped today")
            print("     -v: verbose. Print team resumes and bracketing procedure")
            print("     -t: tracker mode. Generate weights and test their effectiveness")
            sys.exit()
        elif sys.argv[argindex] == '-o':
            outputfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-b':
            webfile = sys.argv[argindex + 1]
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
    return year, outputfile, webfile, datadir, should_scrape, force_scrape, verbose, tracker, weightfile

def main():
    scraper = Scraper()
    scraper.year, scraper.outputfile, scraper.webfile, scraper.datadir, should_scrape, force_scrape, \
            scraper.verbose, scraper.tracker, weightfile = process_args()
    builder = scraper.load_data(should_scrape, force_scrape)
    scorer = Scorer(builder)
    if scraper.tracker:
        tracker = Tracker(builder, scorer, scraper.year, scraper.verbose)
        tracker.load_results()
        tracker.run_tracker(tuple())
        counter = 0
        for weights in sorted(tracker.weight_results, key=lambda x: tracker.weight_results[x]):
            print([str(x).rjust(3) for x in weights], tracker.weight_results[weights])
            counter += 1
            if counter > 50:
                break
    else:
        weights = scorer.get_weights(weightfile)
        scorer.build_scores(weights)
        builder.select_seed_and_print_field()
        builder.build_bracket()
        if scraper.outputfile:
            scorer.outputfile = scraper.outputfile
            scorer.output_scores()
        if scraper.webfile:
            builder.webfile = scraper.webfile
            builder.output_bracket()

if __name__ == '__main__':
    main()

