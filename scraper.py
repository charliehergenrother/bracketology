#!/usr/bin/env python3

from datetime import date
from team import Team
from game import Game
import os
import sys
import json
import requests

NITTY_GRITTY_URL = "https://www.warrennolan.com/basketball/2023/net-nitty"
TEAM_URL_START = "https://www.warrennolan.com"
SCRAPE_DATE_FILE = "scrapedate.txt"

AT_LARGE_MAX = 36
AUTO_MAX = 32

LOSS_WEIGHT = 0.03
NET_WEIGHT = 0.15
POWER_WEIGHT = 0.12
Q1_WEIGHT = 0.17
Q2_WEIGHT = 0.08
Q3_WEIGHT = 0.025
Q4_WEIGHT = 0.025
ROAD_WEIGHT = 0.03
NEUTRAL_WEIGHT = 0.03
TOP_10_WEIGHT = 0.05
TOP_25_WEIGHT = 0.07
SOS_WEIGHT = 0.08
NONCON_SOS_WEIGHT = 0.04
AWFUL_LOSS_WEIGHT = 0.04
BAD_LOSS_WEIGHT = 0.06

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

    #sanity check to make sure my weights are added correctly
    def sum_weights(self):
        s = sum([LOSS_WEIGHT, NET_WEIGHT, POWER_WEIGHT, Q1_WEIGHT, Q2_WEIGHT, Q3_WEIGHT, Q4_WEIGHT, ROAD_WEIGHT, NEUTRAL_WEIGHT, TOP_10_WEIGHT, TOP_25_WEIGHT, SOS_WEIGHT, NONCON_SOS_WEIGHT, AWFUL_LOSS_WEIGHT, BAD_LOSS_WEIGHT])
        if s != 1:
            print(s)
            print("ya dun goofed with your weights")
            sys.exit()

    #grab the data from where it's stored on disk or scrape it if necessary
    #param datadir: directory where the data is stored
    #param should_scrape: If true, scrape the data from the web if we haven't yet today
    def load_data(self, datadir, should_scrape):
        if not os.path.exists(datadir):
            print("creating datadir", datadir)
            os.makedirs(datadir)
        if not os.path.exists(datadir + SCRAPE_DATE_FILE):
            f = open(datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(datadir + SCRAPE_DATE_FILE, "r+")
        today = date.today()
        today_date = today.strftime("%m-%d")
        saved_date = f.read().strip()
        f.close()
        if should_scrape and today_date != saved_date:
            self.do_scrape(datadir, today_date)
        else:
            self.do_load(datadir)

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
                with open(os.path.join(root, filename)) as f:
                    team_obj = json.loads(f.read())
                games = set()
                for game in team_obj["games"]:
                    games.add(Game(game["opponent"], game["location"], game["opp_NET"], game["team_score"], game["opp_score"]))
                curr_team = Team()
                curr_team.fill_data(team_obj["conference"], team_obj["NET"], team_obj["KenPom"], team_obj["BPI"],
                        team_obj["Sagarin"], team_obj["KPI"], team_obj["SOR"], team_obj["NET_SOS"], \
                        team_obj["noncon_SOS"], games)
                self.teams[filename[:filename.find(".json")]] = curr_team
    
    #scrape college basketball data from the web
    #param datadir: directory where the data should be stored
    #param today_date: MM-DD representation of today's date. written to file to record that scraping took place
    def do_scrape(self, datadir, today_date):
        nittygrittypage = requests.get(NITTY_GRITTY_URL)
        if nittygrittypage.status_code != 200:
            print('scraper problem!')
            sys.exit()
        print("NET page obtained!")
        table_start = False
        for line in nittygrittypage.text.split("\n"):
            if not table_start:
                if "tbody" in line:
                    table_start = True
                continue
            if "team-net-sheet" in line:
                team = line[line.find("sheet")+11:line.find("<img")-2]
                team_url = TEAM_URL_START + line[line.find("href")+6:line.find("<img")-2]
                if self.verbose:
                    print("Scraping", team)
                self.teams[team] = Team()
                self.teams[team].scrape_data(team_url)
                f = open(datadir + team + ".json", "w+")
                f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
                f.close()

        f = open(datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

    #calculate score for a team's raw number of losses (scale: 1.000 = 0, 0.000 = 12)
    def get_loss_score(self, team):
        if self.verbose:
            print("losses", int(team.record.split("-")[1]))
        return LOSS_WEIGHT*int(team.record.split("-")[1])/12

    #calculate score for a team's NET rank  (scale: 1.000 = 1, 0.000 = 60)
    def get_NET_score(self, team):
        if self.verbose:
            print("NET", team.NET)
        return NET_WEIGHT*(60-team.NET)/59

    #calculate score for a team's predictive rating (scale: 1.000 = 1, 0.000 = 60)
    def get_power_score(self, team):
        if self.verbose:
            print("power", team.predictive)
        return POWER_WEIGHT*(60-team.predictive)/59

    #TODO: want to use the better methods here?
    #calculate score for a team's record in quadrant 1 (scale: 1.000 = 1, 0.000 = .000)
    def get_Q1_score(self, team):
        if self.verbose:
            print("Quadrant 1", team.Q1_pct)
        return Q1_WEIGHT*team.Q1_pct

    #calculate score for a team's record in quadrant 2 (scale: 1.000 = 1, 0.000 = .500)
    def get_Q2_score(self, team):
        if self.verbose:
            print("Quadrant 2", team.Q2_pct)
        return Q2_WEIGHT*(team.Q2_pct-0.5)/0.5

    #TODO: are these good scales, here and Q4?
    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    def get_Q3_score(self, team):
        if self.verbose:
            print("Quadrant 3", team.Q3_pct)
        return Q3_WEIGHT*(team.Q3_pct-0.8)/0.2

    #calculate score for a team's record in quadrant 4 (scale: 1.000 = 1, 0.000 = .950)
    def get_Q4_score(self, team):
        if self.verbose:
            print("Quadrant 4", team.Q4_pct)
        return Q4_WEIGHT*(team.Q4_pct-0.95)/0.05

    #calculate score for a team's road wins (scale: 1.000 = 5, 0.000 = 0)
    def get_road_score(self, team):
        good_road_wins = 0
        for game in team.games:
            if game.margin > 0 and game.location == "A":
                if game.opp_NET <= 50:
                    good_road_wins += 1
                elif game.opp_NET <= 100:
                    good_road_wins += (100 - game.opp_NET)/50
        if self.verbose:
            print("road wins", good_road_wins)
        return ROAD_WEIGHT*good_road_wins/5

    #calculate score for a team's neutral court wins (scale: 1.000 = 5, 0.000 = 0)
    def get_neutral_score(self, team):
        good_neutral_wins = 0
        for game in team.games:
            if game.margin > 0 and game.location == "N":
                if game.opp_NET <= 50:
                    good_neutral_wins += 1
                elif game.opp_NET <= 100:
                    good_neutral_wins += (100 - game.opp_NET)/50
        if self.verbose:
            print("neutral wins", good_neutral_wins)
        return NEUTRAL_WEIGHT*good_neutral_wins/5

    #TODO: Use Quad 1A or whatever?
    #calculate score for a team's top 10 wins (scale: 1.000 = 3, 0.000 = 0)
    def get_top10_score(self, team):
        top_10_wins = 0
        for game in team.games:
            if game.margin > 0:
                if game.opp_NET <= 5:
                    top_10_wins += 1
                elif game.opp_NET <= 15:
                    top_10_wins += (16 - game.opp_NET)/10
        if self.verbose:
            print("top 10 wins", top_10_wins)
        return TOP_10_WEIGHT*top_10_wins/5

    #calculate score for a team's top 25 wins (scale: 1.000 = 5, 0.000 = 0)
    def get_top25_score(self, team):
        top_25_wins = 0
        for game in team.games:
            if game.margin > 0:
                if game.opp_NET <= 20:
                    top_25_wins += 1
                elif game.opp_NET <= 30:
                    top_25_wins += (31 - game.opp_NET)/10
        if self.verbose:
            print("top 25 wins", top_25_wins)
        return TOP_25_WEIGHT*top_25_wins/5

    #calculate score for a team's strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    def get_SOS_score(self, team):
        if self.verbose:
            print("SOS", team.NET_SOS)
        return SOS_WEIGHT*(151 - team.NET_SOS)/150

    #calculate score for a team's nonconference strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    def get_NCSOS_score(self, team):
        if self.verbose:
            print("Noncon SOS", team.noncon_SOS)
        return NONCON_SOS_WEIGHT*(151 - team.noncon_SOS)/150
    
    #calculate score for a team's awful (NET > 200) losses (scale: 1.000 = 0, 0.000 = 1)
    def get_awful_loss_score(self,team):
        awful_losses = 0
        for game in team.games:
            if game.margin < 0:
                if game.opp_NET > 230:
                    awful_losses += 1
                elif game.opp_NET > 170:
                    awful_losses += (game.opp_NET - 170)/60
        if self.verbose:
            print("awful losses", awful_losses)
        return AWFUL_LOSS_WEIGHT*(1 - awful_losses)

    #calculate score for a team's bad losses (scale: 1.000 = 0, 0.000 = 3)
    def get_bad_loss_score(self,team):
        bad_losses = 0
        bad_losses += int(team.Q2_record[team.Q2_record.find("-")+1:])
        bad_losses += int(team.Q3_record[team.Q3_record.find("-")+1:])
        bad_losses += int(team.Q4_record[team.Q4_record.find("-")+1:])
        if self.verbose:
            print("bad losses", bad_losses)
        return BAD_LOSS_WEIGHT*(1 - bad_losses)

    #calculate a team's resume score
    def build_score(self):
        self.sum_weights()
        for team in self.teams:
            if self.verbose:
                print("Scoring", team)
            score = 0
            score += self.get_loss_score(self.teams[team])
            score += self.get_NET_score(self.teams[team])
            score += self.get_power_score(self.teams[team])
            score += self.get_Q1_score(self.teams[team])
            score += self.get_Q2_score(self.teams[team])
            score += self.get_Q3_score(self.teams[team])
            score += self.get_Q4_score(self.teams[team])
            score += self.get_road_score(self.teams[team])
            score += self.get_neutral_score(self.teams[team])
            score += self.get_top10_score(self.teams[team])
            score += self.get_top25_score(self.teams[team])
            score += self.get_SOS_score(self.teams[team])
            score += self.get_NCSOS_score(self.teams[team])
            score += self.get_awful_loss_score(self.teams[team])
            score += self.get_bad_loss_score(self.teams[team])
            self.teams[team].score = score

    #seed and print the field, including a bubble section
    def print_results(self):
        curr_seed = 1
        num_curr_seed = 1
        curr_seed_max = 4
        at_large_bids = 0
        auto_bids = 0
        confs_used = set()
        bubble_count = 0
        bubble_string = "BUBBLE: \n"
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            at_large_bid = False
            if self.teams[team].conference in confs_used:
                if at_large_bids < AT_LARGE_MAX:
                    at_large_bids += 1
                    at_large_bid = True
                elif bubble_count < 4:
                    bubble_string += (team + " - First Four Out\n")
                    bubble_count += 1
                    continue
                elif bubble_count < 8:
                    bubble_string += (team + " - Next Four Out\n")
                    bubble_count += 1
                    continue
                else:
                    continue
            else:
                if auto_bids < AUTO_MAX:
                    auto_bids += 1
                    confs_used.add(self.teams[team].conference)
                else:
                    continue
            print("(" + str(curr_seed) + ")" + team, end="")
            if at_large_bid:
                if at_large_bids >= AT_LARGE_MAX - 3:
                    if at_large_bids % 2 == 1:
                        curr_seed_max += 1
                    bubble_string += (team + " - Last Four In\n")
                    print(" - Last Four In")
                elif at_large_bids >= AT_LARGE_MAX - 7:
                    bubble_string += (team + " - Last Four Byes\n")
                    print(" - Last Four Byes")
                else:
                    print()
            else:
                print("*")
            if num_curr_seed == curr_seed_max and curr_seed < 16:
                curr_seed += 1
                num_curr_seed = 1
                curr_seed_max = 4
            else:
                num_curr_seed += 1

        print()
        print(bubble_string)

#accept command line arguments
def process_args():
    argindex = 1
    outputfile = "bracketlist.csv"
    datadir = "data/"
    should_scrape = True
    verbose = False
    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-d datadir] [-o outputfile] [-e] [-v]")
            print("     -h: print this help message")
            print("     -d: set a directory where the scraped data will live")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -v: verbose")
            sys.exit()
        elif sys.argv[argindex] == '-o':
            outputfile = sys.argv[argindex + 1]
            argindex += 2
        elif sys.argv[argindex] == '-d':
            datadir = sys.argv[argindex + 1]
            if datadir[-1] != "/":
                datadir = datadir + ["/"]
            argindex += 2
        elif sys.argv[argindex] == '-e':
            should_scrape = False
        elif sys.argv[argindex] == '-v':
            verbose = True
    return outputfile, datadir, should_scrape, verbose

if __name__ == '__main__':
    outputfile, datadir, should_scrape, verbose = process_args()
    scraper = Scraper()
    scraper.verbose = verbose
    scraper.load_data(datadir, should_scrape)
    scraper.build_score()
    scraper.print_results()

