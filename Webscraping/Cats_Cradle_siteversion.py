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

# set variables for spotify access. NOTE: Do note share these keys. 
os.environ['SPOTIPY_CLIENT_ID']='<KEY HERE>'
os.environ['SPOTIPY_CLIENT_SECRET']='<KEY HERE>'
os.environ['SPOTIPY_REDIRECT_URI']='<KEY HERE>'

# initialize spotipy 
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

# define function to grab cats cradle data
def getData(url="https://catscradle.com/events/"):
    # get webpage info
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_byte = urlopen(req).read()
    soup = BeautifulSoup(web_byte, "html.parser")

    # get results
    results = soup.find_all("div", class_='col-12 eventWrapper rhpSingleEvent py-4 px-0')

    # define venue feature list
    feature_list = ['name', 'date', 'cost', 'location']
    df = pd.DataFrame(columns = feature_list)

    # iterate through results to pull out data 
    for item in results:
        features = {}
        features['name'] = item.find("h2", class_="font1by25 font1By5remMD marginBottom3PX lineHeight12 font1By75RemSM font1By5RemXS mt-md-0 mb-md-2").text.strip()
        features['date'] = item.find("div", class_="mb-0 eventMonth singleEventDate text-uppercase").text.strip()
        try: features['cost'] = item.find("div", class_="col-12 d-inline-block eventsColor eventCost pt-md-0 mt-md-0 mb-md-2").find("span", class_="").text.strip() 
        except: AttributeError
        features['location'] = item.find("div", class_="d-inline-block eventVenue").find("a", class_="venueLink").text.strip()
        event_df = pd.DataFrame(features, index=[0])
        df = pd.concat([df, event_df], ignore_index = True)
    
    # define function to clan the column for advanced ticket prices 
    def cleanAdvCost(row):
        '''
        input: a column of a pandas df (or similar array) containing ticket cost info
        output: a column of a pandas df (or similar array) with extra words/symbols removed
        '''
        newrow = str(row)
        
        if newrow.find('/') > 0:
            val = row.split('/', 1)[0] 
        elif newrow.find(',') > 0:
            val = row.split(',', 1)[0] 
        else:
            val = row

        if type(val) != str:
            return val
        else:
            val = str(val)
            pattern = re.compile(r'[a-zA-Z\-]+')
            new = re.sub(pattern, ' ', val)
            new = new.split()[0]
            return new

    def cleanDayCost(row):
        '''
        input: a column of a pandas df (or similar array) containing ticket cost info
        output: a column of a pandas df (or similar array) with extra words/symbols removed
        '''
        newrow = str(row)

        if newrow.find('/') > 0:
            val = row.split('/', 1)[1] 
        elif newrow.find(',') > 0:
            val = row.split(',', 1)[1] 
        else:
            val = row
            
        if type(val) != str:
            return val
        else:
            val = str(val)
            pattern = re.compile(r'[a-zA-Z\-:]+')
            new = re.sub(pattern, ' ', val)
            new = new.split()[0]
            return new

    # apply functions to clean cost
    df['advanced_cost'] = df['cost'].apply(cleanAdvCost)
    df['dayof_cost'] = df['cost'].apply(cleanDayCost)

    # remove rows without cost data--this is the cradle's way of showing sold out shows
    df = df.dropna(subset='cost').reset_index(drop=True)

    # define function to get related genres for an artist
    def getGenres(df):
        '''
        input: dataframe created above 
        output: column of dataframe with list of artist genres--blank list, full list, or 'na' when there are no results 
        '''
        q = df['name']
        results = sp.search(q, type='artist')
        try: sp_name = results['artists']['items'][0]['name']
        except IndexError: sp_name = []
        if sp_name == df['name']:
            try: genres = results['artists']['items'][0]['genres']
            except IndexError: genres = []
            return genres
        else: return 'na'

    # define function to get similar artists for an artist
    def getArtists(df):
        '''
        input: dataframe created above 
        output: column of dataframe with list of related artists--blank list, full list, or 'na' when there are no results 
        '''
        q = df['name']
        results = sp.search(q, type='artist')
        try: sp_name = results['artists']['items'][0]['name']
        except IndexError: sp_name = []
        if sp_name == df['name']:
            try: id = results['artists']['items'][0]['id']
            except IndexError: id = 'none'
            if id == 'none':
                return 'na'
            else:
                try: rel_artists = [sp.artist_related_artists(id)['artists'][i]['name'] for i in range(len(sp.artist_related_artists(id)['artists']))]
                except IndexError: rel_artists = []
                return rel_artists
        else: return 'na'

    df['genres'] = df.apply(getGenres, axis=1)
    df['rel_artists'] = df.apply(getArtists, axis=1)

    return df


# get data
df = getData()

# export to csv 
df.to_csv("cats_cradle_events.csv")

# test cases for filtering data to specific criteria 

# create the datapoints you want to filter by; examples are turn cost into float var, extract month and day, only indie music
# def isGenre(row, genre):
#     gen_string = " ".join(str(elem) for elem in row) # joins all the elements of list together into one string
#     if gen_string.find(genre) > 0:
#         return True
#     else: return False # looks for any instance of the genre in the resulting string

# genre = 'indie'
# df[genre] = df['genres'].apply(isGenre, args=([genre]))
# df['advanced_cost'] = df['advanced_cost'].apply(lambda x:float(x.replace("$","")))
# df['month'] = df['date'].apply(lambda x:x[4:8])
# df['day'] = df['date'].apply(lambda x:x[0:3])

# # filter by a single item where item is boolean or string
# my_preferred_shows = df[ df['indie'] == True]

# # filter by single item where item is int or float
# my_preferred_shows = df[ df['advanced_cost'] <= 20]

# # filter by multiple conditions; use | for or if needed
# my_preferred_shows = df[ (df['advanced_cost'] <= 20) & (df['indie'] == True) & (df['day'] == 'Fri')]
