"mock-ap-poll.py"

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

YEARS = range(2014, 2020)
YEARS_AND_WEEKS = [
    (2014, 16),
    (2015, 15),
    (2016, 15),
    (2017, 15),
    (2018, 15),
    (2019, 16),
    #(2020, 16)
]

def is_winner(team, game):
    home_points = game['home_points']
    away_points = game['away_points']
    if team == game['home_team']:
        return home_points > away_points
    else:
        return away_points > home_points

def make_records_df(season, polls):
    # Get FBS teams
    home_teams = season[season['home_conference'].notna()]['home_team']
    away_teams = season[season['away_conference'].notna()]['away_team']
    teams = set(home_teams).union(set(away_teams))
    
    # Get records
    records = []
    for team in teams:
        team_records = []
        games = season[(season['home_team'] == team) | (season['away_team'] == team)]
        for year, weeks in YEARS_AND_WEEKS:
            wins, losses = 0, 0
            for week in range(1, weeks + 1):
                game = games[(games['season'] == year) & (games['week'] == week)]
                if game.shape[0] > 0:
                    if game.shape[0] > 1:
                        #print(f'WARN: More than 1 game for a year/week/team combination:\n{game}')
                        pass
                    # TODO - is this much more performant when the loop is removed?
                    for i in range(0, game.shape[0]):
                        if is_winner(team, game.iloc[i]):
                            wins += 1
                        else:
                            losses += 1
                records.append([year, week, team, wins, losses])
    return pd.DataFrame(records, columns=['season', 'week', 'team', 'wins', 'losses'])

def make_poll():
	# Read season and preprocess
    season_dfs = [pd.read_csv(f'season-{year}.csv') for year in YEARS]
    season = pd.concat(season_dfs, ignore_index=True)
    season = season[['season', 'week', 'home_team', 'home_conference', 'home_points', 'away_team', 'away_conference', 'away_points']]
    
    # Read polls and preprocess
    polls = pd.read_csv(f'polls.csv')
    polls = polls.replace(to_replace=['UTSA'], value='UT San Antonio')
    
    # Do stuff here
    records_df = make_records_df(season, polls)
    print(records_df)

def main():
    make_poll()

if __name__ == '__main__':
    main()
