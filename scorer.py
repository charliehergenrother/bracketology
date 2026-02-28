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
        "RESULTS_BASED_WEIGHT": 0,
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
# TODO just make the year a constant, man
SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_MEN_URL_START = "https://www.warrennolan.com/basketball/2026/team-clubhouse?team="
TEAM_WOMEN_URL_START = "https://www.warrennolan.com/basketballw/2026/team-clubhouse?team="

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
            round(WEIGHTS["RESULTS_BASED_WEIGHT"], 5), \
            #round(WEIGHTS["Q3_WEIGHT"], 5), \
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

    def get_season_progress(self):
        today_date = date.today()
        selection_sunday = date(int(self.year), 3, SELECTION_SUNDAY_DATES[self.year])
        season_start = date(int(self.year) - 1, 11, 3)
        season_days = (selection_sunday - season_start).days
        if season_start > today_date:
            days_left = season_days
        else:
            days_left = (selection_sunday - today_date).days
        return season_days, days_left

    #calculate score for a team's winning percentage (scale: 1.000 = 1.000, 0.000 = 0.600)
    #param team: Team object to calculate score for
    def get_loss_score(self, team, team_obj):
        if self.tracker:
            try:
                return team_obj.loss_score
            except AttributeError:
                pass
        return self.calculate_loss_score(team, team_obj)

    def calculate_loss_score(self, team, team_obj):
        record = team_obj.record.split("-")
        num_wins, num_losses = int(record[0]), int(record[1])
        if self.future and not self.monte_carlo:
            for game in team_obj.future_games:
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                num_wins += win_prob
                num_losses += (1 - win_prob)
        try:
            team_obj.loss_score = ((num_wins/(num_wins + num_losses)) - 0.6)/0.4
        except ZeroDivisionError:   #team did not play any games. COVID, ain't it crazy
            team_obj.loss_score = 0
        return team_obj.loss_score

    def get_results_based_score(self, team, team_obj):
        if self.tracker:
            try:
                return team_obj.resume_score
            except AttributeError:
                pass
        return self.calculate_results_based_score(team, team_obj)

    def calculate_results_based_score(self, team, team_obj):
        season_days, days_left = self.get_season_progress()
        RES_weight = min(1, (season_days - days_left)/(season_days - 30))
        if self.monte_carlo:    # let other categories be a higher weight than resume score
            team_obj.results_based_score = RES_weight*(-math.log(team_obj.results_based + 19, 2)/2 + 3.16)
        elif self.future:
            # estimated RES begins as all KenPom and builds more actual RES in as the season progresses until 30 days, all becomes RES
            RES_estimate = (RES_weight*team_obj.results_based) + (1 - RES_weight)*self.team_kenpoms[team]["rank"]
            team_obj.results_based_score = (-math.log(RES_estimate + 19, 2)/2 + 3.16)
        else:
            team_obj.results_based_score = RES_weight*(-math.log(team_obj.results_based + 19, 2)/2 + 3.16)
        return team_obj.results_based_score

    #calculate score for a team's NET rank  (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_NET_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.NET_score
            except AttributeError:
                pass
        return self.calculate_NET_score(team, team_obj, simmed_kenpoms)

    def calculate_NET_score(self, team, team_obj, simmed_kenpoms):
        if self.monte_carlo:
            team_obj.NET_score = (-math.log(simmed_kenpoms[team]['rank'] + 19, 2)/2 + 3.16)
        elif self.future:
            team_obj.NET_score = (-math.log(self.get_NET_estimate(team_obj.NET, self.team_kenpoms[team]["rank"]) + 19, 2)/2 + 3.16)
        else:
            team_obj.NET_score = (-math.log(team_obj.NET + 19, 2)/2 + 3.16)
        return team_obj.NET_score

    #calculate score for a team's predictive rating (scale: 1.000 = 1, 0.000 = 60)
    #param team: Team object to calculate score for
    def get_power_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.power_score
            except AttributeError:
                pass
        return self.calculate_power_score(team, team_obj, simmed_kenpoms)

    def calculate_power_score(self, team, team_obj, simmed_kenpoms):
        if self.monte_carlo:
            team_obj.power_score = (-math.log(simmed_kenpoms[team]["rank"] + 19, 2)/2 + 3.16)
        else:
            team_obj.power_score = (-math.log(team_obj.predictive + 19, 2)/2 + 3.16)
        return team_obj.power_score

    #calculate score for a team's record in quadrant 1 (scale: 0.800 = 1, 0.000 = .000)
    #param team: Team object to calculate score for
    def get_Q1_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.Q1_score
            except AttributeError:
                pass
        return self.calculate_Q1_score(team, team_obj, simmed_kenpoms)

    def calculate_Q1_score(self, team, team_obj, simmed_kenpoms):
        if self.future and not self.monte_carlo:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if "Non Div I" in game.opponent:
                    opp_NET = 365
                else:
                    opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                game_quad = self.get_quadrant(opp_NET, game.location)
                if game.win:
                    if game_quad == 1:
                        wins += 1
                else:
                    losses += 1
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                game_quad = self.get_quadrant(opp_NET, game['location'])
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if game_quad == 1:
                    wins += win_prob
                losses += (1 - win_prob)
        else:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                        game_quad = self.get_quadrant(opp_NET, game.location)
                else:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        game_quad = self.get_quadrant(self.teams[game.opponent].NET, game.location)
                if game.win:
                    if game_quad == 1:
                        wins += 1
                else:
                    losses += 1
        try:
            q1_pct = wins/(wins + losses)
        except ZeroDivisionError:
            q1_pct = 0
        team_obj.Q1_score = q1_pct/0.8
        return team_obj.Q1_score

    #calculate score for a team's record in quadrant 2 (scale: 1.000 = 1, 0.000 = .500)
    #param team: Team object to calculate score for
    def get_Q2_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.Q2_score
            except AttributeError:
                pass
        return self.calculate_Q2_score(team, team_obj, simmed_kenpoms)

    def calculate_Q2_score(self, team, team_obj, simmed_kenpoms):
        if self.future and not self.monte_carlo:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if "Non Div I" in game.opponent:
                    opp_NET = 365
                else:
                    opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                game_quad = self.get_quadrant(opp_NET, game.location)
                if game.win:
                    if game_quad <= 2:
                        wins += 1
                else:
                    if game_quad >= 2:
                        losses += 1
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                game_quad = self.get_quadrant(opp_NET, game['location'])
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if game_quad <= 2:
                    wins += win_prob
                if game_quad >= 2:
                    losses += (1 - win_prob)
        else:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                        game_quad = self.get_quadrant(opp_NET, game.location)
                else:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        game_quad = self.get_quadrant(self.teams[game.opponent].NET, game.location)
                if game.win:
                    if game_quad <= 2:
                        wins += 1
                else:
                    if game_quad >= 2:
                        losses += 1
        try:
            q2_pct = wins/(wins + losses)
        except ZeroDivisionError:
            q2_pct = 0
        team_obj.Q2_score = (q2_pct-0.5)/0.5
        return team_obj.Q2_score

    #calculate score for a team's record in quadrant 3 (scale: 1.000 = 1, 0.000 = .800)
    #param team: Team object to calculate score for
    def get_Q3_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.Q3_score
            except AttributeError:
                pass
        return self.calculate_Q3_score(team, team_obj, simmed_kenpoms)

    def calculate_Q3_score(self, team, team_obj, simmed_kenpoms):
        if self.future and not self.monte_carlo:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if "Non Div I" in game.opponent:
                    opp_NET = 365
                else:
                    opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                game_quad = self.get_quadrant(opp_NET, game.location)
                if game.win:
                    if game_quad <= 3:
                        wins += 1
                else:
                    if game_quad >= 3:
                        losses += 1
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                game_quad = self.get_quadrant(opp_NET, game['location'])
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if game_quad <= 3:
                    wins += win_prob
                if game_quad >= 3:
                    losses += (1 - win_prob)
        else:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                        game_quad = self.get_quadrant(opp_NET, game.location)
                else:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        game_quad = self.get_quadrant(self.teams[game.opponent].NET, game.location)
                if game.win:
                    if game_quad <= 3:
                        wins += 1
                else:
                    if game_quad >= 3:
                        losses += 1

        try:
            q3_pct = wins/(wins + losses)
        except ZeroDivisionError:
            q3_pct = 0
        team_obj.Q3_score = (q3_pct-0.8)/0.2
        return team_obj.Q3_score

    #calculate score for a team's record in quadrant 4 (scale: 1.000 = 1, 0.000 = .950)
    #param team: Team object to calculate score for
    def get_Q4_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.Q4_score
            except AttributeError:
                pass
        return self.calculate_Q4_score(team, team_obj, simmed_kenpoms)

    def calculate_Q4_score(self, team, team_obj, simmed_kenpoms):
        if self.future and not self.monte_carlo:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if "Non Div I" in game.opponent:
                    opp_NET = 365
                else:
                    opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                game_quad = self.get_quadrant(opp_NET, game.location)
                if game.win:
                    wins += 1
                else:
                    if game_quad == 4:
                        losses += 1
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                game_quad = self.get_quadrant(opp_NET, game['location'])
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                wins += win_prob
                if game_quad == 4:
                    losses += (1 - win_prob)
        else:
            wins = 0
            losses = 0
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                        game_quad = self.get_quadrant(opp_NET, game.location)
                else:
                    if "Non Div I" in game.opponent:
                        game_quad = 4
                    else:
                        game_quad = self.get_quadrant(self.teams[game.opponent].NET, game.location)
                if game.win:
                    wins += 1
                else:
                    if game_quad == 4:
                        losses += 1

        try:
            q4_pct = wins/(wins + losses)
        except ZeroDivisionError:
            q4_pct = 0
        if q4_pct >= 0.95:
            team_obj.Q4_score = (q4_pct-0.95)/0.05
        else:   #limit how bad multiple Q4 losses can hurt you
            team_obj.Q4_score = (q4_pct-0.95)/0.3
        return team_obj.Q4_score

    #calculate score for a team's road wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
    #param team: Team object to calculate score for
    def get_road_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.road_score
            except AttributeError:
                pass
        return self.calculate_road_score(team, team_obj, simmed_kenpoms)

    def calculate_road_score(self, team, team_obj, simmed_kenpoms):
        good_road_wins = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if game.win and game.location == "A":
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                    if opp_NET <= 50:
                        good_road_wins += 1
                    elif opp_NET <= 100:
                        good_road_wins += (100 - opp_NET)/50
            for game in team_obj.future_games:
                if game['location'] == "A":
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                    win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                    if opp_NET <= 50:
                        good_road_wins += win_prob
                    elif opp_NET <= 100:
                        good_road_wins += (100 - opp_NET)*win_prob/50
        else:
            for game in team_obj.games:
                if game.win and game.location == "A":
                    if self.monte_carlo:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                    else:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.teams[game.opponent].NET
                    if opp_NET <= 50:
                        good_road_wins += 1
                    elif opp_NET <= 100:
                        good_road_wins += (100 - opp_NET)/50
        team_obj.road_score = good_road_wins/5
        return team_obj.road_score

    #calculate score for a team's neutral court wins (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. #1-#50: full win. #51-#99: decreases win count by 0.02 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_neutral_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.neutral_score
            except AttributeError:
                pass
        return self.calculate_neutral_score(team, team_obj, simmed_kenpoms)

    def calculate_neutral_score(self, team, team_obj, simmed_kenpoms):
        good_neutral_wins = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if game.win and game.location == "N":
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                    if opp_NET <= 50:
                        good_neutral_wins += conf_tourn_multiplier * 1
                    elif opp_NET <= 100:
                        good_neutral_wins += conf_tourn_multiplier * (100 - opp_NET)/50
            for game in team_obj.future_games:
                if game['location'] == "N":
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                    win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                    if opp_NET <= 50:
                        good_neutral_wins += win_prob
                    elif opp_NET <= 100:
                        good_neutral_wins += (100 - opp_NET)*win_prob/50
        else:
            for game in team_obj.games:
                if game.win and game.location == "N":
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if self.monte_carlo:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                    else:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.teams[game.opponent].NET
                    if opp_NET <= 50:
                        good_neutral_wins += conf_tourn_multiplier * 1
                    elif opp_NET <= 100:
                        good_neutral_wins += conf_tourn_multiplier * (100 - opp_NET)/50
        team_obj.neutral_score = good_neutral_wins/5
        return team_obj.neutral_score

    #calculate score for a team's top 10 wins (scale: 1.000 = 3, 0.000 = 0)
        #sliding scale. #1-#5: full win. #6-#14: decreases win count by 0.1 for each rank down.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_top10_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.top10_score
            except AttributeError:
                pass
        return self.calculate_top10_score(team, team_obj, simmed_kenpoms)

    def calculate_top10_score(self, team, team_obj, simmed_kenpoms):
        top_10_wins = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if game.win:
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                    if opp_NET <= 5:
                        top_10_wins += conf_tourn_multiplier * 1
                    elif opp_NET <= 15:
                        top_10_wins += conf_tourn_multiplier * (15 - opp_NET)/10
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if opp_NET <= 5:
                    top_10_wins += win_prob
                elif opp_NET <= 15:
                    top_10_wins += (15 - opp_NET)*win_prob/10
        else:
            for game in team_obj.games:
                if game.win:
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if self.monte_carlo:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                    else:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.teams[game.opponent].NET
                    if opp_NET <= 5:
                        top_10_wins += conf_tourn_multiplier * 1
                    elif opp_NET <= 15:
                        top_10_wins += conf_tourn_multiplier * (15 - opp_NET)/10

        team_obj.top10_score = top_10_wins/3
        return team_obj.top10_score

    #calculate score for a team's top 25 wins (Quad 1A) (scale: 1.000 = 5, 0.000 = 0)
        #sliding scale. Quad 1A is 1-15 (H), 1-25 (N), 1-40 (A). win count decreases by 0.1 for each rank down when within 5 of end.
        #also, sliding penalty for conference tournament games. this is done for accuracy, not cause I like it.
    #param team: Team object to calculate score for
    def get_top25_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.top25_score
            except AttributeError:
                pass
        return self.calculate_top25_score(team, team_obj, simmed_kenpoms)

    def calculate_top25_score(self, team, team_obj, simmed_kenpoms):
        top_25_wins = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if game.win > 0:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if game.location == "H":
                        if opp_NET <= 10:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 20:
                            top_25_wins += conf_tourn_multiplier * (20 - opp_NET)/10
                    elif game.location == "N":
                        if opp_NET <= 20:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 30:
                            top_25_wins += conf_tourn_multiplier * (30 - opp_NET)/10
                    elif game.location == "A":
                        if opp_NET <= 35:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 45:
                            top_25_wins += conf_tourn_multiplier * (45 - opp_NET)/10
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if game['location'] == "H":
                    if opp_NET <= 10:
                        top_25_wins += win_prob
                    elif opp_NET <= 20:
                        top_25_wins += win_prob * (20 - opp_NET)/10
                elif game['location'] == "N":
                    if opp_NET <= 20:
                        top_25_wins += win_prob
                    elif opp_NET <= 30:
                        top_25_wins += win_prob * (30 - opp_NET)/10
                elif game['location'] == "A":
                    if opp_NET <= 35:
                        top_25_wins += win_prob
                    elif opp_NET <= 45:
                        top_25_wins += win_prob * (45 - opp_NET)/10
        else:
            for game in team_obj.games:
                if game.win > 0:
                    if self.monte_carlo:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                    else:
                        if "Non Div I" in game.opponent:
                            opp_NET = 365
                        else:
                            opp_NET = self.teams[game.opponent].NET
                    conf_tourn_multiplier = 1
                    date_month, date_num = int(game.date.split('-')[0]), int(game.date.split('-')[1])
                    if date_month == 3:
                        if date_num > SELECTION_SUNDAY_DATES[self.year] - 7:
                            conf_tourn_multiplier = (SELECTION_SUNDAY_DATES[self.year] - date_num)/7
                    if game.location == "H":
                        if opp_NET <= 10:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 20:
                            top_25_wins += conf_tourn_multiplier * (20 - opp_NET)/10
                    elif game.location == "N":
                        if opp_NET <= 20:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 30:
                            top_25_wins += conf_tourn_multiplier * (30 - opp_NET)/10
                    elif game.location == "A":
                        if opp_NET <= 35:
                            top_25_wins += conf_tourn_multiplier * 1
                        elif opp_NET <= 45:
                            top_25_wins += conf_tourn_multiplier * (45 - opp_NET)/10

        team_obj.top25_score = top_25_wins/5
        return team_obj.top25_score

    #calculate score for a team's strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_SOS_score(self, team, team_obj):
        #TODO: could calculate a future estimate here. Might be good.
        try:
            return team_obj.SOS_score
        except AttributeError:
            if team_obj.NET_SOS < 151:
                team_obj.SOS_score = (151 - team_obj.NET_SOS)/150
            else:   #limit how bad a really bad schedule can hurt you
                team_obj.SOS_score = (151 - team_obj.NET_SOS)/300
            return team_obj.SOS_score

    #calculate score for a team's nonconference strength of schedule (scale: 1.000 = 1, 0.000 = 150)
    #param team: Team object to calculate score for
    def get_NCSOS_score(self, team, team_obj):
        try:
            return team_obj.NCSOS_score
        except AttributeError:
            if team_obj.noncon_SOS < 151:
                team_obj.NCSOS_score = (151 - team_obj.noncon_SOS)/150
            else:   #limit how bad a really bad noncon schedule can hurt you
                team_obj.NCSOS_score = (151 - team_obj.noncon_SOS)/450
            return team_obj.NCSOS_score

    #calculate score for a team's awful (NET > 200) losses (scale: 1.000 = 0, 0.000 = 1)
        #sliding scale. loss count increases by 0.02 for each rank down past 175. #225 and worse are a full loss.
    #param team: Team object to calculate score for
    def get_awful_loss_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.awful_loss_score
            except AttributeError:
                pass
        return self.calculate_awful_loss_score(team, team_obj, simmed_kenpoms)

    def calculate_awful_loss_score(self, team, team_obj, simmed_kenpoms):
        awful_losses = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if "Non Div I" in game.opponent:
                    opp_NET = 365
                else:
                    opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                if not game.win:
                    if opp_NET > 225:
                        awful_losses += 1
                    elif opp_NET > 175:
                        awful_losses += (opp_NET - 175)/50
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if opp_NET > 225:
                    awful_losses += (1 - win_prob)
                elif opp_NET > 175:
                    awful_losses += (opp_NET - 175)*(1 - win_prob)/50
        else:
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                else:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.teams[game.opponent].NET
                if not game.win:
                    if opp_NET > 225:
                        awful_losses += 1
                    elif opp_NET > 175:
                        awful_losses += (opp_NET - 175)/50

        team_obj.awful_loss_score = (1 - awful_losses)
        return team_obj.awful_loss_score

    #calculate score for a team's bad (sub-Q1) losses (scale: 1.000 = 0, 0.000 = 5)
    #param team: Team object to calculate score for
    def get_bad_loss_score(self, team, team_obj, simmed_kenpoms):
        if self.tracker:
            try:
                return team_obj.bad_loss_score
            except AttributeError:
                pass
        return self.calculate_bad_loss_score(team, team_obj, simmed_kenpoms)

    def calculate_bad_loss_score(self, team, team_obj, simmed_kenpoms):
        bad_losses = 0
        if self.future and not self.monte_carlo:
            for game in team_obj.games:
                if not game.win:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, self.team_kenpoms[team]["rank"])
                    game_quad = self.get_quadrant(opp_NET, game.location)
                    if game_quad > 1:
                        bad_losses += 1
            for game in team_obj.future_games:
                try:
                    opp_NET = self.get_NET_estimate(self.teams[game['opponent']].NET, self.team_kenpoms[team]["rank"])
                except KeyError: #Until New Haven makes the NET
                    opp_NET = 365
                game_quad = self.get_quadrant(opp_NET, game['location'])
                win_prob = self.get_win_prob(self.team_kenpoms[team]["rating"], self.team_kenpoms[game['opponent']]["rating"], game['location'])
                if game_quad >= 2:
                    bad_losses += (1 - win_prob) 
        else:
            for game in team_obj.games:
                if self.monte_carlo:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.get_NET_estimate(self.teams[game.opponent].NET, simmed_kenpoms[game.opponent]["rank"])
                else:
                    if "Non Div I" in game.opponent:
                        opp_NET = 365
                    else:
                        opp_NET = self.teams[game.opponent].NET
                if not game.win:
                    game_quad = self.get_quadrant(opp_NET, game.location)
                    if game_quad >= 2:
                        bad_losses += 1 

        team_obj.bad_loss_score = (1 - bad_losses/5)
        return team_obj.bad_loss_score
    
    def get_weights(self, weightfile):
        with open(weightfile, "r") as f:
            for line in f.read().split("\n"):
                if not line:
                    continue
                weight_name, weight_val = line.split(" = ")
                WEIGHTS[weight_name] = float(weight_val)
        return WEIGHTS

    def get_win_prob(self, team_kenpom, opp_kenpom, location):
        team_spread_neutral = (team_kenpom - opp_kenpom)*0.675  #average possessions: 67.5
        if location == 'H':
            spread = team_spread_neutral + 3
        elif location == 'N':
            spread = team_spread_neutral
        elif location == 'A':
            spread = team_spread_neutral - 3

        if abs(spread) <= 21:
            return -0.00002609*spread*spread*spread + 0.00002466*spread*spread + 0.033206*spread + 0.5
        elif spread > 21:
            return 0.98
        elif spread < -21:
            return 0.02

    def get_NET_estimate(self, curr_NET, curr_KenPom):
        season_days, days_left = self.get_season_progress()
        # estimated NET begins as all KenPom and builds more actual NET in as the season progresses until 30 days, all becomes NET
        NET_weight = min(1, (season_days - days_left)/(season_days - 30))
        NET_estimate = (NET_weight*curr_NET) + (1 - NET_weight)*curr_KenPom
        return NET_estimate

    #calculate resume score for all teams
    def build_scores(self, WEIGHTS, simmed_kenpoms=dict()):
        for team in self.teams:
            if self.verbose and not self.monte_carlo:
                print("Scoring", team)
            team_obj = self.teams[team]
            score = 0
            score += WEIGHTS["LOSS_WEIGHT"]*self.get_loss_score(team, team_obj)
            score += WEIGHTS["NET_WEIGHT"]*self.get_NET_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["POWER_WEIGHT"]*self.get_power_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["Q1_WEIGHT"]*self.get_Q1_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["Q2_WEIGHT"]*self.get_Q2_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["Q3_WEIGHT"]*self.get_Q3_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["RESULTS_BASED_WEIGHT"]*self.get_results_based_score(team, team_obj)
            score += WEIGHTS["Q4_WEIGHT"]*self.get_Q4_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["ROAD_WEIGHT"]*self.get_road_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["NEUTRAL_WEIGHT"]*self.get_neutral_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["TOP_10_WEIGHT"]*self.get_top10_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["TOP_25_WEIGHT"]*self.get_top25_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["SOS_WEIGHT"]*self.get_SOS_score(team, team_obj)
            score += WEIGHTS["NONCON_SOS_WEIGHT"]*self.get_NCSOS_score(team, team_obj)
            score += WEIGHTS["AWFUL_LOSS_WEIGHT"]*self.get_awful_loss_score(team, team_obj, simmed_kenpoms)
            score += WEIGHTS["BAD_LOSS_WEIGHT"]*self.get_bad_loss_score(team, team_obj, simmed_kenpoms)
            self.teams[team].score = score
        if self.future or self.monte_carlo:
            f = open(self.schedule_datadir + SCRAPE_DATE_FILE, "w+")
            today_date = date.today().strftime("%m-%d")    #format: mm-dd
            f.write(today_date)
            f.close()

    #write all team scores for each category to specified file
    def output_scores(self):
        with open(self.outputfile, "w") as f:
            if self.mens:
                f.write("Team," + \
                    "Losses(" + str(round(WEIGHTS["LOSS_WEIGHT"], 5)) + \
                    "),NET(" + str(round(WEIGHTS["NET_WEIGHT"], 5)) + \
                    "),Power(" + str(round(WEIGHTS["POWER_WEIGHT"], 5)) + \
                    "),Q1(" + str(round(WEIGHTS["Q1_WEIGHT"], 5)) + \
                    "),Q2(" + str(round(WEIGHTS["Q2_WEIGHT"], 5)) + \
                    "),Results(" + str(round(WEIGHTS["RESULTS_BASED_WEIGHT"], 5)) + \
                    #"),Q3(" + str(round(WEIGHTS["Q3_WEIGHT"], 5)) + \
                    "),Q4(" + str(round(WEIGHTS["Q4_WEIGHT"], 5)) + \
                    "),Road(" + str(round(WEIGHTS["ROAD_WEIGHT"], 5)) + \
                    "),Neutral(" + str(round(WEIGHTS["NEUTRAL_WEIGHT"], 5)) + \
                    "),Top 10(" + str(round(WEIGHTS["TOP_10_WEIGHT"], 5)) + \
                    "),Top 25(" + str(round(WEIGHTS["TOP_25_WEIGHT"], 5)) + \
                    "),SOS(" + str(round(WEIGHTS["SOS_WEIGHT"], 5)) + \
                    "),Noncon SOS(" + str(round(WEIGHTS["NONCON_SOS_WEIGHT"], 5)) + \
                    "),Awful losses(" + str(round(WEIGHTS["AWFUL_LOSS_WEIGHT"], 5)) + \
                    "),Bad losses(" + str(round(WEIGHTS["BAD_LOSS_WEIGHT"], 5)) + \
                    "),Total Score\n")
            else:
                f.write("Team," + \
                    "Losses(" + str(round(WEIGHTS["LOSS_WEIGHT"], 5)) + \
                    "),NET(" + str(round(WEIGHTS["NET_WEIGHT"], 5)) + \
                    "),Power(" + str(round(WEIGHTS["POWER_WEIGHT"], 5)) + \
                    "),Q1(" + str(round(WEIGHTS["Q1_WEIGHT"], 5)) + \
                    "),Q2(" + str(round(WEIGHTS["Q2_WEIGHT"], 5)) + \
                    "),Q3(" + str(round(WEIGHTS["Q3_WEIGHT"], 5)) + \
                    "),Road(" + str(round(WEIGHTS["ROAD_WEIGHT"], 5)) + \
                    "),Neutral(" + str(round(WEIGHTS["NEUTRAL_WEIGHT"], 5)) + \
                    "),Top 10(" + str(round(WEIGHTS["TOP_10_WEIGHT"], 5)) + \
                    "),Top 25(" + str(round(WEIGHTS["TOP_25_WEIGHT"], 5)) + \
                    "),Awful losses(" + str(round(WEIGHTS["AWFUL_LOSS_WEIGHT"], 5)) + \
                    "),Bad losses(" + str(round(WEIGHTS["BAD_LOSS_WEIGHT"], 5)) + \
                    "),Total Score\n")
            for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
                if self.mens:
                    line = self.teams[team].team_out + "," + \
                        str(round(self.teams[team].loss_score, 5)) + "," + \
                        str(round(self.teams[team].NET_score, 5)) + "," + \
                        str(round(self.teams[team].power_score, 5)) + "," + \
                        str(round(self.teams[team].Q1_score, 5)) + "," + \
                        str(round(self.teams[team].Q2_score, 5)) + "," + \
                        str(round(self.teams[team].results_based_score, 5)) + "," + \
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
                else:
                    line = self.teams[team].team_out + "," + \
                        str(round(self.teams[team].loss_score, 5)) + "," + \
                        str(round(self.teams[team].NET_score, 5)) + "," + \
                        str(round(self.teams[team].power_score, 5)) + "," + \
                        str(round(self.teams[team].Q1_score, 5)) + "," + \
                        str(round(self.teams[team].Q2_score, 5)) + "," + \
                        str(round(self.teams[team].Q3_score, 5)) + "," + \
                        str(round(self.teams[team].road_score, 5)) + "," + \
                        str(round(self.teams[team].neutral_score, 5)) + "," + \
                        str(round(self.teams[team].top10_score, 5)) + "," + \
                        str(round(self.teams[team].top25_score, 5)) + "," + \
                        str(round(self.teams[team].awful_loss_score, 5)) + "," + \
                        str(round(self.teams[team].bad_loss_score, 5)) + "," + \
                        str(round(self.teams[team].score, 5)) + "\n"
                f.write(line)

