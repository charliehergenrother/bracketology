#!/usr/bin/env python3

#class that represents one college basketball game from one team's perspective
class Game:

    def __init__(self, opp, loc, scr, oscr, dt):
        self.opponent = opp
        self.location = loc
        self.team_score = scr
        self.opp_score = oscr
        self.date = dt

    def get_margin(self):
        return self.team_score - self.opp_score
    
    def get_win(self):
        if self.team_score - self.opp_score > 0:
            return True
        return False

    def reprJSON(self):
        return dict(opponent=self.opponent, location=self.location, team_score=self.team_score, opp_score=self.opp_score, date=self.date)

    margin = property(get_margin)
    win = property(get_win)
