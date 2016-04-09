# ScrapeYahooBaseball
Scrape Yahoo Fantasy Baseball player page for statistics. This is a significant rewrite of isaacmiller2004's GetYahooFBBData to update it for the 2016 season, as well as adding the option to scrape pitchers and batters at the same time and save them into separate CSV files.

## Usage:
###Required Arguments:
* pitchers: scrapes pitchers given the optional arguments
* batters: scrapes batters given the optional arguments
* both: scrapes both pitchers and batters

### Optional:
* -h, --help: Displays help message and exits
* -c CONFIG, --config CONFIG: loads given configuration file (default: config.ini)
* -p MAX_PAGES, --max-pages MAX_PAGES: scrapes MAX_PAGES pages from Yahoo (default: 1)
* -t, --timeframe: Scrapes statistics from either the whole 2016 or 2015 seasons, or the last 7, 14 or 30 days, or from the current day.
* -s, --sort: Changes how Yahoo sorts the players, either by their O-Rank or the current ranking
* --available: Flag to indicate that you only want to scrape players not owned by a fantasy team (default: false)
