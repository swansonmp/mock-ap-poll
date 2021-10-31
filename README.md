# mock-ap-poll

Most computer polls are created in the futile attempt to rank teams based on how good they are.

_What if we didn't do that?_

The Mock AP Poll attempts to predict this Sunday's Associated Press Top 25 poll before it happens.
By knowing last week's poll, the results of Saturday's games, and the history of past polls, how close can we get to predicting the real thing?

## Data

Game and results data is graciously provided by [CollegeFootballData](https://collegefootballdata.com/).

Historical poll data is artfully scraped from ESPN.
Sadly, CFBD doesn't include vote counts past the top 25 teams
and ESPN's API was misbehaving.

## Predictions

Predictions powered by [scikit-learn](https://scikit-learn.org/stable/index.html).

TK.
