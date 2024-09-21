#!/usr/bin/env python3

#class to run simulations based on combinations of weights to determine predictive power of each resume attribute
class Tracker:

    def __init__(self, bdr, scr, yr, vrb, m):
        self.year = yr
        self.teams = bdr.teams
        self.verbose = vrb
        self.ineligible_teams = bdr.ineligible_teams
        self.weight_results = dict()
        self.scorer = scr
        self.mens = m
        return

    def load_results(self):
        self.actual_results = dict()
        counter = 0
        if self.mens:
            resultfile = "lib/men/" + self.year + "/actual_results.txt"
        else:
            resultfile = "lib/women/" + self.year + "/actual_results.txt"
        with open(resultfile) as f:
            for line in f.read().split("\n"):
                if not line:
                    break
                self.actual_results[line] = counter
                counter += 1
        self.actual_max = counter

    def run_tracker(self, weights_collected):
        if len(weights_collected) == 1:
            print("~~~~~~~~~~")
        elif len(weights_collected) == 2:
            print("~~~~~~~~")
        elif len(weights_collected) == 3:
            print("~~~~~~")

        if len(weights_collected) in []:
            for num in [27, 28]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [26, 27]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [25, 26]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [24, 25]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [23, 24]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [2]:
            for num in [22, 23]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [21, 22]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [20, 21]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [19, 20]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [18, 19]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [17.5, 18.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [17, 18]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [16.5, 17.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [0]:
            for num in [16, 17]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [15.5, 16.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [15, 16]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [14.5, 15.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [3, 5]:
            for num in [14, 15]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [13.5, 14.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [13, 14]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [12.5, 13.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [12, 13]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [11.5, 12.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [11, 12]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [10.5, 11.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [10, 11]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [9.5, 10]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [9, 9.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [8.5, 9]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [8, 8.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [7.5, 8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [7.2, 7.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [11]:
            for num in [7, 7.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [6.7, 7]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [6.5, 6.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [6.2, 6.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [6, 6.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [5.7, 6]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [9]:
            for num in [5.5, 5.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [5.2, 5.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [5, 5.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [4.7, 5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [4.5, 4.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [4.2, 4.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [7, 10]:
            for num in [4, 4.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [8]:
            for num in [3.7, 4]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [3.5, 3.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [3.2, 3.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [3, 3.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [4]:
            for num in [2.7, 3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [2.5, 2.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [2.2, 2.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [12]:
            for num in [2, 2.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [1.7, 2]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [1.5, 1.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [1.2, 1.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [6]:
            for num in [1, 1.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [13]:
            for num in [0.7, 1]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [0.5, 0.8]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [14]:
            for num in [0.2, 0.5]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in [1]:
            for num in [0, 0.3]:
                self.run_tracker(weights_collected + (num,))
        elif len(weights_collected) in []:
            for num in [0]:
                self.run_tracker(weights_collected + (num,))
        else:
            WEIGHTS = dict()
            WEIGHTS["LOSS_WEIGHT"] = weights_collected[0]
            WEIGHTS["NET_WEIGHT"] = weights_collected[1]
            WEIGHTS["POWER_WEIGHT"] = weights_collected[2]
            WEIGHTS["Q1_WEIGHT"] = weights_collected[3]
            WEIGHTS["Q2_WEIGHT"] = weights_collected[4]
            WEIGHTS["Q3_WEIGHT"] = 0#weights_collected[5]
            WEIGHTS["RESULTS_BASED_WEIGHT"] = weights_collected[5]
            WEIGHTS["Q4_WEIGHT"] = weights_collected[6]
            WEIGHTS["ROAD_WEIGHT"] = weights_collected[7]
            WEIGHTS["NEUTRAL_WEIGHT"] = weights_collected[8]
            WEIGHTS["TOP_10_WEIGHT"] = weights_collected[9]
            WEIGHTS["TOP_25_WEIGHT"] = weights_collected[10]
            WEIGHTS["SOS_WEIGHT"] = weights_collected[11]
            WEIGHTS["NONCON_SOS_WEIGHT"] = weights_collected[12]
            WEIGHTS["AWFUL_LOSS_WEIGHT"] = weights_collected[13]
            WEIGHTS["BAD_LOSS_WEIGHT"] = weights_collected[14]
            self.scorer.build_scores(WEIGHTS)
            self.assess_results(weights_collected)

    def assess_results(self, weights_collected):
        result_score = 0
        bid_count = 0
        actual_count = 0
        for team in sorted(self.teams, key=lambda x: self.teams[x].score, reverse=True):
            if team in self.ineligible_teams or self.teams[team].record_pct < 0.5:
                continue
            try:
                result_score += abs(bid_count - self.actual_results[team])
                actual_count += 1
            except KeyError:
                pass
            bid_count += 1
            if actual_count >= self.actual_max - 2:
                break
        self.weight_results[weights_collected] = result_score
