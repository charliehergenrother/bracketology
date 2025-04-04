#!/usr/bin/env python3

from itertools import permutations
from datetime import date
import math

AUTO_MAXES = {"2020": 32, "2021": 31, "2022": 32, "2023": 32, "2024": 32, "2025": 31}
TEAM_COORDINATES_FILE = "lib/team_locations.txt"

#class to build a bracket from resume ratings of college basketball teams
class Builder:

    def __init__(self, m, year, teams, verbose, of, fws, fwr, rr, et, iss, it, cw, rtd, fu, mc):
        self.mens = m
        self.year = year
        self.teams = teams
        self.verbose = verbose
        self.outputfile = of
        self.first_weekend_sites = fws
        self.first_weekend_rankings = fwr
        self.region_rankings = rr
        self.eliminated_teams = et
        self.ineligible_sites = iss
        self.ineligible_teams = it
        self.conference_winners = cw
        self.reverse_team_dict = rtd
        self.first_weekend_coords = dict()
        self.future = fu
        self.monte_carlo = mc
        return

    #seed and print the field, including a bubble section
    def select_seed_and_print_field(self):
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
            if team in self.eliminated_teams or (self.conference_winners[self.teams[team].conference] and \
                    self.conference_winners[self.teams[team].conference] != team):
                #teams under .500 are ineligible for at-large bids
                if self.teams[team].record_pct < 0.5 and not self.future:
                    continue
                if at_large_bids < AT_LARGE_MAX:
                    at_large_bids += 1
                    at_large_bid = True
                    self.teams[team].at_large_bid = True
                elif bubble_count < 4:
                    bubble_string += (self.teams[team].team_out + " - First Four Out\n")
                    bubble_count += 1
                    self.teams[team].seed = "FFO"
                    continue
                elif bubble_count < 8:
                    bubble_string += (self.teams[team].team_out + " - Next Four Out\n")
                    bubble_count += 1
                    self.teams[team].seed = "NFO"
                    continue
                else:
                    continue
            else:
                if self.teams[team].conference != "Independent" and \
                        ((self.teams[team].conference in self.conference_winners and \
                        self.conference_winners[self.teams[team].conference] == team) or \
                        (self.conference_winners[self.teams[team].conference] == "" and \
                        team not in self.eliminated_teams and auto_bids < AUTO_MAX)):
                    auto_bids += 1
                    self.conference_winners[self.teams[team].conference] = team
                    self.teams[team].auto_bid = True
                else:
                    continue
            if not self.monte_carlo:
                print("(" + str(curr_seed) + ") " + self.teams[team].team_out, end="")
            if at_large_bid:
                if at_large_bids >= AT_LARGE_MAX - 3:
                    if (AT_LARGE_MAX - at_large_bids) % 2 == 1:
                        curr_seed_max += 1
                    bubble_string += (self.teams[team].team_out + " - Last Four In\n")
                    if not self.monte_carlo:
                        print(" - Last Four In")
                elif at_large_bids >= AT_LARGE_MAX - 7:
                    bubble_string += (self.teams[team].team_out + " - Last Four Byes\n")
                    if not self.monte_carlo:
                        print(" - Last Four Byes")
                else:
                    if not self.monte_carlo:
                        print()
            elif not self.monte_carlo:
                print("*")
            if num_curr_seed == curr_seed_max and curr_seed < 16:
                curr_seed += 1
                num_curr_seed = 1
                curr_seed_max = 4
            else:
                num_curr_seed += 1
        if not self.monte_carlo:
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
    
    #construct a line of the bracket
    #param max_len: maximum length of a line containing two teams
    #param region_1: 0 or 3, corresponding to one of the regions on the left side of the bracket
    #param region_2: 1 or 2, corresponding to one of the regions on the right side of the bracket
    #param seed: seed of the teams to print
    def construct_line(self, max_len, region_1, region_2, seed):
        line = ""
        team_1 = self.get_team_out(self.regions[region_1][seed])
        team_2 = self.get_team_out(self.regions[region_2][seed])
        if (seed == 16) or ("/" not in team_1 and self.teams[self.regions[region_1][seed]].auto_bid):
            team_1 += "*"
        if (seed == 16) or ("/" not in team_2 and self.teams[self.regions[region_2][seed]].auto_bid):
            team_2 += "*"
        max_site_len = max([len(x) for x in self.first_weekend_name_to_num])
        line += " "*max_site_len + "(" + str(seed) + ") " + team_1 + \
                " "*(max_len - (len(team_1) + len(team_2)) - (len(str(seed)) + 3)*2) + \
                " (" + str(seed) + ") " + team_2 + "\n"
        if seed == 13:
            region_1_name = self.region_num_to_name[region_1]
            region_2_name = self.region_num_to_name[region_2]
            line += " "*(20 + max_site_len) + region_1_name + " "*max([max_len - (len(region_1_name) + len(region_2_name) + 40), 5]) + region_2_name
        elif seed == 16:
            site_1 = self.first_weekend_num_to_name[region_1][1]
            site_2 = self.first_weekend_num_to_name[region_2][1]
            line += site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2
        elif seed == 12: 
            site_1 = self.first_weekend_num_to_name[region_1][4]
            site_2 = self.first_weekend_num_to_name[region_2][4]
            line += site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2
        elif seed == 11: 
            site_1 = self.first_weekend_num_to_name[region_1][3]
            site_2 = self.first_weekend_num_to_name[region_2][3]
            line += site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2
        elif seed == 10:
            site_1 = self.first_weekend_num_to_name[region_1][2]
            site_2 = self.first_weekend_num_to_name[region_2][2]
            line += site_1 + " "*(max_site_len - len(site_1) + 1) + " "*max_len + site_2
        return line

    #check if placing a team in a particular bracket location will follow all the rules
    #param team: name of team to attempt to place
    #param region_num: region number (0-3) to try to place the team in
    #param seed_num: seed number (1-16) to try to place the team in
    def check_rules(self, team, region_num, seed_num, for_play_in=False):
        if team == "":
            return True
        if "/" in team:
            return (self.check_rules(team.split("/")[0], region_num, seed_num, for_play_in) and \
                    self.check_rules(team.split("/")[1], region_num, seed_num, for_play_in))
        
        team_conference = self.teams[team].conference
        if self.mens and seed_num > 4:   #men's teams can't play at their home court
            first_weekend_site = self.first_weekend_num_to_name[region_num][self.get_host_seed(seed_num)]
            region_site = self.region_num_to_name[region_num]
            for site in [first_weekend_site, region_site]:
                #if site == region_site and team == "BYU":   #TODO: this was making me mad so. fix later, I guess
                #    continue
                if team in self.ineligible_sites[site]:
                    if self.verbose:
                        print(team, "can't play in", site, "you silly goose")
                    return False

        #the top four teams from a conference must be in different regions if they are on the top four seed lines
        if self.conferences[team_conference].index(team) < 4 and seed_num <= 4:
            for test_team in self.conferences[team_conference][:3]:
                if test_team == team:
                    continue
                try:
                    if self.teams[test_team].region == region_num and self.teams[test_team].seed <= 4:
                        if self.verbose:
                            print("multiple top four teams can't all go here", region_num, self.conferences[team_conference])
                        return False
                except AttributeError:      #there are two teams from this conference in the play-ins
                    continue

        #two teams from the same conference cannot meet before the...
            #...regional final (Elite 8) if they've played 3 times
            #...regional semifinal (Sweet 16) if they've played 2 times
            #...second round if they've played 1 time
        for test_team in self.conferences[team_conference]:
            if test_team == team:
                continue
            try:
                if self.teams[test_team].region != region_num or self.teams[test_team].region == -1:
                    continue
            except AttributeError:      #there are two teams from this conference in the play-ins
                continue
            game_count = 0
            for game in self.teams[test_team].games:
                if game.opponent == team:
                    game_count += 1
            if self.future:
                for game in self.teams[test_team].future_games:
                    if game['opponent'] == team:
                        game_count += 1
            if self.teams[test_team].seed + seed_num == 17: #first round matchup
                if self.verbose:
                    print("teams are meeting too early in this region", region_num, team, test_team)
                return False
            #TODO BUG: when we check if a play in team can go in a spot, this works correctly.
            #The rules about meeting too early are waived.
            #However, when we check if the better team can play a play in team, this works incorrectly.
            #The team object doesn't have that information.
            if game_count >= 2:     #sweet 16 matchup
                for seed_set in [[1, 16, 8, 9], [5, 12, 4, 13], [6, 11, 3, 14], [7, 10, 2, 15]]:
                    if self.teams[test_team].seed in seed_set and seed_num in seed_set and not for_play_in \
                            and self.teams[test_team].seed != seed_num:
                        if self.verbose:
                            print("teams are meeting tooo early in this region", region_num, team, test_team)
                        return False
            if game_count >= 3:     #elite 8 matchup
                for seed_set in [[1, 16, 8, 9, 5, 12, 4, 13], [6, 11, 3, 14, 7, 10, 2, 15]]:
                    if self.teams[test_team].seed in seed_set and seed_num in seed_set and not for_play_in \
                            and self.teams[test_team].seed != seed_num:
                        if self.verbose:
                            print("teams are meeting toooo early in this region", region_num, team, test_team)
                        return False

        #Want to avoid regular season rematches in the first round
        if 17 - seed_num in self.regions[region_num]:
            for game in self.teams[team].games:
                if game.opponent == self.regions[region_num][17 - seed_num]:
                    if self.verbose:
                        print("regular season rematch in the first round")
                    return False
        if self.future and 17 - seed_num in self.regions[region_num]:
            for game in self.teams[team].future_games:
                if game['opponent'] == self.regions[region_num][17 - seed_num]:
                    if self.verbose:
                        print("regular season rematch in the first round")
                    return False

        return True

    #remove all teams from their seed lines in order to attempt to reorganize them
    #param seed_num: seed number to delete
    #returns: list of teams being deleted, list of [team, region_num, site_name] for each
    #TODO BUG: if a team gets bumped down past one play-in game, but not both, this breaks. the play-in matchup doesn't get deleted and saved
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
        if seed_num < 5:
            if self.verbose:
                print(seed_num, "Deleted", teams_to_fix, sites)
        return teams_to_fix, sites

    #check a permutation of four teams to see if the bracket can accept it
    #param perm: permutation of four teams on the same seed line
    #param seed_num: seed of teams
    def check_perm(self, perm, seed_num, team="", for_play_in=False):
        play_in = dict()
        for counter, perm_team in enumerate(perm):
            if perm_team and (team == perm_team or "/" in perm_team) and for_play_in:
                if not self.check_rules(perm_team, counter, seed_num, True):
                    return False
            else:
                if not self.check_rules(perm_team, counter, seed_num, False):
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
                if seed_num in self.regions[region_num]:
                    del self.regions[region_num][seed_num]
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

    def get_host_seed(self, seed_num):
        if seed_num in [1, 16, 8, 9]:
            host_seed = 1
        elif seed_num in [4, 5, 12, 13]:
            host_seed = 4
        elif seed_num in [3, 6, 11, 14]:
            host_seed = 3
        elif seed_num in [2, 7, 10, 15]:
            host_seed = 2
        return host_seed

    #return a list of a team's regional preferences
    #param team: string of team to get preferences for
    #param seed_num: seed of team. if higher (i.e. lower number) than 5, use regional sites; otherwise, use first-weekend sites
    def get_region_order(self, team, seed_num):
        order = list()
        if seed_num < 5:
            for site in self.region_rankings[team]:
                order.append(self.region_name_to_num[site])
        else:
            #construct list of possible sites
            host_seed = self.get_host_seed(seed_num)
            possible_sites = list()
            for index, region in enumerate(self.first_weekend_num_to_name):
                try:
                    possible_sites.append(region[host_seed])
                except KeyError:
                    print(team, seed_num)
                    print(self.regions)
                    print(self.first_weekend_num_to_name)
                    raise KeyError
            if self.mens:
                for site in self.first_weekend_rankings[team]:
                    while site in possible_sites:
                        order.append(possible_sites.index(site))
                        possible_sites[possible_sites.index(site)] = ""
            else:   #womens
                site_distances = dict()
                for site in self.first_weekend_coords:
                    distance = math.sqrt((self.teams[team].latitude - self.first_weekend_coords[site][0])**2 + \
                            (self.teams[team].longitude - self.first_weekend_coords[site][1])**2)
                    site_distances[site] = distance
                site_order = list()
                for site in sorted(site_distances, key=lambda x: site_distances[x]):
                    site_order.append(site)
                for site in site_order:
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
    def ensure_region_balance(self, sorted_teams):
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
            found_perm = False
            for perm in permutations(teams_to_fix):
                if perm in bad_perms:
                    continue
                if self.check_perm(perm, 4, "", False):
                    self.save_and_print_perm(4, perm, sites)
                    found_perm = True
                    break
            if not found_perm:
                bad_perms = [bad_perms[0]]
                continue
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
    def place_play_in(self, teams, seeds):
        matchups = self.get_play_in_matchups(teams)
        matchup_1 = '/'.join(matchups[0])
        matchup_2 = '/'.join(matchups[1])

        region_order = self.get_region_order(matchups[0][0], seeds[0])
        save_team_1, region_num = self.find_team_spot(matchup_1, \
                self.get_region_num(seeds[0], region_order[0], region_order), seeds[0],\
                region_order, True)
        if region_num != -1:
            self.place_team(region_num, seeds[0], matchup_1)
            if self.verbose:
                print("Placed (" + str(seeds[0]) + ") " + matchup_1 + \
                    ": region (" + str(region_num) + ") " + self.region_num_to_name[region_num])

        region_order = self.get_region_order(matchups[1][0], seeds[2])
        save_team_2, region_num = self.find_team_spot(matchup_2, \
                self.get_region_num(seeds[2], region_order[0], region_order), seeds[2], \
                region_order, True)
        if region_num != -1:
            self.place_team(region_num, seeds[2], matchup_2)
            if self.verbose:
                print("Placed (" + str(seeds[2]) + ") " + matchup_2 + \
                    ": region (" + str(region_num) + ") " + self.region_num_to_name[region_num])
                print()
        if len(save_team_1) and len(save_team_2):
            return tuple([save_team_1, save_team_2])
        if len(save_team_1):
            return save_team_1
        return save_team_2

    def replace_from_sites(self, seed_num, sites):
        for team in sites:
            team_name = team[0]
            region_num = team[1]
            site_name = team[2]
            self.regions[region_num][seed_num] = team_name
            self.first_weekend_name_to_num[site_name].append([region_num, seed_num])
            self.first_weekend_num_to_name[region_num][seed_num] = site_name
            self.teams[team_name].region = region_num
            self.teams[team_name].seed = seed_num
 
    #find a place in the bracket where a team can fit
    #param team: string of team to place
    #param region_num: region number (0-3) to try to place the team in
    #param seed_num: seed number (1-16) to try to place the team in
    #param region_order: ordered list of a team's region preferences
    #param for_play_in: whether this team is actually two teams that are matched up in a play-in game
    #returns: the team if we weren't able to place it, the region_num if we were
    def find_team_spot(self, team, region_num, seed_num, region_order, for_play_in):
        save_team = ()
        bad_regions = set()
        check_switch = False
        orig_region_num = region_num
        
        while not self.check_rules(team, region_num, seed_num, for_play_in):
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
                if check_switch and self.check_rules(team, region_num, seed_num, for_play_in) and \
                        self.check_rules(new_team, orig_region_num, seed_num, new_for_play_in):
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
                        print("Switched (" + str(seed_num) + ") " + new_team + " to: region (" + str(orig_region_num) + ") " + self.region_num_to_name[orig_region_num])
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
                    if self.check_perm(perm, seed_num, team, for_play_in):
                        self.save_and_print_perm(seed_num, perm, sites)
                        region_num = perm.index(team)
                        found_perm = True
                        break

                #if no permutation works, work backward through the seed list trying every permutation of those seeds as well as ours
                if not found_perm:
                    found_perm, save_team, region_num = self.try_reorganize(team, seed_num, reorg_seed, teams_to_fix, \
                            sites, for_play_in)
                    if save_team:
                        break
        return save_team, region_num

    #recurse up the seed list, trying to brute-force a fix to fit all of the teams in the bracket
    def try_reorganize(self, team, seed_num, reorg_seed, teams_to_fix, sites, for_play_in):
        tries = 0
        curr_reorg_max = 3  #lowest-numbered seed to try reorganizing
        while True:
            reorg_seed -= 1
            if reorg_seed < curr_reorg_max:
                #run through it 100 times
                tries += 1
                if tries <= 100:
                    #don't want to mess up region positioning if possible
                    if self.verbose:
                        print("Retrying from beginning")
                    reorg_seed = seed_num
                else:
                    tries = 0
                    curr_reorg_max -= 1     #can start trying to reorganize with lower seeds as we go
                    if curr_reorg_max < 3:
                        save_team = [team, seed_num]
                        if self.verbose:
                            print("moving", team, "down from", seed_num)
                        for fixing_count, fixing_team in enumerate(teams_to_fix):
                            if fixing_team and fixing_team != team:
                                self.regions[fixing_count][seed_num] = fixing_team
                        return False, save_team, -1
            if reorg_seed == curr_reorg_max:    #we've gone as far as we can go
                if self.verbose:
                    print("Moving", team, "down from", seed_num)
                if seed_num < 5:
                    self.replace_from_sites(seed_num, sites)
                else:
                    index = 3
                    while index > 0:
                        if teams_to_fix[index]:
                            teams_to_fix[index] = ""
                            break
                        index -= 1
                    for perm in permutations(teams_to_fix):
                        if self.verbose:
                            print(perm)
                        if self.check_perm(perm, seed_num, team, for_play_in):
                            self.save_and_print_perm(seed_num, perm, [])
                            return False, [team, seed_num], -1
                    
                    #oops, we messed up the bracket such that we can't fit the original teams back in. hopefully we can fix it.
                    found_perm, second_save_team, region_num = self.try_reorganize(teams_to_fix[0], seed_num, reorg_seed, teams_to_fix, \
                            sites, for_play_in)
                    if found_perm:
                        return False, [team, seed_num], -1
                    raise IndexError
                    continue
                return False, [team, seed_num], -1
            if self.verbose:
                print('trying the next seed up', reorg_seed)
            other_teams_to_fix, other_sites = self.delete_and_save_seed(reorg_seed)
            perm_to_save = list()
            for other_perm in permutations(other_teams_to_fix):
                if self.check_perm(other_perm, reorg_seed, "", for_play_in):
                    self.save_and_print_perm(reorg_seed, other_perm, other_sites)
                    perm_to_save = other_perm
                    for perm in permutations(teams_to_fix):
                        if self.check_perm(perm, seed_num, team, for_play_in):
                            self.save_and_print_perm(seed_num, perm, sites)
                            region_num = perm.index(team)
                            return True, [], region_num
            #if nothing worked, save the most recent successful try for this seed and recurse up the seed list
            #this also allows us to loop back through the seeds and have different results
            if perm_to_save:
                self.save_and_print_perm(reorg_seed, perm_to_save, other_sites)
            else:
                print(self.regions)
                print(teams_to_fix, seed_num)
                print(other_teams_to_fix, reorg_seed)
                raise IndexError
        return True, [], region_num

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
                try:
                    region_num = region_order[region_order.index(region_num)+1]
                except IndexError:
                    print(seed_num, region_order, region_num)
                    print(self.regions)
                    raise IndexError
            else:
                region_num = (region_num + 1) % 4
        return region_num

    def save_play_in_team(self, team_list, seed_list, team, seed_num):
        team_list.append(team)
        seed_list.append(seed_num)
        self.teams[team].play_in = True

    #choose a regional site that a #1 seed will play at
    def choose_regional(self, team, seed_num, region_num):
        for site_name in self.region_rankings[team]:
            if site_name not in self.region_name_to_num and \
                    (not self.first_weekend_sites or team not in self.ineligible_sites[site_name]):
                self.region_name_to_num[site_name] = region_num
                self.region_num_to_name[region_num] = site_name
                if self.verbose:
                    print(site_name, "chosen for", region_num)
                break
    
    #choose a first weekend site that a #1-#4 seed will be the highest-seeded team at
    def choose_first_weekend(self, team, region_num, seed_num, team_index):
        if self.mens:
            for site_name in self.first_weekend_rankings[team]:
                if site_name in self.first_weekend_sites and team not in self.ineligible_sites[site_name]:
                    if self.verbose:
                        print("Choosing", site_name)
                    self.first_weekend_sites.remove(site_name)
                    if site_name in self.first_weekend_name_to_num:
                        self.first_weekend_name_to_num[site_name].append([region_num, seed_num])
                    else:
                        self.first_weekend_name_to_num[site_name] = [[region_num, seed_num]]
                    self.first_weekend_num_to_name[region_num][seed_num] = site_name
                    break
            if seed_num not in self.first_weekend_num_to_name[region_num]:
                if self.verbose:
                    print("no remaining sites work for", team)
                #couldn't choose a site bc the only site left is one where a team is ineligible to play at
                sorted_teams = sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True)
                remaining_site = self.first_weekend_sites[0]
                check_team_index = team_index
                #grab previously-placed team. thanks for making this difficult, BYU
                while True:
                    check_team_index -= 1
                    team_to_switch = self.teams[sorted_teams[check_team_index]]
                    if self.verbose:
                        print("try to switch with", team_to_switch.team_out)
                    if self.teams[sorted_teams[check_team_index]].seed < 1: #team hasn't been placed
                        continue
                    team_switch_site = self.first_weekend_num_to_name[team_to_switch.region][team_to_switch.seed]
                    if team_switch_site in self.first_weekend_sites: #we already know the team can't go there
                        continue
                    if team in self.ineligible_sites[team_switch_site]: #BYU, you can't go here either
                        continue
                    self.do_site_switch(team_to_switch, team_switch_site, self.first_weekend_sites[0], region_num, seed_num)
                    break

        else:   #womens
            site_name = self.get_team_out(team)
            self.first_weekend_name_to_num[site_name] = [[region_num, seed_num]]
            self.first_weekend_num_to_name[region_num][seed_num] = site_name
            f = open(TEAM_COORDINATES_FILE)
            for line in f:
                site_team = line[:line.find("[")]
                if site_team == team:
                    latitude = float(line[line.find("[")+1:line.find(" N, ")-1])
                    longitude = float(line[line.find(" N, ")+4:line.find(" W]")-1])
                    break
            self.first_weekend_coords[site_name] = [latitude, longitude]
               
    def do_site_switch(self, team_to_switch, team_switch_site, remaining_site, region_num, seed_num):
        self.first_weekend_num_to_name[region_num][seed_num] = team_switch_site
        coord_index = 0
        switch_site_list = self.first_weekend_name_to_num[team_switch_site]
        while coord_index < len(switch_site_list):
            if switch_site_list[coord_index][0] == team_to_switch.region and switch_site_list[coord_index][1] == team_to_switch.seed:
                del self.first_weekend_name_to_num[team_switch_site][coord_index]
                break
            coord_index += 1
        self.first_weekend_name_to_num[team_switch_site].append([region_num, seed_num])
                
        self.first_weekend_num_to_name[team_to_switch.region][team_to_switch.seed] = remaining_site
        if remaining_site not in self.first_weekend_name_to_num:
            self.first_weekend_name_to_num[remaining_site] = [[team_to_switch.region, team_to_switch.seed]]
        else:
            self.first_weekend_name_to_num[remaining_site].append([team_to_switch.region, team_to_switch.seed])

    #create a bracket based on the ordered team scores
    def build_bracket(self):
        self.regions = [dict(), dict(), dict(), dict()]
        self.region_num_to_name = dict()
        self.region_name_to_num = dict()
        region_order = list()
        self.first_weekend_num_to_name = [dict(), dict(), dict(), dict()]
        self.first_weekend_name_to_num = dict()
        auto_count = 0
        at_large_count = 0
        self.conferences = dict()
        at_large_play_in_teams = list()
        at_large_play_in_seeds = list()
        auto_play_in_teams = list()
        auto_play_in_seeds = list()
        save_team = list()
        saved_teams = list()
        self.seed_list = list()
        AUTO_MAX = AUTO_MAXES[self.year]
        AT_LARGE_MAX = 68 - AUTO_MAX

        #traverse seed list, placing teams in bracket as you go
        sorted_teams = sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True)
        team_index = 0
        while team_index < len(sorted_teams):
            team = sorted_teams[team_index]
            team_conference = self.teams[team].conference
            for_play_in = False
            placing_saved_team = False
            if not (self.teams[team].auto_bid or self.teams[team].at_large_bid):
                team_index += 1
                continue
            
            seed_count = 4
            seed_num = 0
            while seed_count == 4 and seed_num < 16:
                play_in_count = 0
                seed_count = 0
                seed_num += 1
                for region_num in [0, 1, 2, 3]:
                    if seed_num in self.regions[region_num]:
                        seed_count += 1
                for seed in at_large_play_in_seeds:
                    if seed == seed_num:
                        play_in_count += 1
                if self.teams[team].at_large_bid and (not saved_teams or saved_teams[0][0] != team):
                    seed_count += play_in_count // 2
                else:
                    seed_count += (play_in_count + 1) // 2
            #print(team, seed_num, at_large_count, auto_count)
            #print(self.regions)

            if seed_num > 1:
                region_order = self.get_region_order(team, seed_num)
                try:
                    region_num = region_order[0]
                except IndexError:
                    print(team, seed_num)
                    print(self.regions)
                    print(self.first_weekend_num_to_name)
                    raise IndexError
            else:
                region_num = team_index

            #if we moved a team down a seed line, try to place it
            if saved_teams and saved_teams[0][1] != seed_num:
                if self.verbose:
                    print("now that we're at", seed_num, "trying", saved_teams[0])
                team = saved_teams[0][0]
                saved_teams.pop(0)
                placing_saved_team = True
                if "/" not in team:
                    team_index -= 1
            else:
                if team_conference not in self.conferences:
                    self.conferences[team_conference] = list()
                self.conferences[team_conference].append(team)
                self.seed_list.append(self.teams[team].team_out)
            if self.verbose:
                print("placing", team, seed_num)
            
            #we had to move a play-in matchup down a seed
            if "/" in team:
                region_order = self.get_region_order(team.split("/")[0], seed_num)
                save_team, region_num = self.find_team_spot(team, \
                    self.get_region_num(seed_num, region_order[0], region_order), seed_num,\
                    region_order, True)
                if len(save_team):
                    saved_teams.append(save_team)
                else:
                    self.place_team(region_num, seed_num, team)
                continue
            #save play-in teams to be placed all together
            elif self.teams[team].at_large_bid and at_large_count >= AT_LARGE_MAX - 4 and (not placing_saved_team):
                self.save_play_in_team(at_large_play_in_teams, at_large_play_in_seeds, team, seed_num)
                if at_large_count == AT_LARGE_MAX - 1:
                    #print("placing", at_large_play_in_teams, at_large_play_in_seeds)
                    save_team = self.place_play_in(at_large_play_in_teams, at_large_play_in_seeds)
                    if len(save_team):
                        if self.verbose:
                            print("problems with", save_team, self.regions)
                        if type(save_team) == tuple:    #couldn't place either play-in matchup in the bracket
                            saved_teams.append(save_team[0])
                            saved_teams.append(save_team[1])
                        else:
                            saved_teams.append(save_team)
                    at_large_play_in_teams = list()
                    at_large_play_in_seeds = list()
                at_large_count += 1
                team_index += 1
                continue
            
            elif self.teams[team].auto_bid and auto_count >= AUTO_MAX - 4:
                self.save_play_in_team(auto_play_in_teams, auto_play_in_seeds, team, seed_num)
                if auto_count == AUTO_MAX - 1:
                    self.place_play_in(auto_play_in_teams, auto_play_in_seeds)
                auto_count += 1
                team_index += 1
                continue

            #get a region that is empty for the current seed
            region_num = self.get_region_num(seed_num, region_num, region_order)

            #follow the rules to place the team in the bracket
            save_team, region_num = self.find_team_spot(team, region_num, seed_num, region_order, for_play_in)

            if not placing_saved_team:
                if self.teams[team].auto_bid:
                    auto_count += 1
                if self.teams[team].at_large_bid:
                    at_large_count += 1
            #if the team can't be placed at the current seed, save it
            if len(save_team) and save_team[0] == team:
                for region in self.regions:
                    if seed_num in region and region[seed_num] == team:
                        del region[seed_num]
                team_index += 1
                saved_teams.append(save_team)
                save_team = list()
                continue
            else:
                self.place_team(region_num, seed_num, team)

            #if we're placing the top seed, pick a regional site for it
            if seed_num == 1:
                self.choose_regional(team, seed_num, region_num)

            #if we're placing a top-4 seed, pick a first weekend site for it
            if seed_num < 5:
                self.choose_first_weekend(team, region_num, seed_num, team_index)
            
            if self.verbose:
                print("Placed (" + str(seed_num) + ") " + team + \
                        ": region (" + str(region_num) + ") " + self.region_num_to_name[region_num])
                print()

            if not len(save_team) or team != save_team[0]:
                team_index += 1
            else:
                if self.verbose:
                    print("placed", save_team)
                save_team = list()

            #once all the top-four seeds are placed, make sure the regions are reasonably equal
            #if team_index == 16:
                #self.ensure_region_balance(sorted_teams)

        try:
            max_len = self.get_max_len()
        except KeyError:
            print(self.regions)
            raise KeyError
        if not self.monte_carlo:
            print()
            for region_nums in [[0, 1], [3, 2]]:
                for seed_num in [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]:
                    print(self.construct_line(max_len, region_nums[0], region_nums[1], seed_num))
    
    def projection_type(self):
        if self.future:
            return "Projected Selection Sunday Bracket"
        return "Projected Bracket (if the season ended today)"

    def output_meta(self, f, styling_path=""):
        f.write('<!DOCTYPE html>\n\n')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write('  <link rel="icon" type="image/x-icon" href="' + styling_path + 'assets/chergieball.ico">\n')
        f.write('  <link rel="stylesheet" href="' + styling_path + 'styling.css">\n')
        f.write('</head>\n\n')
 
    def output_link_row(self, f, styling_path=""):
        f.write('<div class="link_row">\n')
        f.write('  <nav>\n')
        f.write('    <ul class="link_list">\n')
        f.write('      <li>\n')
        f.write('        <img src=' + styling_path + 'assets/chergieball.ico height="50px" style="padding-top: 5px;"></img>\n')
        f.write('      </li>\n')
        f.write('      <li class="non_image_element">\n')
        f.write('        <b style="font-size: 20px;">Charlie Hergenrother\'s Bracketology</b>\n')
        f.write('      </li>\n')
        f.write('      <li class="non_image_element dropdown_element">\n')
        f.write('        <button class="dropdown_button">Men\'s Bracketology</button>\n')
        f.write('        <div class="dropdown_content">\n')
        f.write('          <a href="men.html">Men\'s Bracket</a>\n')
        f.write('          <a href="menfuture.html">Men\'s Future Bracket</a>\n')
        f.write('          <a href="menresumes.html">Men\'s Resumes</a>\n')
        f.write('          <a href="menschedule.html">Men\'s Schedule</a>\n')
        f.write('        </div>\n')
        f.write('      </li>\n')
        f.write('      <li class="non_image_element dropdown_element">\n')
        f.write('        <button class="dropdown_button">Women\'s Bracketology</button>\n')
        f.write('        <div class="dropdown_content">\n')
        f.write('          <a href="women.html">Women\'s Bracket</a>\n')
        f.write('          <a href="womenfuture.html">Women\'s Future Bracket</a>\n')
        f.write('          <a href="womenresumes.html">Women\'s Resumes</a>\n')
        f.write('          <a href="womenschedule.html">Women\'s Schedule</a>\n')
        f.write('        </div>\n')
        f.write('      </li>\n')
        f.write('      <li class="non_image_element link_element">\n')
        f.write('        <a href="about.html">About</a>\n')
        f.write('      </li>\n')
        f.write('    </ul>\n')
        f.write('  </nav>\n')
        f.write('</div>\n')
 
    def output_bracket(self):
        site_seed_lines = {8: 1, 4: 4, 3: 3, 2: 2}
        f = open(self.webfile, "w")
        self.output_meta(f)
        self.output_link_row(f)
        f.write('<body>\n\n')
        f.write('<div class="title_row">\n')
        f.write('  <h3> ' + self.projection_type() + '</h3>\n')
        f.write('</div>\n')
        f.write('<div class="date_row">\n')
        f.write('  <h4>Updated: ' + date.today().strftime("%m/%d/%y") + '</h4>\n')
        f.write('</div>\n')
        f.write('<div class="bracket_container">\n')
        f.write('  <div class="region_column column1">\n')
        for region_num in [0, 3, 1, 2]:
            if region_num == 1:
                f.write('  </div>\n')
                f.write('  <div class="region_column column2">\n')
            f.write('    <div class="table_container" id="region' + str(region_num) + '">\n')
            f.write('      <h2 class="region_header">' + self.region_num_to_name[region_num] + '</h2>\n')
            f.write('      <table class="region_table">\n')
            if region_num in [0, 3]:
                f.write('        <colgroup><col class="siteleftcol"><col class="seedcol"><col class="logocol"><col></colgroup>\n')
            else:
                f.write('        <colgroup><col class="seedcol"><col class="logocol"><col><col class="siterightcol"></colgroup>\n')
            f.write('        <tbody>\n')
            for seed_num in [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]:
                if seed_num in [1, 16, 8, 9, 6, 11, 3, 14]:
                    f.write('          <tr class="bracket_row gray_row">')
                else:
                    f.write('          <tr class="bracket_row">')
                if region_num in [0, 3]:
                    f.write('<td>')
                    if seed_num in [8, 4, 3, 2]:
                        f.write(self.first_weekend_num_to_name[region_num][site_seed_lines[seed_num]])
                    f.write('</td>')
                team = self.regions[region_num][seed_num]
                f.write('<td>(' + str(seed_num) + ')</td>')
                
                if "/" not in team:
                    f.write('<td><img class="team_logo" src=assets/' + team + '.png></img></td><td>' + self.get_team_out(team))
                    if self.teams[team].auto_bid:
                        f.write("*")
                    f.write(" (" + self.teams[team].record + ")</td>")
                else:
                    team1 = team.split("/")[0]
                    team2 = team.split("/")[1]
                    f.write('<td><img class="tiny_logo" src=assets/' + team1 + '.png></img>' + \
                            '<img class="tiny_logo" src=assets/' + team2 + '.png></img></td><td>' + \
                        self.get_team_out(team1))
                    if self.teams[team1].auto_bid:
                        f.write("*")
                    f.write(" (" + self.teams[team1].record + ")/" + self.get_team_out(team2))
                    if self.teams[team2].auto_bid:
                        f.write("*")
                    f.write(" (" + self.teams[team2].record + ")</td>")
                if region_num in [1, 2]:
                    f.write('<td>')
                    if seed_num in [8, 4, 3, 2]:
                        f.write(self.first_weekend_num_to_name[region_num][site_seed_lines[seed_num]])
                    f.write('</td>')
                f.write('</tr>\n')

            f.write('        </tbody>\n')
            f.write('      </table>\n')
            f.write('    </div>\n')
        f.write('  </div>\n')
        f.write('</div>\n\n')
        f.write('<div class="bubble_container table_container">\n')
        f.write('  <table class="bubble_table">\n')
        f.write('    <tbody>\n')
        f.write('      <tr class="gray_row bubble_row"><td><h4>Last Four Byes</h4></td>')
        at_large_counter = 0
        bubble_counter = 0
        AT_LARGE_MAX = 68 - AUTO_MAXES[self.year]
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            if self.teams[team].at_large_bid:
                at_large_counter += 1
                if at_large_counter > AT_LARGE_MAX - 8:
                    f.write('<td><img class="team_logo" src=assets/' + team + '.png></img></td><td>' + \
                        self.get_team_out(team) + ' (' + self.teams[team].record + ')</td>')
                    if at_large_counter == AT_LARGE_MAX - 4:
                        f.write('</tr>\n')
                        f.write('      <tr class="bubble_row"><td><h4>Last Four In</h4></td>')
                    elif at_large_counter == AT_LARGE_MAX:
                        f.write('</tr>\n')
                        f.write('      <tr class="gray_row bubble_row"><td><h4>First Four Out</h4></td>')
            elif not self.teams[team].auto_bid and team not in self.ineligible_teams:
                bubble_counter += 1
                f.write('<td><img class="team_logo" src=assets/' + team + '.png></img></td><td>' + \
                        self.get_team_out(team) + ' (' + self.teams[team].record + ')</td>')
                if bubble_counter == 4:
                    f.write('</tr>\n')
                    f.write('      <tr class="bubble_row"><td><h4>Next Four Out</h4></td>')
                elif bubble_counter == 8:
                    f.write('</tr>\n')
                    break
        f.write('    </tbody>\n')
        f.write('  </table>\n')
        f.write('</div>\n')
        f.write('<div class="conference_container table_container">\n')
        f.write('  <table>\n')
        f.write('    <tr class="header_row gray_row">')
        rows = list()
        columns = len([x for x in self.conferences if len(self.conferences[x]) > 1])
        for confindex, conference in enumerate(sorted(self.conferences, key=lambda x: len(self.conferences[x]), reverse=True)):
            if len(self.conferences[conference]) > 1:
                f.write('<td>' + conference + ' - ' + str(len(self.conferences[conference])) + '</td>')
                for teamindex, team in enumerate(self.conferences[conference]):
                    if len(rows) == teamindex:
                        rows.append(['']*columns)
                    rows[teamindex][confindex] = (team, self.teams[team].seed)
        f.write('</tr>\n')
        for index, row in enumerate(rows):
            if index % 2:
                f.write('    <tr class="gray_row">')
            else:
                f.write('    <tr>')
            for team in row:
                if type(team) == tuple:
                    f.write('<td>' + self.teams[team[0]].team_out + ' (' + str(team[1]) + ')</td>')
            f.write('</tr>\n')
        f.write('  </table>\n')
        f.write('</div>\n')
        f.write('<div class="seed_list_container">\n')
        f.write('  <ol>\n')
        for team in self.seed_list:
            f.write('    <li>' + team + '</li>\n')
        f.write('  </ol>\n')
        f.write('</div>\n')
        f.write('</body>\n')
        f.write('</html>\n')








