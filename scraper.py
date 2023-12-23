#!/usr/bin/env python3

from datetime import date
from team import Team
from game import Game
from builder import Builder, TEAM_COORDINATES_FILE
from tracker import Tracker
from scorer import Scorer
import os
import sys
import json
import requests
import math
import random

SCRAPE_DATE_FILE = "scrapedate.txt"

reverse_team_dict = dict()

better_team_abbrs = {"San Diego State": "SDSU", 
        "Kansas State": "KSU",
        "Ohio State": "OSU",
        "Oklahoma State": "OKST",
        "Oregon State": "ORST",
        "Michigan State": "MSU",
        "Mississippi State": "MSST",
        "Washington State": "WSU",
        "Texas Tech": "TTU",
        "Indiana State": "INST",
        "Iowa State": "ISU",
        "Georgia Tech": "GT",
        "Virginia Tech": "VT",
        "Colorado State": "CSU",
        "Kentucky": "UK",
        "Saint Mary's": "SMC",
        "Saint John's": "STJN",
        "Saint Joseph's": "STJS",
        "Ole Miss": "MISS",
        "Utah State": "UTST",
        "Texas A&M": "TA&M",
        "San Francisco": "SF",
        "Santa Clara": "SCL",
        "North Carolina": "UNC",
        "North Carolina State": "NCST",
        "Northwestern": "NWST",
        "Notre Dame": "ND",
        "Seton Hall": "HALL",
        "Penn State": "PSU",
        "Eastern Washington": "EWU",
        "George Washington": "GW",
        "Florida State": "FSU",
        "Arizona State": "ASU",
        "Florida": "FLA",
        "Pittsburgh": "PITT",
        "Virginia": "UVA",
        "Grand Canyon": "GCU",
        "South Carolina": "SCAR",
        "Missouri": "MIZZ",
        "New Mexico": "NMX"
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
        
        if self.mens:
            SITE_COORDINATES_FILE = "lib/men/" + self.year + "/site_locations.txt"
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
        else:
            SITE_COORDINATES_FILE = "lib/women/" + self.year + "/site_locations.txt"
            f = open(SITE_COORDINATES_FILE, "r")
            for count, line in enumerate(f):
                site_name = line[:line.find("[")]
                latitude = float(line[line.find("[")+1:line.find(" N, ")-1])
                longitude = float(line[line.find(" N, ")+4:line.find(" W]")-1])
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
            if self.mens:
                first_weekend_rankings[team] = self.get_site_order(first_sites, latitude, longitude)
            region_rankings[team] = self.get_site_order(regional_sites, latitude, longitude)
        f.close()
        return first_weekend_sites, first_weekend_rankings, region_rankings

    #load ineligible teams, eliminated teams, and conference winners for a specific year
    def load_special_teams(self):
        if self.mens:
            SPECIAL_TEAMS_FILE = "lib/men/" + self.year + "/special_teams.json"
        else:
            SPECIAL_TEAMS_FILE = "lib/women/" + self.year + "/special_teams.json"
        with open(SPECIAL_TEAMS_FILE, "r") as f:
            special_teams = json.loads(f.read())
        eliminated_teams = special_teams["eliminated_teams"]
        ineligible_teams = special_teams["ineligible_teams"]
        conference_winners = special_teams["conference_winners"]
        if self.mens:
            ineligible_sites = special_teams["ineligible_sites"]
            return eliminated_teams, ineligible_teams, conference_winners, ineligible_sites
        return eliminated_teams, ineligible_teams, conference_winners, {}

    #grab the data from where it's stored on disk or scrape it if necessary
    #param should_scrape: If true, scrape the data from the web if we haven't yet today
    #param force_scrape: If true, scrape the data from the web regardless of if we have or haven't
    def load_data(self, should_scrape, force_scrape, future, monte_carlo):
        if not os.path.exists(self.datadir):
            print("creating datadir", self.datadir)
            os.makedirs(self.datadir)
        if not os.path.exists(self.datadir + SCRAPE_DATE_FILE):
            f = open(self.datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(self.datadir + SCRAPE_DATE_FILE, "r+")
        today_date = date.today().strftime("%m-%d")    #format: mm-dd
        saved_date = f.read().strip()
        f.close()
        if force_scrape or (should_scrape and today_date != saved_date):
            self.do_scrape(today_date)
        else:
            self.do_load()
        first_weekend_sites, first_weekend_rankings, region_rankings = self.load_coordinates()
        eliminated_teams, ineligible_teams, conference_winners, ineligible_sites = self.load_special_teams()
        return Builder(self.year, self.teams, self.verbose, self.outputfile, first_weekend_sites, \
                first_weekend_rankings, region_rankings, eliminated_teams, ineligible_sites, \
                ineligible_teams, conference_winners, reverse_team_dict, future, monte_carlo)

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
        if self.mens:
            TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketball/" + self.year + "/team-net-sheet?team="
        else:
            TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketballw/" + self.year + "/team-net-sheet?team="
        team_url = TEAM_NITTY_URL_START + team
        self.teams[team] = Team()
        self.teams[team].scrape_data(team, team_url, self.year)
        f = open(self.datadir + team + ".json", "w+")
        f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
        f.close()
        reverse_team_dict[self.teams[team].team_out] = team

    #scrape college basketball data from the web
    #param today_date: MM-DD representation of today's date. written to file to record that scraping took place
    def do_scrape(self, today_date):
        if self.mens:
            net_url = "https://www.warrennolan.com/basketball/" + self.year + "/net"
        else:
            net_url = "https://www.warrennolan.com/basketballw/" + self.year + "/net"
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

    def get_location_prefix(self, game):
        location_prefix = ""
        if game.location == "A":
            location_prefix = "@"
        elif game.location == "N":
            location_prefix = "v. "
        return location_prefix

    def output_resume(self):
        f = open(self.resumefile, "w+")
        f.write("Team,Record,NET,PWR,SOS,Q1,Q2,Q3/4,Q1 wins,Q2+ losses\n")
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            f.write(self.teams[team].team_out + ",")
            f.write("'" + self.teams[team].record + ",")
            f.write(str(self.teams[team].NET) + ",")
            f.write(str(round(self.teams[team].predictive, 3)) + ",")
            f.write(str(self.teams[team].NET_SOS) + ",")
            f.write("'" + self.teams[team].get_derived_record(1) + ",")
            f.write("'" + self.teams[team].get_derived_record(2) + ",")
            
            #quad 4+ wins, quad 3- losses
            q3_record = self.teams[team].get_derived_record(3)
            q4_record = self.teams[team].get_derived_record(4)
            f.write("'" + q4_record[:q4_record.find('-')] + q3_record[q3_record.find('-'):] + ',')
            
            good_wins = list()
            bad_losses = list()
            for game in self.teams[team].games:
                if game.opponent in better_team_abbrs:
                    team_abbr = better_team_abbrs[game.opponent]
                else:
                    team_abbr = game.opponent[:3].upper()
                if game.win and game.quadrant == 1:
                    good_wins.append({"team": self.get_location_prefix(game) + team_abbr, "NET": game.opp_NET})
                elif not game.win and game.quadrant >= 2:
                    bad_losses.append({"team": self.get_location_prefix(game) + game.opponent, "NET": game.opp_NET})
            win_string = '"'
            for game in sorted(good_wins, key=lambda x: x["NET"]):
                win_string += game["team"] + "(" + str(game["NET"]) + "), "
            if len(win_string) > 1:
                win_string = win_string[:-2]
            f.write(win_string)
            f.write('","')
            loss_string = ""
            for game in sorted(bad_losses, key=lambda x: x["NET"]):
                loss_string += game["team"] + " (" + str(game["NET"]) + "), "
            if len(loss_string) > 1:
                loss_string = loss_string[:-2]
            f.write(loss_string)
            f.write('",\n')

#accept command line arguments
def process_args():
    year = "2024"
    argindex = 1
    outputfile = ""
    resumefile = ""
    webfile = ""
    should_scrape = True
    force_scrape = False
    verbose = False
    weightfile = ""
    tracker = False
    mens = True
    future = False
    monte_carlo = False
    simulations = 0

    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-m/-w] [-f] [-c <sims>] [-y year] [-i weightfile] [-o outputfile] [-r resumefile] [-b webfile] [-e|-s] [-v]")
            print("     -h: print this help message")
            print("     -m: men's tournament projection [default]")
            print("     -w: women's tournament projection")
            print("     -f: future (end-of-season) projection. default is to project the field as if the season ended today.")
            print("     -c: Monte Carlo simulation. run <sims> number of simulation and report on how often a team made the tournament/got to final four/won championship")
            print("     -y: make a bracket for given year. 2021-present only")
            print("     -i: use weights located in given file")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -r: set a csv filename where the final readable resume will live")
            print("     -b: set an html filename where the displayed bracket will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -s: scrape data anew regardless of whether data has been scraped today")
            print("     -v: verbose. Print team resumes and bracketing procedure")
            print("     -t: tracker mode. Generate weights and test their effectiveness")
            sys.exit()
        elif sys.argv[argindex] == '-w':
            mens = False
        elif sys.argv[argindex] == '-o':
            outputfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-r':
            resumefile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-b':
            webfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-e':
            should_scrape = False
        elif sys.argv[argindex] == '-t':
            tracker = True
        elif sys.argv[argindex] == '-f':
            future = True
        elif sys.argv[argindex] == '-c':
            monte_carlo = True
            simulations = int(sys.argv[argindex + 1])
            argindex += 1
        elif sys.argv[argindex] == '-v':
            verbose = True
        elif sys.argv[argindex] == '-s':
            force_scrape = True
        elif sys.argv[argindex] == '-i':
            weightfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-y':
            if int(sys.argv[argindex + 1]) < 2021:
                print("year not supported, sorry. Try 2021-present.")
                sys.exit()
            year = sys.argv[argindex + 1]
            argindex += 1
        argindex += 1
    if mens:
        datadir = "data/men/" + year + "/resumes/"
    else:
        datadir = "data/women/" + year + "/resumes/"
    if not weightfile:
        if mens:
            weightfile = "lib/men/weights.txt"
        else:
            weightfile = "lib/women/weights.txt"
    return year, mens, outputfile, resumefile, webfile, datadir, should_scrape, force_scrape, \
            verbose, tracker, weightfile, future, monte_carlo, simulations

def add_or_increment_key(key, dictionary):
    try:
        dictionary[key] += 1
    except KeyError:
        dictionary[key] = 1

def reverse_location(location):
    if location == "A":
        return "H"
    if location == "H":
        return "A"
    return "N"

def simulate_games(scorer, builder, weightfile):
    results = {'tournament': list(), 'final_four': list(), 'champion': list()}
    teams = list(scorer.teams.keys())
    team_kenpoms = dict()
    random.shuffle(teams)
    for team in teams:
        team_kenpom = scorer.kenpom_estimate(scorer.teams[team].KenPom)
        #print(team)
        #print(scorer.teams[team].future_games)
        #print(scorer.teams[team].games)
        for game in scorer.teams[team].future_games:
            game_exists = False
            for existing_game in scorer.teams[team].games:
                if existing_game.date != "10-10":
                    break
                if existing_game.opponent == game['opponent'] and \
                        existing_game.location == game['location']:
                    game_exists = True
                    break
            if game_exists: 
                continue
            opponent = game['opponent']
            if opponent in team_kenpoms:
                opp_kenpom = team_kenpoms[opponent]
            else:
                opp_kenpom = scorer.kenpom_estimate(scorer.teams[opponent].KenPom)
                team_kenpoms[opponent] = opp_kenpom
            team_spread = scorer.get_spread(team_kenpom, opp_kenpom, game['location'])
            win_prob = scorer.get_win_prob(team_spread)
            new_game = Game(scorer.teams[opponent].team_out, game['location'], game['NET'], 75, 0, '10-10')
            opp_game = Game(scorer.teams[team].team_out, reverse_location(game['location']), scorer.teams[team].NET, 0, 75, '10-10')
            win_result = random.random()
            kenpom_change = random.random()
            if win_result < win_prob:
                new_game.opp_score = 70
                opp_game.team_score = 70
                if kenpom_change > 0.85:
                    team_kenpom += 1
                    team_kenpoms[opponent] -= 1
                elif kenpom_change > 0.5:
                    team_kenpom += 0.5
                    team_kenpoms[opponent] -= 0.5
                elif kenpom_change < 0.15:
                    team_kenpom += 0.5
                    team_kenpoms[opponent] -= 0.5
            else:
                new_game.opp_score = 80
                opp_game.team_score = 80
                if kenpom_change < 0.15:
                    team_kenpom -= 1
                    team_kenpoms[opponent] += 1
                elif kenpom_change < 0.5:
                    team_kenpom -= 0.5
                    team_kenpoms[opponent] -= 0.5
                elif kenpom_change > 0.85:
                    team_kenpom += 0.5
                    team_kenpoms[opponent] -= 0.5
            scorer.teams[team].games.add(new_game)
            scorer.teams[opponent].games.add(opp_game)
            for index, future_game in enumerate(scorer.teams[opponent].future_games):
                if future_game['opponent'] == team and future_game['location'] == opp_game.location:
                    break
            try:
                scorer.teams[opponent].future_games = scorer.teams[opponent].future_games[:index] + \
                    scorer.teams[opponent].future_games[index+1:]
            except IndexError:
                scorer.teams[opponent].future_games = scorer.teams[opponent].future_games[:index]
        team_kenpoms[team] = team_kenpom
   
    #print_Illinois(scorer, team_kenpoms)
    weights = scorer.get_weights(weightfile)
    scorer.build_scores(weights, team_kenpoms)
    builder.select_seed_and_print_field()
    builder.build_bracket()
    for team in scorer.teams:
        if scorer.teams[team].auto_bid or scorer.teams[team].at_large_bid:
            results['tournament'].append([team, scorer.teams[team].seed])
    return results

def print_Illinois(scorer, team_kenpoms):
    wins = 0
    losses = 0
    conf_wins = 0
    conf_losses = 0
    for game in scorer.teams["Illinois"].games:
        print(game.opponent.ljust(25), game.location, game.team_score, game.opp_score, game.opp_NET)
        if game.win:
            wins += 1
            try:
                if scorer.teams[game.opponent].conference == "Big Ten":
                    conf_wins += 1
            except KeyError:
                if scorer.teams[reverse_team_dict[game.opponent]].conference == "Big Ten":
                    conf_wins += 1
        else:
            losses += 1
            try:
                if scorer.teams[game.opponent].conference == "Big Ten":
                    conf_losses += 1
            except KeyError:
                if scorer.teams[reverse_team_dict[game.opponent]].conference == "Big Ten":
                    conf_losses += 1
    print(str(wins) + "-" + str(losses) + " (" + str(conf_wins) + "-" + str(conf_losses) + ")")
    print(team_kenpoms["Illinois"])

def run_monte_carlo(simulations, scorer, builder, weightfile):
    made_tournament = dict()
    final_fours = dict()
    national_champion = dict()
    team_seeds = dict()
    first_weekend_sites = list(builder.first_weekend_sites)
    conference_winners = dict(builder.conference_winners)
    for team in scorer.teams:
        scorer.load_schedule(team)
        scorer.teams[team].saved_games = set(scorer.teams[team].games)
        scorer.teams[team].saved_future_games = list([dict(x) for x in scorer.teams[team].future_games])
    for i in range(simulations):
        print("Running sim", i)
        for team in scorer.teams:
            scorer.teams[team].games = set(scorer.teams[team].saved_games)
            scorer.teams[team].future_games = list(scorer.teams[team].saved_future_games)
            scorer.teams[team].at_large_bid = False
            scorer.teams[team].auto_bid = False
        builder.first_weekend_sites = list(first_weekend_sites)
        builder.conference_winners = dict(conference_winners)
        results = simulate_games(scorer, builder, weightfile)
        for team in results['tournament']:
            add_or_increment_key(team[0], made_tournament)
            if team[0] in team_seeds:
                team_seeds[team[0]].append(team[1])
            else:
                team_seeds[team[0]] = [team[1]]
        for team in results['final_four']:
            add_or_increment_key(team, final_fours)
        for team in results['champion']:
            add_or_increment_key(team, national_champion)
    for team in sorted(made_tournament, key=lambda x: sum(team_seeds[x])/made_tournament[x]):
        print(team.ljust(20), made_tournament[team], round(sum(team_seeds[team])/made_tournament[team], 2), \
                min(team_seeds[team]), max(team_seeds[team]))
    print(final_fours)
    print(national_champion)

def main():
    scraper = Scraper()
    scraper.year, scraper.mens, scraper.outputfile, scraper.resumefile, scraper.webfile, scraper.datadir, should_scrape, \
            force_scrape, scraper.verbose, scraper.tracker, weightfile, future, \
            monte_carlo, simulations = process_args()
    builder = scraper.load_data(should_scrape, force_scrape, future, monte_carlo)
    scorer = Scorer(builder, future, scraper.mens, scraper.tracker, monte_carlo)
    if scraper.tracker:
        tracker = Tracker(builder, scorer, scraper.year, scraper.verbose, scraper.mens)
        tracker.load_results()
        tracker.run_tracker(tuple())
        counter = 0
        for weights in sorted(tracker.weight_results, key=lambda x: tracker.weight_results[x]):
            print([str(x).rjust(3) for x in weights], tracker.weight_results[weights])
            counter += 1
            if (scraper.mens and counter > 50) or (not scraper.mens and counter > 100):
                break
    elif monte_carlo:
        run_monte_carlo(simulations, scorer, builder, weightfile)
    else:
        weights = scorer.get_weights(weightfile)
        scorer.build_scores(weights)
        builder.select_seed_and_print_field()
        builder.build_bracket()
        if scraper.outputfile:
            scorer.outputfile = scraper.outputfile
            scorer.output_scores()
        if scraper.resumefile:
            scraper.output_resume()
        if scraper.webfile:
            builder.webfile = scraper.webfile
            builder.output_bracket()

if __name__ == '__main__':
    main()

