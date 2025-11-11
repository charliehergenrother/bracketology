#!/usr/bin/env python3

def do_fd_setup(oddsfile):
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "You need to enable" in line:
            break
    odds_tables = line.replace(">", ">\n")
    return odds_tables

def scrape_fanduel_conference():
    oddsfile = "/mnt/c/Users/charl/Downloads/fd conf"
    odds_tables = do_fd_setup(oddsfile)
    results = dict()
    conference = ""
    team = ""
    for line in odds_tables.split("\n"):
        if "NCAAB Odds" in line:
            break
        if " Regular Season Winner 2025-2026</span>" in line or " Regular Season Winner 2025-2026 (Without IL Schools)</span>" in line:
            conference = line[:line.find(" Regular")]
            results[conference] = dict()
            continue
        if conference and "</span>" in line and "Show less" not in line:
            if not team:
                team = line[:line.index("</span>")]
            else:
                odds = line[:line.index("</span>")]
                results[conference][team] = int(odds)
                team = ""
    return results

def scrape_fanduel_main_list(oddsfile):
    odds_tables = do_fd_setup(oddsfile)
    results = dict()
    conference = ""
    team = ""
    start_table = False
    for line in odds_tables.split("\n"):
        if "Show less" in line:
            break
        if not start_table:
            if "To Reach the Final" in line or "Championship Winner" in line:
                start_table = True
            continue
        if "</span>" in line:
            if not team:
                team = line[:line.index("</span>")]
            else:
                odds = line[:line.index("</span>")]
                results[team] = int(odds)
                team = ""
    return results

def scrape_fanduel():
    results = dict()
    results['championship'] = scrape_fanduel_main_list("/mnt/c/Users/charl/Downloads/fd champ")
    results['final_four'] = scrape_fanduel_main_list("/mnt/c/Users/charl/Downloads/fd ff")
    results['conference'] = scrape_fanduel_conference()
    return results

def do_dk_setup(oddsfile):
    f = open(oddsfile, "r")
    for line in f:
        if "Team to Reach" in line or "Men's NCAA Tournament Winner" in line or "Men's NCAAB Conference" in line:
            break
    odds_tables = line.replace(">", ">\n")
    return odds_tables

def scrape_draftkings_conference():
    oddsfile = "/mnt/c/Users/charl/Downloads/dk conf"
    found_team = False
    found_odds = False
    odds_tables = do_dk_setup(oddsfile)
    results = dict()
    for line in odds_tables.split("\n"):
        if " Regular Season Conference Winner" in line:
            conference = line[:line.find(" Regular")]
            results[conference] = dict()
        if "cb-market__button-title" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</span>")]
            found_team = False
        if "cb-market__button-odds" in line:
            found_odds = True
            continue
        if found_odds:
            odds = line[:line.find("</span>")]
            found_odds = False
            try:
                results[conference][team] = int(odds)
            except ValueError:  #aren't em dashes fun
                results[conference][team] = -int(odds[1:])
    return results

def scrape_draftkings_main_list(oddsfile):
    found_team = False
    found_odds = False
    odds_tables = do_dk_setup(oddsfile)
    results = dict()
    for line in odds_tables.split("\n"):
        if "cb-market__button-title" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</span>")]
            found_team = False
        if "cb-market__button-odds" in line:
            found_odds = True
            continue
        if found_odds:
            odds = line[:line.find("</span>")]
            found_odds = False
            results[team] = int(odds)
    return results


def scrape_draftkings():
    results = dict()
    results['championship'] = scrape_draftkings_main_list("/mnt/c/Users/charl/Downloads/dk champ")
    results['final_four'] = scrape_draftkings_main_list("/mnt/c/Users/charl/Downloads/dk ff")
    results['conference'] = scrape_draftkings_conference()
    return results

def get_string_odds(odds):
    if odds < 0:
        return str(odds)
    return "+" + str(odds)

def get_plus_odds(odds):
    if int(odds) < 0:
        return str((100/(int(odds)/(int(odds) - 100))) - 100)
    return odds

def translate_team_name(team):
    ad_hoc_dict = {
        "Miami": "Miami-FL",
        "WV Mountaineers": "West-Virginia",
        "St. Johns": "Saint-Johns",
        "St. John's": "Saint-Johns",
        "UConn": "Connecticut",
        "San Jose St": "San-Jose-State",
        "Saint Mary's": "Saint-Marys-College",
        "Saint Marys": "Saint-Marys-College",
        "NC State": "North-Carolina-State",
        "Texas A&amp;M": "Texas-AM",
        "GW Revolutionaries": "George-Washington",
        "Saint Joseph's": "Saint-Josephs",
        "St. Bonaventure": "Saint-Bonaventure",
        "Miami (OH)": "Miami-OH",
        "Seattle": "Seattle-University",
        "Florida Atlantic": "FAU",
        "Florida International": "FIU",
        "UNC Greensboro": "UNCG",
        "Citadel": "The-Citadel",
    }
    if team in ad_hoc_dict:
        return ad_hoc_dict[team]
    fixed_team = team.replace(" ", "-")
    return fixed_team

def combine_results(fd, dk):
    results = {'conference': dict(), 'final_four': dict(), 'championship': dict()}
    conference_lookup = {
        "ACC Conference": "ACC",
        "Big 10 Conference": "Big Ten",
        "Big 12 Conference": "Big 12",
        "Big East Conference": "Big East",
        "SEC Conference": "SEC",
        "American Athletic Conference": "American",
        "Atlantic 10 Conference": "Atlantic 10",
        "Conference USA": "Conference USA",
        "MAC": "Mid-American",
        "Missouri Valley Conference": "Missouri Valley",
        "Mountain West Conference": "Mountain West",
        "Southern Conference": "Southern",
        "West Coast Conference": "West Coast"
    }
    for conference in fd['conference']:
        conf_name = conference_lookup[conference]
        results['conference'][conf_name] = dict()
        for team in fd['conference'][conference]:
            fixed_team = translate_team_name(team)
            results['conference'][conf_name][fixed_team] = {"FD": fd['conference'][conference][team]}
    for conference in dk['conference']:
        if conference not in results['conference']:
            print(conference)
            raise Exception
        for team in dk['conference'][conference]:
            fixed_team = translate_team_name(team)
            if fixed_team not in results['conference'][conference]:
                print(team)
                print(results['conference'][conference])
                raise Exception
            results['conference'][conference][fixed_team]["DK"] = dk['conference'][conference][team]
    
    for team in fd['final_four']:
        fixed_team = translate_team_name(team)
        results['final_four'][fixed_team] = {'FD': fd['final_four'][team]}
    for team in dk['final_four']:
        fixed_team = translate_team_name(team)
        if fixed_team not in results['final_four']:
            print(team)
            print(results['final_four'])
            raise Exception
        results['final_four'][fixed_team]['DK'] = dk['final_four'][team]
    
    for team in fd['championship']:
        fixed_team = translate_team_name(team)
        results['championship'][fixed_team] = {'FD': fd['championship'][team]}
    for team in dk['championship']:
        fixed_team = translate_team_name(team)
        if fixed_team not in results['championship']:
            print(team)
            print(results['championship'])
            raise Exception
        results['championship'][fixed_team]['DK'] = dk['championship'][team]
 

    return results

def get_best_odds(fd, dk):
    if fd == "":
        return dk
    if dk == "":
        return fd
    return str(max(float(fd), float(dk)))

def main():
    output = "./currentodds.csv"
    f = open(output, "w")
    fd_results = scrape_fanduel()
    dk_results = scrape_draftkings()
    results = combine_results(fd_results, dk_results)
    for conference in results['conference']:
        f.write(conference + "\n")
        f.write("Team,Odds,FanDuel,FanDuel+,DraftKings,DK+,best odds\n")
        for team in sorted(results['conference'][conference]):
            fd_odds = get_string_odds(results['conference'][conference][team]["FD"])
            fd_plus_odds = get_plus_odds(fd_odds)
            if "DK" in results['conference'][conference][team]:
                dk_odds = get_string_odds(results['conference'][conference][team]["DK"])
                dk_plus_odds = get_plus_odds(dk_odds)
                f.write(team + ",," + \
                    fd_odds + "," + fd_plus_odds + "," + \
                    dk_odds + "," + dk_plus_odds + "," + \
                    str(max(float(fd_plus_odds), float(dk_plus_odds))) + "\n")
            else:
                f.write(team + ",," + \
                    fd_odds + "," + fd_plus_odds + "," + \
                    "," + "," + \
                    fd_plus_odds + "\n")
        f.write("\n")

    f.write("FINAL FOUR\n")
    f.write("Team,Odds,FanDuel,FanDuel+,DraftKings,DK+,best odds\n")
    for team in sorted(results['final_four']):
        try:
            fd_odds = get_string_odds(results['final_four'][team]["FD"])
            fd_plus_odds = get_plus_odds(fd_odds)
        except KeyError:
            fd_odds = ""
            fd_plus_odds = ""
        try:
            dk_odds = get_string_odds(results['final_four'][team]["DK"])
            dk_plus_odds = get_plus_odds(dk_odds)
        except KeyError:
            dk_odds = ""
            dk_plus_odds = ""
        best_odds = get_best_odds(fd_plus_odds, dk_plus_odds)
        f.write(team + ",," + \
            fd_odds + "," + fd_plus_odds + "," + \
            dk_odds + "," + dk_plus_odds + "," + \
            best_odds + "\n")
    f.write("\n")

    f.write('CHAMPIONSHIP\n')
    f.write("Team,Odds,FanDuel,FanDuel+,DraftKings,DK+,best odds\n")
    for team in sorted(results['championship']):
        try:
            fd_odds = get_string_odds(results['championship'][team]["FD"])
            fd_plus_odds = get_plus_odds(fd_odds)
        except KeyError:
            fd_odds = ""
            fd_plus_odds = ""
        try:
            dk_odds = get_string_odds(results['championship'][team]["DK"])
            dk_plus_odds = get_plus_odds(dk_odds)
        except KeyError:
            dk_odds = ""
            dk_plus_odds = ""
        best_odds = get_best_odds(fd_plus_odds, dk_plus_odds)
        f.write(team + ",," + \
            fd_odds + "," + fd_plus_odds + "," + \
            dk_odds + "," + dk_plus_odds + "," + \
            best_odds + "\n")
    f.write("\n")
    print()
    print("Successfully wrote odds!")
    print()


if __name__ == "__main__":
    main()
