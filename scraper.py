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
TEAM_MEN_URL_START = "https://www.warrennolan.com/basketball/2026/team-clubhouse?team="
TEAM_WOMEN_URL_START = "https://www.warrennolan.com/basketballw/2026/team-clubhouse?team="

reverse_team_dict = dict()

#for use when outputting resumes in "Q1 Wins" column
better_team_abbrs = {
        "Montana-State": "MTST",
        "Arkansas-State": "ARST",
        "Fairfield": "FFLD",
        "Southern-Indiana": "SOIN",
        "Northern-Iowa": "UNI",
        "UC-San-Diego": "UCSD",
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
        "South-Florida": "USF",
        "Saint-Louis": "SLU",
        "Bowling-Green": "BG",
        "Tulsa": "TULS",
        "UC-Santa-Barbara": "UCSB",
        "North-Dakota-State": "NDSU",
        "Troy": "TROY",
        "Rhode-Island": "URI",
        "Belmont": "BELM",
        "Princeton": "PRIN",
        "Columbia": "CMBA"
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
                    games.add(Game(game_obj["opponent"], game_obj["location"], game_obj["team_score"], \
                    game_obj["opp_score"], game_obj["date"], game_obj["conference_game"]))
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

        for team in self.teams:
            #go back through and back-translate
            for game in self.teams[team].games:
                if "Non Div I" not in game.opponent:
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
            conf_game_line_tracker = 0
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
                elif " <div class=\"team-schedule__conf-logo\">" in line:
                    conf_game_line_tracker = 1
                elif conf_game_line_tracker == 1:
                    conf_game_line_tracker += 1
                elif conf_game_line_tracker == 2:
                    if "team-schedule__conf-logo" in line:
                        game["conference_game"] = True
                    else:
                        game["conference_game"] = False
                    conf_game_line_tracker = 0
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
            elif not game.win and "Non Div I" in game.opponent:
                bad_losses.append({"team": self.get_location_prefix(game) + game.opponent, "NET": 365})
            elif not game.win and scorer.get_quadrant(self.teams[game.opponent].NET, game.location) >= 2:
                bad_losses.append({"team": self.get_location_prefix(game) + self.teams[game.opponent].team_out, "NET": self.teams[game.opponent].NET})
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
            if "Non Div I" in game.opponent:
                game_quad = 4
            else:
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
        f.write('    <thead>\n')
        f.write('      <tr class="header_row"><th>Team</th><th>Record</th><th>NET</th>')
        if self.mens:
            f.write('<th>Power</th><th>RES</th>')
        f.write('<th>Q1</th><th>Q2</th><th>Q3/4</th><th>Quality Wins</th><th>Q2+ losses</th></tr>\n')
        f.write('    </thead>\n')
        f.write('    <tbody>\n')
        for index, team in enumerate(sorted(scorer.teams, key=lambda x: scorer.teams[x].score, reverse=True)):
            if not index % 2:
                f.write('      <tr class="gray_row resume_row">')
            else:
                f.write('      <tr class="resume_row">')
            if self.mens:
                f.write('<td><a href="team_pages/' + team + '.html">' + scorer.teams[team].team_out + '</a></td>')
            else:
                f.write('<td><a href="team_pagesw/' + team + '.html">' + scorer.teams[team].team_out + '</a></td>')
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
                except KeyError: # New Haven
                    game_score = team_seed + 20
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
                            except KeyError: # New Haven
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
                        if self.mens:
                            f.write('<a href="team_pages/' + away_team + '.html">')
                        else:
                            f.write('<a href="team_pagesw/' + away_team + '.html">')
                        try:
                            f.write(scorer.teams[away_team].team_out + '</a> ' + location + ' ' + home_seed)
                        except KeyError: # New Haven
                            f.write("New Haven" + '</a > ' + location + ' ' + home_seed)
                        f.write('<img class="team_logo" src=assets/' + home_team + '.png></img>')
                        if self.mens:
                            f.write('<a href="team_pages/' + home_team + '.html">')
                        else:
                            f.write('<a href="team_pagesw/' + home_team + '.html">')
                        f.write(scorer.teams[home_team].team_out + '</a></td>')
                        f.write('<td>' + game[3] + '</td><td>' + game[4] + '</td>')
                        f.write('</tr>\n')
                        gray = not gray
                    f.write('</table>\n')    
        f.write('</div>\n')
        f.write('</body>\n')
        f.write('</html>\n')

#accept command line arguments
def process_args():
    year = "2026"
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
    mc_output_html = ""
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
            print("     -p: set an html filename where the monte carlo output will live")
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
        elif sys.argv[argindex] == '-p':
            mc_output_html = sys.argv[argindex + 1]
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
            monte_carlo, mc_outputfile, simulations, mc_output_html

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

def simulate_one_tournament_game(team1, team2, team_kenpoms, scorer, results):
    if "/" in team2:
        team2 = simulate_one_tournament_game(team2.split("/")[0], team2.split("/")[1], team_kenpoms, scorer, results)
        results['teams'][team2]['ncaa_round'] = 1
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

def simulate_tournament(builder, team_kenpoms, scorer, results):
    winners = list()
    for region_num in [0, 3, 1, 2]:
        for seed in [1, 8, 5, 4, 6, 3, 7, 2]:
            team_1 = builder.regions[region_num][seed]
            team_2 = builder.regions[region_num][17 - seed]
            results['teams'][team_1]['ncaa_seed'] = seed
            results['teams'][team_1]['ncaa_round'] = 1
            try:
                results['teams'][team_2]['ncaa_seed'] = 17 - seed
                results['teams'][team_2]['ncaa_round'] = 1
            except KeyError:    # play in game
                results['teams'][team_2.split("/")[0]]['ncaa_seed'] = 17 - seed
                results['teams'][team_2.split("/")[1]]['ncaa_seed'] = 17 - seed
                results['teams'][team_2.split("/")[0]]['ncaa_round'] = 0
                results['teams'][team_2.split("/")[1]]['ncaa_round'] = 0
            #if "/" not in team_1 and "/" not in team_2:
                #print(seed, team_1, team_kenpoms[team_1], 'vs.', 17-seed, team_2, team_kenpoms[team_2], end=": ")
            winners.append(simulate_one_tournament_game(team_1, team_2, team_kenpoms, scorer, results))
            results['teams'][winners[-1]]['ncaa_round'] = 2
            #print(winners[-1])
    index = 0
    while index + 1 < len(winners):
        #print(winners[index], team_kenpoms[winners[index]], 'vs.', winners[index + 1], team_kenpoms[winners[index + 1]], end=": ")
        winners.append(simulate_one_tournament_game(winners[index], winners[index + 1], team_kenpoms, scorer, results))
        if len(winners) == 63:
            results['teams'][winners[-1]]['ncaa_round'] = 7
        elif len(winners) >= 61:
            results['teams'][winners[-1]]['ncaa_round'] = 6
        elif len(winners) >= 57:
            results['teams'][winners[-1]]['ncaa_round'] = 5
        elif len(winners) >= 49:
            results['teams'][winners[-1]]['ncaa_round'] = 4
        else:
            results['teams'][winners[-1]]['ncaa_round'] = 3
        #print(winners[-1])
        index += 2
    return winners

def record_vs_range(team, group):
    wins = 0
    losses = 0
    for game in team.games:
        if game.opponent in group:
            if game.win:
                wins += 1
            else:
                losses += 1
    try:
        return wins/(wins + losses)
    except ZeroDivisionError: # shouldn't happen, but need it while data isn't perfect
        return 0

def break_tie(teams, win_dict, scorer, simmed_kenpoms):
    return_order = list()

    tied_teams = [x["name"] for x in teams]

    #try head-to-head tiebreaker first
    for team in teams:
        win_pct = record_vs_range(scorer.teams[team["name"]], [x["name"] for x in teams])
        team["tiebreaker_record"] = win_pct
    win_pcts = sorted([team["tiebreaker_record"] for team in teams], reverse=True)
    sorted_teams = sorted(teams, key = lambda x: x["tiebreaker_record"], reverse=True)
    while len(win_pcts) > 1 and win_pcts[0] != win_pcts[1]:
        return_order.append(sorted_teams.pop(0))
        win_pcts.pop(0)
    if len(win_pcts) == 1:
        return_order.append(sorted_teams[0])
    elif len(win_pcts) != len(teams):
        return_order += break_tie(sorted_teams, win_dict, scorer, simmed_kenpoms)
        sorted_teams = list()
    else:
        teams_needing_tiebreak = sorted_teams
        for win_amount in sorted(win_dict.keys(), reverse=True):
            for team in sorted_teams:
                win_pct = record_vs_range(scorer.teams[team["name"]], [x["name"] for x in win_dict[win_amount]])
                team["tiebreaker_record"] = win_pct
                
            win_pcts = sorted([team["tiebreaker_record"] for team in sorted_teams], reverse=True)
            sorted_teams = sorted(sorted_teams, key = lambda x: x["tiebreaker_record"], reverse=True)
            while len(win_pcts) > 1 and win_pcts[0] != win_pcts[1]:
                return_order.append(sorted_teams.pop(0))
                win_pcts.pop(0)
            if len(win_pcts) == 1:
                return_order.append(sorted_teams[0])
                break
            elif len(win_pcts) != len(teams_needing_tiebreak):
                return_order += break_tie(sorted_teams, win_dict, scorer, simmed_kenpoms)
                sorted_teams = list()
                break
            else:
                continue
    if len(sorted_teams) > 1: #recursed all the way down the seed list, no way to break tie
        sorted_teams.sort(key=lambda x: scorer.get_NET_estimate(scorer.teams[x["name"]].NET, simmed_kenpoms[x["name"]]["rank"]), reverse=True)
        return_order += sorted_teams
    return return_order

def get_seeds(teams, scorer, simmed_kenpoms):
    seed_list = list()
    win_dict = dict()
    for team in teams:
        if team["conference_wins"] in win_dict:
            win_dict[team["conference_wins"]].append(team)
        else:
            win_dict[team["conference_wins"]] = [team]
    for win_amount in reversed(sorted(win_dict.keys())):
        if len(win_dict[win_amount]) == 1:
            seed_list.append(win_dict[win_amount][0])
        else:
            broken_tie_order = break_tie(win_dict[win_amount], win_dict, scorer, simmed_kenpoms)
            for team in broken_tie_order:
                seed_list.append(team)
    return seed_list

def simulate_conference_tournaments(scorer, builder, simmed_kenpoms, results):
    #TODO: check on new formats
    conference_teams = dict()
    if builder.mens:
        with open("lib/ctourn_formats.json", "r") as f:
            formats = json.loads(f.read())
    else:
        with open("lib/ctourn_formatsw.json", "r") as f:
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
            if rnd[0] == "T":
                cur_round_teams = 10
            else:
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
        seeds = []
        
        seeded_teams = get_seeds(conference_teams[conference], scorer, simmed_kenpoms)
        # Uncomment below to test for missing/extra games, etc
        #print(conference)
        for index, team in enumerate(seeded_teams):
            results['teams'][team["name"]]["conference_seed"] = index + 1
            results['teams'][team["name"]]["conference_wins"] = team["conference_wins"]
            results['teams'][team["name"]]["conference_losses"] = team["conference_losses"]
            if len(seeds) < num_teams:
                seeds.append(team["name"])
            #print(team["name"], "(" + str(team["conference_wins"]) + "-" + str(team["conference_losses"]) + ")")
        #print()
        conf_reg_winners[conference] = seeds[0]
        seed_to_team = dict()
        for index, team in enumerate(seeds):
            seed_to_team[index + 1] = team
        seeds_to_use = list(seeds)
        previous_winners = []
        num_eliminated_teams = 0
        for rnd in rounds:
            if rnd[0] == "T":
                cur_round_teams = 10
            else:
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
                win_prob = scorer.get_win_prob(simmed_kenpoms[matchup[0]]["rating"], simmed_kenpoms[matchup[1]]["rating"], round_location)
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
        results['teams'][builder.conference_winners[conference]]["ctourn_winner"] = True
    return conf_reg_winners

#run one simulation of the rest of the college basketball season
def simulate_games(scorer, builder, weights, simmed_kenpoms):
    results = {'tournament': list(), 'final_four': list(), 'champion': list(), 'conference': dict(), 'teams': dict()}
    for conference in builder.conference_winners:
        results['conference'][conference] = list()
    teams = list(scorer.teams.keys())
    random.shuffle(teams)
    for team in teams:
        team_kenpom = simmed_kenpoms[team]
        for game in scorer.teams[team].games:
            if game.date == "10-10":   #previously simulated game
                continue
            opponent = game.opponent
            if game.conference_game:
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
            opp_kenpom = simmed_kenpoms[opponent]
            win_prob = scorer.get_win_prob(team_kenpom['rating'], opp_kenpom['rating'], game['location'])
            new_game = Game(opponent, game['location'], 75, 0, '10-10', game['conference_game'])
            opp_game = Game(team, reverse_location(game['location']), 0, 75, '10-10', game['conference_game'])
            win_result = random.random()
            if win_result < win_prob:
                new_game.opp_score = 70
                opp_game.team_score = 70
                if game['conference_game']:
                    scorer.teams[team].conference_wins += 1
                    scorer.teams[opponent].conference_losses += 1
            else:
                new_game.opp_score = 80
                opp_game.team_score = 80
                if game['conference_game']:
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
        simmed_kenpoms[team] = team_kenpom
        results['teams'][team] = {
                "wins": len(list(filter(lambda x: x.win, scorer.teams[team].games))),
                "losses": len(list(filter(lambda x: not x.win, scorer.teams[team].games))),
                "conference_wins": 0,
                "conference_losses": 0,
                "conference_seed": 0,
                "ctourn_winner": False,
                "ncaa_seed": -1,
                "ncaa_round": -1
            }
    
    conf_reg_winners = simulate_conference_tournaments(scorer, builder, simmed_kenpoms, results)
    #print_Illinois(scorer, simmed_kenpoms)
    scorer.build_scores(weights, simmed_kenpoms)
    builder.select_seed_and_print_field()
    builder.build_bracket()
    for team in scorer.teams:
        if scorer.teams[team].auto_bid or scorer.teams[team].at_large_bid:
            results['tournament'].append([team, scorer.teams[team].seed])
    winners = simulate_tournament(builder, simmed_kenpoms, scorer, results)
    results['final_four'] += winners[-7:-3]
    results['champion'].append(winners[-1])
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
                    if line.strip() == "<BR>":
                        break
                    team = line[4:32].strip().title()
                    team = translate_team_sonny(team)
                    rank = int(line[:3].strip())
                    rating = float(line[54:].strip())
                    team_kenpoms[team] = {"rating": rating, "rank": rank}
    return team_kenpoms
#{
        #   wins: X
        #   losses: X
        #   conference_wins: X
        #   conference_losses: X
        #   conference_seed: X
        #   ctourn_winner: T/F
        #   ncaa_seed: X/-1
        #   ncaa_round: -1/0/1/2/3/4/5/6/7
        #}
def output_team_html(mens, team, team_out, record, conference_record, team_results, all_conference_results, builder):
    conf_results = all_conference_results[builder.teams[team].conference]
    total_runs = len(team_results)
    win_conference = len(list(filter(lambda x: x['conference_seed'] == 1, team_results)))
    make_tournament = len(list(filter(lambda x: x['ncaa_seed'] > 0, team_results)))
    auto_bid = len(list(filter(lambda x: x['ctourn_winner'], team_results)))
    final_four = len(list(filter(lambda x: x['ncaa_round'] >= 5, team_results)))
    national_championship = len(list(filter(lambda x: x['ncaa_round'] == 7, team_results)))

    if mens:
        if not os.path.exists("./team_pages/"):
            os.makedirs("./team_pages/")
        f = open("./team_pages/" + team + ".html", "w")
    else:
        if not os.path.exists("./team_pagesw/"):
            os.makedirs("./team_pagesw/")
        f = open("./team_pagesw/" + team + ".html", "w")
    builder.output_meta(f, "../")
    builder.output_link_row(f, "../")
    f.write('<div class="title_row_team">\n')
    f.write('  <img class="team_page_logo" src=../assets/' + team + '.png></img><h1>' + team_out + \
        ' (' + record + ', ' + conference_record + ' ' + builder.teams[team].conference + ')</h1>\n')
    f.write('</div>\n')
    f.write('<div class="oddsbox_row">\n')
    f.write('  <div class="oddsbox">\n')
    f.write('    <div class="oddsbox_title">\n')
    f.write('      <h3 class="metric_title">Win conference:</h3>\n')
    f.write('    </div>\n')
    f.write('    <div class="oddsbox_number">\n')
    f.write('      <h4 class="metric_number">' + str(round(100*win_conference/total_runs, 2)) + '%</h4>\n')
    f.write('    </div>\n')
    f.write('  </div>\n')
    f.write('  <div class="oddsbox">\n')
    f.write('    <div class="oddsbox_title">\n')
    f.write('      <h3 class="metric_title">Make tournament:</h3>\n')
    f.write('    </div>\n')
    f.write('    <div class="oddsbox_number">\n')
    f.write('      <h4 class="metric_number">' + str(round(100*make_tournament/total_runs, 2)) + '%</h4>\n')
    f.write('    </div>\n')
    f.write('  </div>\n')
    f.write('  <div class="oddsbox">\n')
    f.write('    <div class="oddsbox_title">\n')
    f.write('      <h3 class="metric_title">Auto bid:</h3>\n')
    f.write('    </div>\n')
    f.write('    <div class="oddsbox_number">\n')
    f.write('      <h4 class="metric_number">' + str(round(100*auto_bid/total_runs, 2)) + '%</h4>\n')
    f.write('    </div>\n')
    f.write('  </div>\n')
    f.write('  <div class="oddsbox">\n')
    f.write('    <div class="oddsbox_title">\n')
    f.write('      <h3 class="metric_title">Final Four:</h3>\n')
    f.write('    </div>\n')
    f.write('    <div class="oddsbox_number">\n')
    f.write('      <h4 class="metric_number">' + str(round(100*final_four/total_runs, 2)) + '%</h4>\n')
    f.write('    </div>\n')
    f.write('  </div>\n')
    f.write('  <div class="oddsbox">\n')
    f.write('    <div class="oddsbox_title">\n')
    f.write('      <h3 class="metric_title">Win championship:</h3>\n')
    f.write('    </div>\n')
    f.write('    <div class="oddsbox_number">\n')
    f.write('      <h4 class="metric_number">' + str(round(100*national_championship/total_runs, 2)) + '%</h4>\n')
    f.write('    </div>\n')
    f.write('  </div>\n')
    f.write('</div>\n')
    f.write('<div style="display: inline-flex">\n')
    f.write('<div class="seed_tables_container">\n')
    team_table_output(f, 'wins', 'losses', team_results)
    team_table_output(f, 'conference_wins', 'conference_losses', team_results)
    f.write('</div>\n')
    f.write('<div class="conference_standings_container">\n')
    f.write('  <h3>' + builder.teams[team].conference + ' Projected Standings</h3>\n')
    f.write('  <table class="conference_table">\n')
    f.write('    <thead>\n')
    f.write('      <tr><th>Team</th><th>Wins</th><th>Losses</th></tr>\n')
    f.write('    </thead>\n')
    f.write('    <tbody>\n')
    for conf_team in sorted(conf_results, key=lambda x: conf_results[x]['conference_wins'], reverse=True):
        f.write('      <tr')
        conf_team_out = builder.teams[conf_team].team_out
        if conf_team_out == team_out:
            f.write(' style="background-color: yellow"')
        if mens:
            f.write('><td><a href="../team_pages/' + conf_team + '.html">' + conf_team_out + '</a></td><td>')
        else:
            f.write('><td><a href="../team_pagesw/' + conf_team + '.html">' + conf_team_out + '</a></td><td>')
        f.write(str(round(conf_results[conf_team]['conference_wins'], 2)) + '</td><td>' + \
        str(round(conf_results[conf_team]['conference_losses'], 2)) + '</td></tr>\n')
    f.write('    </tbody>\n')
    f.write('  </table>\n')
    f.write('</div>\n')
    f.write('</div>\n')

def team_table_output(f, win_string, loss_string, team_results):
    total_runs = len(team_results)
    total_games = team_results[0][win_string] + team_results[0][loss_string]
    win_totals = [x[win_string] for x in team_results]
    all_seeds = [x['ncaa_seed'] for x in team_results]
    try:
        highest_seed = min(list(filter(lambda x: x > 0, all_seeds)))
    except ValueError: # team did not make tournament
        highest_seed = 16

    f.write('<div>\n')
    if win_string == "wins":
        f.write('  <h3 style="text-align: center"><u>Overall Record</u></h3>\n')
    else:
        f.write('  <h3 style="text-align: center"><u>Conference Record</u></h3>\n')
    f.write('  <table class="record_table">\n')
    f.write('    <thead>\n')
    f.write('      <tr><th>Record</th><th>% chance</th>')
    for x in range(highest_seed, max(all_seeds) + 1):
        if x == highest_seed:
            f.write('<th>' + str(x) + ' seed</th>')
        else:
            f.write('<th>' + str(x) + '</th>')
    f.write('<th>Miss</th>')
    f.write('</tr>\n')
    f.write('    </thead>\n')
    f.write('    <tbody>\n')
    f.write('<tr><td/><td/>')
    for seed in range(highest_seed, max(all_seeds) + 1):
        outcome_percentage = round(100*all_seeds.count(seed)/total_runs, 2)
        color_percentage = str(-outcome_percentage / 2 + 100)
        f.write('<td style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(outcome_percentage) + '%</td>')
    outcome_percentage = round(100*all_seeds.count(-1)/total_runs, 2)
    color_percentage = str(-outcome_percentage / 2 + 100)
    f.write('<td style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(outcome_percentage) + '%</td>')
    f.write('</tr>\n')
    for win_total in sorted(set(win_totals), reverse=True):
        relevant_runs = list(list(filter(lambda x: x[win_string] == win_total, team_results)))
        relevant_seeds = [x['ncaa_seed'] for x in relevant_runs]
        win_total_count = win_totals.count(win_total)
        win_total_pct = round(100*win_total_count / total_runs, 2)
        color_percentage = str(-win_total_pct / 2 + 100)

        f.write('    <tr><td>' + str(win_total) + "-" + str(total_games - win_total) + '</td>')
        f.write('<td style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(win_total_pct) + '%</td>')
        for seed in range(highest_seed, max(all_seeds) + 1):
            outcome_percentage = round(100*relevant_seeds.count(seed)/total_runs, 2)
            color_percentage = str(-outcome_percentage / 2 + 100)
            f.write('<td style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(outcome_percentage) + '%</td>')
        outcome_percentage = round(100*relevant_seeds.count(-1)/total_runs, 2)
        color_percentage = str(-outcome_percentage / 2 + 100)
        f.write('<td style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(outcome_percentage) + '%</td>')
        f.write('</tr>\n')
    f.write('    </tbody>\n')
    f.write('  </table>\n')
    f.write('</div>\n')

def get_current_odds(conferences):
    results = {'conference': dict(), 'final_four': dict(), 'championship': dict(),
               'tournament_yes': dict(), 'tournament_no': dict()}
    g = open("./currentodds.csv", "r")
    conference = ""
    tournament_yes = False
    tournament_no = False
    final_four = False
    championship = False
    for line in g.read().split("\n"):
        if line in conferences:
            conference = line
            results['conference'][conference] = dict()
            continue
        if "Team," in line:
            continue
        if "TOURNAMENT - YES" in line:
            tournament_yes = True
            conference = ""
            continue
        if "TOURNAMENT - NO" in line:
            tournament_no = True
            tournament_yes = False
            continue
        if "FINAL FOUR" in line:
            final_four = True
            tournament_no = False
            continue
        if "CHAMPIONSHIP" in line:
            championship = True
            final_four = False
            continue
        if conference and len(line) > 2:
            if line[:line.find(",")] in conferences[conference]:
                team_line = line.split(",")
                team = team_line[0]
                results['conference'][conference][team] = {"FD": team_line[1], "DK": team_line[3], "CS": team_line[5], "BM": team_line[7], "BT": team_line[9], "best": team_line[11]}
        elif tournament_yes and len(line) > 2:
            team_line = line.split(",")
            team = team_line[0]
            results['tournament_yes'][team] = {"FD": team_line[1], "DK": team_line[3], "CS": team_line[5], "BM": team_line[7], "BT": team_line[9], "best": team_line[11]}
        elif tournament_no and len(line) > 2:
            team_line = line.split(",")
            team = team_line[0]
            results['tournament_no'][team] = {"FD": team_line[1], "DK": team_line[3], "CS": team_line[5], "BM": team_line[7], "BT": team_line[9], "best": team_line[11]}
        elif final_four and len(line) > 2:
            team_line = line.split(",")
            team = team_line[0]
            results['final_four'][team] = {"FD": team_line[1], "DK": team_line[3], "CS": team_line[5], "BM": team_line[7], "BT": team_line[9], "best": team_line[11]}
        elif championship and len(line) > 2:
            team_line = line.split(",")
            team = team_line[0]
            results['championship'][team] = {"FD": team_line[1], "DK": team_line[3], "CS": team_line[5], "BM": team_line[7], "BT": team_line[9], "best": team_line[11]}
    return results

def get_plus_odds(odds):
    if odds == "":
        return ""
    if float(odds) < 0:
        return str((100/(float(odds)/(float(odds) - 100))) - 100)
    return odds

#run a monte carlo simulation of the remaining college basketball season
def run_monte_carlo(simulations, scorer, builder, mens, weightfile, mc_outputfile, mc_output_html):
    rng = numpy.random.default_rng()
    today_date = date.today()
    selection_sunday = date(2026, 3, 15)
    season_start = date(2025, 11, 3)
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
    team_results = dict()
    for conference in builder.conference_winners:
        final_conference_winners[conference] = dict()
    first_weekend_sites = list(builder.first_weekend_sites)
    conference_winners = dict(builder.conference_winners)
    scorer.team_kenpoms = scrape_initial_kenpom(builder.year, scorer)
    base_weights = scorer.get_weights(weightfile)
    if os.path.exists("./my_bets.json"):
        f = open("./my_bets.json", "r")
        my_bets = json.loads(f.read())
    else:
        my_bets = {}

    for team in scorer.teams:
        scorer.teams[team].saved_games = set(scorer.teams[team].games)
        scorer.teams[team].saved_future_games = list([dict(x) for x in scorer.teams[team].future_games])

        #each object in list:
        #{
        #   wins: X
        #   losses: X
        #   conference_wins: X
        #   conference_losses: X
        #   conference_seed: X
        #   ctourn_winner: T/F
        #   ncaa_seed: X/-1
        #   ncaa_round: -1/0/1/2/3/4/5/6/7
        #}
        team_results[team] = list()
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
            weights[weight] = random.uniform(0.8, 1.2)*base_weights[weight]
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
        for team in results['teams']:
            team_results[team].append(results['teams'][team])
        for conference in results['conference']:
            add_or_increment_key(results['conference'][conference][0], final_conference_winners[conference])
        successful_runs += 1
    
    conference_results = dict()
    for conference in final_conference_winners:
        conference_results[conference] = dict()

    for team in scorer.teams: #do this so that the output has the correct current record
        scorer.teams[team].games = set(scorer.teams[team].saved_games)
        scorer.teams[team].future_games = list(scorer.teams[team].saved_future_games)
        conference_results[builder.teams[team].conference][team] = {
            'conference_wins': sum(x['conference_wins'] for x in team_results[team])/len(team_results[team]),
            'conference_losses': sum(x['conference_losses'] for x in team_results[team])/len(team_results[team])
        }

    ## OUTPUT RESULTS ##
    result_percents = dict()

    print("Successful runs:", successful_runs)
    print("CONFERENCES")
    if mc_outputfile:
        try:
            f = open(mc_outputfile, "w")
        except PermissionError:
            print("You dumb dumb!")
            print("opening backup")
            f = open("./data/montecarlooutput.csv", "w")
        current_odds = get_current_odds(final_conference_winners)
        f.write("successes:," + str(successful_runs) + "\n")
        f.write("WIN CONFERENCE\n")
    
    for conference in final_conference_winners:
        print()
        print(conference)
        if mc_outputfile:
            f.write(conference + "\n")
            f.write("Team,Odds,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds,Good bet?,Already bet?\n")
        for team in sorted(final_conference_winners[conference], key = lambda x: final_conference_winners[conference][x], reverse=True):
            conf_pct = final_conference_winners[conference][team]/successful_runs
            result_percents[team] = {'conference': conf_pct}
            odds = str(int((100/conf_pct)-100))
            print(team.ljust(20), final_conference_winners[conference][team], "+" + odds)
            
        if mc_outputfile:
            for team in sorted(final_conference_winners[conference]):
                odds = str(int((100/(final_conference_winners[conference][team]/successful_runs))-100))
                f.write(team + "," + odds + ",")
                for book in ["FD", "DK", "CS", "BM", "BT"]:
                    try:
                        write_book_odds(f, current_odds['conference'][conference][team], book)
                    except KeyError:    # odds not posted anywhere for this team
                        f.write(",,")
                try:
                    best_odds = current_odds['conference'][conference][team]["best"]
                    f.write(best_odds + ",")
                    if float(odds) > float(best_odds):
                        f.write("0,")
                    else:
                        try:
                            f.write(str(float(best_odds)/float(odds)) + ",")
                        except ZeroDivisionError:   #team is 100% to win its conference
                            f.write("XXXXX,")
                    if team in my_bets['conference']:
                        if my_bets['conference'][team] > 0:
                            f.write("Yes: +" + str(my_bets['conference'][team]))
                        else:
                            f.write("Yes: " + str(my_bets['conference'][team]))
                
                except KeyError:
                    f.write(",")

                f.write("\n")
        if mc_outputfile:
            f.write("\n")

    if mc_outputfile:
        f.write("MAKE TOURNAMENT\n")
        f.write("Team,Chance\n")
    print()
    print("TOURNAMENT CHANCES")
    for team in sorted(made_tournament, key=lambda x: sum(team_seeds[x])/made_tournament[x]):
        print(team.ljust(20), str(made_tournament[team]).rjust(len(str(successful_runs))), str(round(sum(team_seeds[team])/made_tournament[team], 2)).rjust(5), \
                str(min(team_seeds[team])).rjust(2), str(max(team_seeds[team])).rjust(2))
        tourn_pct = made_tournament[team]/successful_runs
        try:
            result_percents[team]['tournament'] = tourn_pct
        except KeyError: # team didn't win conference
            result_percents[team] = {'conference': 0, 'tournament': tourn_pct}
        if mc_outputfile:
            f.write(team + "," + str(tourn_pct) + "\n")
    
    if mc_outputfile:
        f.write("\n")
        f.write("MAKE TOURNAMENT - YES\n")
        f.write("Team,Odds,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds,Good bet?,Already bet?\n")
        for team in sorted(current_odds['tournament_yes']):
            odds = str(int((100/(made_tournament[team]/successful_runs))-100))
            f.write(team + "," + odds + ",")
            for book in ["FD", "DK", "CS", "BM","BT"]:
                write_book_odds(f, current_odds['tournament_yes'][team], book)
            write_odds_margin(f, team, odds, current_odds, 'tournament_yes', my_bets)
        
        f.write("\n")
        f.write("MAKE TOURNAMENT - NO\n")
        f.write("Team,Odds,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds,Good bet?,Already bet?\n")
        for team in sorted(current_odds['tournament_no']):
            odds = str(int((100/(1 - (made_tournament[team]/successful_runs)))-100))
            f.write(team + "," + odds + ",")
            for book in ["FD", "DK", "CS", "BM","BT"]:
                write_book_odds(f, current_odds['tournament_no'][team], book)
            write_odds_margin(f, team, odds, current_odds, 'tournament_no', my_bets)

    if mc_outputfile:
        f.write("\n")
        f.write("FINAL FOURS\n")
        f.write("Team,Odds,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds,Good bet?,Already bet?\n")
    print()
    print("FINAL FOURS")
    for team in sorted(final_fours, key=lambda x: final_fours[x], reverse=True):
        ff_pct = final_fours[team]/successful_runs
        odds = str(int((100/ff_pct)-100))
        result_percents[team]['final_four'] = ff_pct
        print(team.ljust(20), final_fours[team], "+" + odds)
    if mc_outputfile:
        for team in sorted(final_fours):
            odds = str(int((100/(final_fours[team]/successful_runs))-100))
            f.write(team + "," + odds + ",")
            for book in ["FD", "DK", "CS", "BM","BT"]:
                try:
                    write_book_odds(f, current_odds['final_four'][team], book)
                except KeyError:    # odds not posted anywhere for this team
                    f.write(",,")
            write_odds_margin(f, team, odds, current_odds, 'final_four', my_bets)

    print()
    print("NATIONAL CHAMPIONS")
    if mc_outputfile:
        f.write("\n")
        f.write("NATIONAL CHAMPIONS\n")
        f.write("Team,Odds,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds,Good bet?,Already bet?\n")
    for team in sorted(national_champion, key=lambda x: national_champion[x], reverse=True):
        nc_pct = national_champion[team]/successful_runs
        odds = str(int((100/nc_pct)-100))
        result_percents[team]['championship'] = nc_pct
        print(team.ljust(20), national_champion[team], "+" + str(int((100/(national_champion[team]/successful_runs))-100)))
    if mc_outputfile:
        for team in sorted(national_champion):
            odds = str(int((100/(national_champion[team]/successful_runs))-100))
            f.write(team + "," + odds + ",")
            for book in ["FD", "DK", "CS", "BM", "BT"]:
                try:
                    write_book_odds(f, current_odds['championship'][team], book)
                except KeyError:    # odds not posted anywhere for this team
                    f.write(",,")
            write_odds_margin(f, team, odds, current_odds, 'championship', my_bets)

    for team in made_tournament:
        result_percents[team]['auto_bid'] = len(list(filter(lambda x: x['ctourn_winner'], team_results[team])))/successful_runs
        for tourney_round in [('second_round', 2), ('sweet_sixteen', 3), ('elite_eight', 4), ('ncg', 6)]:
            result_percents[team][tourney_round[0]] = len(list(filter(lambda x: x['ncaa_round'] >= tourney_round[1], team_results[team])))/successful_runs

    if mc_output_html:
        f = open(mc_output_html, "w")
        builder.output_meta(f)
        builder.output_link_row(f, "")
        f.write('<body>\n')
        f.write('<div class="table_container">\n')
        f.write('  <table class="outcomes_table">\n')
        f.write('    <colgroup><col class="teamcol"><col class="confcol"><col class="autocol"><col class="tourncol">')
        f.write('<col class="srcol"><col class="sscol"><col class="eecol">')
        f.write('<col class="ffcol"><col class="ncgcol"><col class="nccol"></colgroup>\n')
        f.write('    <thead>\n')
        f.write('      <tr class="header_row"><th>Team</th><th>Avg. seed</th><th>Win conf</th>')
        f.write('<th>Auto bid</th><th>Tournament</th>')
        f.write('<th>2nd Round</th><th>Sweet 16</th><th>Elite 8</th><th>Final Four</th>')
        f.write('<th>Champ game</th><th>Win champ</th>')
        f.write('</tr>')
        f.write('    </thead>\n')
        f.write('    <tbody>\n')
        for index, team in enumerate(sorted(made_tournament, key=lambda x: sum(team_seeds[x])/made_tournament[x])):
            if mens:
                f.write('    <tr><td><img class="tiny_logo" src="assets/' + team + '.png"/><a href="team_pages/' + team + '.html">' + scorer.teams[team].team_out + '</a></td>')
            else:
                f.write('    <tr><td><img class="tiny_logo" src="assets/' + team + '.png"/><a href="team_pagesw/' + team + '.html">' + scorer.teams[team].team_out + '</a></td>')
            f.write('<td>' + str(round(sum(team_seeds[team])/made_tournament[team], 2)) + '</td>')
            for outcome_string in ['conference', 'auto_bid', 'tournament', 'second_round', 'sweet_sixteen', 'elite_eight', 'final_four', 'ncg', 'championship']:
                try:
                    outcome_percentage = round(result_percents[team][outcome_string]*100, 2)
                except KeyError:
                    outcome_percentage = 0
                color_percentage = str(-outcome_percentage / 2 + 100)
                f.write('<td class="pct_col" style="background-color: hsl(120, 50%, ' + color_percentage + '%)">' + str(outcome_percentage) + '%</td>')
            f.write('</tr>\n')
        f.write('    </tbody>')
        f.write('  </table>\n')
        f.write('</div>\n')
        f.write('</body>\n')

    for team in team_results:
        output_team_html(mens, team, scorer.teams[team].team_out, scorer.teams[team].record,
        scorer.teams[team].conference_record, team_results[team], conference_results, builder)

def write_book_odds(f, current_odds, book):
    f.write(current_odds[book] + ",")
    f.write(get_plus_odds(current_odds[book]) + ",")

def write_odds_margin(f, team, team_odds, current_odds, bet_type, my_bets):
    try:
        best_odds = current_odds[bet_type][team]['best']
        f.write(best_odds + ",")
        if float(team_odds) > float(best_odds):
            f.write("0,")
        else:
            f.write(str(float(best_odds)/float(team_odds)) + ",")
        if team in my_bets[bet_type]:
            f.write("Yes: +" + str(my_bets[bet_type][team]))
    except KeyError:
        pass
    f.write("\n")

def main():
    scraper = Scraper()
    scraper.year, scraper.mens, scraper.outputfile, scraper.resumefile, scraper.webfile, resumewebfile, \
            upcomingschedulefile, scraper.datadir, should_scrape, force_scrape, scraper.verbose, \
            scraper.tracker, weightfile, future, monte_carlo, mc_outputfile, simulations, mc_output_html = process_args()
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
        run_monte_carlo(simulations, scorer, builder, scraper.mens, weightfile, mc_outputfile, mc_output_html)
        if scraper.outputfile:
            scorer.outputfile = scraper.outputfile
            scorer.output_scores()
        if scraper.resumefile:
            scraper.output_resume(scorer, builder)
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

