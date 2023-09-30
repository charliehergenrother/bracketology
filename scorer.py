#!/usr/bin/env python3

from team import SELECTION_SUNDAYS
from itertools import permutations
import sys
import math

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

#class to build a bracket from scraped data about college basketball teams
class Scorer:

    def __init__(self, builder):
        self.teams = builder.teams
        self.verbose = builder.verbose
        self.year = builder.year
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

    #calculate score for a team's raw number of losses (scale: 1.000 = 0, 0.000 = 10)
    #param team: Team object to calculate score for
    def get_loss_score(self, team):
        if self.verbose:
            print("losses", int(team.record.split("-")[1]))
        try:
            return team.loss_score
        except AttributeError:
            team.loss_score = (10-int(team.record.split("-")[1]))/10
            return team.loss_score

    #calculate score for a team's NET rank  (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_NET_score(self, team):
        if self.verbose:
            print("NET", team.NET)
        try:
            return team.NET_score
        except AttributeError:
            team.NET_score = (-math.log(team.NET + 19, 2)/2 + 3.12)#(60-team.NET)/59
            return team.NET_score

    #calculate score for a team's predictive rating (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_power_score(self, team):
        if self.verbose:
            print("power", team.predictive)
        try:
            return team.power_score
        except AttributeError:
            team.power_score = (-math.log(team.predictive + 19, 2)/2 + 3.12)#(60-team.predictive)/59
            return team.power_score

    #calculate score for a team's record in quadrant 1 (scale: 0.800 = 1, 0.000 = .000)
    #param team: Team object to calculate score for
    def get_Q1_score(self, team):
        if self.verbose:
            print("Quadrant 1", team.get_derived_pct(1))
        try:
            return team.Q1_score
        except AttributeError:
            team.Q1_score = (team.get_derived_pct(1)/0.8)
            return team.Q1_score

    #calculate score for a team's record in quadrant 2 (scale: 1.000 = 1, 0.000 = .500)
    #param team: Team object to calculate score for
    def get_Q2_score(self, team):
        if self.verbose:
            print("Quadrant 2", team.get_derived_pct(2))
        try:
            return team.Q2_score
        except AttributeError:
            team.Q2_score = (team.get_derived_pct(2)-0.5)/0.5
            return team.Q2_score

    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    #param team: Team object to calculate score for
    def get_Q3_score(self, team):
        if self.verbose:
            print("Quadrant 3", team.get_derived_pct(3))
        try:
            return team.Q3_score
        except AttributeError:
            team.Q3_score = (team.get_derived_pct(3)-0.8)/0.2
            return team.Q3_score

    #calculate score for a team's record in quadrant 4 (scale: 1.000 = 1, 0.000 = .950)
    #param team: Team object to calculate score for
    def get_Q4_score(self, team):
        if self.verbose:
            print("Quadrant 4", team.get_derived_pct(4))
        try:
            return team.Q4_score
        except AttributeError:
            if team.get_derived_pct(4) >= 0.95:
                team.Q4_score = (team.get_derived_pct(4)-0.95)/0.05
            else:   #limit how bad multiple Q4 losses can hurt you
                team.Q4_score = (team.get_derived_pct(4)-0.95)/0.3
            return team.Q4_score

    #calculate score for a team's road wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
    #param team: Team object to calculate score for
    def get_road_score(self, team):
        try:
            return team.road_score
        except AttributeError:
            good_road_wins = 0
            for game in team.games:
                if game.margin > 0 and game.location == "A":
                    if game.opp_NET <= 50:
                        good_road_wins += 1
                    elif game.opp_NET <= 100:
                        good_road_wins += (100 - game.opp_NET)/50
            if self.verbose:
                print("road wins", good_road_wins)
            team.road_score = good_road_wins/5
            return team.road_score

    #calculate score for a team's neutral court wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_neutral_score(self, team):
        try:
            return team.neutral_score
        except AttributeError:
            good_neutral_wins = 0
            for game in team.games:
                if game.margin > 0 and game.location == "N":
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAYS[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAYS[self.year] - date_num)/7
                    if game.opp_NET <= 50:
                        good_neutral_wins += conf_tourn_multiplier * 1
                    elif game.opp_NET <= 100:
                        good_neutral_wins += conf_tourn_multiplier * (100 - game.opp_NET)/50
            if self.verbose:
                print("neutral wins", good_neutral_wins)
            team.neutral_score = good_neutral_wins/5
            return team.neutral_score

    #calculate score for a team's top 10 wins (scale: 1.000 = 3, 0.000 = 0)
        #sliding scale. #1-#5: full win. #6-#14: decreases win count by 0.1 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_top10_score(self, team):
        try:
            return team.top10_score
        except AttributeError:
            top_10_wins = 0
            for game in team.games:
                if game.margin > 0:
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAYS[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAYS[self.year] - date_num)/7
                    if game.opp_NET <= 5:
                        top_10_wins += conf_tourn_multiplier * 1
                    elif game.opp_NET <= 15:
                        top_10_wins += conf_tourn_multiplier * (15 - game.opp_NET)/10
            if self.verbose:
                print("top 10 wins", top_10_wins)
            team.top10_score = top_10_wins/5
            return team.top10_score

    #calculate score for a team's top 25 wins (Quad 1A) (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. Quad 1A is 1-15 (H), 1-25 (N), 1-40 (A). win count decreases by 0.1 for each rank down when within 5 of end.
    #param team: Team object to calculate score for
    def get_top25_score(self, team):
        try:
            return team.top25_score
        except AttributeError:
            top_25_wins = 0
            for game in team.games:
                if game.margin > 0:
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAYS[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAYS[self.year] - date_num)/7
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
            if self.verbose:
                print("top 25 wins", top_25_wins)
            team.top25_score = top_25_wins/5
            return team.top25_score

    #calculate score for a team's strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_SOS_score(self, team):
        try:
            return team.SOS_score
        except AttributeError:
            if self.verbose:
                print("SOS", team.NET_SOS)
            team.SOS_score = (151 - team.NET_SOS)/150
            return team.SOS_score

    #calculate score for a team's nonconference strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_NCSOS_score(self, team):
        try:
            return team.NCSOS_score
        except AttributeError:
            if self.verbose:
                print("Noncon SOS", team.noncon_SOS)
            if team.noncon_SOS > 151:
                team.NCSOS_score = (151 - team.noncon_SOS)/150
            else:   #limit how bad a really bad noncon schedule can hurt you
                team.NCSOS_score = (151 - team.noncon_SOS)/450
            return team.NCSOS_score

    #calculate score for a team's awful (NET > 200) losses (scale: 1.000 = 0, 0.000 = 1)
        #sliding scale. loss count increases by 0.02 for each rank down past 175. #225 and worse are a full loss.
    #param team: Team object to calculate score for
    def get_awful_loss_score(self,team):
        try:
            return team.awful_loss_score
        except AttributeError:
            awful_losses = 0
            for game in team.games:
                if game.margin < 0:
                    if game.opp_NET > 225:
                        awful_losses += 1
                    elif game.opp_NET > 175:
                        awful_losses += (game.opp_NET - 175)/50
            if self.verbose:
                print("awful losses", awful_losses)
            team.awful_loss_score = (1 - awful_losses)
            return team.awful_loss_score

    #calculate score for a team's bad (sub-Q1) losses (scale: 1.000 = 0, 0.000 = 5)
    #param team: Team object to calculate score for
    def get_bad_loss_score(self,team):
        try:
            return team.bad_loss_score
        except AttributeError:
            bad_losses = 0
            bad_losses += int(team.Q2_record.split("-")[1])
            bad_losses += int(team.Q3_record.split("-")[1])
            bad_losses += int(team.Q4_record.split("-")[1])
            if self.verbose:
                print("bad losses", bad_losses)
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

    #calculate resume score for all teams
    def build_scores(self, WEIGHTS):
        for team in self.teams:
            if self.verbose:
                print("Scoring", team)
            score = 0
            score += WEIGHTS["LOSS_WEIGHT"]*self.get_loss_score(self.teams[team])
            score += WEIGHTS["NET_WEIGHT"]*self.get_NET_score(self.teams[team])
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

