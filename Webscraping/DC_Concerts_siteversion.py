# imports
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import pandas as pd
import numpy as np
import regex as re
import spotipy
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# set variables for spotify access. NOTE: Do note share these keys. 
os.environ['SPOTIPY_CLIENT_ID']='<KEY HERE>'
os.environ['SPOTIPY_CLIENT_SECRET']='<KEY HERE>'
os.environ['SPOTIPY_REDIRECT_URI']='<KEY HERE>'


# webdriver options
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")

# initialize spotipy 
cache_path = cache_path=str(os.path.dirname(os.path.abspath(__file__))) + '\\' + '.cache'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(cache_path=cache_path))



# helper functions
# define function to get related genres for an artist
def getGenres(row):
    '''
    input: dataframe column with artist name
    output: column of dataframe with list of artist genres--blank list, full list, or 'na' when there are no results 
    '''
    if len(row) > 0:
        results = sp.search(row, type='artist')
        try: sp_name = results['artists']['items'][0]['name']
        except IndexError: sp_name = 'none'
        if sp_name.lower() == row.lower():
            try: genres = results['artists']['items'][0]['genres']
            except IndexError: genres = 'none'
            return genres
        else: return 'na'
    else:
        return 'na'

# define function to get similar artists for an artist
def getArtists(row):
    '''
    input: dataframe column with artist name
    output: column of dataframe with list of related artists--blank list, full list, or 'na' when there are no results 
    '''
    if len(row) > 0:
        results = sp.search(row, type='artist')
        try: sp_name = results['artists']['items'][0]['name']
        except IndexError: sp_name = 'none'
        if sp_name.lower() == row.lower():
            try: id = results['artists']['items'][0]['id']
            except IndexError: id = 'none'
            if id == 'none':
                return 'na'
            else:
                #try: rel_artists = [sp.artist_related_artists(id)['artists'][i]['name'] for i in range(len(sp.artist_related_artists(id)['artists']))]
                try: rel_artists = [sp.artist_related_artists(id)['artists'][i]['name'] for i in range(5)]
                except IndexError: rel_artists = []
                return rel_artists
        else: return 'na'
    else:
        return 'na'


# define function to clean main act line 
def cleanName(row, *args):
    '''
    input: a column of a pandas df (or similar array) containing main act info
    output: a column of a pandas df (or similar array) with extra words/symbols removed
    '''
    row = str(row) # force string
    nonalpha = re.compile(r'[^a-zA-Z\d\s:]')
    trailwhite = re.compile(r'[ \t]+$')
    newrow = re.sub(nonalpha, '', row)
    for item in args:
        newrow = newrow.replace(item, "")
    newrow2 = re.sub(trailwhite, '', newrow)
    if newrow2.find(':') > 0:
        val = newrow2.split(':', 1)[0]
    else:
        val = newrow2
    return val

def replaceSeps(row, *args):
    '''
    input: a column of a pandas df (or similar array) containing main act info (or other)
    output: a column of a pandas df (or similar array) with symbols removed
    '''
    row = str(row) # force string
    # nonalpha = re.compile(r'[^a-zA-Z\d\s:]')
    # trailwhite = re.compile(r'[ \t]+$')
    # newrow = re.sub(nonalpha, '', row)
    # for item in args:
    #     newrow = newrow.replace(item, "")
    # newrow2 = re.sub(trailwhite, '', newrow)
    for char in [':', '|', '–']:
        if row.count(char) > 0:
            row = row.split(char)[0]
    return row

# define function to clean cost. Chooses first cost if more than one (buy in advance!) 
def CleanCost(df):
    '''
    input: dataframe 
    output: column containing cleaned cost information 
    '''
    val = df['cost']
    val = str(val)
    val = val.replace("$", "")
    val = val.replace("From", "")
    val = val.split(' ')[0]
    try: val = float(val)
    except ValueError: val = np.NaN
    return val 

# define function to clean date based on venue format 
def CleanDate(df):
    '''
    input: dataframe
    output: column with cleaned date information, based on the venue
    '''
    venue = df['venue']
    date = df['date']
    if venue == "9:30":
        date = date.replace(' ', '')
        weekday, day, month = date[0:3], date[3:5], date[-3:]
        fulldate = '2023' + '-' + month + '-' + day
        format = '%Y-%b-%d'
        datetime_str = datetime.strptime(fulldate, format)
    elif venue == "Black Cat":
        if type(date) == str:
            weekday, month, day = date.split(' ')
            fulldate = '2023' + '-' + month + '-' + day
            format = '%Y-%B-%d'
            datetime_str = datetime.strptime(fulldate, format)
        else:
            datetime_str = 'NA'
    elif venue == "DC9":
        weekday, month, day = date.split(' ')
        fulldate = '2023' + '-' + month + '-' + day
        format = '%Y-%b-%d'
        datetime_str = datetime.strptime(fulldate, format)
    elif venue == "Songbyrd":
        weekday, day, month = date.split('\n')
        fulldate = '2023' + '-' + month + '-' + day
        format = '%Y-%b-%d'
        datetime_str = datetime.strptime(fulldate, format)

    return datetime_str

# define function to get the day of the week, depending on venue format 
def GetWeekday(df):
    '''
    input: dataframe
    output: column with the day of the week abbreviation parsed, based on the venue
    '''
    venue = df['venue']
    date = df['date']
    if venue == "9:30":
        date = date.replace(' ', '')
        weekday, day, month = date[0:3], date[3:5], date[-3:]
    elif venue == "Black Cat":
        if type(date) != float:
            weekday, month, day = date.split(' ')
            weekday = weekday[0:2] # concat day of the week to match the others 
        else:
            weekday = 'NA'
    elif venue == "DC9":
        weekday, month, day = date.split(' ')
    elif venue == "Songbyrd":
        weekday, day, month = date.split('\n')
    return weekday

# define function to get the genre(s) of an artist 
def isGenre(row, genre):
    '''
    inputs: dataframe column with genre information, genre of interest
    output: dataframe column (or similar) with boolean value for specified genre 
    '''
    gen_string = " ".join(str(elem) for elem in row) # joins all the elements of list together into one string
    if gen_string.count(genre) > 0:
        return True
    else: return False # looks for any instance of the genre in the resulting string

# helper function to get the cost from the external site url 
def getSBPRice(url):
    '''
    input: url containing cost information for Songbyrd venue
    output: price (string)
    '''
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    try: price = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[2]/div[1]/div[2]/div[3]/div/div/span").text
    except: price = np.NaN
    driver.close()
    return price

#%%
# define function to grab data
# gets webpage info

def getData(venue):
    black_cat = "https://www.blackcatdc.com/schedule.html"
    dcnine = "https://dc9.club/"
    ninethirty = "https://www.930.com/"
    songbyrd = "https://songbyrddc.com/events/"
    if venue == 'Black Cat':
        url = black_cat
    elif venue == 'DC9':
        url = dcnine
    elif venue == '9:30':
        url = ninethirty
    elif venue == 'Songbyrd':
        url = songbyrd
    else:
        return "Unsupported Venue!"
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_byte = urlopen(req).read()
    soup = BeautifulSoup(web_byte, "html.parser")

    if venue == 'Black Cat':
        # get results
        results = soup.find_all("div", class_='show-details')

        # define venue feature list
        feature_list = ['name', 'openers', 'date', 'doors', 'cost']
        df = pd.DataFrame(columns = feature_list)

        # iterate through results to pull out data 
        for item in results:
            # iterate through results to pull out data 
            features = {}
            features['name'] = item.find("h1", class_="headline").text.strip()
            try: features['openers'] = item.find("h2", class_="support").text.strip()
            except: AttributeError
            try: features['date'] = item.find("h2", class_="date").text.strip()
            except: AttributeError
            try: doors_cost = item.find("p", class_="show-text").text.strip().split("/")
            except: AttributeError
            if len(doors_cost) == 1:
                features['doors'] = doors_cost[0]
                features['cost'] = np.NaN
            elif len(doors_cost) == 2:
                features['doors'] = doors_cost[1]
                features['cost'] = doors_cost[0]
            elif len(doors_cost) == 3:
                features['doors'] = doors_cost[2]
                features['cost'] = doors_cost[0] # use advance cost
            else:
                features['doors'] = np.NaN
                features['cost'] = np.NaN
            event_df = pd.DataFrame(features, index=[0])
            df = pd.concat([df, event_df], ignore_index = True)

        df['name'] = df['name'].apply(lambda x:x.title())
    
    elif venue == '9:30':
        # get results
        results = soup.find_all("article", class_='list-view-item card event-status-live')

        # define venue feature list
        feature_list = ['name', 'openers', 'date', 'doors', 'cost']
        df = pd.DataFrame(columns = feature_list)

        # iterate through results to pull out data 
        for item in results[1:]:
            features = {}
            features['name'] = item.find("h3", class_="h1 event-name headliners").text.strip()
            try: features['openers'] = item.find("h2", class_="supports").text.strip()
            except: AttributeError
            features['date'] = item.find("span", class_="dates").text.strip()
            features['doors'] = item.find("span", class_="doors").text.strip()
            try: features['cost'] = item.find("span", class_="price-range").text.strip()
            except: AttributeError
            event_df = pd.DataFrame(features, index=[0])
            df = pd.concat([df, event_df], ignore_index = True)

    elif venue == 'DC9':
        # get results
        results = soup.find_all("article", class_='wfea-venue__event status-live city-washington region-dc country-us event__available')


        # define venue feature list
        feature_list = ['name', 'openers', 'date', 'doors', 'cost']
        df = pd.DataFrame(columns = feature_list)

        # iterate through results to pull out data 
        for item in results:
            # iterate through results to pull out data 
            features = {}
            features['name'] = item.find("h2", class_="wfea-venue__title wfea-header__title entry-title").text.strip()
            try: features['openers'] = item.find("div", class_="wfea-venue__excerpt excerpt").text.strip()
            except: AttributeError
            features['date'] = item.find("time", class_="eaw-time published").text.strip()
            features['doors'] = item.find("div", class_="wfea-venue__door-time door-time").text.strip()
            try: features['cost'] = item.find("div", class_="wfea-venue__prices price").text.strip()
            except: AttributeError
            event_df = pd.DataFrame(features, index=[0])
            df = pd.concat([df, event_df], ignore_index = True)

        main_list = ["DC9 Residency", "(FINAL SHOW)"]
        opener_list = ["✰ ✰ ✰ More info", "More info"]
        df['name'] = df['name'].apply(cleanName, args=(main_list))
        df['openers'] = df['openers'].apply(cleanName, args=(opener_list))
        
    elif venue == 'Songbyrd':

        # get results
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        result = driver.find_element(By.XPATH, "//*[@id='event-listing-view']").get_attribute("innerHTML")
        driver.close()
        soup = BeautifulSoup(result, "html.parser")
        results = soup.find_all("div", class_="wpem-event-box-col wpem-col wpem-col-12 wpem-col-md-6 wpem-col-lg-4")


        # define venue feature list
        feature_list = ['name', 'openers', 'date', 'doors', 'cost']
        df = pd.DataFrame(columns = feature_list)

        # iterate through results to pull out data 
        for item in results:
            features = {}
            features['name'] = item.find("div", class_="wpem-event-title").text.strip()
            try: features['openers'] = item.find("div", class_="wpem-event-supporting-acts").text.strip()
            except: AttributeError
            features['date'] = item.find("div", class_="wpem-from-date").text.strip()
            try: features['doors'] = item.find("span", class_="wpem-event-date-time-text").text.strip()
            except: AttributeError
            price_url = item.find("div", class_="wpem-event-ticket-type").find("a").get("href")
            if price_url.count("dice") > 0:
                features['cost'] = getSBPRice(price_url)
            else:
                features['cost'] = np.NaN
            event_df = pd.DataFrame(features, index=[0])
            df = pd.concat([df, event_df], ignore_index = True)
        df['name'] = df['name'].apply(replaceSeps)
        df['name'] = df['name'].apply(lambda x:x.title())
        
    
    df['venue'] = venue
    df['genres'] = df['name'].apply(getGenres)
    df['rel_artists'] = df['name'].apply(getArtists)

    return df


# Run 
dc9_df = getData('DC9')
songbyrd_df = getData('Songbyrd')
nine30_df = getData('9:30')
blackcat_df = getData('Black Cat')

# concat all individual dfs 
df = pd.concat([dc9_df, nine30_df, blackcat_df, songbyrd_df], ignore_index = True)


# clean columns 
df['clean_cost']= df.apply(CleanCost, axis=1)
df['clean_date'] = df.apply(CleanDate, axis=1)
df['weekday'] = df.apply(GetWeekday, axis=1)    


# test cases for filtering data to specific criteria 
genres = ['indie', 'alt', 'alternative']
for genre in genres:
    df[genre] = df['genres'].apply(isGenre, args=([genre]))

# # filter by a single item where item is boolean or string
my_preferred_shows = df[ df['indie'] == True]

# # filter by single item where item is int or float
cheap_shows = df[ (df['clean_cost'] <= 20) | (df['clean_cost'].isna()) ]

# # filter by multiple conditions; use | for or if needed
my_preferred_shows = df[ (df['clean_cost'] <= 25) & (df['weekday'] != 'Tue') &((df['indie'] == True) | (df['alt'] == True) | (df['alternative'] == True))]

# export dataframe, shows of interest to .csv 
df.to_csv('DC_Concerts.csv')
my_preferred_shows.to_csv('Top_Shows.csv')
