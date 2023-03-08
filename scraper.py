#!/usr/bin/env python3

from datetime import date
from team import Team
from game import Game
from itertools import permutations
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

LOSS_WEIGHT = 0.09
NET_WEIGHT = 0.125
POWER_WEIGHT = 0.11
Q1_WEIGHT = 0.24
Q2_WEIGHT = 0.08
Q3_WEIGHT = 0.02
Q4_WEIGHT = 0.015
ROAD_WEIGHT = 0.06
NEUTRAL_WEIGHT = 0.035
TOP_10_WEIGHT = 0.07
TOP_25_WEIGHT = 0.065
SOS_WEIGHT = 0.03
NONCON_SOS_WEIGHT = 0.015
AWFUL_LOSS_WEIGHT = 0.015
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
        "Cleveland-State": "Cleveland State",
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

region_rankings = {
    "Houston": ["Kansas City", "Louisville", "Las Vegas", "New York"],
    "Alabama": ["Louisville", "Kansas City", "New York", "Las Vegas"],
    "Tennessee": ["Louisville", "New York", "Kansas City", "Las Vegas"],
    "UCLA": ["Las Vegas", "Kansas City", "Louisville", "New York"],
    "Purdue": ["Louisville", "Kansas City", "New York", "Las Vegas"],
    "Connecticut": ["New York", "Louisville", "Kansas City", "Las Vegas"],
    "Kansas": ["Kansas City", "Louisville", "New York", "Las Vegas"],
    "Saint-Marys-College": ["Las Vegas", "Kansas City", "Louisville", "New York"],
    "Gonzaga": ["Las Vegas", "Kansas City", "Louisville", "New York"],
    "Texas": ["Kansas City", "Louisville", "Las Vegas", "New York"],
    "Arizona": ["Las Vegas", "Kansas City", "Louisville", "New York"],
    "Baylor": ["Kansas City", "Louisville", "Las Vegas", "New York"],
    "Marquette": ["Kansas City", "Louisville", "New York", "Las Vegas"],
    "Creighton": ["Kansas City", "Louisville", "New York", "Las Vegas"],
    "FAU": ["Louisville", "New York", "Kansas City", "Las Vegas"],
    "San-Diego-State": ["Las Vegas", "Kansas City", "Louisville", "New York"],
    "Kansas-State": ["Kansas City", "Louisville", "New York", "Las Vegas"],
    "Xavier": ["Louisville", "Kansas City", "New York", "Las Vegas"],
    "Iowa-State": ["Kansas City", "Louisville", "New York", "Las Vegas"],
    "Indiana": ["Louisville", "Kansas City", "New York", "Las Vegas"],
    "Kentucky": ["Louisville", "Kansas City", "New York", "Las Vegas"],
    "TCU": ["Kansas City", "Louisville", "Las Vegas", "New York"]
}

first_weekend_rankings = {
    "Houston": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Denver", "Columbus", "Albany", "Sacramento"],
    "Alabama": ["Birmingham", "Orlando", "Greensboro", "Columbus", "Des Moines", "Albany", "Denver", "Sacramento"],
    "Tennessee": ["Greensboro", "Birmingham", "Orlando", "Columbus", "Albany", "Des Moines", "Denver", "Sacramento"],
    "UCLA": ["Sacramento", "Denver", "Des Moines", "Birmingham", "Columbus", "Orlando", "Greensboro", "Albany"],
    "Purdue": ["Columbus", "Des Moines", "Greensboro", "Birmingham", "Albany", "Orlando", "Denver", "Sacramento"],
    "Connecticut": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Kansas": ["Des Moines", "Denver", "Columbus", "Birmingham", "Greensboro", "Albany", "Orlando", "Sacramento"],
    "Saint-Marys-College": ["Sacramento", "Denver", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "Gonzaga": ["Sacramento", "Denver", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "Texas": ["Birmingham", "Des Moines", "Orlando", "Greensboro", "Denver", "Columbus", "Sacramento", "Albany"],
    "Arizona": ["Denver", "Sacramento", "Des Moines", "Birmingham", "Columbus", "Orlando", "Greensboro", "Albany"],
    "Baylor": ["Birmingham", "Des Moines", "Orlando", "Greensboro", "Denver", "Columbus", "Sacramento", "Albany"],
    "Marquette": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Creighton": ["Des Moines", "Denver", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Sacramento"],
    "FAU": ["Orlando", "Birmingham", "Greensboro", "Columbus", "Albany", "Des Moines", "Denver", "Sacramento"],
    "San-Diego-State": ["Sacramento", "Denver", "Des Moines", "Birmingham", "Columbus", "Orlando", "Greensboro", "Albany"],
    "Kansas-State": ["Des Moines", "Denver", "Columbus", "Birmingham", "Greensboro", "Albany", "Orlando", "Sacramento"],
    "Xavier": ["Columbus", "Des Moines", "Greensboro", "Birmingham", "Albany", "Orlando", "Denver", "Sacramento"],
    "Iowa-State": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Indiana": ["Columbus", "Des Moines", "Greensboro", "Birmingham", "Albany", "Orlando", "Denver", "Sacramento"],
    "Kentucky": ["Columbus", "Greensboro", "Birmingham", "Orlando", "Albany", "Des Moines", "Denver", "Sacramento"],
    "TCU": ["Birmingham", "Des Moines", "Orlando", "Greensboro", "Denver", "Columbus", "Sacramento", "Albany"],
    "Virginia": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "West-Virginia": ["Columbus", "Greensboro", "Albany", "Birmingham", "Orlando", "Des Moines", "Denver", "Sacramento"],
    "Duke": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Michigan-State": ["Des Moines", "Columbus", "Albany", "Birmingham", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Texas-AM": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Denver", "Columbus", "Albany", "Sacramento"],
    "Northwestern": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Missouri": ["Des Moines", "Columbus", "Denver", "Birmingham", "Greensboro", "Albany", "Orlando", "Sacramento"],
    "Illinois": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Miami-FL": ["Orlando", "Birmingham", "Greensboro", "Columbus", "Albany", "Des Moines", "Denver", "Sacramento"],
    "Arkansas": ["Birmingham", "Des Moines", "Greensboro", "Orlando", "Denver", "Columbus", "Albany", "Sacramento"],
    "Maryland": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Auburn": ["Birmingham", "Orlando", "Greensboro", "Columbus", "Des Moines", "Albany", "Denver", "Sacramento"],
    "Boise-State": ["Sacramento", "Denver", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "Memphis": ["Birmingham", "Des Moines", "Greensboro", "Orlando", "Columbus", "Denver", "Albany", "Sacramento"],
    "Oklahoma-State": ["Birmingham", "Des Moines", "Denver", "Orlando", "Greensboro", "Columbus", "Sacramento", "Albany"],
    "Iowa": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Providence": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "USC": ["Sacramento", "Denver", "Des Moines", "Birmingham", "Columbus", "Orlando", "Greensboro", "Albany"],
    "Mississippi-State": ["Birmingham", "Orlando", "Greensboro", "Des Moines", "Columbus", "Albany", "Denver", "Sacramento"],
    "Oral-Roberts": ["Birmingham", "Des Moines", "Denver", "Orlando", "Greensboro", "Columbus", "Sacramento", "Albany"],
    "Nevada": ["Sacramento", "Denver", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "North-Carolina-State": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Wisconsin": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "Texas-Tech": ["Denver", "Birmingham", "Des Moines", "Orlando", "Greensboro", "Columbus", "Sacramento", "Albany"],
    "Penn-State": ["Columbus", "Albany", "Greensboro", "Birmingham", "Orlando", "Des Moines", "Denver", "Sacramento"],
    "Sam-Houston-State": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Denver", "Columbus", "Albany", "Sacramento"],
    "Charleston": ["Greensboro", "Orlando", "Birmingham", "Columbus", "Albany", "Des Moines", "Denver", "Sacramento"],
    "Drake": ["Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando", "Denver", "Sacramento"],
    "VCU": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Kent-State": ["Columbus", "Des Moines", "Greensboro", "Albany", "Birmingham", "Orlando", "Denver", "Sacramento"],
    "Yale": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Louisiana": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Columbus", "Denver", "Albany", "Sacramento"],
    "UC-Irvine": ["Sacramento", "Denver", "Des Moines", "Birmingham", "Columbus", "Orlando", "Greensboro", "Albany"],
    "Kennesaw-State": ["Birmingham", "Orlando", "Greensboro", "Columbus", "Des Moines", "Albany", "Denver", "Sacramento"],
    "Iona": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Montana-State": ["Denver", "Sacramento", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "Vermont": ["Albany", "Columbus", "Greensboro", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Furman": ["Greensboro", "Birmingham", "Orlando", "Columbus", "Albany", "Des Moines", "Denver", "Sacramento"],
    "UNC-Asheville": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Colgate": ["Albany", "Columbus", "Greensboro", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Grambling-State": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Columbus", "Denver", "Albany", "Sacramento"],
    "Cleveland-State": ["Columbus", "Des Moines", "Greensboro", "Albany", "Birmingham", "Orlando", "Denver", "Sacramento"],
    "Howard": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Texas-AM-Corpus-Christi": ["Birmingham", "Orlando", "Des Moines", "Greensboro", "Denver", "Columbus", "Albany", "Sacramento"],
    "Southeast-Missouri": ["Birmingham", "Des Moines", "Greensboro", "Orlando", "Columbus", "Denver", "Albany", "Sacramento"],
    "Fairleigh-Dickinson": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Utah-State": ["Denver", "Sacramento", "Des Moines", "Columbus", "Birmingham", "Albany", "Greensboro", "Orlando"],
    "Norfolk-State": ["Greensboro", "Albany", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
    "Rutgers": ["Albany", "Greensboro", "Columbus", "Orlando", "Birmingham", "Des Moines", "Denver", "Sacramento"],
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
        #TODO: update and make sure all the auto qualifiers are actually being scraped
        extra_scrapes = ["Northern-Kentucky"]
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

    #calculate score for a team's raw number of losses (scale: 1.000 = 0, 0.000 = 10)
    #param team: Team object to calculate score for
    def get_loss_score(self, team):
        if self.verbose:
            print("losses", int(team.record.split("-")[1]))
        team.loss_score = LOSS_WEIGHT*(10-int(team.record.split("-")[1]))/12
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

    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    #param team: Team object to calculate score for
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

    #calculate score for a team's bad (sub-Q1) losses (scale: 1.000 = 0, 0.000 = 5)
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

    #return a nicer-looking representation of a team's name, if one is present
    #param team: string containing a team's name
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
        #TODO: update and make sure teams who have been eliminated and shouldn't be getting automatic bids are not getting them
        eliminated_teams = ["Morehead-State", "Southern-Miss", "Merrimack", "Liberty", "Bradley", "Youngstown-State", "Cleveland-State"]
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            at_large_bid = False
            if self.teams[team].conference in confs_used:
                #teams under .500 are ineligible for at-large bids
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
            print("(" + str(curr_seed) + ") " + self.get_team_out(team), end="")
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

    #get the maximum length of a line when printing the bracket (two team names + their seeds + some buffer)
    #param regions: region dictionaries containing seeded teams
    def get_max_len(self, regions):
        l = []
        for coords in [[0, 1], [3, 2]]:
            for seed in range(1, 17):
                l.append(len(regions[coords[0]][seed]) + len(regions[coords[1]][seed]))
        return 15 + max(l)

    #print a line of the bracket
    #param max_len: maximum length of a line containing two teams
    #param regions: region dictionaries containing seeded teams
    #param region_1: 0 or 3, corresponding to one of the regions on the left side of the bracket
    #param region_2: 1 or 2, corresponding to one of the regions on the right side of the bracket
    #param seed: seed of the teams to print
    #param region_num_to_name: dictionary to translate a region's number to its location
    #param first_weekend_name_to_num: dictionary to translate a first weekend site's location to its coordinates (two possibilities)
    #param first_weekend_num_to_name: dictionary to translate a first weekend site's coordinates to its location
    def print_line(self, max_len, regions, region_1, region_2, seed, region_num_to_name, first_weekend_name_to_num, first_weekend_num_to_name):
        team_1 = self.get_team_out(regions[region_1][seed])
        team_2 = self.get_team_out(regions[region_2][seed])
        if (seed == 16) or ("/" not in team_1 and self.teams[regions[region_1][seed]].auto_bid):
            team_1 += "*"
        if (seed == 16) or ("/" not in team_2 and self.teams[regions[region_2][seed]].auto_bid):
            team_2 += "*"
        max_site_len = max([len(x) for x in first_weekend_name_to_num])
        print(" "*max_site_len + "(" + str(seed) + ") " + team_1 + \
                " "*(max_len - (len(team_1) + len(team_2)) - (len(str(seed)) + 3)*2) + \
                " (" + str(seed) + ") " + team_2)
        if seed == 13:
            region_1_name = region_num_to_name[region_1]
            region_2_name = region_num_to_name[region_2]
            print(" "*(20 + max_site_len) + region_1_name + " "*(max_len - (len(region_1_name) + len(region_2_name) + 40)) + region_2_name)
        elif seed == 16:
            site_1 = first_weekend_num_to_name[region_1][1]
            site_2 = first_weekend_num_to_name[region_2][1]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 12: 
            site_1 = first_weekend_num_to_name[region_1][4]
            site_2 = first_weekend_num_to_name[region_2][4]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 11: 
            site_1 = first_weekend_num_to_name[region_1][3]
            site_2 = first_weekend_num_to_name[region_2][3]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 10:
            site_1 = first_weekend_num_to_name[region_1][2]
            site_2 = first_weekend_num_to_name[region_2][2]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        else:
            print()

    #check if placing a team in a particular bracket location will follow all the rules
    #param regions: region dictionaries containing seeded teams
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    #param team: name of team to attempt to place
    #param region_num: region number (0-3) to try to place the team in
    #param seed_num: seed number (1-16) to try to place the team in
    def check_rules(self, regions, conferences, team, region_num, seed_num):
        if team == "":
            return True
        team_conference = self.teams[team].conference

        #the top three teams from a conference must be in different regions
        if conferences[team_conference].index(team) < 3:
            for test_team in conferences[team_conference][:3]:
                if test_team == team:
                    continue
                if self.teams[test_team].region == region_num:
                    if self.verbose:
                        print("multiple top three teams can't all go here", region_num, conferences[team_conference])
                    return False

        #unless there are nine teams from a conference, three teams from that conference cannot be in the same region
        if len(conferences[team_conference]) < 9:
            team_conf_counter = 0
            for test_team in conferences[team_conference]:
                if test_team == team:
                    continue
                if self.teams[test_team].region == region_num:
                    team_conf_counter += 1
                if team_conf_counter >= 2:
                    if self.verbose:
                        print("three top eight teams can't all go here", region_num, conferences[team_conference])
                    return False

        #unless a conference has 5 teams seeded 1-4, all teams from a conference seeded 1-4 must be in different regions
        if len(conferences[team_conference]) < 5 and seed_num <= 4:
            for test_team in conferences[team_conference]:
                if test_team == team:
                    continue
                if self.teams[test_team].seed >= 5:
                    break
                if self.teams[test_team].region == region_num:
                    if self.verbose:
                        print("multiple top 4 seed teams can't go here", region_num, conferences[team_conference])
                    return False

        #two teams from the same conference cannot meet before the regional semifinal (Sweet 16)
        for test_team in conferences[team_conference]:
            if test_team == team:
                continue
            if self.teams[test_team].region == region_num and \
                    (self.teams[test_team].seed + seed_num == 17 or self.teams[test_team].seed + seed_num == 9 or \
                    self.teams[test_team].seed + seed_num == 25 or abs(self.teams[test_team].seed - seed_num) == 8 or \
                    self.teams[test_team].seed == seed_num):
                if self.verbose:
                    print("teams are meeting too early in this region", region_num, conferences[team_conference])
                return False
        return True

    #remove all teams from their seed lines in order to attempt to reorganize them
    #param regions: region dictionaries containing seeded teams
    #param seed_num: seed number to delete
    def delete_and_save_seed(self, regions, seed_num, first_weekend_num_to_name):
        teams_to_fix = list()
        sites = list()
        for region_num, region in enumerate(regions):
            if seed_num in region:
                save_team = region[seed_num]
                teams_to_fix.append(save_team)
                self.teams[save_team].region = -1
                self.teams[save_team].seed = -1
                del region[seed_num]
                if seed_num < 5:
                    if seed_num in first_weekend_num_to_name[region_num]:
                        sites.append(tuple([save_team, region_num, first_weekend_num_to_name[region_num][seed_num]]))
                        del first_weekend_num_to_name[region_num][seed_num]
        #if the seed wasn't fully filled out, put placeholders in
        while len(teams_to_fix) < 4:
            teams_to_fix.append("")
        return teams_to_fix, sites

    #check a permutation of four teams to see if the bracket can accept it
    #param regions: region dictionaries containing seeded teams
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    #param perm: permutation of four teams on the same seed line
    #param seed_num: seed of teams
    def check_perm(self, regions, conferences, perm, seed_num):
        if self.check_rules(regions, conferences, perm[0], 0, seed_num) and \
            self.check_rules(regions, conferences, perm[1], 1, seed_num) and \
            self.check_rules(regions, conferences, perm[2], 2, seed_num) and \
            self.check_rules(regions, conferences, perm[3], 3, seed_num):
            return True
    
    #insert a permutation of four teams into the bracket
    #param regions: region dictionaries containing seeded teams
    #param seed_num: seed of teams
    #param perm: permutation of four teams on the same seed line
    def save_and_print_perm(self, regions, seed_num, perm, first_weekend_num_to_name, first_weekend_name_to_num, sites):
        for region_num in range(0, 4):
            if not perm[region_num]:
                if seed_num in first_weekend_num_to_name[region_num]:
                    del first_weekend_num_to_name[region_num][seed_num]
                continue
            regions[region_num][seed_num] = perm[region_num]
            self.teams[perm[region_num]].region = region_num
            self.teams[perm[region_num]].seed = seed_num
            if seed_num < 5:
                for team_site in sites:
                    if team_site[0] == perm[region_num]:
                        first_weekend_num_to_name[region_num][seed_num] = team_site[2]
                        first_weekend_name_to_num[team_site[2]][first_weekend_name_to_num[team_site[2]].index([team_site[1], seed_num])] = [region_num, seed_num]
            if self.verbose:
                print("Placed (" + str(seed_num) + ") " + perm[region_num] + ": region (" + str(region_num) + ")")

    #return a list of a team's regional preferences
    #param team: string of team to get preferences for
    #param seed_num: seed of team. if higher (i.e. lower number) than 5, use regional sites; otherwise, use first-weekend sites
    #param region_name_to_num: dictionary to translate region sites to coordinate
    #param first_weekend_num_to_name: dictionary to translate first weekend site coordinates to locations
    def get_region_order(self, team, seed_num, region_name_to_num, first_weekend_num_to_name):
        order = list()
        if seed_num < 5:
            for site in region_rankings[team]:
                order.append(region_name_to_num[site])
        else:
            #construct list of possible sites
            possible_sites = list()
            if seed_num in [16, 8, 9]:
                host_seed = 1
            elif seed_num in [5, 12, 13]:
                host_seed = 4
            elif seed_num in [6, 11, 14]:
                host_seed = 3
            elif seed_num in [7, 10, 15]:
                host_seed = 2
            for index, region in enumerate(first_weekend_num_to_name):
                possible_sites.append(region[host_seed])
            for site in first_weekend_rankings[team]:
                while site in possible_sites:
                    order.append(possible_sites.index(site))
                    possible_sites[possible_sites.index(site)] = ""
        return order

    def place_and_print_play_in_team(self, region, seed_num, team, region_num):
        region[seed_num] = region[seed_num] + "/" + team
        self.teams[team].region = region_num
        self.teams[team].seed = seed_num
        if self.verbose:
            print("Placed (" + str(seed_num) + ") " + team + ": region (" + str(region_num) + ")")

    def build_bracket(self):
        regions = [dict(), dict(), dict(), dict()]
        region_num_to_name = dict()
        region_name_to_num = dict()
        first_weekend_num_to_name = [dict(), dict(), dict(), dict()]
        first_weekend_name_to_num = dict()
        auto_count = 0
        at_large_count = 0
        bracket_pos = 1
        conferences = dict()
        play_in_teams = list()
        play_in_pos = ()
        first_weekend_sites = ["Birmingham", "Birmingham", "Orlando", "Orlando", "Greensboro", "Greensboro", "Albany", "Albany", \
                "Columbus", "Columbus", "Des Moines", "Des Moines", "Denver", "Denver", "Sacramento", "Sacramento"]

        #traverse seed list, placing teams in bracket as you go
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            team_conference = self.teams[team].conference
            if not (self.teams[team].auto_bid or self.teams[team].at_large_bid):
                continue
            if team_conference not in conferences:
                conferences[team_conference] = list()
            conferences[team_conference].append(team)
            seed_num = (bracket_pos + 3) // 4
            if seed_num > 1:
                region_order = self.get_region_order(team, seed_num, region_name_to_num, first_weekend_num_to_name)
                region_num = region_order[0]
            else:
                region_num = bracket_pos - 1

            #get a region that is empty for the current seed
            while seed_num in regions[region_num]:
                if self.teams[team].at_large_bid and (at_large_count == AT_LARGE_MAX - 3 or at_large_count == AT_LARGE_MAX - 1):
                    break
                elif self.teams[team].auto_bid and (auto_count == AUTO_MAX - 3 or auto_count == AUTO_MAX - 1):
                    break
                if seed_num > 1:
                    region_num = region_order[region_order.index(region_num)+1]
                else:
                    region_num = (region_num + 1) % 4
            region = regions[region_num]

            #if this is the second team in a play in game, just place them. (TODO: fix)
            if self.teams[team].at_large_bid and (at_large_count == AT_LARGE_MAX - 3 or at_large_count == AT_LARGE_MAX - 1):
                region_num = play_in_pos[0]
                seed = play_in_pos[1]
                at_large_count += 1
                self.place_and_print_play_in_team(regions[play_in_pos[0]], play_in_pos[1], team, region_num)
            elif self.teams[team].auto_bid and (auto_count == AUTO_MAX - 3 or auto_count == AUTO_MAX - 1):
                region_num = play_in_pos[0]
                seed = play_in_pos[1]
                auto_count += 1
                self.place_and_print_play_in_team(regions[play_in_pos[0]], play_in_pos[1], team, region_num)

            #if this is a normal bid, follow the rules to place the team in the bracket
            else:
                bad_regions = set()
                check_switch = False
                orig_region_num = region_num
                
                #if this placement didn't pass the rules, try more options
                while not self.check_rules(regions, conferences, team, region_num, seed_num):
                    if self.verbose:
                        print('rules failed for', str(region_num))
                    bad_regions.add(region_num)
                    region_num = region_order[(region_order.index(region_num)+1) % 4]
                    if self.verbose:
                        print('edited region to', region_num)

                    #find a region that doesn't have this seed in it (or, if switching is on, try to switch that team for current team)
                    while seed_num in regions[region_num]:
                        if self.verbose:
                            print('already this seed in', str(region_num))
                        new_team = regions[region_num][seed_num]
                        if check_switch and self.check_rules(regions, conferences, team, region_num, seed_num) and \
                                self.check_rules(regions, conferences, new_team, orig_region_num, seed_num):
                            regions[orig_region_num][seed_num] = new_team
                            self.teams[new_team].region = orig_region_num
                            if seed_num < 5:
                                site = first_weekend_num_to_name[region_num][seed_num]
                                first_weekend_num_to_name[orig_region_num][seed_num] = site
                                del first_weekend_num_to_name[region_num][seed_num]
                                first_weekend_name_to_num[site][first_weekend_name_to_num[site].index([region_num, seed_num])] = [orig_region_num, seed_num]
                            if self.verbose:
                                print("Switched (" + str(seed_num) + ") " + new_team + " to: region (" + str(orig_region_num) + ")")
                            bad_regions = set()
                            break

                        #if we've tried every region, try something else
                        bad_regions.add(region_num)
                        if len(bad_regions) == 4:
                            break
                        region_num = region_order[(region_order.index(region_num)+1) % 4]
                        if self.verbose:
                            print('changed region to', region_num)

                    #if we haven't tried to switch teams yet, try that
                    if len(bad_regions) == 4 and check_switch == False:
                        check_switch = True
                        if self.verbose:
                            print('turned switch on')
                        bad_regions = set()
                        region_num = orig_region_num
                        continue

                    #if we have tried to switch teams, try every permutation for the current seed
                    if len(bad_regions) == 4 and check_switch == True:
                        if self.verbose:
                            print("can't make just one switch to fix this. Let's try to brute force it.")
                        reorg_seed = seed_num
                        teams_to_fix, sites = self.delete_and_save_seed(regions, seed_num, first_weekend_num_to_name)
                        if team not in teams_to_fix:
                            teams_to_fix[-1] = team
                        self.teams[team].region = -1
                        self.teams[team].seed = -1
                        found_perm = False
                        for perm in permutations(teams_to_fix):
                            if self.check_perm(regions, conferences, perm, seed_num):
                                self.save_and_print_perm(regions, seed_num, perm, first_weekend_num_to_name, first_weekend_name_to_num, sites)
                                found_perm = True
                                break

                        #if no permutation works, work backward through the seed list trying every permutation of those seeds as well as ours
                        tries = 0
                        while not found_perm:
                            curr_reorg_max = 5
                            reorg_seed -= 1
                            if reorg_seed < curr_reorg_max:
                                tries += 1
                                if tries <= 50:
                                    #don't want to mess up region positioning if possible
                                    if self.verbose:
                                        print("Retrying from beginning")
                                    reorg_seed = seed_num - 1
                                else:
                                    tries = 0
                                    curr_reorg_max -= 1
                            if self.verbose:
                                print('trying the next seed up', reorg_seed)
                            other_teams_to_fix, other_sites = self.delete_and_save_seed(regions, reorg_seed, first_weekend_num_to_name)
                            perm_to_save = list()
                            for other_perm in permutations(other_teams_to_fix):
                                if self.check_perm(regions, conferences, other_perm, reorg_seed):
                                    self.save_and_print_perm(regions, reorg_seed, other_perm, first_weekend_num_to_name, first_weekend_name_to_num, other_sites)
                                    perm_to_save = other_perm
                                    for perm in permutations(teams_to_fix):
                                        if self.check_perm(regions, conferences, perm, seed_num):
                                            self.save_and_print_perm(regions, seed_num, perm, first_weekend_num_to_name, first_weekend_name_to_num, sites)
                                            region_num = perm.index(team)
                                            found_perm = True
                                            break
                                    if found_perm:
                                        break
                            if not found_perm:
                                #if nothing worked, save the most recent successful try for this seed and recurse up the seed list
                                #this also allows us to loop back through the seeds and have different results
                                self.save_and_print_perm(regions, reorg_seed, perm_to_save, first_weekend_num_to_name, first_weekend_name_to_num, other_sites)

                regions[region_num][seed_num] = team
                self.teams[team].region = region_num
                self.teams[team].seed = seed_num
                if self.teams[team].auto_bid:
                    auto_count += 1
                if self.teams[team].at_large_bid:
                    at_large_count += 1

                #if we're placing the top seed, pick a regional site for it
                if seed_num == 1:
                    for site_name in region_rankings[team]:
                        if site_name not in region_name_to_num:
                            region_name_to_num[site_name] = region_num
                            region_num_to_name[region_num] = site_name
                            if self.verbose:
                                print(site_name, "chosen for", region_num)
                            break

                #if we're placing a top-4 seed, pick a first weekend site for it
                if seed_num < 5:
                    for site_name in first_weekend_rankings[team]:
                        if site_name in first_weekend_sites:
                            if self.verbose:
                                print("Choosing", site_name)
                            first_weekend_sites.remove(site_name)
                            if site_name in first_weekend_name_to_num:
                                first_weekend_name_to_num[site_name].append([region_num, seed_num])
                            else:
                                first_weekend_name_to_num[site_name] = [[region_num, seed_num]]
                            first_weekend_num_to_name[region_num][seed_num] = site_name
                            break
                if self.verbose:
                    print("Placed (" + str(seed_num) + ") " + team + ": region (" + str(region_num) + ") " + region_num_to_name[region_num])
                    print()

            #if we just placed the first play in team, save its coordinates
            if (self.teams[team].at_large_bid and (at_large_count == AT_LARGE_MAX - 3 or at_large_count == AT_LARGE_MAX - 1)) or \
                    (self.teams[team].auto_bid and (auto_count == AUTO_MAX - 3 or auto_count == AUTO_MAX - 1)):
                play_in_pos = (region_num, seed_num)
            else:
                bracket_pos += 1
                play_in_pos = (0, 0)
        max_len = self.get_max_len(regions)
        print()
        for region_nums in [[0, 1], [3, 2]]:
            for seed_num in [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]:
                self.print_line(max_len, regions, region_nums[0], region_nums[1], seed_num, \
                        region_num_to_name, first_weekend_name_to_num, first_weekend_num_to_name)

    #write all team scores for each category to specified file
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
    scraper.build_bracket()
    if outputfile:
        scraper.output_scores()

