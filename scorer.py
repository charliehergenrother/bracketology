#!/usr/bin/env python3

from team import SELECTION_SUNDAY_DATES
import sys
import math
import requests
import os
from datetime import date
import json

WEIGHTS = {
        "LOSS_WEIGHT": 0,
        "NET_WEIGHT": 0,
        "POWER_WEIGHT": 0,
        "Q1_WEIGHT": 0,
        "Q2_WEIGHT": 0,
        "Q3_WEIGHT": 0,
        "Q4_WEIGHT": 0,
        "ROAD_WEIGHT": 0,
        "NEUTRAL_WEIGHT": 0,
        "TOP_10_WEIGHT": 0,
        "TOP_25_WEIGHT": 0,
        "SOS_WEIGHT": 0,
        "NONCON_SOS_WEIGHT": 0,
        "AWFUL_LOSS_WEIGHT": 0,
        "BAD_LOSS_WEIGHT": 0
}

SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_MEN_URL_START = "https://www.warrennolan.com/basketball/2024/team-clubhouse?team="
TEAM_WOMEN_URL_START = "https://www.warrennolan.com/basketballw/2024/team-clubhouse?team="

#class to generate resume ratings from scraped data about college basketball teams
class Scorer:

    def __init__(self, builder, f, m, t, mc):
        self.teams = builder.teams
        self.verbose = builder.verbose
        self.year = builder.year
        self.future = f
        self.mens = m
        self.tracker = t
        self.monte_carlo = mc
        if self.mens:
            self.schedule_datadir = "data/men/" + self.year + "/schedules/"
        else:
            self.schedule_datadir = "data/women/" + self.year + "/schedules/"
        return

    #sanity check to make sure my weights are added correctly
    def sum_weights(self):
        s = round(sum([\
            round(WEIGHTS["LOSS_WEIGHT"], 5), \
            round(WEIGHTS["NET_WEIGHT"], 5), \
            round(WEIGHTS["POWER_WEIGHT"], 5), \
            round(WEIGHTS["Q1_WEIGHT"], 5), \
            round(WEIGHTS["Q2_WEIGHT"], 5), \
            round(WEIGHTS["Q3_WEIGHT"], 5), \
            round(WEIGHTS["Q4_WEIGHT"], 5), \
            round(WEIGHTS["ROAD_WEIGHT"], 5), \
            round(WEIGHTS["NEUTRAL_WEIGHT"], 5), \
            round(WEIGHTS["TOP_10_WEIGHT"], 5), \
            round(WEIGHTS["TOP_25_WEIGHT"], 5), \
            round(WEIGHTS["SOS_WEIGHT"], 5), \
            round(WEIGHTS["NONCON_SOS_WEIGHT"], 5), \
            round(WEIGHTS["AWFUL_LOSS_WEIGHT"], 5), \
            round(WEIGHTS["BAD_LOSS_WEIGHT"], 5) \
            ]), 5)
        if s != 1:
            print(s)
            print("ya dun goofed with your weights")
            sys.exit()

    def kenpom_estimate(self, rank):
        return -0.0000026505*rank*rank*rank + 0.0015329*rank*rank - 0.349987*rank + 27.803

    def get_quadrant(self, opp_NET, location):
        if location == "H":
            if opp_NET <= 30:
                return 1
            elif opp_NET <= 75:
                return 2
            elif opp_NET <= 160:
                return 3
            return 4
        elif location == "A":
            if opp_NET <= 75:
                return 1
            elif opp_NET <= 135:
                return 2
            elif opp_NET <= 260:
                return 3
            return 4
        elif location == "N":
            if opp_NET <= 50:
                return 1
            elif opp_NET <= 100:
                return 2
            elif opp_NET <= 200:
                return 3
            return 4
        else:
            return "problems have arisen"

    #calculate score for a team's raw number of losses (scale: 1.000 = 0, 0.000 = 10)
    #param team: Team object to calculate score for
    def get_loss_score(self, team):
        if self.tracker:
            try:
                return team.loss_score
            except AttributeError:
                pass
        return self.calculate_loss_score(team)

    def calculate_loss_score(self, team):
        num_losses = int(team.record.split("-")[1])
        if self.future:
            for game in team.future_games:
                num_losses += (1 - game['win_prob'])
        team.loss_score = (10-num_losses)/10
        return team.loss_score

    #calculate score for a team's NET rank  (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_NET_score(self, team):
        if self.tracker:
            try:
                return team.NET_score
            except AttributeError:
                pass
        return self.calculate_NET_score(team)

    def calculate_NET_score(self, team):
        team.NET_score = (-math.log(team.NET + 19, 2)/2 + 3.16)#(60-team.NET)/59
        return team.NET_score

    #calculate score for a team's predictive rating (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_power_score(self, team, team_kenpom=0):
        if self.tracker:
            try:
                return team.power_score
            except AttributeError:
                pass
        return self.calculate_power_score(team, team_kenpom)

    def calculate_power_score(self, team, team_kenpom=0):
        if self.monte_carlo:
            est_rank = (team_kenpom - 33)*(team_kenpom - 33)/5
            team.power_score = (-math.log(est_rank + 19, 2)/2 + 3.16)
        else:
            team.power_score = (-math.log(team.predictive + 19, 2)/2 + 3.16)#(60-team.predictive)/59
        return team.power_score

    #calculate score for a team's record in quadrant 1 (scale: 0.800 = 1, 0.000 = .000)
    #param team: Team object to calculate score for
    def get_Q1_score(self, team):
        if self.tracker:
            try:
                return team.Q1_score
            except AttributeError:
                pass
        return self.calculate_Q1_score(team)

    def calculate_Q1_score(self, team):
        if self.future:
            Q1_record = team.get_derived_record(1)
            wins = int(Q1_record.split("-")[0])
            losses = int(Q1_record.split("-")[1])
            for game in team.future_games:
                game_quad = self.get_quadrant(game['NET'], game['location'])
                if game_quad == 1:
                    wins += game['win_prob']
                losses += (1 - game['win_prob'])
            team.Q1_score = (wins/(wins + losses))/0.8
        else:
            team.Q1_score = (team.get_derived_pct(1)/0.8)
        return team.Q1_score

    #calculate score for a team's record in quadrant 2 (scale: 1.000 = 1, 0.000 = .500)
    #param team: Team object to calculate score for
    def get_Q2_score(self, team):
        if self.tracker:
            try:
                return team.Q2_score
            except AttributeError:
                pass
        return self.calculate_Q2_score(team)

    def calculate_Q2_score(self, team):
        if self.future:
            Q2_record = team.get_derived_record(2)
            wins = int(Q2_record.split("-")[0])
            losses = int(Q2_record.split("-")[1])
            for game in team.future_games:
                game_quad = self.get_quadrant(game['NET'], game['location'])
                if game_quad <= 2:
                    wins += game['win_prob']
                if game_quad >= 2:
                    losses += (1 - game['win_prob'])
            team.Q2_score = ((wins/(wins + losses))-0.5)/0.5
        else:
            team.Q2_score = (team.get_derived_pct(2)-0.5)/0.5
        return team.Q2_score

    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    #param team: Team object to calculate score for
    def get_Q3_score(self, team):
        if self.tracker:
            try:
                return team.Q3_score
            except AttributeError:
                pass
        return self.calculate_Q3_score(team)

    def calculate_Q3_score(self, team):
        if self.future:
            Q3_record = team.get_derived_record(3)
            wins = int(Q3_record.split("-")[0])
            losses = int(Q3_record.split("-")[1])
            for game in team.future_games:
                game_quad = self.get_quadrant(game['NET'], game['location'])
                if game_quad <= 3:
                    wins += game['win_prob']
                if game_quad >= 3:
                    losses += (1 - game['win_prob'])
            team.Q3_score = ((wins/(wins + losses))-0.8)/0.2
        else:
            team.Q3_score = (team.get_derived_pct(3)-0.8)/0.2
        return team.Q3_score

    #calculate score for a team's record in quadrant 4 (scale: 1.000 = 1, 0.000 = .950)
    #param team: Team object to calculate score for
    def get_Q4_score(self, team):
        if self.tracker:
            try:
                return team.Q4_score
            except AttributeError:
                pass
        return self.calculate_Q4_score(team)

    def calculate_Q4_score(self, team):
        if self.future:
            Q4_record = team.get_derived_record(4)
            wins = int(Q4_record.split("-")[0])
            losses = int(Q4_record.split("-")[1])
            for game in team.future_games:
                game_quad = self.get_quadrant(game['NET'], game['location'])
                wins += game['win_prob']
                if game_quad == 4:
                    losses += (1 - game['win_prob'])
            team.Q4_score = ((wins/(wins + losses))-0.95)/0.05
        else:
            if team.get_derived_pct(4) >= 0.95:
                team.Q4_score = (team.get_derived_pct(4)-0.95)/0.05
            else:   #limit how bad multiple Q4 losses can hurt you
                team.Q4_score = (team.get_derived_pct(4)-0.95)/0.3
        return team.Q4_score

    #calculate score for a team's road wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
    #param team: Team object to calculate score for
    def get_road_score(self, team):
        if self.tracker:
            try:
                return team.road_score
            except AttributeError:
                pass
        return self.calculate_road_score(team)

    def calculate_road_score(self, team):
        good_road_wins = 0
        for game in team.games:
            if game.margin > 0 and game.location == "A":
                if game.opp_NET <= 50:
                    good_road_wins += 1
                elif game.opp_NET <= 100:
                    good_road_wins += (100 - game.opp_NET)/50
        if self.future:
            for game in team.future_games:
                if game['location'] == "A":
                    opp_NET = game['NET']
                    if opp_NET <= 50:
                        good_road_wins += game['win_prob']
                    elif opp_NET <= 100:
                        good_road_wins += (100 - opp_NET)*game['win_prob']/50
        team.road_score = good_road_wins/5
        return team.road_score

    #calculate score for a team's neutral court wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_neutral_score(self, team):
        if self.tracker:
            try:
                return team.neutral_score
            except AttributeError:
                pass
        return self.calculate_neutral_score(team)

    def calculate_neutral_score(self, team):
        good_neutral_wins = 0
        for game in team.games:
            if game.margin > 0 and game.location == "N":
                conf_tourn_multiplier = 1
                date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                if date_month == 3:
                    if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                        conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                if game.opp_NET <= 50:
                    good_neutral_wins += conf_tourn_multiplier * 1
                elif game.opp_NET <= 100:
                    good_neutral_wins += conf_tourn_multiplier * (100 - game.opp_NET)/50
        if self.future:
            for game in team.future_games:
                if game['location'] == "N":
                    opp_NET = game['NET']
                    if opp_NET <= 50:
                        good_neutral_wins += game['win_prob']
                    elif opp_NET <= 100:
                        good_neutral_wins += (100 - opp_NET)*game['win_prob']/50
        team.neutral_score = good_neutral_wins/5
        return team.neutral_score

    #calculate score for a team's top 10 wins (scale: 1.000 = 3, 0.000 = 0)
        #sliding scale. #1-#5: full win. #6-#14: decreases win count by 0.1 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_top10_score(self, team):
        if self.tracker:
            try:
                return team.top10_score
            except AttributeError:
                pass
        return self.calculate_top10_score(team)

    def calculate_top10_score(self, team):
        top_10_wins = 0
        for game in team.games:
            if game.margin > 0:
                conf_tourn_multiplier = 1
                date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                if date_month == 3:
                    if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                        conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                if game.opp_NET <= 5:
                    top_10_wins += conf_tourn_multiplier * 1
                elif game.opp_NET <= 15:
                    top_10_wins += conf_tourn_multiplier * (15 - game.opp_NET)/10
        if self.future:
            for game in team.future_games:
                opp_NET = game['NET']
                if opp_NET <= 5:
                    top_10_wins += game['win_prob']
                elif opp_NET <= 15:
                    top_10_wins += (15 - opp_NET)*game['win_prob']/10
        team.top10_score = top_10_wins/3
        return team.top10_score

    #calculate score for a team's top 25 wins (Quad 1A) (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. Quad 1A is 1-15 (H), 1-25 (N), 1-40 (A). win count decreases by 0.1 for each rank down when within 5 of end.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_top25_score(self, team):
        if self.tracker:
            try:
                return team.top25_score
            except AttributeError:
                pass
        return self.calculate_top25_score(team)

    def calculate_top25_score(self, team):
        top_25_wins = 0
        for game in team.games:
            if game.margin > 0:
                conf_tourn_multiplier = 1
                date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                if date_month == 3:
                    if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                        conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                if game.location == "H":
                    if game.opp_NET <= 10:
                        top_25_wins += conf_tourn_multiplier * 1
                    elif game.opp_NET <= 20:
                        top_25_wins += conf_tourn_multiplier * (20 - game.opp_NET)/10
                elif game.location == "N":
                    if game.opp_NET <= 20:
                        top_25_wins += conf_tourn_multiplier * 1
                    elif game.opp_NET <= 30:
                        top_25_wins += conf_tourn_multiplier * (30 - game.opp_NET)/10
                elif game.location == "A":
                    if game.opp_NET <= 35:
                        top_25_wins += conf_tourn_multiplier * 1
                    elif game.opp_NET <= 45:
                        top_25_wins += conf_tourn_multiplier * (45 - game.opp_NET)/10
        if self.future:
            for game in team.future_games:
                opp_NET = game['NET']
                if game['location'] == "H":
                    if opp_NET <= 10:
                        top_25_wins += game['win_prob']
                    elif opp_NET <= 20:
                        top_25_wins += game['win_prob'] * (20 - opp_NET)/10
                elif game['location'] == "N":
                    if opp_NET <= 20:
                        top_25_wins += game['win_prob']
                    elif opp_NET <= 30:
                        top_25_wins += game['win_prob'] * (30 - opp_NET)/10
                elif game['location'] == "A":
                    if opp_NET <= 35:
                        top_25_wins += game['win_prob']
                    elif opp_NET <= 45:
                        top_25_wins += game['win_prob'] * (45 - opp_NET)/10
        team.top25_score = top_25_wins/5
        return team.top25_score

    #calculate score for a team's strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_SOS_score(self, team):
        try:
            return team.SOS_score
        except AttributeError:
            team.SOS_score = (151 - team.NET_SOS)/150
            return team.SOS_score

    #calculate score for a team's nonconference strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_NCSOS_score(self, team):
        try:
            return team.NCSOS_score
        except AttributeError:
            if team.noncon_SOS < 151:
                team.NCSOS_score = (151 - team.noncon_SOS)/150
            else:   #limit how bad a really bad noncon schedule can hurt you
                team.NCSOS_score = (151 - team.noncon_SOS)/450
            return team.NCSOS_score

    #calculate score for a team's awful (NET > 200) losses (scale: 1.000 = 0, 0.000 = 1)
        #sliding scale. loss count increases by 0.02 for each rank down past 175. #225 and worse are a full loss.
    #param team: Team object to calculate score for
    def get_awful_loss_score(self, team):
        if self.tracker:
            try:
                return team.awful_loss_score
            except AttributeError:
                pass
        return self.calculate_awful_loss_score(team)

    def calculate_awful_loss_score(self, team):
        awful_losses = 0
        for game in team.games:
            if game.margin < 0:
                if game.opp_NET > 225:
                    awful_losses += 1
                elif game.opp_NET > 175:
                    awful_losses += (game.opp_NET - 175)/50
        if self.future:
            for game in team.future_games:
                opp_NET = game['NET']
                if opp_NET > 225:
                    awful_losses += (1 - game['win_prob'])
                elif opp_NET > 175:
                    awful_losses += (opp_NET - 175)*(1 - game['win_prob'])/50
        team.awful_loss_score = (1 - awful_losses)
        return team.awful_loss_score

    #calculate score for a team's bad (sub-Q1) losses (scale: 1.000 = 0, 0.000 = 5)
    #param team: Team object to calculate score for
    def get_bad_loss_score(self, team):
        if self.tracker:
            try:
                return team.bad_loss_score
            except AttributeError:
                pass
        return self.calculate_bad_loss_score(team)

    def calculate_bad_loss_score(self, team):
        bad_losses = 0
        bad_losses += int(team.Q2_record.split("-")[1])
        bad_losses += int(team.Q3_record.split("-")[1])
        bad_losses += int(team.Q4_record.split("-")[1])
        if self.future:
            for game in team.future_games:
                game_quad = self.get_quadrant(game['NET'], game['location'])
                if game_quad >= 2:
                    bad_losses += (1 - game['win_prob'])
        team.bad_loss_score = (1 - bad_losses/5)
        return team.bad_loss_score
    
    def get_weights(self, weightfile):
        with open(weightfile, "r") as f:
            for line in f.read().split("\n"):
                if not line:
                    continue
                weight_name, weight_val = line.split(" = ")
                WEIGHTS[weight_name] = float(weight_val)
        return WEIGHTS

    def get_win_prob(self, spread):
        if abs(spread) <= 21:
            return -0.00002609*spread*spread*spread + 0.00002466*spread*spread + 0.033206*spread + 0.5
        elif spread > 21:
            return 0.98
        elif spread < -21:
            return 0.02

    def get_NET_estimate(self, curr_NET, curr_KenPom):
        NET_weight = 0.65
        NET_estimate = (NET_weight*curr_NET) + (1 - NET_weight)*curr_KenPom
        return NET_estimate

    def load_schedule(self, team):
        if not os.path.exists(self.schedule_datadir):
            print("creating schedules dir")
            os.makedirs(self.schedule_datadir)
        if not os.path.exists(self.schedule_datadir + SCRAPE_DATE_FILE):
            f = open(self.schedule_datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(self.schedule_datadir + SCRAPE_DATE_FILE, "r+")
        today_date = date.today().strftime("%m-%d")    #format: mm-dd
        saved_date = f.read().strip()
        f.close()
        if today_date != saved_date:
            self.teams[team].future_games = self.do_schedule_scrape(team)
            print("scraped", team, "schedule!")
        else:
            self.do_schedule_load(team)

    def do_schedule_load(self, team):
        filename = team + ".json"
        f = open(self.schedule_datadir + filename, "r")
        sched_obj = json.loads(f.read())
        self.teams[team].future_games = sched_obj

    def get_spread(self, team_kenpom, opp_kenpom, location):
        team_spread_neutral = team_kenpom - opp_kenpom
        if location == 'H':
            team_spread = team_spread_neutral + 3
        elif location == 'N':
            team_spread = team_spread_neutral
        elif location == 'A':
            team_spread = team_spread_neutral - 3
        return team_spread

    def do_schedule_scrape(self, team):
        month_translations = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06", \
                "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}
        if self.mens:
            schedule_url = TEAM_MEN_URL_START + team
        else:
            schedule_url = TEAM_WOMEN_URL_START + team
        schedule_page = requests.get(schedule_url)
        table_start = False
        schedule_games = list()
        found_game = False
        found_result = False
        found_location = False
        if self.mens:
            team_kenpom = self.kenpom_estimate(self.teams[team].KenPom)
        else:
            team_kenpom = self.kenpom_estimate(self.teams[team].NET)    #crude, but all I've got
        for line in schedule_page.text.split("\n"):
            if not table_start:
                if 'team-schedule' in line:
                    table_start = True
                continue
            if "team-schedule__game-date--month" in line:
                game = dict()
                month = line[line.find("month")+7:line.find("</span>")]
                game["date"] = month_translations[month]
            elif "team-schedule__game-date--day" in line:
                game["date"] += "-" + line[line.find("day")+5:line.find("</span>")]
            elif "team-schedule__location" in line:
                found_location = True
            elif found_location:
                if "VS" in line:
                    game["location"] = "N"
                elif "AT" in line:
                    game["location"] = "A"
                else:
                    game["location"] = "H"
                found_location = False
            elif "images" in line and "conf-logo" not in line and "NA3" not in line:
                found_game = True
                opp_name = line[line.find("80x80")+6:line.find(".png")]
                game["opponent"] = opp_name
            elif "team-schedule__info-tv" in line:
                game["channel"] = line[line.find("TV: ")+4:line.find("</span>")]
            elif found_game:
                if found_result:
                    if "team-schedule__result" not in line:     # game is in the future
                        game["time"] = line[line.find('>')+1:line.find("</span>")]
                        if ":" in game["time"]:
                            game["time"] = str(int(game["time"].split(":")[0])-1) + ":" + game["time"].split(":")[1]
                            if game["time"][0] == "0":
                                game["time"] = "12" + game["time"][1:]
                            if game["time"][:2] == "11" and "PM" in game["time"]:
                                game["time"] = game["time"].replace("PM", "AM")
                        else:   #game time TBA
                            game["time"] = "0:00"
                        if self.mens:
                            opp_kenpom = self.kenpom_estimate(self.teams[game['opponent']].KenPom)
                        else:
                            opp_kenpom = self.kenpom_estimate(self.teams[game['opponent']].NET)
                        team_spread = self.get_spread(team_kenpom, opp_kenpom, game['location'])
                        game['win_prob'] = self.get_win_prob(team_spread)
                        schedule_games.append(game)
                    found_result = False
                    found_game = False
                elif "opp-record-line" in line:
                    curr_NET = int(line[line.find("NET")+5:line.find("</span></span>")])
                    game["NET"] = self.get_NET_estimate(curr_NET, self.teams[game['opponent']].KenPom)
                elif "team-schedule__result" in line:           # game is in the past
                    found_result = True
                    continue
        f = open(self.schedule_datadir + team + ".json", "w+")
        f.write(json.dumps(schedule_games))
        f.close()
        return schedule_games

    #calculate resume score for all teams
    def build_scores(self, WEIGHTS, team_kenpoms={}):
        for team in self.teams:
            if self.future:
                self.load_schedule(team)
            if self.verbose and not self.monte_carlo:
                print("Scoring", team)
            score = 0
            score += WEIGHTS["LOSS_WEIGHT"]*self.get_loss_score(self.teams[team])
            score += WEIGHTS["NET_WEIGHT"]*self.get_NET_score(self.teams[team])
            if self.monte_carlo:
                score += WEIGHTS["POWER_WEIGHT"]*self.get_power_score(self.teams[team], team_kenpoms[team])
            else:
                score += WEIGHTS["POWER_WEIGHT"]*self.get_power_score(self.teams[team])
            score += WEIGHTS["Q1_WEIGHT"]*self.get_Q1_score(self.teams[team])
            score += WEIGHTS["Q2_WEIGHT"]*self.get_Q2_score(self.teams[team])
            score += WEIGHTS["Q3_WEIGHT"]*self.get_Q3_score(self.teams[team])
            score += WEIGHTS["Q4_WEIGHT"]*self.get_Q4_score(self.teams[team])
            score += WEIGHTS["ROAD_WEIGHT"]*self.get_road_score(self.teams[team])
            score += WEIGHTS["NEUTRAL_WEIGHT"]*self.get_neutral_score(self.teams[team])
            score += WEIGHTS["TOP_10_WEIGHT"]*self.get_top10_score(self.teams[team])
            score += WEIGHTS["TOP_25_WEIGHT"]*self.get_top25_score(self.teams[team])
            score += WEIGHTS["SOS_WEIGHT"]*self.get_SOS_score(self.teams[team])
            score += WEIGHTS["NONCON_SOS_WEIGHT"]*self.get_NCSOS_score(self.teams[team])
            score += WEIGHTS["AWFUL_LOSS_WEIGHT"]*self.get_awful_loss_score(self.teams[team])
            score += WEIGHTS["BAD_LOSS_WEIGHT"]*self.get_bad_loss_score(self.teams[team])
            self.teams[team].score = score
        if self.future or self.monte_carlo:
            f = open(self.schedule_datadir + SCRAPE_DATE_FILE, "w+")
            today_date = date.today().strftime("%m-%d")    #format: mm-dd
            f.write(today_date)
            f.close()

    #write all team scores for each category to specified file
    def output_scores(self):
        with open(self.outputfile, "w") as f:
            f.write("Team," + \
                    "Losses(" + str(round(WEIGHTS["LOSS_WEIGHT"], 5)) + \
                    "), NET(" + str(round(WEIGHTS["NET_WEIGHT"], 5)) + \
                    "), Power(" + str(round(WEIGHTS["POWER_WEIGHT"], 5)) + \
                    "), Q1(" + str(round(WEIGHTS["Q1_WEIGHT"], 5)) + \
                    "), Q2(" + str(round(WEIGHTS["Q2_WEIGHT"], 5)) + \
                    "), Q3(" + str(round(WEIGHTS["Q3_WEIGHT"], 5)) + \
                    "), Q4(" + str(round(WEIGHTS["Q4_WEIGHT"], 5)) + \
                    "), Road(" + str(round(WEIGHTS["ROAD_WEIGHT"], 5)) + \
                    "), Neutral(" + str(round(WEIGHTS["NEUTRAL_WEIGHT"], 5)) + \
                    "), Top 10(" + str(round(WEIGHTS["TOP_10_WEIGHT"], 5)) + \
                    "), Top 25(" + str(round(WEIGHTS["TOP_25_WEIGHT"], 5)) + \
                    "), SOS(" + str(round(WEIGHTS["SOS_WEIGHT"], 5)) + \
                    "), Noncon SOS(" + str(round(WEIGHTS["NONCON_SOS_WEIGHT"], 5)) + \
                    "), Awful losses(" + str(round(WEIGHTS["AWFUL_LOSS_WEIGHT"], 5)) + \
                    "), Bad losses(" + str(round(WEIGHTS["BAD_LOSS_WEIGHT"], 5)) + \
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

