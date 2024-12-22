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
import subprocess
import numpy

SCRAPE_DATE_FILE = "scrapedate.txt"
TEAM_MEN_URL_START = "https://www.warrennolan.com/basketball/2025/team-clubhouse?team="
TEAM_WOMEN_URL_START = "https://www.warrennolan.com/basketballw/2025/team-clubhouse?team="

reverse_team_dict = dict()

#for use when outputting resumes in "Q1 Wins" column
better_team_abbrs = {
        "UC-Irvine": "UCI",
        "San-Diego-State": "SDSU", 
        "Kansas-State": "KSU",
        "Ohio-State": "OSU",
        "Oklahoma-State": "OKST",
        "Oregon-State": "ORST",
        "Michigan-State": "MSU",
        "Mississippi-State": "MSST",
        "Washington-State": "WSU",
        "Texas-Tech": "TTU",
        "Indiana-State": "INST",
        "Iowa-State": "ISU",
        "Georgia-Tech": "GT",
        "Virginia-Tech": "VT",
        "Colorado-State": "CSU",
        "Kentucky": "UK",
        "Saint-Marys-College": "SMC",
        "Saint-Johns": "STJN",
        "Saint-Josephs": "STJS",
        "Saint-Bonaventure": "STBN",
        "Ole-Miss": "MISS",
        "Utah-State": "UTST",
        "Texas-AM": "TA&M",
        "San-Francisco": "SF",
        "Santa-Clara": "SCL",
        "North-Carolina": "UNC",
        "North-Carolina-State": "NCST",
        "Northwestern": "NWST",
        "Notre-Dame": "ND",
        "Seton-Hall": "HALL",
        "Penn-State": "PSU",
        "Eastern-Washington": "EWU",
        "FGCU": "FGCU",
        "Green-Bay": "GB",
        "George-Washington": "GW",
        "Florida-State": "FSU",
        "Arizona-State": "ASU",
        "Florida": "FLA",
        "Colorado": "COLO",
        "Pittsburgh": "PITT",
        "Stanford": "STAN",
        "Richmond": "RICH",
        "Rice": "RICE",
        "Iowa": "IOWA",
        "Utah": "UTAH",
        "Oklahoma": "OKLA",
        "Arizona": "ARIZ",
        "Providence": "PROV",
        "Wake-Forest": "WAKE",
        "Virginia": "UVA",
        "Georgia": "UGA",
        "Grand-Canyon": "GCU",
        "George-Mason": "GMU",
        "South-Carolina": "SCAR",
        "Missouri": "MIZZ",
        "New-Mexico": "NMX",
        "Boston-College": "BC",
        "Tennessee": "TENN",
        "Minnesota": "MINN",
        "Washington": "WASH",
        "Connecticut": "CONN",
        "Villanova": "VILL",
        "Marquette": "MARQ",
        "Clemson": "CLEM",
        "West-Virginia": "WVU",
        "UCLA": "UCLA",
        "UNLV": "UNLV",
        "North-Texas": "NTX",
        "Maryland": "MARY",
        "Michigan": "MICH",
        "James-Madison": "JMU",
        "Middle-Tennessee": "MTSU",
        "South-Dakota-State": "SDKS",
        "Ball-State": "BALL",
        "South-Florida": "USF"
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
        else:
            SITE_COORDINATES_FILE = "lib/women/" + self.year + "/site_locations.txt"
        f = open(SITE_COORDINATES_FILE, "r")
        for count, line in enumerate(f):
            site_name = line[:line.find("[")]
            latitude = float(line[line.find("[")+1:line.find(" N, ")-1])
            longitude = float(line[line.find(" N, ")+4:line.find(" W]")-1])
            if self.mens:
                if count < 8:
                    first_sites[site_name] = [latitude, longitude]
                    #two pods at each site, so append each site twice
                    first_weekend_sites.append(site_name)
                    first_weekend_sites.append(site_name)
                else:
                    regional_sites[site_name] = [latitude, longitude]
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
        return Builder(self.mens, self.year, self.teams, self.verbose, self.outputfile, first_weekend_sites, \
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
                    games.add(Game(game_obj["opponent"], game_obj["location"], \
                        game_obj["team_score"], game_obj["opp_score"], game_obj["date"]))
                curr_team = Team()
                curr_team.fill_data(team_obj["conference"], team_obj["NET"], team_obj["KenPom"], team_obj["BPI"],
                        team_obj["Sagarin"], team_obj["Trank"], team_obj["KPI"], team_obj["SOR"], team_obj["WAB"],
                        team_obj["NET_SOS"], team_obj["noncon_SOS"], games, team_obj["team_out"])
                self.teams[filename[:filename.find(".json")]] = curr_team
                team = filename[:filename.find(".json")]
                reverse_team_dict[curr_team.team_out] = team
    
    #fetch one team's data from warrennolan.com
    #team: string indicating which team's data should be scraped
    def scrape_team_data(self, team):
        if self.mens:
            TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketball/" + self.year + "/team-net-sheet?team="
        else:
            TEAM_NITTY_URL_START = "https://www.warrennolan.com/basketballw/" + self.year + "/team-net-sheet?team="
        team_url = TEAM_NITTY_URL_START + team
        self.teams[team] = Team()
        self.teams[team].scrape_data(team, team_url, self.year)
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
        
        #TODO women's pages not working yet
        reverse_team_dict["West Georgia"] = "West-Georgia"
        reverse_team_dict["Mercyhurst"] = "Mercyhurst"
        reverse_team_dict["IU Indianapolis"] = "IU-Indianapolis"
        
        for team in self.teams:
            #go back through and back-translate
            for game in self.teams[team].games:
                game.opponent = reverse_team_dict[game.opponent]
            f = open(self.datadir + team + ".json", "w+")
            f.write(json.dumps(self.teams[team], cls=ComplexEncoder))
            f.close()

        f = open(self.datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

    def load_schedule_data(self, should_scrape, force_scrape):
        if self.mens:
            schedule_datadir = "data/men/" + self.year + "/schedules/"
        else:
            schedule_datadir = "data/women/" + self.year + "/schedules/"
        if not os.path.exists(schedule_datadir):
            print("creating schedules dir")
            os.makedirs(schedule_datadir)
        if not os.path.exists(schedule_datadir + SCRAPE_DATE_FILE):
            f = open(schedule_datadir + SCRAPE_DATE_FILE, "x")
            f.close()
        f = open(schedule_datadir + SCRAPE_DATE_FILE, "r+")
        today_date = date.today().strftime("%m-%d")    #format: mm-dd
        saved_date = f.read().strip()
        f.close()
        if force_scrape or (should_scrape and today_date != saved_date):
            self.do_schedule_scrape(schedule_datadir, today_date)
        else:
            self.do_schedule_load(schedule_datadir)

    def do_schedule_scrape(self, schedule_datadir, today_date):
        month_translations = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06", \
                "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"}
        for team in self.teams:
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
                elif "images" in line and "TBD" not in line and "conf-logo" not in line and "NA3" not in line:
                    found_game = True
                    opp_name = line[line.find("80x80")+6:line.find(".png")]
                    game["opponent"] = opp_name
                elif "team-schedule__info-tv" in line:
                    if "TV: " in line:
                        game["channel"] = line[line.find("TV: ")+4:line.find("</span>")]
                    else:
                        game["channel"] = ""
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
                            schedule_games.append(game)
                        found_result = False
                        found_game = False
                    elif "team-schedule__result" in line:           # game is in the past
                        found_result = True
                        continue
            f = open(schedule_datadir + team + ".json", "w+")
            f.write(json.dumps(schedule_games))
            f.close()
            print("scraped", team, "schedule!")
            self.teams[team].future_games = schedule_games
        f = open(schedule_datadir + SCRAPE_DATE_FILE, "w+")
        f.write(today_date)
        f.close()

    def do_schedule_load(self, schedule_datadir):
        for team in self.teams:
            filename = team + ".json"
            f = open(schedule_datadir + filename, "r")
            sched_obj = json.loads(f.read())
            self.teams[team].future_games = sched_obj

    #translate warrennolan.com's representation of a game's location to mine for outputting to resume
    def get_location_prefix(self, game):
        location_prefix = ""
        if game.location == "A":
            location_prefix = "@"
        elif game.location == "N":
            location_prefix = "v. "
        return location_prefix

    #construct the strings for a team's Q1 wins and Q2 and below losses for use in the resume
    def get_wins_losses_strings(self, scorer, builder, team):
        good_wins = list()
        bad_losses = list()
        quality_seeds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, "FFO", "NFO"]
        for game in self.teams[team].games:
            if game.opponent in better_team_abbrs:
                team_abbr = better_team_abbrs[game.opponent]
            else:
                team_abbr = game.opponent[:3].upper()
            if game.win and (scorer.get_quadrant(self.teams[game.opponent].NET, game.location) == 1 or \
                    (hasattr(builder.teams[game.opponent], "seed") and \
                    builder.teams[game.opponent].seed in quality_seeds)):
                good_wins.append({"team": self.get_location_prefix(game) + team_abbr, "NET": self.teams[game.opponent].NET})
            elif not game.win and scorer.get_quadrant(self.teams[game.opponent].NET, game.location) >= 2:
                bad_losses.append({"team": self.get_location_prefix(game) + game.opponent, "NET": self.teams[game.opponent].NET})
        win_string = ''
        loss_string = ''
        for game in sorted(good_wins, key=lambda x: x["NET"]):
            win_string += game["team"] + "(" + str(game["NET"]) + "), "
        if len(win_string) > 1:
            win_string = win_string[:-2]
        for game in sorted(bad_losses, key=lambda x: x["NET"]):
            loss_string += game["team"] + " (" + str(game["NET"]) + "), "
        if len(loss_string) > 1:
            loss_string = loss_string[:-2]
 
        return win_string, loss_string

    def get_derived_record(self, scorer, team, quad_num):
        wins = 0
        losses = 0
        for game in self.teams[team].games:
            game_quad = scorer.get_quadrant(self.teams[game.opponent].NET, game.location)
            if game.win and game_quad <= quad_num:
                wins += 1
            if not game.win and game_quad >= quad_num:
                losses += 1
        return str(wins) + "-" + str(losses)

    #output a csv file containing resume information about all college basketball teams
    def output_resume(self, scorer, builder):
        f = open(self.resumefile, "w+")
        f.write("Team,Record,NET,PWR,RES,SOS,Q1,Q2,Q3/4,Quality Wins,Q2+ losses\n")
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            f.write(self.teams[team].team_out + ",")
            f.write("'" + self.teams[team].record + ",")
            f.write(str(self.teams[team].NET) + ",")
            f.write(str(round(self.teams[team].predictive, 3)) + ",")
            f.write(str(round(self.teams[team].results_based, 3)) + ",")
            f.write(str(self.teams[team].NET_SOS) + ",")
            f.write("'" + self.get_derived_record(scorer, team, 1) + ",")
            f.write("'" + self.get_derived_record(scorer, team, 2) + ",")
            
            #quad 4+ wins, quad 3- losses
            q3_record = self.get_derived_record(scorer, team, 3)
            q4_record = self.get_derived_record(scorer, team, 4)
            f.write("'" + q4_record[:q4_record.find('-')] + q3_record[q3_record.find('-'):] + ',')
           
            win_string, loss_string = self.get_wins_losses_strings(scorer, builder, team)
            f.write('"' + win_string + '","' + loss_string + '"\n')
    
    #output an HTML resume page for all college basketball teams
    def output_resume_html(self, filename, scorer, builder):
        f = open(filename, "w")
        builder.output_meta(f)
        builder.output_link_row(f)
        f.write('<body>\n')
        f.write('<div class="table_container">\n')
        f.write('  <table class="resume_table">\n')
        f.write('    <colgroup><col class="teamcol"><col class="recordcol"><col class="rankcol">')
        if self.mens:   #power & strength of schedule columns, no data for women
            f.write('<col class="rankcol"><col class="rankcol">')
        f.write('<col class="recordcol"><col class="recordcol"><col class="recordcol"><col class="wincol"><col class="losscol"></colgroup>\n')
        f.write('    <tbody>\n')
        f.write('      <tr class="header_row"><td>Team</td><td>Record</td><td>NET</td>')
        if self.mens:
            f.write('<td>Power</td><td>RES</td>')
        f.write('<td>Q1</td><td>Q2</td><td>Q3/4</td><td>Quality Wins</td><td>Q2+ losses</td></tr>\n')
        for index, team in enumerate(sorted(scorer.teams, key=lambda x: scorer.teams[x].score, reverse=True)):
            if not index % 2:
                f.write('      <tr class="gray_row resume_row">')
            else:
                f.write('      <tr class="resume_row">')
            f.write('<td>' + scorer.teams[team].team_out + '</td>')
            f.write('<td>' + scorer.teams[team].record + '</td>')
            f.write('<td>' + str(scorer.teams[team].NET) + '</td>')
            if self.mens:
                f.write('<td>' + str(round(scorer.teams[team].predictive, 2)) + '</td>')
                f.write('<td>' + str(round(scorer.teams[team].results_based, 2)) + '</td>')
            f.write('<td>' + self.get_derived_record(scorer, team, 1) + '</td>')
            f.write('<td>' + self.get_derived_record(scorer, team, 2) + '</td>')
            #quad 4+ wins, quad 3- losses
            q3_record = self.get_derived_record(scorer, team, 3)
            q4_record = self.get_derived_record(scorer, team, 4)
            f.write('<td>' + q4_record[:q4_record.find('-')] + q3_record[q3_record.find('-'):] + '</td>')
            win_string, loss_string = self.get_wins_losses_strings(scorer, builder, team)
            f.write('<td>' + win_string + '</td>')
            f.write('<td>' + loss_string + '</td>')
            f.write('</tr>\n')


        f.write('    </tbody>\n')
        f.write('  </table>\n')
        f.write('</div>\n')
        f.write('</body>\n')
        f.write('</html>\n')

    #output an HTML page containing a schedule of tournament-relevant college basketball games
    def output_schedule_html(self, filename, scorer, builder):
        f = open(filename, "w")
        builder.output_meta(f)
        builder.output_link_row(f)
        f.write('<body>\n')
        f.write('<div class="schedule_block">\n')
        future_games = dict()

        for team in sorted(scorer.teams, key=lambda x: scorer.teams[x].score, reverse=True):
            try:
                team_seed = int(scorer.teams[team].seed)
            except AttributeError:  #team not tourney-relevant
                continue
            except ValueError:      #team is First Four Out or Next Four Out
                if scorer.teams[team].seed == "FFO":
                    team_seed = 13
                if scorer.teams[team].seed == "NFO":
                    team_seed = 14
            if not hasattr(scorer.teams[team], "seed") or \
                    (type(scorer.teams[team].seed) == int and scorer.teams[team].seed > 12):
                continue
            for game in scorer.teams[team].future_games:
                try:
                    game_score = team_seed + int(scorer.teams[game["opponent"]].seed)
                except AttributeError:
                    game_score = team_seed + 20
                except ValueError:
                    if scorer.teams[game["opponent"]].seed == "FFO":
                        game_score = team_seed + 13
                    if scorer.teams[game["opponent"]].seed == "NFO":
                        game_score = team_seed + 14
                if game["date"] in future_games and (game["opponent"], team, reverse_location(game["location"]), \
                        game["time"], game["channel"], game_score) not in future_games[game["date"]]:
                    future_games[game["date"]].append((team, game["opponent"], game["location"], \
                            game["time"], game["channel"], game_score))
                elif game["date"] not in future_games:
                    future_games[game["date"]] = [(team, game["opponent"], game["location"], \
                            game["time"], game["channel"], game_score)]

        month_translations = {"10": "October", "11": "November", "12": "December", "01": "January", \
                "02": "February", "03": "March"}
        for month in month_translations:
            for day in range(1, 32):
                strday = str(day)
                datestring = month + "-" + strday
                if datestring in future_games:
                    f.write('  <h2>' + month_translations[month] + ' ' + strday + '</h2>\n')
                    f.write('  <table class="schedule_table">\n')
                    gray = True
                    #TODO: move this to own function, run on AM games and then PM games
                    for game in sorted(future_games[datestring], key=lambda x: sorted_time(x[3])):
                        if game[2] == "H":
                            try:
                                away_seed = "(" + str(scorer.teams[game[1]].seed) + ") "
                            except AttributeError:
                                away_seed = ""
                            away_team = game[1]
                            location = '@'
                            try:
                                home_seed = "(" + str(scorer.teams[game[0]].seed) + ") "
                            except AttributeError:
                                home_seed = ""
                            home_team = game[0]
                        elif game[2] == "A":
                            try:
                                away_seed = "(" + str(scorer.teams[game[0]].seed) + ") "
                            except AttributeError:
                                away_seed = ""
                            away_team = game[0]
                            location = '@'
                            try:
                                home_seed = "(" + str(scorer.teams[game[1]].seed) + ") "
                            except AttributeError:
                                home_seed = ""
                            home_team = game[1]
                        elif game[2] == "N":
                            try:
                                away_seed = "(" + str(scorer.teams[game[0]].seed) + ") "
                            except AttributeError:
                                away_seed = ""
                            away_team = game[0]
                            location = 'v.'
                            try:
                                home_seed = "(" + str(scorer.teams[game[1]].seed) + ") "
                            except AttributeError:
                                home_seed = ""
                            home_team = game[1]
                        f.write('    <tr class="game_line')
                        if gray:
                            f.write(' gray_row')
                        f.write('"><td>' + away_seed)
                        f.write('<img class="team_logo" src=assets/' + away_team + '.png></img>')
                        f.write(scorer.teams[away_team].team_out + ' ' + location + ' ' + home_seed)
                        f.write('<img class="team_logo" src=assets/' + home_team + '.png></img>')
                        f.write(scorer.teams[home_team].team_out + '</td>')
                        f.write('<td>' + game[3] + '</td><td>' + game[4] + '</td>')
                        f.write('</tr>\n')
                        gray = not gray
                    f.write('</table>\n')    
        f.write('</div>\n')
        f.write('</body>\n')
        f.write('</html>\n')

#accept command line arguments
def process_args():
    year = "2025"
    argindex = 1
    outputfile = ""
    resumefile = ""
    webfile = ""
    resumewebfile = ""
    upcomingschedulefile = ""
    should_scrape = True
    force_scrape = False
    verbose = False
    weightfile = ""
    tracker = False
    mens = True
    future = False
    monte_carlo = False
    mc_outputfile = ""
    simulations = 0

    while argindex < len(sys.argv):
        if sys.argv[argindex] == '-h':
            print("Welcome to auto-bracketology!")
            print("Usage:")
            print("./scraper.py [-h] [-m/-w] [-y year] [-f [-g schedulefile]] [-c <sims> [-d montecarlofile]] [-i weightfile] [-o outputfile] [-r resumefile] [-b webfile] [-u resumewebfile] [-e|-s] [-t] [-v]")
            print("     -h: print this help message")
            print("     -m: men's tournament projection [default]")
            print("     -w: women's tournament projection")
            print("     -y: make a bracket for given year. 2021-present only")
            print("     -f: future (end-of-season) projection. default is to project the field as if the season ended today.")
            print("     -g: set an html filename where the upcoming schedule will live")
            print("     -c: Monte Carlo simulation. run <sims> number of simulation and report on how often a team made the tournament/got to final four/won championship")
            print("     -d: set a csv filename where the monte carlo output will live")
            print("     -i: use weights located in given file")
            print("     -o: set a csv filename where the final ranking will live")
            print("     -r: set a csv filename where the final readable resume will live")
            print("     -b: set an html filename where the displayed bracket will live")
            print("     -u: set an html filename where the resume page will live")
            print("     -e: override the scraping and use data currently stored")
            print("     -s: scrape data anew regardless of whether data has been scraped today")
            print("     -t: tracker mode. Generate weights and test their effectiveness")
            print("     -v: verbose. Print team resumes and bracketing procedure")
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
        elif sys.argv[argindex] == '-u':
            resumewebfile = sys.argv[argindex + 1]
            argindex += 1
        elif sys.argv[argindex] == '-g':
            upcomingschedulefile = sys.argv[argindex + 1]
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
        elif sys.argv[argindex] == '-d':
            mc_outputfile = sys.argv[argindex + 1]
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
    return year, mens, outputfile, resumefile, webfile, resumewebfile, upcomingschedulefile, \
            datadir, should_scrape, force_scrape, verbose, tracker, weightfile, future, \
            monte_carlo, mc_outputfile, simulations

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

def simulate_one_tournament_game(team1, team2, team_kenpoms, scorer):
    if "/" in team2:
        team2 = simulate_one_tournament_game(team2.split("/")[0], team2.split("/")[1], team_kenpoms, scorer)
    win_prob = scorer.get_win_prob(team_kenpoms[team1]["rating"], team_kenpoms[team2]["rating"], 'N')
    #print(round(win_prob*100, 2), end="% ")
    win_result = random.random()
    kenpom_change = random.random()
    if win_result < win_prob:
        winner = team1
        #print(team1, "over", team2)
    else:
        winner = team2
        #print(team2, "over", team1)
    return winner

def simulate_tournament(builder, team_kenpoms, scorer):
    winners = list()
    for region_num in [0, 3, 1, 2]:
        for seed in [1, 8, 5, 4, 6, 3, 7, 2]:
            team_1 = builder.regions[region_num][seed]
            team_2 = builder.regions[region_num][17 - seed]
            #if "/" not in team_1 and "/" not in team_2:
                #print(seed, team_1, team_kenpoms[team_1], 'vs.', 17-seed, team_2, team_kenpoms[team_2], end=": ")
            winners.append(simulate_one_tournament_game(team_1, team_2, team_kenpoms, scorer))
            #print(winners[-1])
    index = 0
    while index + 1 < len(winners):
        #print(winners[index], team_kenpoms[winners[index]], 'vs.', winners[index + 1], team_kenpoms[winners[index + 1]], end=": ")
        winners.append(simulate_one_tournament_game(winners[index], winners[index + 1], team_kenpoms, scorer))
        #print(winners[-1])
        index += 2
    return winners

def top_wins(tied_champs, team):
    wins_vs_champs = 0
    losses_vs_champs = 0
    for game in team.games:
        if game.opponent in tied_champs:
            if game.win:
                wins_vs_champs += 1
            else:
                losses_vs_champs += 1
    try:
        return wins_vs_champs/(wins_vs_champs + losses_vs_champs)
    except ZeroDivisionError:
        return 0

def simulate_conference_tournaments(scorer, builder, team_kenpoms):
    conference_teams = dict()
    with open("lib/ctourn_formats.json", "r") as f:
        formats = json.loads(f.read())
    for conference in builder.conference_winners:
        conference_teams[conference] = list()
    for team in scorer.teams:
        conference_teams[scorer.teams[team].conference].append(
                {"name": team,
                 "conference_wins": scorer.teams[team].conference_wins,
                 "conference_losses": scorer.teams[team].conference_losses}
                )
    conf_reg_winners = dict()
    for conference in conference_teams:
        #BUILD BRACKET FORMAT
        tourn_format = formats[conference]["format"]
        ineligible_teams = formats[conference]["ineligible_winners"]
        reseed = tourn_format[0] == "R"
        if tourn_format[0] == "R":
            tourn_format = tourn_format[1:]
        rounds = []
        while tourn_format:
            rounds.append(tourn_format[0:2])
            tourn_format = tourn_format[2:]
        num_teams = 1
        bracket = []
        for rnd in reversed(rounds):
            matchups = []
            cur_round_teams = int(rnd[0])
            if cur_round_teams == num_teams * 2:
                num_teams *= 2
                if not reseed:
                    higher_seed = 1
                    lower_seed = num_teams
                    for _ in range(cur_round_teams//2):
                        matchups.append([higher_seed, lower_seed])
                        higher_seed += 1
                        lower_seed -= 1
            else:
                num_teams += cur_round_teams//2
                if not reseed:
                    higher_seed = num_teams - (cur_round_teams - 1)
                    lower_seed = num_teams
                    for _ in range(cur_round_teams//2):
                        matchups.append([higher_seed, lower_seed])
                        higher_seed += 1
                        lower_seed -= 1
            if not reseed:
                bracket = list(matchups) + bracket

        #SET UP BRACKET WITH TEAMS
        #TODO make sure this is working. Add NET as tiebreaker
        seeds = []
        top_seed_wins = max([x["conference_wins"] for x in conference_teams[conference]])
        tied_champs = list(filter(lambda x: x["conference_wins"] == top_seed_wins, conference_teams[conference]))
        tied_champs = [x["name"] for x in tied_champs]
        for team in sorted(conference_teams[conference],
                    key=lambda x: (x["conference_wins"], top_wins(tied_champs, scorer.teams[x["name"]]), scorer.get_NET_estimate(scorer.teams[x["name"]].NET, team_kenpoms[x["name"]]["rank"])), reverse=True):
            seeds.append(team["name"])
            if len(seeds) == num_teams:
                break
        conf_reg_winners[conference] = seeds[0]
        seed_to_team = dict()
        for index, team in enumerate(seeds):
            seed_to_team[index + 1] = team
        seeds_to_use = list(seeds)
        previous_winners = []
        num_eliminated_teams = 0
        for rnd in rounds:
            cur_round_teams = int(rnd[0])
            round_location = rnd[1]
            higher_seed = num_teams - (cur_round_teams - 1) - num_eliminated_teams
            lower_seed = num_teams - num_eliminated_teams
            matchups = []
            for _ in range(cur_round_teams//2):
                if reseed:
                    matchups.append([seeds_to_use[higher_seed-1], seeds_to_use[lower_seed-1]])
                else:
                    matchups.append([seed_to_team[higher_seed], seed_to_team[lower_seed]])
                higher_seed += 1
                lower_seed -= 1
            for matchup in matchups:
                win_prob = scorer.get_win_prob(team_kenpoms[matchup[0]]["rating"], team_kenpoms[matchup[1]]["rating"], round_location)
                win_result = random.random()
                if reseed:
                    if win_result < win_prob:
                        seeds_to_use.remove(matchup[1])
                    else:
                        seeds_to_use.remove(matchup[0])
                else:
                    if win_result >= win_prob:
                        seed_to_team[lower_seed] = matchup[1]
                num_eliminated_teams += 1
        if reseed:
            if len(seeds_to_use) == 1:
                if seeds_to_use[0] not in ineligible_teams:
                    builder.conference_winners[conference] = seeds_to_use[0]
                else:
                    index = 0
                    while seeds[index] in ineligible_teams:
                        index += 1
                    builder.conference_winners[conference] = seeds[index]
            else:
                print("wuh oh")
                sys.exit()
        else:
            if seed_to_team[1] not in ineligible_teams:
                builder.conference_winners[conference] = seed_to_team[1]
            else:
                index = 0
                while seeds[index] in ineligible_teams:
                    index += 1
                builder.conference_winners[conference] = seeds[index]
    return conf_reg_winners

#run one simulation of the rest of the college basketball season
def simulate_games(scorer, builder, weights, team_kenpoms):
    #TODO: all the games are using the present day's NET. Hmm.
    # probably should divorce the NET from a team's opponents
    # 1 - scrape pages for results and games
    # 2 - generate NET ranks. if present, present NET, if future, build estimate
    # 3 - build scores
    results = {'tournament': list(), 'final_four': list(), 'champion': list(), 'conference': dict()}
    for conference in builder.conference_winners:
        results['conference'][conference] = list()
    teams = list(scorer.teams.keys())
    random.shuffle(teams)
    for team in teams:
        team_kenpom = team_kenpoms[team]
        for game in scorer.teams[team].games:
            if game.date == "10-10":   #previously simulated game
                continue
            opponent = game.opponent
            if scorer.teams[team].conference == scorer.teams[opponent].conference:
                if game.win:
                    scorer.teams[team].conference_wins += 1
                else:
                    scorer.teams[team].conference_losses += 1
        for game in scorer.teams[team].future_games:
            game_exists = False
            for existing_game in scorer.teams[team].games:
                if existing_game.date != "10-10":   #previously simulated game
                    break
                if existing_game.opponent == game['opponent'] and \
                        existing_game.location == game['location']:
                    game_exists = True
                    break
            if game_exists: 
                continue
            opponent = game['opponent']
            conference_game = scorer.teams[team].conference == scorer.teams[opponent].conference
            opp_kenpom = team_kenpoms[opponent]
            win_prob = scorer.get_win_prob(team_kenpom['rating'], opp_kenpom['rating'], game['location'])
            new_game = Game(opponent, game['location'], 75, 0, '10-10')
            opp_game = Game(team, reverse_location(game['location']), 0, 75, '10-10')
            win_result = random.random()
            if win_result < win_prob:
                new_game.opp_score = 70
                opp_game.team_score = 70
                if conference_game:
                    scorer.teams[team].conference_wins += 1
                    scorer.teams[opponent].conference_losses += 1
            else:
                new_game.opp_score = 80
                opp_game.team_score = 80
                if conference_game:
                    scorer.teams[team].conference_losses += 1
                    scorer.teams[opponent].conference_wins += 1
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
   
    if builder.mens:
        conf_reg_winners = simulate_conference_tournaments(scorer, builder, team_kenpoms)
    #print_Illinois(scorer, team_kenpoms)
    scorer.build_scores(weights)
    builder.select_seed_and_print_field()
    builder.build_bracket()
    for team in scorer.teams:
        if scorer.teams[team].auto_bid or scorer.teams[team].at_large_bid:
            results['tournament'].append([team, scorer.teams[team].seed])
    winners = simulate_tournament(builder, team_kenpoms, scorer)
    results['final_four'] += winners[-7:-3]
    results['champion'].append(winners[-1])
    if builder.mens:
        for conference in conf_reg_winners:
            results['conference'][conference].append(conf_reg_winners[conference])
    return results

def print_Illinois(scorer, team_kenpoms):
    wins = 0
    losses = 0
    conf_wins = 0
    conf_losses = 0
    for game in scorer.teams["Illinois"].games:
        print("W" if game.team_score > game.opp_score else "L", end=' ')
        print(game.opponent.ljust(25), game.location, game.team_score, game.opp_score)
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

def translate_team_sonny(team):
    translations = {
            "St. Peter'S": "Saint-Peters",
            "Texas Rio Grande Valley": "UTRGV",
            "Nebraska Omaha": "Omaha",
            "Byu": "BYU",
            "Texas El Paso": "UTEP",
            "Southern Mississippi": "Southern-Miss",
            "Queens Nc": "Queens",
            "St. Joseph'S Pa.": "Saint-Josephs",
            "Wisconsin Green Bay": "Green-Bay",
            "Vcu": "VCU",
            "Long Island University": "Long-Island",
            "St. Thomas Mn.": "Saint-Thomas",
            "Smu": "SMU",
            "St. John'S": "Saint-Johns",
            "California Riverside": "UC-Riverside",
            "Tarleton": "Tarleton-State",
            "Iupui": "IU-Indianapolis",
            "Pennsylvania": "Penn",
            "William & Mary": "William-Mary",
            "Texas Arlington": "UTA",
            "Miami Florida": "Miami-FL",
            "Tennessee Chattanooga": "Chattanooga",
            "North Carolina Charlotte": "Charlotte",
            "Southern Cal": "USC",
            "Utah Valley St.": "Utah-Valley",
            "Oakland Mi": "Oakland",
            "Nevada Las Vegas": "UNLV",
            "Missouri Kansas City": "UMKC",
            "Massachusetts": "UMass",
            "Louisiana-Monroe": "ULM",
            "California Irvine": "UC-Irvine",
            "St. Francis Pa.": "Saint-Francis-PA",
            "Middle Tennessee St.": "Middle-Tennessee",
            "California San Diego": "UC-San-Diego",
            "California Santa Barbara": "UC-Santa-Barbara",
            "Texas San Antonio": "UTSA",
            "Towson St.": "Towson",
            "Mississippi": "Ole-Miss",
            "Louisiana-Lafayette": "Louisiana",
            "Siu Edwardsville": "SIUE",
            "Ohio University": "Ohio",
            "N.J. Tech": "NJIT",
            "Lsu": "LSU",
            "Alabama Birmingham": "UAB",
            "Wisconsin Milwaukee": "Milwaukee",
            "Ucla": "UCLA",
            "Mass-Lowell": "UMass-Lowell",
            "Se Louisiana": "Southeastern-Louisiana",
            "Mt. St. Mary'S Md.": "Mount-Saint-Marys",
            "Maryland Baltimore County": "UMBC",
            "Miami Ohio": "Miami-OH",
            "Troy St.": "Troy",
            "Florida Atlantic": "FAU",
            "Central Florida": "UCF",
            "Depaul": "DePaul",
            "Arkansas Little Rock": "Little-Rock",
            "Nicholls St.": "Nicholls",
            "Central Connecticut St.": "Central-Connecticut",
            "Cal Baptist": "California-Baptist",
            "California Davis": "UC-Davis",
            "Purdue Ft. Wayne": "Purdue-Fort-Wayne",
            "Tcu": "TCU",
            "Illinois Chicago": "UIC",
            "Seattle": "Seattle-University",
            "North Carolina Greensboro": "UNCG",
            "Loyola Illinois": "Loyola-Chicago",
            "Se Missouri St.": "Southeast-Missouri",
            "College Of Charleston": "Charleston",
            "Florida International": "FIU",
            "North Carolina Asheville": "UNC-Asheville",
            "Prairie View": "Prairie-View-AM",
            "S. F. Austin": "Stephen-F-Austin",
            "Mcneese St.": "McNeese",
            "St. Mary'S Ca.": "Saint-Marys-College",
            "Monmouth Nj": "Monmouth",
            "Florida Gulf Coast": "FGCU",
            "North Carolina Wilmington": "UNCW",
    }
    if team in translations:
        return translations[team]
    if team[:3] == "St.":
        team = team.replace("St.", "Saint")
    return team.replace(" ", "-").replace("St.", "State").replace("'", "").replace("&", "")

#translates team string from kenpom's format to warren nolan's. all others are the same
def translate_team_kenpom(team):
    translations = {
            "Kansas City": "UMKC",
            "CSUN": "Cal-State-Northridge",
            "IU Indy": "IU-Indianapolis",
            "Saint Mary's": "Saint-Marys-College",
            "Florida Atlantic": "FAU",
            "Mississippi": "Ole-Miss",
            "McNeese St.": "McNeese",
            "N.C. State": "North-Carolina-State",
            "Massachusetts": "UMass",
            "UNC Wilmington": "UNCW",
            "Seattle": "Seattle-University",
            "UNC Greensboro": "UNCG",
            "Stephen F. Austin": "Stephen-F-Austin",
            "UT Arlington": "UTA",
            "Cal Baptist": "California-Baptist",
            "Illinois Chicago": "UIC",
            "Texas A&M Corpus Chris": "Texas-AM-Corpus-Christi",
            "Mount St. Mary's": "Mount-Saint-Marys",
            "Nebraska Omaha": "Omaha",
            "Florida Gulf Coast": "FGCU",
            "Nicholls St.": "Nicholls",
            "SIU Edwardsville": "SIUE",
            "USC Upstate": "South-Carolina-Upstate",
            "Louisiana Monroe": "ULM",
            "Presbyterian": "Presbyterian-College",
            "UT Rio Grande Valley": "UTRGV",
            "William & Mary": "William-Mary",
            "Loyola MD": "Loyola-Maryland",
            "LIU": "Long-Island",
            "Saint Francis": "Saint-Francis-PA",
            "Southeast Missouri St.": "Southeast-Missouri",
            "Detroit Mercy": "Detroit",
            "Texas A&M Commerce": "East-Texas-AM"
    }
    if team in translations:
        return translations[team]
    if team[:3] == "St.":
        team = team.replace("St.", "Saint")
    return team.replace(" ", "-").replace("St.", "State").replace("'", "").replace("&", "")

def scrape_initial_kenpom(year, scorer):
    #TODO maybe only do this once a day
    team_kenpoms = dict()
    if scorer.mens:
        os.system('wget --user-agent="Mozilla" -O data/men/' + year + '/kenpoms.html https://kenpom.com/')
        with open("data/men/" + year + "/kenpoms.html", "r") as f:
            for line in f.read().split("\n"):
                if "team.php?" in line:
                    anchor_index = line.find("team.php?")
                    team = line[line.find('">', anchor_index)+2:line.find("</a>")]
                    team = translate_team_kenpom(team)
                    rank = int(line[line.find("hard_left")+11:line.find('</td>')])
                    rating = float(line[line.find("<td>")+4:line.find('</td><td class="td-left divide')])
                    team_kenpoms[team] = {"rating": rating, "rank": rank}
    else:
        os.system('wget -O data/women/' + year + '/sonnys.html https://sonnymoorepowerratings.com/w-basket.htm')
        with open("data/women/" + year + "/sonnys.html", "r") as f:
            table_start = False
            for line in f.read().split("\n"):
                if line.strip() == "<B>":
                    table_start = True
                    continue
                if table_start:
                    team = line[4:32].strip().title()
                    team = translate_team_sonny(team)
                    rank = int(line[:3].strip())
                    rating = float(line[55:])
                    team_kenpoms[team] = {"rating": rating, "rank": rank}
                    if rank == 362:     #TODO ? How many teams are there?
                        break
    return team_kenpoms

#run a monte carlo simulation of the remaining college basketball season
def run_monte_carlo(simulations, scorer, builder, weightfile, mc_outputfile):
    rng = numpy.random.default_rng()
    today_date = date.today()
    selection_sunday = date(2025, 3, 16)
    season_start = date(2024, 11, 4)
    season_days = (selection_sunday - season_start).days
    if season_start > today_date:
        days_left = season_days
    else:
        days_left = (selection_sunday - today_date).days

    made_tournament = dict()
    final_fours = dict()
    national_champion = dict()
    team_seeds = dict()
    final_conference_winners = dict()
    for conference in builder.conference_winners:
        final_conference_winners[conference] = dict()
    first_weekend_sites = list(builder.first_weekend_sites)
    conference_winners = dict(builder.conference_winners)
    scorer.team_kenpoms = scrape_initial_kenpom(builder.year, scorer)
    base_weights = scorer.get_weights(weightfile)
    for team in scorer.teams:
        scorer.teams[team].saved_games = set(scorer.teams[team].games)
        scorer.teams[team].saved_future_games = list([dict(x) for x in scorer.teams[team].future_games])
    successful_runs = 0
    for i in range(simulations):
        print("Running sim", i)
        simmed_kenpoms = dict()
        for team in scorer.teams:
            scorer.teams[team].games = set(scorer.teams[team].saved_games)
            scorer.teams[team].future_games = list(scorer.teams[team].saved_future_games)
            scorer.teams[team].at_large_bid = False
            scorer.teams[team].auto_bid = False
            scorer.teams[team].region = -1
            scorer.teams[team].seed = -1
            scorer.teams[team].conference_wins = 0
            scorer.teams[team].conference_losses = 0
            simmed_kenpoms[team] = {"rating": rng.normal(scorer.team_kenpoms[team]["rating"], 5.8639*days_left/season_days)}
        rank_counter = 1
        for team in sorted(simmed_kenpoms, key=lambda x: simmed_kenpoms[x]["rating"], reverse=True):
            simmed_kenpoms[team]["rank"] = rank_counter
            rank_counter += 1
        builder.first_weekend_sites = list(first_weekend_sites)
        builder.conference_winners = dict(conference_winners)
        weights = dict()
        # vary weights a little bit
        for weight in base_weights:
            weights[weight] = random.uniform(0.9, 1.1)*base_weights[weight]
        try:
            results = simulate_games(scorer, builder, weights, simmed_kenpoms)
        except Exception as e:
            print(e)
            print("big ol failure, bummer boy")
            continue
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
        if builder.mens:
            for conference in results['conference']:
                add_or_increment_key(results['conference'][conference][0], final_conference_winners[conference])
        successful_runs += 1
    

    print("Successful runs:", successful_runs)
    print("CONFERENCES")
    if mc_outputfile:
        f = open(mc_outputfile, "w")
        f.write("successes:," + str(successful_runs) + "\n")
        f.write("WIN CONFERENCE\n")
    
    for conference in final_conference_winners:
        print()
        print(conference)
        if mc_outputfile:
            f.write(conference + "\n")
        for team in sorted(final_conference_winners[conference], key = lambda x: final_conference_winners[conference][x], reverse=True):
            odds = str(int((100/(final_conference_winners[conference][team]/successful_runs))-100))
            print(team.ljust(20), final_conference_winners[conference][team], "+" + odds)
            if mc_outputfile:
                f.write(team + "," + odds + "\n")
        if mc_outputfile:
            f.write("\n")

    if mc_outputfile:
        f.write("MAKE TOURNAMENT\n")
        f.write("Team,Chance\n")
    print()
    print("TOURNAMENT CHANCES")
    for team in sorted(made_tournament, key=lambda x: sum(team_seeds[x])/made_tournament[x]):
        print(team.ljust(20), made_tournament[team], round(sum(team_seeds[team])/made_tournament[team], 2), \
                min(team_seeds[team]), max(team_seeds[team]))
        if mc_outputfile:
            f.write(team + "," + str(made_tournament[team]/successful_runs) + "\n")
    
    if mc_outputfile:
        f.write("\n")
        f.write("FINAL FOURS\n")
        f.write("Team,Odds\n")
    print()
    print("FINAL FOURS")
    for team in sorted(final_fours, key=lambda x: final_fours[x], reverse=True):
        odds = str(int((100/(final_fours[team]/successful_runs))-100))
        print(team.ljust(20), final_fours[team], "+" + odds)
        if mc_outputfile:
            f.write(team + "," + odds + "\n")
    print()
    print("NATIONAL CHAMPIONS")
    if mc_outputfile:
        f.write("\n")
        f.write("NATIONAL CHAMPIONS\n")
        f.write("Team,Odds\n")
    for team in sorted(national_champion, key=lambda x: national_champion[x], reverse=True):
        odds = str(int((100/(national_champion[team]/successful_runs))-100))
        print(team.ljust(20), national_champion[team], "+" + str(int((100/(national_champion[team]/successful_runs))-100)))
        if mc_outputfile:
            f.write(team + "," + odds + "\n")

def main():
    scraper = Scraper()
    scraper.year, scraper.mens, scraper.outputfile, scraper.resumefile, scraper.webfile, resumewebfile, \
            upcomingschedulefile, scraper.datadir, should_scrape, force_scrape, scraper.verbose, \
            scraper.tracker, weightfile, future, monte_carlo, mc_outputfile, simulations = process_args()
    builder = scraper.load_data(should_scrape, force_scrape, future, monte_carlo)
    scorer = Scorer(builder, future, scraper.mens, scraper.tracker, monte_carlo)
    if scraper.tracker:
        tracker = Tracker(builder, scorer, scraper.year, scraper.verbose, scraper.mens)
        tracker.load_results()
        tracker.run_tracker(tuple())
        counter = 0
        summed_weights = [0]*16
        for weights in sorted(tracker.weight_results, key=lambda x: tracker.weight_results[x]):
            counter += 1
            for index, weight in enumerate(weights):
                summed_weights[index] += weight
            summed_weights[15] += tracker.weight_results[weights]
            if (scraper.mens and counter > 50) or (not scraper.mens and counter > 100):
                break
        print([str(round(x/51, 3)).ljust(5) for x in summed_weights])
        return
    elif monte_carlo:
        scraper.load_schedule_data(should_scrape, force_scrape)
        run_monte_carlo(simulations, scorer, builder, weightfile, mc_outputfile)
    else:
        if future:
            scraper.load_schedule_data(should_scrape, force_scrape)
            scorer.team_kenpoms = scrape_initial_kenpom(builder.year, scorer)
        weights = scorer.get_weights(weightfile)
        scorer.build_scores(weights)
        builder.select_seed_and_print_field()
        builder.build_bracket()
        if scraper.outputfile:
            scorer.outputfile = scraper.outputfile
            scorer.output_scores()
        if scraper.resumefile:
            scraper.output_resume(scorer, builder)
        if scraper.webfile:
            builder.webfile = scraper.webfile
            builder.output_bracket()
        if resumewebfile:
            scraper.output_resume_html(resumewebfile, scorer, builder)
        if upcomingschedulefile:
            scraper.output_schedule_html(upcomingschedulefile, scorer, builder)

def sorted_time(time):
    num_time = float(time.replace(":", ".").split(" ")[0])
    if "PM" in time and time[:2] != "12":
        num_time += 12
    return num_time

if __name__ == '__main__':
    main()

