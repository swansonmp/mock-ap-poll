"espn-cfb-rankings-scraper.py"

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

URL_FORMAT = 'https://www.espn.com/college-football/rankings/_/poll/1/week/{}/year/{}/seasontype/2'
SELECTOR = '.Table'
DETAILS_SELECTOR = '.TableDetails'
INTERMEDIATE_FILE_FORMAT = 'espn-polls-{}.csv'
YEARS_AND_WEEKS = [
    (2014, 16),
    (2015, 15),
    (2016, 15),
    (2017, 15),
    (2018, 15),
    (2019, 16),
    (2020, 16)
]

def get_index_string(year, week):
    return f'y{year}w{str(week).zfill(2)}'

def download_pages(crawl_delay):
    """Download the pages that we'll use later for scraping"""
    for (year, weeks) in YEARS_AND_WEEKS:
        for week in range(1, weeks + 1):
            index_string = get_index_string(year=year, week=week)
            response = requests.get(URL_FORMAT.format(week, year))
            with open(f'polls-{index_string}.html', 'w') as outfile:
                outfile.write(response.text)
                print(f'Poll {index_string} processed.')
            time.sleep(crawl_delay)

def get_poll(year, week):
    # Get table 
    soup = None
    index_string = get_index_string(year=year, week=week)
    with open(f'polls-{index_string}.html') as infile:
        soup = BeautifulSoup(infile, 'html.parser')
    table = soup.select_one(SELECTOR)
    
    # Process header
    # This code gets the real header
    #header_row = table.thead.tr
    #columns = [cell.string.strip() for cell in header_row.children]
    # This code makes a header for what we actually scrape
    columns = ['team', 'points', 'wins', 'losses']
    
    # Process body
    body_rows = table.tbody.children
    data = []
    for row in body_rows:
        children = list(row.children)
        # [0] - Rank
        # [1] - Team
        team = children[1].find('img')['title']
        # [2] - Record
        record = children[2].string
        wins, losses, *other = record.split('-')
        # [3] - Points
        points = children[3].string
        
        data.append([team.strip(), points.strip(), wins.strip(), losses.strip()])
    
    # Process details
    details = soup.select_one(DETAILS_SELECTOR)
    others = list(details.children)[0].text[25:]
    for other in others.split(', '):
        team = ''.join([c for c in other if not c.isdigit()]).strip()
        points = ''.join([c for c in other if c.isdigit()]).strip()
        data.append([team, points])
    
    # Create data frame
    df = pd.DataFrame(data, columns=columns)
    df['year'] = year
    df['week'] = week
    return df

def write_polls(outfile, intermediate_results):
    polls = []
    for (year, weeks) in YEARS_AND_WEEKS:
        for week in range(1, weeks + 1):
            index_string = get_index_string(year=year, week=week)
            try:
                poll = get_poll(year=year, week=week)
                if intermediate_results:
                    poll.to_csv(INTERMEDIATE_FILE_FORMAT.format(index_string), index=False)
                    print(f'Poll {index_string} processed.')
                polls.append(poll)
            except Exception as e:
                print(f'Error processing poll {index_string} ({e}). Continuing anyway...')
    df = pd.concat(polls, axis=0)
    df.to_csv(outfile, index=False)

def main():
    #download_pages(crawl_delay=5)
    write_polls(outfile='polls.csv', intermediate_results=False)

if __name__ == '__main__':
    main()
