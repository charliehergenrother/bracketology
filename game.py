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
    
    def reprJSON(self):
        return dict(opponent=self.opponent, location=self.location, opp_NET=self.opp_NET, team_score=self.team_score, opp_score=self.opp_score, date=self.date)

    margin = property(get_margin)
