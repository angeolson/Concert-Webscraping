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
cache_path = cache_path=str(os.path.dirname(os.path.abspath(__file__))) + '\\' + '.cache'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(cache_path=cache_path))

# helper functions
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
            #try: rel_artists = [sp.artist_related_artists(id)['artists'][i]['name'] for i in range(len(sp.artist_related_artists(id)['artists']))]
            try: rel_artists = [sp.artist_related_artists(id)['artists'][i]['name'] for i in range(5)]
            except IndexError: rel_artists = []
            return rel_artists
    else: return 'na'


# define function to grab cats cradle data
# def getData(url="https://www.930.com/"):
# get webpage info
url="https://www.930.com/"

def getData(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_byte = urlopen(req).read()
    soup = BeautifulSoup(web_byte, "html.parser")

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

    return df


# get data
df = getData(url)

df['genres'] = df.apply(getGenres, axis=1)
df['rel_artists'] = df.apply(getArtists, axis=1)

# export to csv 
df.to_csv("930_club.csv")

