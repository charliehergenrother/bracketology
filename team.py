#!/usr/bin/env python3

from game import Game
import requests
import sys
import os

SELECTION_SUNDAY_DATES = {"2026": 15, "2025": 16, "2024": 17, "2023": 12, "2022": 13, "2021": 14}

#class representing one college basketball team
class Team:

    def reprJSON(self):
        return dict(conference=self.conference, NET=self.NET, KenPom=self.KenPom, BPI=self.BPI, Sagarin=self.Sagarin, Trank=self.Trank, KPI=self.KPI, SOR=self.SOR, WAB=self.WAB, NET_SOS=self.NET_SOS, noncon_SOS=self.noncon_SOS, games=self.games, team_out=self.team_out)

    def __init__(self):
        self.conference = ""
        self.team_out = ""
        self.NET = 0
        self.KenPom = 0
        self.BPI = 0
        self.Sagarin = 0
        self.Trank = 0
        self.KPI = 0
        self.SOR = 0
        self.WAB = 0
        self.NET_SOS = 0
        self.noncon_SOS = 0
        self.games = set()
        self.auto_bid = False
        self.at_large_bid = False
        self.play_in = False
    
    def fill_data(self, conf, net, kp, bpi, sag, tr, kpi, sor, wab, netsos, ncsos, gms, to):
        self.conference = conf
        self.team_out = to
        self.NET = net
        self.KenPom = kp
        self.BPI = bpi
        self.Sagarin = sag
        self.Trank = tr
        self.KPI = kpi
        self.SOR = sor
        self.WAB = wab
        self.NET_SOS = netsos
        self.noncon_SOS = ncsos
        self.games = gms

    def scrape_data(self, team, url, year):
        team_page = requests.get(url)
        if team_page.status_code != 200:
            print("team problem!", url)
            sys.exit()
        SOS_line = 0
        KPI_line = 0
        BPI_line = 0
        header_line = False
        non_di_header_line = False
        game_line = 0
        self.games = set()
        non_di = False
        for line in team_page.text.split("\n"):
            if "Non-Division I Games" in line:
                non_di = True
                continue
            if "team-menu__image\"" in line and not os.path.exists("./assets/" + team + ".png"):
                image_url = "http://www.warrennolan.com" + line[line.find("src=")+5:line.find(" />")-1]
                team_image = requests.get(image_url, stream=True)
                with open("./assets/" + team + ".png", "xb") as f:
                    for chunk in team_image:
                        f.write(chunk)
            if "team-menu__name\"" in line:
                self.team_out = line[line.find(">")+1:line.find(" <span")]
            if "team-menu__conference" in line:
                self.conference = line[line.find('">', line.find("/conference/"))+2:line.find("</a>")]
                continue
            if "font-weight: bold; font-size: 16px;" in line:
                try:
                    self.NET = int(line[line.find("16px")+7:line.find("</span>")])
                except ValueError:  #TODO this is for the women's pages that aren't working. Mercyhurst, IU Indianapolis, West Georgia
                    self.NET = 361
                continue
            if not SOS_line:
                if ("NET SOS") in line:
                    SOS_line += 1
                continue
            elif SOS_line < 4:
                SOS_line += 1
                continue
            elif SOS_line == 4:
                if line.strip()[:line.strip().find("<")] == "N/A":
                    self.NET_SOS = 150
                else:
                    try:
                        self.NET_SOS = int(line.strip()[:line.strip().find("<")])
                    except ValueError: #TODO see above
                        self.NET_SOS = 150
                SOS_line += 1
                continue
            elif SOS_line == 5:
                if line.strip() == "N/A":   #2020-21 was crazy
                    self.noncon_SOS = 150
                else:
                    try:
                        self.noncon_SOS = int(line.strip())
                    except ValueError: #TODO see above
                        self.noncon_SOS = 150
                SOS_line += 1
                continue
            
            if not KPI_line:
                if ("KPI") in line:
                    KPI_line += 1
                    continue
            elif KPI_line < 5:
                KPI_line += 1
                continue
            elif KPI_line == 5:
                try:
                    self.KPI = int(line.strip()[:line.strip().find("<")])
                except ValueError: #TODO see above #TODO this is also cause KPI is blank rn
                    self.KPI = 0
                KPI_line += 1
                continue
            elif KPI_line == 6:
                try:
                    self.SOR = int(line.strip()[:line.strip().find("<")])
                except ValueError: #TODO see above
                    self.SOR = 0
                KPI_line += 1
                continue
            elif KPI_line == 7:
                try:
                    self.WAB = int(line.strip())
                except ValueError: #TODO see above
                    self.WAB = 0
                KPI_line += 1
                continue
            
            if not BPI_line:
                if ("BPI") in line:
                    BPI_line += 1
                    continue
            elif BPI_line < 6:
                BPI_line += 1
                continue
            elif BPI_line == 6:
                try:
                    self.BPI = int(line.strip()[:line.strip().find("<")])
                except ValueError: #TODO see above
                    self.BPI = 0
                BPI_line += 1
                continue
            elif BPI_line == 7:
                try:
                    self.KenPom = int(line.strip()[:line.strip().find("<")])
                except ValueError: #TODO see above
                    self.KenPom = 0
                BPI_line += 1
                continue
            #TODO i'm just putting T-rank in sagarin rn cause i'm lazy. gotta fix & stay compatible with old years
            elif BPI_line == 8:
                try:
                    self.Sagarin = int(line.strip())
                except ValueError: #TODO see above
                    self.Sagarin = 0
                BPI_line += 1
                continue

            if "ts-nitty-row" in line:
                game_line = 1
                continue
            if game_line == 1 and "NET" in line:
                header_line = True
                game_line += 1
                continue
            if header_line and game_line < 6:
                game_line += 1
                continue
            if header_line and game_line == 6:
                header_line = False
                game_line = 0
                continue
            if game_line == 1 and ">S<" in line:
                non_di_header_line = True
                game_line += 1
            if non_di_header_line and game_line < 5:
                game_line += 1
                continue
            if non_di_header_line and game_line == 5:
                non_di_header_line = False
                game_line = 0
                continue
            if game_line == 1:
                curr_game = Game("", "", 0, 0, "", False)
                game_line += 1
                if not non_di:
                    continue
            if game_line == 2:
                curr_game.location = line[line.find(">")+1]
                game_line += 1
                continue
            if game_line == 3:
                curr_game.opponent = line[line.find(">")+1:line.find("</div>")]
                if "ts-nitty-nonconf" not in line:
                    curr_game.conference_game = True
                game_line += 1
                continue
            if game_line == 4:
                curr_game.team_score = int(line[line.find(">")+1:line.find("</div>")])
                game_line += 1
                continue
            if game_line == 5:
                curr_game.opp_score = int(line[line.find(">")+1:line.find("</div>")])
                game_line += 1
                continue
            if game_line == 6:
                date = line[line.find(">")+1:line.find("</div>")]
                curr_game.date = date
                # cut out NCAA tournament games
                # only include non-DI losses. I think this is the closest thing to how the committee treats it
                if (int(date[1]) != 4 and (int(date[1]) != 3 or int(date[3:]) <= SELECTION_SUNDAY_DATES[year])) and \
                        (not non_di or curr_game.opp_score > curr_game.team_score):
                    self.games.add(curr_game)
                game_line = 0
                continue

    def get_conference_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if game.conference_game:
                if game.margin > 0:
                    wins += 1
                else:
                    losses += 1
        return str(wins) + "-" + str(losses)

    def get_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if game.margin > 0:
                wins += 1
            else:
                losses += 1
        return str(wins) + "-" + str(losses)
   
    def get_record_pct(self):
        record = self.record
        wins = int(record.split("-")[0])
        losses = int(record.split("-")[1])
        if not wins:
            return 0
        return wins/(wins + losses)

    def get_derived_record(self, quad):
        Q1_record = self.Q1_record
        Q2_record = self.Q2_record
        Q3_record = self.Q3_record
        Q4_record = self.Q4_record
        wins = int(Q1_record.split("-")[0])
        if quad > 1:
            wins += int(Q2_record.split("-")[0])
        if quad > 2:
            wins += int(Q3_record.split("-")[0])
        if quad > 3:
            wins += int(Q4_record.split("-")[0])
        losses = int(Q4_record.split("-")[1])
        if quad < 4:
            losses += int(Q3_record.split("-")[1])
        if quad < 3:
            losses += int(Q2_record.split("-")[1])
        if quad < 2:
            losses += int(Q1_record.split("-")[1])
        return str(wins) + "-" + str(losses)

    def get_derived_pct(self, quad):
        record = self.get_derived_record(quad)
        wins = int(record.split("-")[0])
        losses = int(record.split("-")[1])
        try:
            return wins/(wins + losses)
        except ZeroDivisionError:
            return 0

    def get_predictive(self):
        if self.Sagarin == 0:
            return sum([self.KenPom, self.BPI])/2
        else:
            return sum([self.KenPom, self.BPI, self.Sagarin])/3

    def get_results_based(self):
        if self.KPI == 0:
            return sum([self.WAB, self.SOR])/2
        else:
            return sum([self.KPI, self.SOR, self.WAB])/3

    record = property(get_record)
    conference_record = property(get_conference_record)
    record_pct = property(get_record_pct)
    #derived_Q1_record = property(get_derived_Q1_record)
    #derived_Q2_record = property(get_derived_Q2_record)
    #derived_Q3_record = property(get_derived_Q3_record)
    #derived_Q4_record = property(get_derived_Q4_record)
    predictive = property(get_predictive)
    results_based = property(get_results_based)








