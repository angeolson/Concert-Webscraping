import requests
import json 
import pandas as pd
# set vars for url 
my_key = '<KEY HERE>'

def getData(key,state,start_date,end_date):
    sort = 'date,asc'
    response = requests.get(f"https://app.ticketmaster.com/discovery/v2/events.json?classificationName=music&countryCode=US&stateCode={state}&sort={sort}&size=100&startDateTime={start_date}&endDateTime={end_date}&apikey={key}")
    json_response = json.loads(response.content)
    event_count = len(json_response.get('_embedded').get('events'))
    feature_list = ['name', 'date', 'genre', 'low_price', 'high_price', 'venue', 'city', 'state', 'address', 'lat', 'lon']
    df = pd.DataFrame(columns = feature_list)
    for i in range(event_count): 
        features = {}
        features['name'] = json_response.get('_embedded').get('events')[i].get('name')
        features['date'] = json_response.get('_embedded').get('events')[i].get('dates').get('start').get('localDate')
        features['genre'] = json_response.get('_embedded').get('events')[i].get('classifications')[0].get('genre').get('name')
        try: features['low_price'] = json_response.get('_embedded').get('events')[i].get('priceRanges')[0].get('min')
        except: TypeError
        try: features['high_price'] = json_response.get('_embedded').get('events')[i].get('priceRanges')[0].get('max')
        except: TypeError
        features['venue'] = low_price = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('name')
        features['city'] = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('city').get('name')
        features['state'] = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('state').get('name')
        features['address'] = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('address').get('line1')
        features['lat'] = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('location').get('latitude')
        features['lon'] = json_response.get('_embedded').get('events')[i].get('_embedded').get('venues')[0].get('location').get('longitude')

        event_df = pd.DataFrame(features, index=[0])
        df = pd.concat([df, event_df], ignore_index = True)
    return df

DC_df = getData(key=my_key,state='DC',start_date='2022-10-24T00:00:00Z',end_date='2023-10-24T00:00:00Z')
NC_df = getData(key=my_key,state='NC',start_date='2022-10-24T00:00:00Z',end_date='2023-10-24T00:00:00Z')
