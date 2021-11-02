"mock-ap-poll.py"

import argparse
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn import svm

YEARS_AND_WEEKS = [
    (2014, 16),
    (2015, 15),
    (2016, 15),
    (2017, 15),
    (2018, 15),
    (2019, 16),
    #(2020, 16),
    (2021, 9)
]

def log_with_timestamp(message):
    timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    print(f'{timestamp}\t{message}')

def is_winner(team, game):
    home_points = game['home_points']
    away_points = game['away_points']
    if team == game['home_team']:
        return home_points > away_points
    else:
        return away_points > home_points

def get_teams(season):
    # Get FBS teams
    home_teams = season[season['home_conference'].notna()]['home_team']
    away_teams = season[season['away_conference'].notna()]['away_team']
    return set(home_teams).union(set(away_teams))

def make_records(season, polls, teams):
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
    records_df = pd.DataFrame(records, columns=['season', 'week', 'team', 'wins', 'losses'])
    
    records_df.to_csv('records.csv', index=False)
    return records_df

def get_record(year, week, team, records):
    if week <= 1:
        return 0, 0
    else:
        record = records[(records['season'] == year) & (records['week'] == week - 1) & (records['team'] == team)]
        if record.shape[0] == 0:
            raise Exception(f'Can\'t get record for team {team} and y{year}w{week.zfill(2)}. Continuing anyway...')
        else:
            record = record.iloc[0]
            return record['wins'], record['losses']

def get_points(year, week, team, polls):
    poll = polls[(polls['year'] == year) & (polls['week'] == week) & (polls['team'] == team)]
    num_rows = poll.shape[0]
    if num_rows == 0:
        return 0
    elif num_rows > 1:
        raise Exception(f'Team {team} shows up more than once in poll y{year}w{week}.')
    else:
        poll = poll.iloc[0]
        return poll['points']

def get_game_info(year, week, team, season):
    games = season[(season['season'] == year) & (season['week'] == week) & ((season['home_team'] == team) | (season['away_team'] == team))]
    num_rows = games.shape[0]
    if num_rows == 0:
        return {
            'score_for': 0,
            'score_against': 0,
            'team_conference': None,
            'opponent_conference': None
        }
    else:
        # What if there are multiple games?
        # With this code, we only process the first
        game = games.iloc[0]
        is_home = game['home_team'] == team
        opponent = game['away_team'] if is_home else game['home_team']
        home_score = game['home_points']
        away_score = game['away_points']
        home_conference = game['home_conference']
        away_conference = game['away_conference']
        return {
            'score_for': home_score if is_home else away_score,
            'score_against': away_score if is_home else home_score,
            'team_conference': home_conference if is_home else away_conference,
            'opponent_conference': away_conference if is_home else home_conference,
        }

def get_conferences(season):
    home_conferences = set(season['home_conference'])
    away_conferences = set(season['away_conference'])
    conferences = home_conferences.union(away_conferences)
    return sorted([str(c) for c in conferences])

def get_conference_one_hot(team_conference, opponent_conference, conferences):
    team_conference_one_hot = [1 if conference == team_conference else 0 for conference in conferences]
    opponent_conference_one_hot = [1 if conference == opponent_conference else 0 for conference in conferences]
    return team_conference_one_hot + opponent_conference_one_hot

def get_conference_columns(conferences):
    team_columns = [f'team_is_{conference}' for conference in conferences]
    opponent_columns = [f'opponent_is_{conference}' for conference in conferences]
    return team_columns + opponent_columns

def get_model_data(season, polls, teams, conferences, records):
    X = []
    y = []
    for team in teams:
        for year, weeks in YEARS_AND_WEEKS:
            # Start at week 1 and omit last week
            for week in range(1, weeks):
                # Add X row
                points_0 = get_points(year=year, week=week, team=team, polls=polls)
                wins, losses = get_record(year=year, week=week, team=team, records=records)
                game_info = get_game_info(year=year, week=week, team=team, season=season)
                score_for = game_info.get('score_for')
                score_against = game_info.get('score_against')
                conference_one_hots = get_conference_one_hot(game_info['team_conference'], game_info['opponent_conference'], conferences)
                X.append([points_0, wins, losses, score_for, score_against] + conference_one_hots)

                # Add y row
                points_1 = get_points(year=year, week=week+1, team=team, polls=polls)
                y.append(points_1)

    
    conference_columns = get_conference_columns(conferences)

    # TODO - we need an X_0, X_1, y_0, and y_1 here
    X_df = pd.DataFrame(X, columns=['points_0', 'wins', 'losses', 'score_for', 'score_against'] + conference_columns)
    y_arr = np.array(y)
    X_df.to_csv('X.csv', index=False)
    y_arr.tofile('y.csv', sep=',')
    return X_df, y_arr

def get_model(X, y):
    """
    X dimensions:
    - points_0, wins, losses, score_for, score_against, [team_is_...], [team_is...]
    Y dimensions:
    - points_1
    """
    model = svm.SVR()
    model.fit(X, y)
    return model

def make_poll(compute_records, compute_model_data):
    # Read season and preprocess
    YEARS = [year for year, weeks in YEARS_AND_WEEKS]
    season_dfs = [pd.read_csv(f'season-{year}.csv') for year in YEARS]
    season = pd.concat(season_dfs, ignore_index=True)
    season = season[['season', 'week', 'home_team', 'home_conference', 'home_points', 'away_team', 'away_conference', 'away_points']]
    
    # Read polls and preprocess
    polls = pd.read_csv('polls.csv')
    polls = polls.replace(to_replace=['UTSA'], value='UT San Antonio')
    
    # Make or retrieve calculated data
    teams = get_teams(season=season)
    records = None
    if compute_records:
        log_with_timestamp('Computing records...')
        records = make_records(season, polls, teams)
        log_with_timestamp('Done.')
    else:
        records = pd.read_csv('records.csv')
    
    # Get model data and model
    X_0, X_1, y_0 = None, None, None
    if compute_model_data:
        log_with_timestamp('Computing model data...')
        conferences = get_conferences(season=season)
        X_0, X_1, y_0 = get_model_data(season=season, polls=polls, teams=teams, conferences=conferences, records=records)
        log_with_timestamp('Done.')
    else:
        X_0 = pd.read_csv('X_0.csv')
        X_1 = pd.read_csv('X_1.csv')
        y_0 = np.genfromtxt('y_0.csv', delimiter=',')
    model = get_model(X_0, y_0)
    y_1 = model.predict(X_1)
    y_1.to_csv('y_1.csv', index=False)

def main():
    parser = argparse.ArgumentParser(description='Mock the AP Top 25 Poll with sklearn predictions.')
    parser.add_argument('--compute_records', action='store_true', help='Compute and store records.csv.')
    parser.add_argument('--compute_model_data', action='store_true', help='Compute and store model data.')
    args = parser.parse_args()
    make_poll(args.compute_records, args.compute_model_data)

if __name__ == '__main__':
    main()
