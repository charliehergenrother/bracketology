#!/usr/bin/env python3

#class that represents one college basketball game from one team's perspective
class Game:

    def __init__(self, opp, loc, oNET, scr, oscr, dt):
        self.opponent = opp
        self.location = loc
        self.opp_NET = oNET
        self.team_score = scr
        self.opp_score = oscr
        self.date = dt

    def get_margin(self):
        return self.team_score - self.opp_score
    
    def get_quadrant(self):
        if self.location == "H":
            if self.opp_NET <= 30:
                return 1
            elif self.opp_NET <= 75:
                return 2
            elif self.opp_NET <= 160:
                return 3
            return 4
        elif self.location == "A":
            if self.opp_NET <= 75:
                return 1
            elif self.opp_NET <= 135:
                return 2
            elif self.opp_NET <= 260:
                return 3
            return 4
        elif self.location == "N":
            if self.opp_NET <= 50:
                return 1
            elif self.opp_NET <= 100:
                return 2
            elif self.opp_NET <= 200:
                return 3
            return 4
        else:
            return "problems have arisen"

    def get_win(self):
        if self.team_score - self.opp_score > 0:
            return True
        return False

    def reprJSON(self):
        return dict(opponent=self.opponent, location=self.location, opp_NET=self.opp_NET, team_score=self.team_score, opp_score=self.opp_score, date=self.date)

    margin = property(get_margin)
    quadrant = property(get_quadrant)
    win = property(get_win)
