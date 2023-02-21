#!/usr/bin/env python3

from game import Game
import requests
import sys

class Team:

    def reprJSON(self):
        return dict(conference=self.conference, NET=self.NET, KenPom=self.KenPom, BPI=self.BPI, Sagarin=self.Sagarin, KPI=self.KPI, SOR=self.SOR, NET_SOS=self.NET_SOS, noncon_SOS=self.noncon_SOS, games=self.games)

    def __init__(self):
        self.conference = ""
        self.NET = 0
        self.KenPom = 0
        self.BPI = 0
        self.Sagarin = 0
        self.KPI = 0
        self.SOR = 0
        self.NET_SOS = 0
        self.noncon_SOS = 0
        self.games = set()
    
    def fill_data(self, conf, net, kp, bpi, sag, kpi, sor, netsos, ncsos, gms):
        self.conference = conf
        self.NET = net
        self.KenPom = kp
        self.BPI = bpi
        self.Sagarin = sag
        self.KPI = kpi
        self.SOR = sor
        self.NET_SOS = netsos
        self.noncon_SOS = ncsos
        self.games = gms

    def scrape_data(self, url):
        team_page = requests.get(url)
        if team_page.status_code != 200:
            print("team problem!", url)
            sys.exit()
        SOS_line = 0
        KPI_line = 0
        BPI_line = 0
        header_line = True
        game_line = 0
        self.games = set()
        for line in team_page.text.split("\n"):
            if "Non-Division I Games" in line:
                break
            if "team-menu__conference" in line:
                self.conference = line[line.find('">', line.find("/conference/"))+2:line.find("</a>")]
                continue
            if "font-weight: bold; font-size: 16px;" in line:
                self.NET = int(line[line.find("16px")+7:line.find("</span>")])
                continue
            if not SOS_line:
                if ("NET SOS") in line:
                    SOS_line += 1
                continue
            elif SOS_line < 4:
                SOS_line += 1
                continue
            elif SOS_line == 4:
                self.NET_SOS = int(line.strip()[:line.strip().find("<")])
                SOS_line += 1
                continue
            elif SOS_line == 5:
                self.noncon_SOS = int(line.strip())
                SOS_line += 1
                continue
            
            if not KPI_line:
                if ("KPI") in line:
                    KPI_line += 1
                    continue
            elif KPI_line < 4:
                KPI_line += 1
                continue
            elif KPI_line == 4:
                self.KPI = int(line.strip()[:line.strip().find("<")])
                KPI_line += 1
                continue
            elif KPI_line == 5:
                self.SOR = int(line.strip())
                KPI_line += 1
                continue
            
            if not BPI_line:
                if ("BPI") in line:
                    BPI_line += 1
                    continue
            elif BPI_line < 5:
                BPI_line += 1
                continue
            elif BPI_line == 5:
                self.BPI = int(line.strip()[:line.strip().find("<")])
                BPI_line += 1
                continue
            elif BPI_line == 6:
                self.KenPom = int(line.strip()[:line.strip().find("<")])
                BPI_line += 1
                continue
            elif BPI_line == 7:
                self.Sagarin = int(line.strip())
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
            if game_line == 1:
                curr_game = Game("", "", 0, 0, 0)
                curr_game.opp_NET = int(line[line.find(">")+1:line.find("</div>")])
                game_line += 1
                continue
            if game_line == 2:
                curr_game.location = line[line.find(">")+1]
                game_line += 1
                continue
            if game_line == 3:
                curr_game.opponent = line[line.find(">")+1:line.find("</div>")]
                game_line += 1
                continue
            if game_line == 4:
                curr_game.team_score = int(line[line.find(">")+1:line.find("</div>")])
                game_line += 1
                continue
            if game_line == 5:
                curr_game.opp_score = int(line[line.find(">")+1:line.find("</div>")])
                self.games.add(curr_game)
                game_line = 0
                continue


    def get_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if game.margin > 0:
                wins += 1
            else:
                losses += 1
        return str(wins) + "-" + str(losses)
    
    def get_Q1_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if game.opp_NET <= 30 or (game.opp_NET <= 50 and game.location == "N") or (game.opp_NET <= 75 and game.location == "A"):
                if game.margin > 0:
                    wins += 1
                else:
                    losses += 1
        return str(wins) + "-" + str(losses)

    def get_Q1_pct(self):
        record = self.Q1_record
        try:
            return int(record[:record.find("-")]) / \
                (int(record[record.find("-")+1:]) + int(record[:record.find("-")]))
        except ZeroDivisionError:
            return 0

    def get_Q2_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if (game.opp_NET >= 31 and game.opp_NET <= 75 and game.location == "H") or \
                (game.opp_NET >= 51 and game.opp_NET <= 100 and game.location == "N") or \
                (game.opp_NET >= 76 and game.opp_NET <= 135 and game.location == "A"):
                if game.margin > 0:
                    wins += 1
                else:
                    losses += 1
        return str(wins) + "-" + str(losses)

    def get_Q2_pct(self):
        record = self.Q2_record
        try:
            return int(record[:record.find("-")]) / \
                (int(record[record.find("-")+1:]) + int(record[:record.find("-")]))
        except ZeroDivisionError:
            return 0

    def get_Q3_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if (game.opp_NET >= 76 and game.opp_NET <= 160 and game.location == "H") or \
                (game.opp_NET >= 101 and game.opp_NET <= 200 and game.location == "N") or \
                (game.opp_NET >= 136 and game.opp_NET <= 240 and game.location == "A"):
                if game.margin > 0:
                    wins += 1
                else:
                    losses += 1
        return str(wins) + "-" + str(losses)

    def get_Q3_pct(self):
        record = self.Q3_record
        try:
            return int(record[:record.find("-")]) / \
                (int(record[record.find("-")+1:]) + int(record[:record.find("-")]))
        except ZeroDivisionError:
            return 0

    def get_Q4_record(self):
        wins = 0
        losses = 0
        for game in self.games:
            if game.opp_NET >= 241 or (game.opp_NET >= 201 and game.location == "N") or (game.opp_NET >= 161 and game.location == "H"):
                if game.margin > 0:
                    wins += 1
                else:
                    losses += 1
        return str(wins) + "-" + str(losses)

    def get_Q4_pct(self):
        record = self.Q4_record
        try:
            return int(record[:record.find("-")]) / \
                (int(record[record.find("-")+1:]) + int(record[:record.find("-")]))
        except ZeroDivisionError:
            return 0

    def get_predictive(self):
        return sum([self.KenPom, self.BPI, self.Sagarin])/3

    def get_results_based(self):
        return sum(self.KPI, self.SOR)/2

    record = property(get_record)
    Q1_record = property(get_Q1_record)
    Q2_record = property(get_Q2_record)
    Q3_record = property(get_Q3_record)
    Q4_record = property(get_Q4_record)
    Q1_pct = property(get_Q1_pct)
    Q2_pct = property(get_Q2_pct)
    Q3_pct = property(get_Q3_pct)
    Q4_pct = property(get_Q4_pct)
    derived_Q1_record = property(get_derived_Q1_record)
    derived_Q2_record = property(get_derived_Q2_record)
    derived_Q3_record = property(get_derived_Q3_record)
    derived_Q4_record = property(get_derived_Q4_record)
    predictive = property(get_predictive)
    results_based = property(get_results_based)








