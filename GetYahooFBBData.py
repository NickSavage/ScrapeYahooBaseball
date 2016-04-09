#!/usr/bin/env python

import mechanize
import cookielib
from bs4 import BeautifulSoup
import csv
import getpass
import datetime
import sys
import configobj
import argparse

CONFIG_PLAYERTYPE = ""
CONFIG_TIMEFRAME = ""
CONFIG_AVAILABLE = ""
CONFIG_LEAGUEID = 0
CONFIG_FILENAME = ""
CONFIG_SORT = ""

def main():
        global CONFIG_LEAGUEID
        global CONFIG_FILENAME
        global CONFIG_SORT 

        # command line parsing
        parser = argparse.ArgumentParser(description="Scrape baseball player data from Yahoo Fantasy Sports")
        parser.add_argument('-c','--config', default="config.ini")
        parser.add_argument('-p','--max-pages', default=1)
        parser.add_argument('-t','--timeframe', choices=['2016', '2015', 'today', '7', '14', '30'], default='2016')
        parser.add_argument('-s','--sort', choices=['OR','AR'], default="AR")
        parser.add_argument('--available', action='store_true')
        parser.add_argument('action', choices=['pitchers', 'batters', 'both'], help="scrape pitchers")
        
        args = parser.parse_args()
        action = str(args.action)

        if (action == "pitchers"):
                CONFIG_PLAYERTYPE = "1"
        elif (action == "batters"):
                CONFIG_PLAYERTYPE = "2"
        elif (action == "both"):
                CONFIG_PLAYERTYPE = "3"
        CONFIG_FILENAME = args.config
        maxPages = int(args.max_pages)
        CONFIG_TIMEFRAME = args.timeframe
        CONFIG_SORT = args.sort
        if (args.available):
                CONFIG_AVAILABLE = 2
        elif (args.available == False):
                CONFIG_AVAILABLE = 1

        # load config from config file. At the moment, its only for leagueID, username and password
        # but in the future it will include overriding the defaults of the options
        (CONFIG_LEAGUEID, username, password) = loadConfig(CONFIG_FILENAME)

        # Start scraping process
	br = authentication(username, password)
        if CONFIG_PLAYERTYPE == "1": 
                (writer, ofile) = buildWriter("1")
                scrape(br, writer, ofile, 1, CONFIG_TIMEFRAME, CONFIG_AVAILABLE, maxPages)
        elif CONFIG_PLAYERTYPE == "2":
                (writer, ofile) = buildWriter("2")
                scrape(br, writer, ofile, 2, CONFIG_TIMEFRAME, CONFIG_AVAILABLE, maxPages)
        elif CONFIG_PLAYERTYPE == "3": 
                (writer, ofile) = buildWriter("1")
                scrape(br, writer, ofile, 1, CONFIG_TIMEFRAME, CONFIG_AVAILABLE, maxPages)
                (writer, ofile) = buildWriter("2")
                scrape(br, writer, ofile, 2, CONFIG_TIMEFRAME, CONFIG_AVAILABLE, maxPages)

def buildWriter(CONFIG_PLAYERTYPE):
        global CONFIG_LEAGUEID
        # build filename for export
	if CONFIG_PLAYERTYPE == "1":
		end_filename = 'Pitchers'
	if CONFIG_PLAYERTYPE == "2":
		end_filename = 'Batters'

	filename = 'FBB_data_' + str(CONFIG_LEAGUEID) + '_' + end_filename + '_' + str(datetime.date.today()) + '.csv'
        print filename
	ofile = open(filename, "wb")
	writer = csv.writer(ofile, delimiter = ',', escapechar = ' ')
        return writer, ofile
                
def scrape(br, writer, ofile, localPlayerType, localTimeFrame, localAvailable, localMaxPages):
        #building url for scraping
	url = buildURL(localPlayerType, localTimeFrame, localAvailable)
	content = br.open(url + '0')
	soup = BeautifulSoup(content, "lxml")
        print url

        # build list of stats to scrape, based on what your league counts
	statsList = soup.findAll('th', {'class':'Ta-end'})
	stats = ['Name', 'Team', 'Pos', 'Fantasy Team']
	for s in statsList:
		t = str(s.findAll(text=True))
		t = t[3:len(t)-2]
		stats.append(t.split(",")[0])
		try:
                       stats.remove("Rankings")
		except:
			continue

	writer.writerow(stats) # write first row of csv file
	pageNum = 0 # initialize counter for scraping lists of players

	while True:
		count = 0
		pageCount = str(pageNum * 25)
                print "Loading page",(pageNum+1)

                end = scrapePage(count, pageCount, br, url, stats, writer)
                count += 1
                pageNum += 1
                if pageNum >= localMaxPages: break
                if end == 1: break
        ofile.close() 
                        
                
def loadConfig(filename):
        filename = open(filename, 'r')
        config = configobj.ConfigObj(filename)

        if (config['username']):
                username = config['username']
        else:
                username = ""
        if (config['password']):
                password = config['password']
        else:
                password = ""
        if (config['leagueID']):
                leagueID = config['leagueID']
        else:
                leagueID = 0

        return(leagueID, username, password)
        
def authentication(username, password):
	cj = cookielib.CookieJar()
	br = mechanize.Browser()
	br.set_handle_robots(False)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6')]
	br.set_cookiejar(cj)
	br.open("https://login.yahoo.com/config/login_verify2?&.src=ym&.intl=us")
	br.select_form(nr=0)
	br.form["username"] = username
	submit_response = br.submit()
	br.select_form(nr=0)
	br.form["passwd"] = password
	br.submit()
        return br

def scrapePage(count, pageCount, br, url, stats, writer):
        # gets information from url
        content = br.open(url + pageCount)
        soup = BeautifulSoup(content, "lxml")
        
        players = soup.findAll('div', {'class':'ysf-player-name Nowrap Grid-u Relative Lh-xs Ta-start'})
        dataList = soup.findAll('td', {'class': 'Ta-end'})
        # Following block finds all the fantasy team names and puts them into fanTeams without all the html and formatting
        fantasyTeams = soup.findAll('div', {'style':'text-overflow: ellipsis; overflow: hidden;'})
        # Make array of fantasy team names
        fanTeams = []
        for f in fantasyTeams:
                s = f.findAll(text=True)
                fanTeams.append(str(s)[3:-2])
        fanTeams.pop(0)

        # Find end of player list
        try:
                str(players[0].findAll(text=True))
        except:
                print "End of Players"
                return 1

        for player in players:
                playerStats = []
                # extracts only name, team, position from html.
                # magic python function!
                playerData = str(player.findAll(text=True)) 
                name = getName(playerData)
                (team, pos) = getTeamAndPosition(playerData)

                fanTeam = fanTeams[0]
                fanTeams.pop(0)
                playerStats.extend([name, team, pos, fanTeam])
                for i in range(0, len(stats)-4):
                        tmp = str(dataList[0].findAll(text=True))
                        playerStats.append(tmp[3:-2])
                        dataList.pop(0)
                writer.writerow(playerStats)
        
def buildURL(type, time, available):
        global CONFIG_LEAGUEID
        global CONFIG_SORT
	begin_url = 'http://baseball.fantasysports.yahoo.com/b1/' + str(CONFIG_LEAGUEID) + '/players?status='
	end_url = '&myteam=0&sort=' + str(CONFIG_SORT) + '&sdir=1&count='

	if available == 1: status = 'ALL'
	if available == 2: status = 'A'
	if type == 1: pos = 'P'
	if type == 2: pos = 'B'
	if time == '2016': timeFrame = 'S_2016'
	if time == '2015': timeFrame = 'S_2015'
	if time == '30': timeFrame = 'L30'
	if time == '14': timeFrame = 'L14'
	if time == '7': timeFrame = 'L7'
	if time == 'today': timeFrame = 'L'

	mid_url = status + '&pos=' + pos + '&cut_type=33&stat1=S_' + timeFrame
	return begin_url + mid_url + end_url

def getName(data):
	if data[2] == '"':
		playerDataName = data.split('"')
	else:
		playerDataName = data.split("'")
	return fixText(playerDataName[1])

def getTeamAndPosition(data):
	playerData = data.split("'")
	if data[2] == '"':
		teampos = playerData[4]
	else:
		teampos = playerData[5]
	team = teampos[0:teampos.find("-")-1]
	pos = teampos[teampos.find("-")+2:len(teampos)]
	return (team, pos)


def fixText(str):
	s = str
	s = s.replace('\\xe1', 'a')
	s = s.replace('\\xe0', 'a')
	s = s.replace('\\xc1', 'A')
	s = s.replace('\\xe9', 'e')
	s = s.replace('\\xc9', 'E')
	s = s.replace('\\xed', 'i')
	s = s.replace('\\xcd', 'I')
	s = s.replace('\\xf3', 'o')
	s = s.replace('\\xd3', 'O')
	s = s.replace('\\xfa', 'u')
	s = s.replace('\\xda', 'U')
	s = s.replace('\\xf1', 'n')
	return s

if __name__ == "__main__":
	main()
