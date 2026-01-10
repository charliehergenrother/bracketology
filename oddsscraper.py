#!/usr/bin/env python3

ODDS_PATH = "/mnt/c/Users/charl/Downloads/"

def do_fd_setup(oddsfile):
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "You need to enable" in line:
            break
    odds_tables = line.replace(">", ">\n")
    return odds_tables

def scrape_fanduel_conference():
    oddsfile = ODDS_PATH + "fd conf"
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
    results['championship'] = scrape_fanduel_main_list(ODDS_PATH + "fd champ")
    results['final_four'] = scrape_fanduel_main_list(ODDS_PATH + "fd ff")
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
    oddsfile = ODDS_PATH + "dk conf"
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
            try:
                results[team] = int(odds)
            except ValueError:  # the dash DK uses isn't a minus sign I guess
                results[team] = -int(odds[1:])
    return results


def scrape_draftkings():
    results = dict()
    results['championship'] = scrape_draftkings_main_list(ODDS_PATH + "dk champ")
    results['final_four'] = scrape_draftkings_main_list(ODDS_PATH + "dk ff")
    results['conference'] = scrape_draftkings_conference()
    return results

def do_caesars_setup(oddsfile):
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "2026 Mens NCAA" in line:
            break
    odds_tables = line.replace(">", ">\n")
    return odds_tables

def scrape_caesars_main_list(oddsfile):
    odds_tables = do_caesars_setup(oddsfile)
    results = dict()
    found_team = False
    found_odds = False
    for line in odds_tables.split("\n"):
        if "cui-text-ellipsis" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find(" </div>")]
            found_team = False
            continue
        if "market-button-odds" in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[team] = odds
            found_odds = False
            continue
    return results

def scrape_caesars_conference():
    oddsfile = ODDS_PATH + "cs conf"
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "Conference Winner" in line:
            break
    odds_tables = line.replace(">", ">\n")
    results = dict()
    found_team = False
    found_odds = False
    for line in odds_tables.split("\n"):
        if "Conference Winner" in line and "Regular Season" not in line:
            conference = line[:line.find(" Conference Winner</span>")]
            results[conference] = dict()
            continue
        if "cui-text-ellipsis" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find(" </div>")]
            found_team = False
            continue
        if "market-button-odds" in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[conference][team] = odds
            found_odds = False
            continue
    return results

def scrape_caesars():
    results = dict()
    results['championship'] = scrape_caesars_main_list(ODDS_PATH + "cs champ")
    results['conference'] = scrape_caesars_conference()
    return results

def scrape_betmgm_main_list(oddsfile):
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "National Championship" in line:
            break
    odds_tables = line.replace(">", ">\n")
    results = dict()
    found_team = False
    found_odds = False
    for line in odds_tables.split("\n"):
        if "name ng-star-inserted" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</div>")]
            found_team = False
            continue
        if "custom-odds-value-style" in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[team] = odds
            found_odds = False
            continue
        if "Show Less" in line:
            break
    return results

def scrape_betmgm_conference():
    oddsfile = ODDS_PATH + "bm all"
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "regular season winner" in line:
            break
    odds_tables = line.replace(">", ">\n")
    results = dict()
    found_team = False
    found_odds = False
    table_start = False
    for line in odds_tables.split("\n"):
        if not table_start:
            if "regular season winner" in line:
                table_start = True
            else:
                continue
        if "regular season winner" in line:
            conference = line[9:line.find(" regular season winner")]
            results[conference] = dict()
            continue
        if "name ng-star-inserted" in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</div>")]
            found_team = False
            continue
        if "custom-odds-value-style" in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[conference][team] = odds
            found_odds = False
            continue
        if "Wooden" in line:
            break
    return results

def scrape_betmgm():
    results = dict()
    results['championship'] = scrape_betmgm_main_list(ODDS_PATH + "bm all")
    results['conference'] = scrape_betmgm_conference()
    return results

def scrape_bet365_main_list(oddsfile):
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "NCAA Championship 2025" in line:
            break
    odds_tables = line.replace(">", ">\n")
    results = dict()
    found_team = False
    found_odds = False
    for line in odds_tables.split("\n"):
        if 'ParticipantBorderless_Name">' in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</span>")].rstrip()
            found_team = False
            continue
        if 'ParticipantBorderless_Odds">' in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[team] = odds
            found_odds = False
            continue
    return results

def scrape_bet365_conference():
    oddsfile = ODDS_PATH + "bt conf.html"
    f = open(oddsfile, "r")
    for line in f.read().split("\n"):
        if "Regular Season 2025" in line:
            break
    odds_tables = line.replace(">", ">\n")
    results = dict()
    found_team = False
    found_odds = False
    for line in odds_tables.split("\n"):
        if "Regular Season 2025" in line:
            conference = line[:line.find(" Regular Season 2025")]
            results[conference] = dict()
            continue
        if 'ParticipantBorderless_Name">' in line:
            found_team = True
            continue
        if found_team:
            team = line[:line.find("</span>")].rstrip()
            found_team = False
            continue
        if 'ParticipantBorderless_Odds">' in line:
            found_odds = True
            continue
        if found_odds:
            odds = int(line[:line.find("</span>")])
            results[conference][team] = odds
            found_odds = False
            continue
    return results

def scrape_bet365():
    results = dict()
    results['championship'] = scrape_bet365_main_list(ODDS_PATH + "bt champ.html")
    results['final_four'] = scrape_bet365_main_list(ODDS_PATH + "bt ff.html")
    results['conference'] = scrape_bet365_conference()
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
        "McNeese State": "McNeese",
        "Alabama Crimson": "Alabama",
        "Albany Great": "Albany",
        "Arizona State Sun": "Arizona-State",
        "Arkansas State Red": "Arkansas-State",
        "Army Black": "Army",
        "California Golden": "California",
        "Campbell Fighting": "Campbell",
        "Canisius Golden": "Canisius",
        "Central Connecticut State Blue": "Central-Connecticut",
        "Cornell Big": "Cornell",
        "Dartmouth Big": "Dartmouth",
        "Delaware Fightin' Blue": "Delaware",
        "DePaul Blue": "DePaul",
        "Detroit Mercy": "Detroit",
        "Duke Blue": "Duke",
        "Evansville Purple": "Evansville",
        "Gardner Webb Runnin'": "Gardner-Webb",
        "Georgia Tech Yellow": "Georgia-Tech",
        "Hawaii Rainbow": "Hawaii",
        "Illinois Fighting": "Illinois",
        "Kent State Golden": "Kent-State",
        "Lehigh Mountain": "Lehigh",
        "Louisiana Ragin'": "Louisiana",
        "Maine Black": "Maine",
        "Marist Red": "Marist",
        "Marquette Golden": "Marquette",
        "Marshall Thundering": "Marshall",
        "Massachusetts": "UMass",
        "Miami (FL)": "Miami-FL",
        "Middle Tennessee Blue": "Middle-Tennessee",
        "Minnesota Golden": "Minnesota",
        "Nevada Wolf": "Nevada",
        "Niagara Purple": "Niagara",
        "North Carolina Tar": "North-Carolina",
        "North Carolina A&amp;T": "North-Carolina-AT",
        "North Dakota Fighting": "North-Dakota",
        "North Texas Mean": "North-Texas",
        "Notre Dame Fighting": "Notre-Dame",
        "Oakland Golden": "Oakland",
        "Oral Roberts Golden": "Oral-Roberts",
        "Penn State Nittany": "Penn-State",
        "Pennsylvania": "Penn",
        "Presbyterian Blue": "Presbyterian-College",
        "Queens University": "Queens",
        "Rutgers Scarlet": "Rutgers",
        "Southern Miss Golden": "Southern-Miss",
        "St. John's Red": "Saint-Johns",
        "St. Thomas (MN)": "Saint-Thomas",
        "TCU Horned": "TCU",
        "Texas Tech Red": "Texas-Tech",
        "Tulane Green": "Tulane",
        "Tulsa Golden": "Tulsa",
        "UMass Lowell River": "UMass-Lowell",
        "UNC Wilmington": "UNCW",
        "USC Upstate": "South-Carolina-Upstate",
        "Valparais": "Valparaiso",
        "Wake Forest Demon": "Wake-Forest",
        "William &amp; Mary": "William-Mary",
       
        "Cal St. Bakersfield": "Cal-State-Bakersfield",
        "Cal St. Fullerton": "Cal-State-Fullerton",
        "Cal St. Northridge": "Cal-State-Northridge",
        "E Kentucky": "Eastern-Kentucky",
        "Florida Gulf Coast": "FGCU",
        "GA Southern": "Georgia-Southern",
        "Hawai'i": "Hawaii",
        "Loyola MD": "Loyola-Maryland",
        "N.C. State": "North-Carolina-State",
        "Pitt": "Pittsburgh",
        "Presbyterian": "Presbyterian-College",
        "St. Mary's": "Saint-Marys-College",
        "Western KY": "Western-Kentucky",
        "W Carolina": "Western-Carolina",

        "Miami Florida": "Miami-FL",
        "Miami Ohio": "Miami-OH",
        "Mississippi": "Ole-Miss",
        "VA Commonwealth": "VCU",
    }
    if team in ad_hoc_dict:
        return ad_hoc_dict[team]
    fixed_team = team.replace(" ", "-")
    return fixed_team

def run_combine(book_results, book_abbreviation, full_results):
    for team in book_results:
        if book_abbreviation == "CS":
            if team == "Loyola Ramblers":
                stripped_team = "Loyola-Chicago"
            elif team == "Loyola Greyhounds":
                stripped_team = "Loyola-Maryland"
            else:
                stripped_team = team[:team.rfind(' ')]
            fixed_team = translate_team_name(stripped_team)
        elif book_abbreviation == "BM":
            adjusted_team = team
            if team[-3:] == " St":
                adjusted_team = team[:-3] + " State"
            if team[-4:] == " St.":
                adjusted_team = team[:-4] + " State"
            fixed_team = translate_team_name(adjusted_team)
        else:
            fixed_team = translate_team_name(team)
        if fixed_team not in full_results:
            full_results[fixed_team] = dict()
        full_results[fixed_team][book_abbreviation] = book_results[team]

def combine_results(fd, dk, cs, bm, bt):
    results = {'conference': dict(), 'final_four': dict(), 'championship': dict()}
    conference_lookup = {
        "ACC Conference": "ACC",
        "Big 10 Conference": "Big Ten",
        "Big 12 Conference": "Big 12",
        "Big East Conference": "Big East",
        "SEC Conference": "SEC",
        "American Athletic Conference": "American",
        "AAC": "American",
        "Atlantic 10 Conference": "Atlantic 10",
        "Conference USA": "Conference USA",
        "MAC": "Mid-American",
        "Missouri Valley Conference": "Missouri Valley",
        "Mountain West Conference": "Mountain West",
        "Southern Conference": "Southern",
        "West Coast Conference": "West Coast",
        "Atlantic Sun": "ASUN",
        "Summit League": "The Summit League",
        "Big 10": "Big Ten",
        "American Conference": "American",
        " Atlantic Sun Conference": "ASUN",
        "Big Sky Conference": "Big Sky",
        "Big South Conference": "Big South",
        "Big West Conference": "Big West",
        "Sun Belt Conference": "Sun Belt",
        "American Athletic": "American",
        "CAA Conference": "Coastal Athletic",
    }
    for conference in fd['conference']:
        conf_name = conference_lookup[conference]
        results['conference'][conf_name] = dict()
        for team in fd['conference'][conference]:
            fixed_team = translate_team_name(team)
            results['conference'][conf_name][fixed_team] = {"FD": fd['conference'][conference][team]}
    for conference in dk['conference']:
        if conference not in results['conference']:
            results['conference'][conference] = dict()
        run_combine(dk['conference'][conference], 'DK', results['conference'][conference])
    for conference in cs['conference']:
        conf_name = conference
        if conference in conference_lookup:
            conf_name = conference_lookup[conference]
        if conf_name not in results['conference']:
            results['conference'][conf_name] = dict()
        run_combine(cs['conference'][conference], 'CS', results['conference'][conf_name])
    for conference in bm['conference']:
        conf_name = conference
        if conference in conference_lookup:
            conf_name = conference_lookup[conference]
        if conf_name not in results['conference']:
            results['conference'][conf_name] = dict()
        run_combine(bm['conference'][conference], 'BM', results['conference'][conf_name])
    for conference in bt['conference']:
        conf_name = conference
        if conference in conference_lookup:
            conf_name = conference_lookup[conference]
        if conf_name not in results['conference']:
            results['conference'][conf_name] = dict()
        run_combine(bt['conference'][conference], 'BT', results['conference'][conf_name])
    
    for team in fd['final_four']:
        fixed_team = translate_team_name(team)
        results['final_four'][fixed_team] = {'FD': fd['final_four'][team]}
    run_combine(dk['final_four'], 'DK', results['final_four'])
    run_combine(bt['final_four'], 'BT', results['final_four'])
    
    for team in fd['championship']:
        fixed_team = translate_team_name(team)
        results['championship'][fixed_team] = {'FD': fd['championship'][team]}
    run_combine(dk['championship'], 'DK', results['championship'])
    run_combine(cs['championship'], 'CS', results['championship'])
    run_combine(bm['championship'], 'BM', results['championship'])
    run_combine(bt['championship'], 'BT', results['championship'])

    return results

def get_best_odds(all_odds):
    max_odds = float('-inf')
    for odds in all_odds:
        if odds == '':
            continue
        if float(odds) > max_odds:
            max_odds = float(odds)
    return str(max_odds)

def write_book_odds(f, team, results, books):
    all_odds = list()
    f.write(team + ",")
    for book in books:
        try:
            odds = get_string_odds(results[book])
            plus_odds = get_plus_odds(odds)
        except KeyError:
            odds = ""
            plus_odds = ""
        f.write(odds + "," + plus_odds + ",")
        all_odds.append(plus_odds)
    best_odds = get_best_odds(all_odds)
    f.write(best_odds + "\n")

def main():
    output = "./currentodds.csv"
    f = open(output, "w")
    fd_results = scrape_fanduel()
    dk_results = scrape_draftkings()
    cs_results = scrape_caesars()
    bm_results = scrape_betmgm()
    bt_results = scrape_bet365()
    results = combine_results(fd_results, dk_results, cs_results, bm_results, bt_results)
    for conference in results['conference']:
        f.write(conference + "\n")
        f.write("Team,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds\n")
        for team in sorted(results['conference'][conference]):
            write_book_odds(f, team, results['conference'][conference][team], ["FD", "DK", "CS", "BM", "BT"])
        f.write("\n")

    f.write("FINAL FOUR\n")
    f.write("Team,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds\n")
    for team in sorted(results['final_four']):
        write_book_odds(f, team, results['final_four'][team], ["FD", "DK", "CS", "BM", "BT"])
    f.write("\n")

    f.write('CHAMPIONSHIP\n')
    f.write("Team,FanDuel,FD+,DraftKings,DK+,Caesars,CS+,BetMGM,BM+,Bet365,BT+,best odds\n")
    for team in sorted(results['championship']):
        write_book_odds(f, team, results['championship'][team], ["FD", "DK", "CS", "BM", "BT"])
    f.write("\n")
    print()
    print("Successfully wrote odds!")
    print()

if __name__ == "__main__":
    main()
