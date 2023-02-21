#!/usr/bin/env python3

class Game:

    def __init__(self, opp, loc, oNET, scr, oscr):
        self.opponent = opp
        self.location = loc
        self.opp_NET = oNET
        self.team_score = scr
        self.opp_score = oscr
        #self.OT = ot TODO: figure out

    def get_margin(self):
        return self.team_score - self.opp_score
    
    def reprJSON(self):
        return dict(opponent=self.opponent, location=self.location, opp_NET=self.opp_NET, team_score=self.team_score, opp_score=self.opp_score)

    margin = property(get_margin)
