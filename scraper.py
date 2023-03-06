#!/usr/bin/env python3

from datetime import date
from team import Team
from game import Game
import os
import sys
import json
import requests
import math

NITTY_GRITTY_URL = "https://www.warrennolan.com/basketball/2023/net-nitty"
TEAM_URL_START = "https://www.warrennolan.com"
TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketball/2023/team-net-sheet?team="
SCRAPE_DATE_FILE = "scrapedate.txt"

AT_LARGE_MAX = 36
AUTO_MAX = 32

LOSS_WEIGHT = 0.08
NET_WEIGHT = 0.125
POWER_WEIGHT = 0.11
Q1_WEIGHT = 0.23
Q2_WEIGHT = 0.08
Q3_WEIGHT = 0.03
Q4_WEIGHT = 0.02
ROAD_WEIGHT = 0.06
NEUTRAL_WEIGHT = 0.035
TOP_10_WEIGHT = 0.07
TOP_25_WEIGHT = 0.065
SOS_WEIGHT = 0.03
NONCON_SOS_WEIGHT = 0.015
AWFUL_LOSS_WEIGHT = 0.02
BAD_LOSS_WEIGHT = 0.03

team_dict = {
        "Kansas-State": "Kansas State",
        "San-Diego-State": "San Diego State",
        "Iowa-State": "Iowa State",
        "West-Virginia": "West Virginia",
        "Saint-Marys-College": "Saint Mary's",
        "Michigan-State": "Michigan State",
        "Miami-FL": "Miami (FL)",
        "FAU": "Florida Atlantic",
        "Texas-AM": "Texas A&M",
        "Boise-State": "Boise State",
        "Oral-Roberts": "Oral Roberts",
        "Mississippi-State": "Mississippi State",
        "Texas-Tech": "Texas Tech",
        "Oklahoma-State": "Oklahoma State",
        "North-Carolina": "North Carolina",
        "North-Carolina-State": "NC State",
        "Sam-Houston-State": "Sam Houston State",
        "Southern-Miss": "Southern Miss",
        "Kent-State": "Kent State",
        "Montana-State": "Montana State",
        "Norfolk-State": "Norfolk State",
        "Grambling-State": "Grambling State",
        "Youngstown-State": "Youngstown State",
        "Morehead-State": "Morehead State",
        "Texas-AM-Corpus-Christi": "Texas A&M-Corpus Christi",
        "Utah-State": "Utah State",
        "Arizona-State": "Arizona State",
        "Penn-State": "Penn State",
        "New-Mexico": "New Mexico",
        "North-Texas": "North Texas",
        "Southeast-Missouri": "Southeast Missouri State",
        "Fairleigh-Dickinson": "Fairleigh Dickinson",
        "Kennesaw-State": "Kennesaw State"
}


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
        s = round(sum([round(LOSS_WEIGHT, 5), round(NET_WEIGHT, 5), round(POWER_WEIGHT, 5), round(Q1_WEIGHT, 5), round(Q2_WEIGHT, 5), round(Q3_WEIGHT, 5), round(Q4_WEIGHT, 5), round(ROAD_WEIGHT, 5), round(NEUTRAL_WEIGHT, 5), round(TOP_10_WEIGHT, 5), round(TOP_25_WEIGHT, 5), round(SOS_WEIGHT, 5), round(NONCON_SOS_WEIGHT, 5), round(AWFUL_LOSS_WEIGHT, 5), round(BAD_LOSS_WEIGHT, 5)]), 5)
        if s != 1:
            print(s)
            print("ya dun goofed with your weights")
            sys.exit()

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
    
    #scrape one team's data
    def scrape_team_data(self, team):
        team_url = TEAM_NITTY_URL_START + team
        if self.verbose:
            print("Scraping", team)
        self.teams[team] = Team()
        self.teams[team].scrape_data(team_url)
        f = open(datadir + team + ".json", "w+")
        f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
        f.close()

    #scrape college basketball data from the web
    #param datadir: directory where the data should be stored
    #param today_date: MM-DD representation of today's date. written to file to record that scraping took place
    def do_scrape(self, datadir, today_date):
        extra_scrapes = ["Southeast-Missouri", "Fairleigh-Dickinson", "Kennesaw-State"]
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
                self.scrape_team_data(team)
        for team in extra_scrapes:
            self.scrape_team_data(team)

        f = open(datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

    #calculate score for a team's raw number of losses (scale: 1.000 = 0, 0.000 = 12)
    #param team: Team object to calculate score for
    def get_loss_score(self, team):
        if self.verbose:
            print("losses", int(team.record.split("-")[1]))
        team.loss_score = LOSS_WEIGHT*(12-int(team.record.split("-")[1]))/12
        return team.loss_score

    #calculate score for a team's NET rank  (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_NET_score(self, team):
        if self.verbose:
            print("NET", team.NET)
        team.NET_score = NET_WEIGHT*(-math.log(team.NET + 19, 2)/2 + 3.12)#(60-team.NET)/59
        return team.NET_score

    #calculate score for a team's predictive rating (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_power_score(self, team):
        if self.verbose:
            print("power", team.predictive)
        team.power_score = POWER_WEIGHT*(-math.log(team.predictive + 19, 2)/2 + 3.12)#(60-team.predictive)/59
        return team.power_score

    #calculate score for a team's record in quadrant 1 (scale: 1.000 = 1, 0.000 = .000)
    #param team: Team object to calculate score for
    def get_Q1_score(self, team):
        if self.verbose:
            print("Quadrant 1", team.get_derived_pct(1))
        team.Q1_score = Q1_WEIGHT*team.get_derived_pct(1)
        return team.Q1_score

    #calculate score for a team's record in quadrant 2 (scale: 1.000 = 1, 0.000 = .500)
    #param team: Team object to calculate score for
    def get_Q2_score(self, team):
        if self.verbose:
            print("Quadrant 2", team.get_derived_pct(2))
        team.Q2_score = Q2_WEIGHT*(team.get_derived_pct(2)-0.5)/0.5
        return team.Q2_score

    #TODO: are these good scales, here and Q4?
    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    def get_Q3_score(self, team):
        if self.verbose:
            print("Quadrant 3", team.get_derived_pct(3))
        team.Q3_score = Q3_WEIGHT*(team.get_derived_pct(3)-0.8)/0.2
        return team.Q3_score

    #calculate score for a team's record in quadrant 4 (scale: 1.000 = 1, 0.000 = .950)
    #param team: Team object to calculate score for
    def get_Q4_score(self, team):
        if self.verbose:
            print("Quadrant 4", team.get_derived_pct(4))
        team.Q4_score = Q4_WEIGHT*(team.get_derived_pct(4)-0.95)/0.05
        return team.Q4_score

    #calculate score for a team's road wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
    #param team: Team object to calculate score for
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
        team.road_score = ROAD_WEIGHT*good_road_wins/5
        return team.road_score

    #calculate score for a team's neutral court wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
    #param team: Team object to calculate score for
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
        team.neutral_score = NEUTRAL_WEIGHT*good_neutral_wins/5
        return team.neutral_score

    #calculate score for a team's top 10 wins (scale: 1.000 = 3, 0.000 = 0)
        #sliding scale. #1-#5: full win. #6-#14: decreases win count by 0.1 for each rank down.
    #param team: Team object to calculate score for
    def get_top10_score(self, team):
        top_10_wins = 0
        for game in team.games:
            if game.margin > 0:
                if game.opp_NET <= 5:
                    top_10_wins += 1
                elif game.opp_NET <= 15:
                    top_10_wins += (15 - game.opp_NET)/10
        if self.verbose:
            print("top 10 wins", top_10_wins)
        team.top10_score = TOP_10_WEIGHT*top_10_wins/5
        return team.top10_score

    #calculate score for a team's top 25 wins (Quad 1A) (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. Quad 1A is 1-15 (H), 1-25 (N), 1-40 (A). win count decreases by 0.1 for each rank down when within 5 of end.
    #param team: Team object to calculate score for
    def get_top25_score(self, team):
        top_25_wins = 0
        for game in team.games:
            if game.margin > 0:
                if game.location == "H":
                    if game.opp_NET <= 10:
                        top_25_wins += 1
                    elif game.opp_NET <= 20:
                        top_25_wins += (20 - game.opp_NET)/10
                elif game.location == "N":
                    if game.opp_NET <= 20:
                        top_25_wins += 1
                    elif game.opp_NET <= 30:
                        top_25_wins += (30 - game.opp_NET)/10
                elif game.location == "A":
                    if game.opp_NET <= 35:
                        top_25_wins += 1
                    elif game.opp_NET <= 45:
                        top_25_wins += (45 - game.opp_NET)/10
        if self.verbose:
            print("top 25 wins", top_25_wins)
        team.top25_score = TOP_25_WEIGHT*top_25_wins/5
        return team.top25_score

    #calculate score for a team's strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_SOS_score(self, team):
        if self.verbose:
            print("SOS", team.NET_SOS)
        team.SOS_score = SOS_WEIGHT*(151 - team.NET_SOS)/150
        return team.SOS_score

    #calculate score for a team's nonconference strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_NCSOS_score(self, team):
        if self.verbose:
            print("Noncon SOS", team.noncon_SOS)
        team.NCSOS_score = NONCON_SOS_WEIGHT*(151 - team.noncon_SOS)/150
        return team.NCSOS_score

    #calculate score for a team's awful (NET > 200) losses (scale: 1.000 = 0, 0.000 = 1)
        #sliding scale. loss count increases by 0.02 for each rank down past 175. #225 and worse are a full loss.
    #param team: Team object to calculate score for
    def get_awful_loss_score(self,team):
        awful_losses = 0
        for game in team.games:
            if game.margin < 0:
                if game.opp_NET > 225:
                    awful_losses += 1
                elif game.opp_NET > 175:
                    awful_losses += (game.opp_NET - 175)/50
        if self.verbose:
            print("awful losses", awful_losses)
        team.awful_loss_score = AWFUL_LOSS_WEIGHT*(1 - awful_losses)
        return team.awful_loss_score

    #calculate score for a team's bad (sub-Q1) losses (scale: 1.000 = 0, 0.000 = 3)
    #param team: Team object to calculate score for
    def get_bad_loss_score(self,team):
        bad_losses = 0
        bad_losses += int(team.Q2_record.split("-")[1])
        bad_losses += int(team.Q3_record.split("-")[1])
        bad_losses += int(team.Q4_record.split("-")[1])
        if self.verbose:
            print("bad losses", bad_losses)
        team.bad_loss_score = BAD_LOSS_WEIGHT*(1 - bad_losses/5)
        return team.bad_loss_score

    #calculate resume score for all teams
    def build_scores(self):
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

    def get_team_out(self, team):
        if team in team_dict:
            return team_dict[team]
        return team

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
        eliminated_teams = ["Morehead-State", "Southern-Miss", "Merrimack", "Liberty", "Bradley"]
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            at_large_bid = False
            if self.teams[team].conference in confs_used:
                if self.teams[team].record_pct < 0.5:
                    continue
                if at_large_bids < AT_LARGE_MAX:
                    at_large_bids += 1
                    at_large_bid = True
                    self.teams[team].at_large_bid = True
                elif bubble_count < 4:
                    bubble_string += (self.get_team_out(team) + " - First Four Out\n")
                    bubble_count += 1
                    continue
                elif bubble_count < 8:
                    bubble_string += (self.get_team_out(team) + " - Next Four Out\n")
                    bubble_count += 1
                    continue
                else:
                    continue
            else:
                if team not in eliminated_teams and auto_bids < AUTO_MAX:
                    auto_bids += 1
                    confs_used.add(self.teams[team].conference)
                    self.teams[team].auto_bid = True
                else:
                    continue
            print("(" + str(curr_seed) + ")" + self.get_team_out(team), end="")
            if at_large_bid:
                if at_large_bids >= AT_LARGE_MAX - 3:
                    if at_large_bids % 2 == 1:
                        curr_seed_max += 1
                    bubble_string += (self.get_team_out(team) + " - Last Four In\n")
                    print(" - Last Four In")
                elif at_large_bids >= AT_LARGE_MAX - 7:
                    bubble_string += (self.get_team_out(team) + " - Last Four Byes\n")
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

#    def build_bracket(self):
#        bracket = ["|"]*32
#        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
#            if self.teams[team].auto_bid or self.teams[team].at_large_bid:


    def output_scores(self):
        with open(self.outputfile, "w") as f:
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
                line = self.get_team_out(team) + "," + \
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
    argindex = 1
    outputfile = ""
    datadir = "data/"
    should_scrape = True
    force_scrape = False
    verbose = False
    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-d datadir] [-o outputfile] [-e|-s] [-v]")
            print("     -h: print this help message")
            print("     -d: set a directory where the scraped data will live")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -s: scrape data anew regardless of whether data has been scraped today")
            print("     -v: verbose")
            sys.exit()
        elif sys.argv[argindex] == '-o':
            outputfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-d':
            datadir = sys.argv[argindex + 1]
            if datadir[-1] != "/":
                datadir = datadir + ["/"]
            argindex += 1
        elif sys.argv[argindex] == '-e':
            should_scrape = False
        elif sys.argv[argindex] == '-v':
            verbose = True
        elif sys.argv[argindex] == '-s':
            force_scrape = True
        argindex += 1
    return outputfile, datadir, should_scrape, force_scrape, verbose

if __name__ == '__main__':
    outputfile, datadir, should_scrape, force_scrape, verbose = process_args()
    scraper = Scraper()
    scraper.verbose = verbose
    scraper.outputfile = outputfile
    scraper.load_data(datadir, should_scrape, force_scrape)
    scraper.build_scores()
    scraper.print_results()
    if outputfile:
        scraper.output_scores()

