#!/usr/bin/env python3

from team import SELECTION_SUNDAYS
from itertools import permutations
import sys
import math

SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_COORDINATES_FILE = "lib/team_locations.txt"

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
AUTO_MAXES = {"2021": 31, "2022": 32, "2023": 32}

#class to build a bracket from scraped data about college basketball teams
class Builder:

    def __init__(self, year, teams, verbose, of, fws, fwr, rr, et, it, cw, rtd):
        self.year = year
        self.teams = teams
        self.verbose = verbose
        self.outputfile = of
        self.first_weekend_sites = fws
        self.first_weekend_rankings = fwr
        self.region_rankings = rr
        self.eliminated_teams = et
        self.ineligible_teams = it
        self.conference_winners = cw
        self.reverse_team_dict = rtd
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

    #seed and print the field, including a bubble section
    def select_seed_and_print_field(self, do_print):
        curr_seed = 1
        num_curr_seed = 1
        curr_seed_max = 4
        at_large_bids = 0
        auto_bids = 0
        bubble_count = 0
        bubble_string = "BUBBLE: \n"
        AUTO_MAX = AUTO_MAXES[self.year]
        AT_LARGE_MAX = 68 - AUTO_MAX
        
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            at_large_bid = False
            if team in self.ineligible_teams:
                continue
            if team in self.eliminated_teams or (self.teams[team].conference in self.conference_winners and \
                    self.conference_winners[self.teams[team].conference] != team):
                #teams under .500 are ineligible for at-large bids
                if self.teams[team].record_pct < 0.5:
                    continue
                if at_large_bids < AT_LARGE_MAX:
                    at_large_bids += 1
                    at_large_bid = True
                    self.teams[team].at_large_bid = True
                elif bubble_count < 4:
                    bubble_string += (self.teams[team].team_out + " - First Four Out\n")
                    bubble_count += 1
                    continue
                elif bubble_count < 8:
                    bubble_string += (self.teams[team].team_out + " - Next Four Out\n")
                    bubble_count += 1
                    continue
                else:
                    continue
            else:
                if self.teams[team].conference != "Independent" and \
                        ((self.teams[team].conference in self.conference_winners and \
                        self.conference_winners[self.teams[team].conference] == team) or \
                        (self.teams[team].conference not in self.conference_winners and \
                        team not in self.eliminated_teams and auto_bids < AUTO_MAX)):
                    auto_bids += 1
                    self.conference_winners[self.teams[team].conference] = team
                    self.teams[team].auto_bid = True
                else:
                    continue
            if do_print:
                print("(" + str(curr_seed) + ") " + self.teams[team].team_out, end="")
            if at_large_bid:
                if at_large_bids >= AT_LARGE_MAX - 3:
                    if (AT_LARGE_MAX - at_large_bids) % 2 == 1:
                        curr_seed_max += 1
                    if do_print:
                        bubble_string += (self.teams[team].team_out + " - Last Four In\n")
                        print(" - Last Four In")
                elif at_large_bids >= AT_LARGE_MAX - 7:
                    if do_print:
                        bubble_string += (self.teams[team].team_out + " - Last Four Byes\n")
                        print(" - Last Four Byes")
                elif do_print:
                    print()
            elif do_print:
                print("*")
            if num_curr_seed == curr_seed_max and curr_seed < 16:
                curr_seed += 1
                num_curr_seed = 1
                curr_seed_max = 4
            else:
                num_curr_seed += 1
        if do_print:
            print()
            print(bubble_string)

    #get the maximum length of a line when printing the bracket (two team names + their seeds + some buffer)
    def get_max_len(self):
        l = []
        for coords in [[0, 1], [3, 2]]:
            for seed in range(1, 17):
                l.append(len(self.regions[coords[0]][seed]) + len(self.regions[coords[1]][seed]))
        return 30 + max(l)

    #return a nicer-looking representation of a team's name, if one is present
    #param team: string containing a team's name
    def get_team_out(self, team):
        if "/" in team:
            return self.teams[team.split("/")[0]].team_out + "/" + self.teams[team.split("/")[1]].team_out
        return self.teams[team].team_out
    
    #print a line of the bracket
    #param max_len: maximum length of a line containing two teams
    #param region_1: 0 or 3, corresponding to one of the regions on the left side of the bracket
    #param region_2: 1 or 2, corresponding to one of the regions on the right side of the bracket
    #param seed: seed of the teams to print
    #param region_num_to_name: dictionary to translate a region's number to its location
    def print_line(self, max_len, region_1, region_2, seed, region_num_to_name):
        team_1 = self.get_team_out(self.regions[region_1][seed])
        team_2 = self.get_team_out(self.regions[region_2][seed])
        if (seed == 16) or ("/" not in team_1 and self.teams[self.regions[region_1][seed]].auto_bid):
            team_1 += "*"
        if (seed == 16) or ("/" not in team_2 and self.teams[self.regions[region_2][seed]].auto_bid):
            team_2 += "*"
        max_site_len = max([len(x) for x in self.first_weekend_name_to_num])
        print(" "*max_site_len + "(" + str(seed) + ") " + team_1 + \
                " "*(max_len - (len(team_1) + len(team_2)) - (len(str(seed)) + 3)*2) + \
                " (" + str(seed) + ") " + team_2)
        if seed == 13:
            region_1_name = region_num_to_name[region_1]
            region_2_name = region_num_to_name[region_2]
            print(" "*(20 + max_site_len) + region_1_name + " "*max([max_len - (len(region_1_name) + len(region_2_name) + 40), 5]) + region_2_name)
        elif seed == 16:
            site_1 = self.first_weekend_num_to_name[region_1][1]
            site_2 = self.first_weekend_num_to_name[region_2][1]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 12: 
            site_1 = self.first_weekend_num_to_name[region_1][4]
            site_2 = self.first_weekend_num_to_name[region_2][4]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 11: 
            site_1 = self.first_weekend_num_to_name[region_1][3]
            site_2 = self.first_weekend_num_to_name[region_2][3]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        elif seed == 10:
            site_1 = self.first_weekend_num_to_name[region_1][2]
            site_2 = self.first_weekend_num_to_name[region_2][2]
            print(site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2)
        else:
            print()

    #check if placing a team in a particular bracket location will follow all the rules
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    #param team: name of team to attempt to place
    #param region_num: region number (0-3) to try to place the team in
    #param seed_num: seed number (1-16) to try to place the team in
    def check_rules(self, conferences, team, region_num, seed_num, for_play_in=False):
        if team == "":
            return True
        if for_play_in:
            return (self.check_rules(conferences, team.split("/")[0], region_num, seed_num, False) and \
                    self.check_rules(conferences, team.split("/")[1], region_num, seed_num, False))
        team_conference = self.teams[team].conference

        #the top four teams from a conference must be in different regions if they are on the top four seed lines
        if conferences[team_conference].index(team) < 4 and seed_num <= 4:
            for test_team in conferences[team_conference][:3]:
                if test_team == team:
                    continue
                if self.teams[test_team].region == region_num:
                    if self.verbose:
                        print("multiple top four teams can't all go here", region_num, conferences[team_conference])
                    return False

        #two teams from the same conference cannot meet before the...
            #...regional final (Elite 8) if they've played 3 times
            #...regional semifinal (Sweet 16) if they've played 2 times
            #...second round if they've played 1 time
        for test_team in conferences[team_conference]:
            if test_team == team:
                continue
            try:
                if self.teams[test_team].region != region_num:
                    continue
            except AttributeError:      #there are two teams from this conference in the play-ins
                continue
            game_count = 0
            for game in self.teams[test_team].games:
                if self.reverse_team_dict[game.opponent] == team:
                    game_count += 1
            if self.teams[test_team].seed + seed_num == 17: #first round matchup
                if self.verbose:
                    print("teams are meeting too early in this region", region_num, conferences[team_conference])
                return False
            if game_count >= 2:     #sweet 16 matchup
                for seed_set in [[1, 16, 8, 9], [5, 12, 4, 13], [6, 11, 3, 14], [7, 10, 2, 15]]:
                    if self.teams[test_team].seed in seed_set and seed_num in seed_set:
                        if self.verbose:
                            print("teams are meeting too early in this region", region_num, conferences[team_conference])
                        return False
            if game_count >= 3:     #elite 8 matchup
                for seed_set in [[1, 16, 8, 9, 5, 12, 4, 13], [6, 11, 3, 14, 7, 10, 2, 15]]:
                    if self.teams[test_team].seed in seed_set and seed_num in seed_set:
                        if self.verbose:
                            print("teams are meeting too early in this region", region_num, conferences[team_conference])
                        return False
        return True

    #remove all teams from their seed lines in order to attempt to reorganize them
    #param seed_num: seed number to delete
    #returns: list of teams being deleted, list of [team, region_num, site_name] for each
    def delete_and_save_seed(self, seed_num):
        teams_to_fix = list()
        sites = list()
        for region_num, region in enumerate(self.regions):
            if seed_num in region:
                save_team = region[seed_num]
                teams_to_fix.append(save_team)
                if "/" in save_team:
                    self.teams[save_team.split("/")[0]].region = -1
                    self.teams[save_team.split("/")[1]].region = -1
                    self.teams[save_team.split("/")[0]].seed = -1
                    self.teams[save_team.split("/")[1]].seed = -1
                else:
                    self.teams[save_team].region = -1
                    self.teams[save_team].seed = -1
                del region[seed_num]
                if seed_num < 5:
                    if seed_num in self.first_weekend_num_to_name[region_num]:
                        sites.append([save_team, region_num, self.first_weekend_num_to_name[region_num][seed_num]])
                        del self.first_weekend_num_to_name[region_num][seed_num]
        #if the seed wasn't fully filled out, put placeholders in
        while len(teams_to_fix) < 4:
            teams_to_fix.append("")
        return teams_to_fix, sites

    #check a permutation of four teams to see if the bracket can accept it
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    #param perm: permutation of four teams on the same seed line
    #param seed_num: seed of teams
    def check_perm(self, conferences, perm, seed_num, team="", for_play_in=False):
        play_in = dict()
        for counter, perm_team in enumerate(perm):
            if perm_team and team == perm_team and for_play_in: 
                if not self.check_rules(conferences, perm_team, counter, seed_num, True):
                    return False
            else:
                if not self.check_rules(conferences, perm_team, counter, seed_num, False):
                    return False
        return True
    
    #insert a permutation of four teams into the bracket
    #param seed_num: seed of teams
    #param perm: permutation of four teams on the same seed line
    #param sites: saved locations of sites, if the seed is 1-4
    def save_and_print_perm(self, seed_num, perm, sites):
        for region_num in range(0, 4):
            team = perm[region_num]
            if not team:
                if seed_num in self.first_weekend_num_to_name[region_num]:
                    del self.first_weekend_num_to_name[region_num][seed_num]
                continue
            self.regions[region_num][seed_num] = team
            if "/" in team:
                self.teams[team.split("/")[0]].region = region_num
                self.teams[team.split("/")[1]].region = region_num
                self.teams[team.split("/")[0]].seed = seed_num
                self.teams[team.split("/")[1]].seed = seed_num
            else:
                self.teams[team].region = region_num
                self.teams[team].seed = seed_num
            if seed_num < 5:
                for team_site in sites:
                    if team_site[0] == team:
                        self.first_weekend_num_to_name[region_num][seed_num] = team_site[2]
                        self.first_weekend_name_to_num[team_site[2]][self.first_weekend_name_to_num[team_site[2]].index([team_site[1], seed_num])] = [region_num, seed_num]
                        team_site[1] = region_num
            if self.verbose:
                print("Placed (" + str(seed_num) + ") " + team + ": region (" + str(region_num) + ")")

    #return a list of a team's regional preferences
    #param team: string of team to get preferences for
    #param seed_num: seed of team. if higher (i.e. lower number) than 5, use regional sites; otherwise, use first-weekend sites
    #param region_name_to_num: dictionary to translate region sites to coordinate
    def get_region_order(self, team, seed_num, region_name_to_num):
        order = list()
        if seed_num < 5:
            for site in self.region_rankings[team]:
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
            for index, region in enumerate(self.first_weekend_num_to_name):
                possible_sites.append(region[host_seed])
            for site in self.first_weekend_rankings[team]:
                while site in possible_sites:
                    order.append(possible_sites.index(site))
                    possible_sites[possible_sites.index(site)] = ""
        return order

    #when rebalancing regions after placing 4 seeds, calculate scores for each region
    #param sorted_teams: teams sorted by score, for determining a team's rank in the seed list
    #returns: list of four numbers corresponding to the four region scores
    def get_region_scores(self, sorted_teams):
        scores = list()
        for region in self.regions:
            region_score = 0
            for seed in region:
                if seed == "score":
                    continue
                region_score += sorted_teams.index(region[seed])
            region["score"] = region_score
            scores.append(region_score)
        return scores

    #check if teams need to be rearranged to ensure equal-ish quality, do it if so
    #param sorted_teams: teams sorted by score, for determining a team's rank in the seed list
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    def ensure_region_balance(self, sorted_teams, conferences):
        scores = self.get_region_scores(sorted_teams)
        bad_perms = list()
        while max(scores) > min(scores) + 5:
            if self.verbose:
                print("have to rearrange regions, one is too strong/weak")
            if 4 not in self.regions[0]:
                #couldn't find one that worked. eh. we tried.
                self.save_and_print_perm(4, bad_perms[0], sites)
                break
            teams_to_fix, sites = self.delete_and_save_seed(4)
            bad_perms.append(tuple(teams_to_fix))
            for perm in permutations(teams_to_fix):
                if perm in bad_perms:
                    continue
                if self.check_perm(conferences, perm, 4, "", False):
                    self.save_and_print_perm(4, perm, sites)
                    break
            scores = self.get_region_scores(sorted_teams)
        for region in self.regions:
            del region["score"]

    #create matchups for the two play-in games. avoid matching up two teams from a conference if possible
    #param teams: a list of four team names in the play-in
    def get_play_in_matchups(self, teams):
        if self.teams[teams[0]].conference == self.teams[teams[1]].conference or \
            self.teams[teams[2]].conference == self.teams[teams[3]].conference:
            teams[1], teams[2] = teams[2], teams[1]
        return [[teams[0], teams[1]], [teams[2], teams[3]]]
    
    #find play-in teams a spot in the bracket and place them there
    #param teams: a list of four team names in the play-in
    #param seeds: the four seeds these teams will receive
    #param region_name_to_num: dictionary to translate region sites to coordinate
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    def place_play_in(self, teams, seeds, region_name_to_num, conferences):
        matchups = self.get_play_in_matchups(teams)
        
        region_order = self.get_region_order(matchups[0][0], seeds[0], region_name_to_num)
        _, region_num = self.find_team_spot('/'.join(matchups[0]), \
                self.get_region_num(seeds[0], region_order[0], region_order), seeds[0],\
                conferences, region_order, True)
        self.place_team(region_num, seeds[0], '/'.join(matchups[0]))

        region_order = self.get_region_order(matchups[1][0], seeds[2], region_name_to_num)
        _, region_num = self.find_team_spot('/'.join(matchups[1]), \
                self.get_region_num(seeds[2], region_order[0], region_order), seeds[2], \
                conferences, region_order, True)
        self.place_team(region_num, seeds[2], '/'.join(matchups[1]))
     
    #find a place in the bracket where a team can fit
    #param team: string of team to place
    #param region_num: region number (0-3) to try to place the team in
    #param seed_num: seed number (1-16) to try to place the team in
    #param conferences: dictionary of conference names and lists of teams already in the tournament
    #param region_order: ordered list of a team's region preferences
    #param for_play_in: whether this team is actually two teams that are matched up in a play-in game
    #returns: the team if we weren't able to place it, the region_num if we were
    def find_team_spot(self, team, region_num, seed_num, conferences, region_order, for_play_in):
        save_team = ()
        bad_regions = set()
        check_switch = False
        orig_region_num = region_num
        
        while not self.check_rules(conferences, team, region_num, seed_num, for_play_in):
            if len(save_team):
                return save_team, -1
            if self.verbose:
                print('rules failed for', str(region_num))
            bad_regions.add(region_num)
            region_num = region_order[(region_order.index(region_num)+1) % 4]
            if self.verbose:
                print('edited region to', region_num)

            #find a region that doesn't have this seed in it (or, if switching is on, try to switch that team for current team)
            while seed_num in self.regions[region_num]:
                if self.verbose:
                    print('already this seed in', str(region_num))
                new_team = self.regions[region_num][seed_num]
                if "/" in new_team:
                    new_for_play_in = True
                else:
                    new_for_play_in = False
                if check_switch and self.check_rules(conferences, team, region_num, seed_num, for_play_in) and \
                        self.check_rules(conferences, new_team, orig_region_num, seed_num, new_for_play_in):
                    self.regions[orig_region_num][seed_num] = new_team
                    if new_for_play_in:
                        self.teams[new_team.split('/')[0]].region = orig_region_num
                        self.teams[new_team.split('/')[1]].region = orig_region_num
                    else:
                        self.teams[new_team].region = orig_region_num
                    if seed_num < 5:
                        site = self.first_weekend_num_to_name[region_num][seed_num]
                        self.first_weekend_num_to_name[orig_region_num][seed_num] = site
                        del self.first_weekend_num_to_name[region_num][seed_num]
                        self.first_weekend_name_to_num[site][self.first_weekend_name_to_num[site].index([region_num, seed_num])] = [orig_region_num, seed_num]
                    if self.verbose:
                        print("Switched (" + str(seed_num) + ") " + new_team + " to: region (" + str(orig_region_num) + ")")
                    bad_regions = set()
                    break
                bad_regions.add(region_num)

                #if we've tried every region, try something else
                if len(bad_regions) == 4:
                    break

                #otherwise, try another region for this team
                region_num = region_order[(region_order.index(region_num)+1) % 4]
                if self.verbose:
                    print('changed region to', region_num)

            #if we haven't tried to switch teams with each other yet, try that
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
                teams_to_fix, sites = self.delete_and_save_seed(seed_num)
                if team not in teams_to_fix:
                    teams_to_fix[-1] = team
                if "/" in team:
                    for play_in_team in team.split("/"):
                        self.teams[play_in_team].region = -1
                        self.teams[play_in_team].seed = -1
                else:
                    self.teams[team].region = -1
                    self.teams[team].seed = -1
                found_perm = False
                for perm in permutations(teams_to_fix):
                    if self.check_perm(conferences, perm, seed_num, team, for_play_in):
                        self.save_and_print_perm(seed_num, perm, sites)
                        region_num = perm.index(team)
                        found_perm = True
                        break

                #if no permutation works, work backward through the seed list trying every permutation of those seeds as well as ours
                if not found_perm:
                    found_perm, save_team = self.try_reorganize(team, seed_num, reorg_seed, teams_to_fix, \
                            conferences, sites)
        return save_team, region_num

    #recurse up the seed list, trying to brute-force a fix to fit all of the teams in the bracket
    def try_reorganize(self, team, seed_num, reorg_seed, teams_to_fix, conferences, sites):
        tries = 0
        curr_reorg_max = 5  #lowest-numbered seed to try reorganizing
        found_perm = False
        while not found_perm:
            reorg_seed -= 1
            if reorg_seed < curr_reorg_max:
                #run through it 100 times
                tries += 1
                if tries <= 100:
                    #don't want to mess up region positioning if possible
                    if self.verbose:
                        print("Retrying from beginning")
                    reorg_seed = seed_num - 1
                else:
                    tries = 0
                    curr_reorg_max -= 1     #can start trying to reorganize with lower seeds as we go
                    if curr_reorg_max < 3:
                        #if self.verbose:
                        save_team = [team, seed_num]
                        if self.verbose:
                            print("moving", team, "down from", seed_num)
                        for fixing_count, fixing_team in enumerate(teams_to_fix):
                            if fixing_team and fixing_team != team:
                                self.regions[fixing_count][seed_num] = fixing_team
                        return False, save_team
            if self.verbose:
                print('trying the next seed up', reorg_seed)
            other_teams_to_fix, other_sites = self.delete_and_save_seed(reorg_seed)
            perm_to_save = list()
            for other_perm in permutations(other_teams_to_fix):
                if self.check_perm(conferences, other_perm, reorg_seed):
                    self.save_and_print_perm(reorg_seed, other_perm, other_sites)
                    perm_to_save = other_perm
                    for perm in permutations(teams_to_fix):
                        if self.check_perm(conferences, perm, seed_num, team):
                            self.save_and_print_perm(seed_num, perm, sites)
                            region_num = perm.index(team)
                            return True, []
            if not found_perm:
                #if nothing worked, save the most recent successful try for this seed and recurse up the seed list
                #this also allows us to loop back through the seeds and have different results
                self.save_and_print_perm(reorg_seed, perm_to_save, other_sites)
        return True, []

    #actually place a team in the bracket after finding a spot for it
    #param region_num: region in which to place the team
    #param seed_num: seed at which to place the team
    #param team: string of team name
    def place_team(self, region_num, seed_num, team):
        self.regions[region_num][seed_num] = team
        if "/" in team:
            self.teams[team.split('/')[0]].region = region_num
            self.teams[team.split('/')[0]].seed = seed_num
            self.teams[team.split('/')[1]].region = region_num
            self.teams[team.split('/')[1]].seed = seed_num
        else:
            self.teams[team].region = region_num
            self.teams[team].seed = seed_num

    #find the first region (according to a team's preferences) that has an empty spot
    #param seed_num: seed at which to place the team
    #param region_num: region in which to attempt to place the team
    #param region_order: order of a team's preferences
    def get_region_num(self, seed_num, region_num, region_order):
        while seed_num in self.regions[region_num]:
            if seed_num > 1:
                region_num = region_order[region_order.index(region_num)+1]
            else:
                region_num = (region_num + 1) % 4
        return region_num

    def save_play_in_team(self, team_list, seed_list, team, seed_num):
        team_list.append(team)
        seed_list.append(seed_num)

    #choose a regional site that a #1 seed will play at
    def choose_regional(self, team, seed_num, region_name_to_num, region_num_to_name, region_num):
        for site_name in self.region_rankings[team]:
            if site_name not in region_name_to_num:
                region_name_to_num[site_name] = region_num
                region_num_to_name[region_num] = site_name
                if self.verbose:
                    print(site_name, "chosen for", region_num)
                break
    
    #choose a first weekend site that a #1-#4 seed will be the highest-seeded team at
    def choose_first_weekend(self, team, region_num, seed_num):
        for site_name in self.first_weekend_rankings[team]:
            if site_name in self.first_weekend_sites:
                if self.verbose:
                    print("Choosing", site_name)
                self.first_weekend_sites.remove(site_name)
                if site_name in self.first_weekend_name_to_num:
                    self.first_weekend_name_to_num[site_name].append([region_num, seed_num])
                else:
                    self.first_weekend_name_to_num[site_name] = [[region_num, seed_num]]
                self.first_weekend_num_to_name[region_num][seed_num] = site_name
                break
 
    #create a bracket based on the ordered team scores
    def build_bracket(self):
        self.regions = [dict(), dict(), dict(), dict()]
        region_num_to_name = dict()
        region_name_to_num = dict()
        region_order = list()
        self.first_weekend_num_to_name = [dict(), dict(), dict(), dict()]
        self.first_weekend_name_to_num = dict()
        auto_count = 0
        at_large_count = 0
        bracket_pos = 1
        conferences = dict()
        at_large_play_in_teams = list()
        at_large_play_in_seeds = list()
        auto_play_in_teams = list()
        auto_play_in_seeds = list()
        save_team = list()
        AUTO_MAX = AUTO_MAXES[self.year]
        AT_LARGE_MAX = 68 - AUTO_MAX

        #traverse seed list, placing teams in bracket as you go
        sorted_teams = sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True)
        team_index = 0
        while team_index < len(sorted_teams):
            team = sorted_teams[team_index]
            team_conference = self.teams[team].conference
            for_play_in = False
            if not (self.teams[team].auto_bid or self.teams[team].at_large_bid):
                team_index += 1
                continue
            if team_conference not in conferences:
                conferences[team_conference] = list()
            conferences[team_conference].append(team)
            seed_num = (bracket_pos + 3) // 4
            if seed_num > 1:
                region_order = self.get_region_order(team, seed_num, region_name_to_num)
                region_num = region_order[0]
            else:
                region_num = bracket_pos - 1

            #if we moved a team down a seed line, try to place it
            if save_team and save_team[1] != seed_num:
                if self.verbose:
                    print("now that we're at", seed_num, "trying", save_team)
                team = save_team[0]
                save_team = list()
                team_index -= 1
            print("placing", team, seed_num)
         
            #save play-in teams to be placed all together
            if self.teams[team].at_large_bid and at_large_count >= AT_LARGE_MAX - 4:
                self.save_play_in_team(at_large_play_in_teams, at_large_play_in_seeds, team, seed_num)
                if at_large_count == AT_LARGE_MAX - 3 or at_large_count == AT_LARGE_MAX - 1:
                    bracket_pos += 1
                if at_large_count == AT_LARGE_MAX - 1:
                    self.place_play_in(at_large_play_in_teams, at_large_play_in_seeds, \
                            region_name_to_num, conferences)
                at_large_count += 1
                team_index += 1
                continue
            
            elif self.teams[team].auto_bid and auto_count >= AUTO_MAX - 4:
                self.save_play_in_team(auto_play_in_teams, auto_play_in_seeds, team, seed_num)
                if auto_count == AUTO_MAX - 3 or auto_count == AUTO_MAX - 1:
                    bracket_pos += 1
                if auto_count == AUTO_MAX - 1:
                    self.place_play_in(auto_play_in_teams, auto_play_in_seeds, \
                            region_name_to_num, conferences)
                auto_count += 1
                team_index += 1
                continue

            #get a region that is empty for the current seed
            region_num = self.get_region_num(seed_num, region_num, region_order)

            #follow the rules to place the team in the bracket
            save_team, region_num = self.find_team_spot(team, region_num, seed_num, conferences, region_order, for_play_in)

            #if the team can't be placed at the current seed, save it
            if len(save_team) and save_team[0] == team:
                for region in self.regions:
                    if seed_num in region and region[seed_num] == team:
                        del region[seed_num]
                team_index += 1
                continue
            else:
                self.place_team(region_num, seed_num, team)
                if self.teams[team].auto_bid:
                    auto_count += 1
                if self.teams[team].at_large_bid:
                    at_large_count += 1

            #if we're placing the top seed, pick a regional site for it
            if seed_num == 1:
                self.choose_regional(team, seed_num, region_name_to_num, region_num_to_name, region_num)

            #if we're placing a top-4 seed, pick a first weekend site for it
            if seed_num < 5:
                self.choose_first_weekend(team, region_num, seed_num)
            
            if self.verbose:
                print("Placed (" + str(seed_num) + ") " + team + \
                        ": region (" + str(region_num) + ") " + region_num_to_name[region_num])
                print()

            bracket_pos += 1

            if not len(save_team) or team != save_team[0]:
                team_index += 1
            else:
                if self.verbose:
                    print("placed", save_team)
                save_team = list()

            #once all the top-four seeds are placed, make sure the regions are reasonably equal
            if team_index == 16:
                self.ensure_region_balance(sorted_teams, conferences)

        max_len = self.get_max_len()
        print()
        for region_nums in [[0, 1], [3, 2]]:
            for seed_num in [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]:
                self.print_line(max_len, region_nums[0], region_nums[1], seed_num, region_num_to_name)

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

