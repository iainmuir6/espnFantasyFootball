# Iain Muir
# iam9ez

import pandas as pd
import requests
import time

# League of Extraordinary Gentlemen
swid = "{94FD803F-87FC-4BDC-BD80-3F87FCEBDCFC}"
espn_s2 = "AEA%2Fs7CAHybhPWiuG5cTGqmfaH2%2F%2FeUCDP5bTDB4j0hDCLGW58ieoYJCnEB9uxNNPrx1CRjc8cuCinM54m2mUnf5PwfVmZ6Xup" \
          "0Hx1GSpuVoHuTjibfHSbu%2FDM0Zp%2BDhDygZS7zUVRZ1ag7Dm%2F7S2zcys1Ywxf4Fj1mFVKOmnIygFMV1a8LlMRy5W4ZpkvCvJzmQ" \
          "JTZcgfBncMmt1wh5IbsVWJwAm8ElISHA%2F9ooLplPppnKwIi1jbzeJv1UHIuh%2Bio%3D"

slot_codes = {
    0: 'QB', 1: 'TQB', 2: 'RB', 3: 'RB/WR', 4: 'WR', 5: 'WR/TE',
    6: 'TE', 7: 'OP',  8: 'DT', 9: 'DE', 10: 'LB', 11: 'DL',
    12: 'CB', 13: 'S', 14: 'DB', 15: 'DP', 16: 'D/ST', 17: 'K',
    18: 'P', 19: 'HC', 20: 'BE', 21: 'IR', 22: '', 23: 'RB/WR/TE'
}
default_codes = {
    1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'
}


# def get_position(eligible):
#     if 25 in eligible:
#         eligible.remove(25)
#     return {
#         [2, 3, 23, 7, 20, 21]: 'RB',
#         [3, 4, 5, 23, 7, 20, 21]: 'WR',
#         [5, 6, 23, 7, 20, 21]: 'TE',
#         [0, 7, 20, 21]: 'QB',
#     }.get(eligible, lambda: "Ack!")()


leagueID = 1080747
season = 2020

start = time.time()

# --------------------------- LEAGUE INFO ---------------------------
url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + str(season) + "/segments/0/leagues/" + str(leagueID)
response1 = requests.get(url,
                         cookies={"SWID": swid, "espn_s2": espn_s2}).json()

leagueInfo = {}
owners_dict = {}

for member in response1['members']:
    owners_dict[member['id']] = member['displayName']

for team in response1['teams']:
    leagueInfo[team['id']] = {'playerName1': owners_dict[team['owners'][0]],
                              'playerName2': owners_dict[team['owners'][1]] if len(team['owners']) == 2 else "N/A",
                              'teamName': team['location'] + " " + team['nickname'],
                              'abbreviation': team['abbrev'],
                              'ownerIDs': team['owners']}

df = pd.DataFrame(list(leagueInfo.values()),
                  columns=['playerName1', 'playerName2', 'teamName', 'abbreviation', 'ownerIDs'])
df.name = response1['settings']['name']

url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(season) + '/segments/0/leagues/' + str(leagueID) + \
      '?view=mSettings'
response2 = requests.get(url,
                         cookies={"SWID": swid, "espn_s2": espn_s2}).json()
rosterSettings = {}
for code, quantity in response2['settings']['rosterSettings']['lineupSlotCounts'].items():
    code = int(code)
    quantity = int(quantity)
    if quantity != 0:
        rosterSettings[slot_codes[code]] = quantity

# --------------------------- WEEKLY DATA ---------------------------

week = response1['scoringPeriodId']

url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + str(season) + '/segments/0/leagues/' + str(leagueID) + \
      '?view=mMatchup&view=mMatchupScore'

response3 = requests.get(url,
                         params={'scoringPeriodId': week},
                         cookies={"SWID": swid, "espn_s2": espn_s2}).json()

data = []

for team in response3['teams']:
    teamID = team['id']

    if leagueInfo[teamID]['ownerIDs'][0] != swid:
        continue

    # Source: https://stmorse.github.io/journal/espn-fantasy-projections.html
    # Modified: Iain Muir
    for p in team['roster']['entries']:
        name = p['playerPoolEntry']['player']['fullName']
        default_position = p['playerPoolEntry']['player']['defaultPositionId']
        position = default_codes[default_position]

        # injured status (need try/exc bc of D/ST)
        injury_status = 'NA'
        try:
            injury_status = p['playerPoolEntry']['player']['injuryStatus']
        except (Exception, IndexError) as e:
            pass

        # projected/actual points
        projected, actual = None, None
        for stat in p['playerPoolEntry']['player']['stats']:
            if stat['scoringPeriodId'] != week:
                continue
            if stat['statSourceId'] == 0:
                actual = stat['appliedTotal']
            elif stat['statSourceId'] == 1:
                projected = stat['appliedTotal']

        data.append([
            name, position, injury_status, projected, actual
        ])

    data = pd.DataFrame(data,
                        columns=['Player', 'Pos', 'Status', 'Proj', 'Actual'])

# --------------------------- OPTIMIZED LINEUP ---------------------------

for pos, num in rosterSettings.items():
    print(pos)
    options = data.query("Pos == '" + pos + "'")
    options = options.sort_values(by="Proj", ascending=False)
    print(options)
    print()


print("   --- Finished in %s seconds ---  " % round(time.time() - start, 4))
