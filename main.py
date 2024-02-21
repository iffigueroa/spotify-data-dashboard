import os
from dotenv import load_dotenv
import base64
from requests import post, get
import json
from pprint import pprint
import pandas as pd

load_dotenv()

# CLIENT CREDENTIAL FLOW 
client_id = os.getenv("CLIENT_ID")
client_secret= os.getenv("CLIENT_SECRET")
playlist_id = os.getenv("PLAYLIST_ID")


def get_token() -> str:
    # request an authorization
    auth_bytes = (f"{client_id}:{client_secret}").encode('utf-8')
    auth_64 = str(base64.b64encode(auth_bytes), 'utf-8')

    request_url = 'https://accounts.spotify.com/api/token'
    header_params = {
        "Authorization": "Basic "+auth_64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    body_params = {
        'grant_type': 'client_credentials'
    }

    response = post(request_url, headers=header_params, data=body_params)
    json_response = json.loads(response.content)
    print(json_response)
    return json_response['access_token']


def get_auth_header(token): 
    return {
        "Authorization": f"Bearer {token}"
    }

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search/"
    headers = get_auth_header(token=token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url+query
    response = get(query_url, headers=headers)
    json_response = json.loads(response.content)['artists']['items']
    if len(json_response) == 0:
        print(f"No artist found by name: {artist_name}")
    print(json_response)



def search_for_playlist(token, playlist_name):
    url = "https://api.spotify.com/v1/search/"
    headers = get_auth_header(token=token)
    query = f"?q={playlist_name}&type=playlist&limit=100"
    query_url = url+query
    response = get(query_url, headers=headers)
    json_response = json.loads(response.content)['playlists']['items']
    if len(json_response) == 0:
        print(f"No artist found by name: {playlist_name}")
    pprint(json_response)
    return json_response

def get_playlist_tracks(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token=token)
    response = get(url, headers=headers)
    json_response = json.loads(response.content)
    if not json_response.get("items"):
        return None
    return json_response['items']

token = get_token()

response = get_playlist_tracks(token=token, playlist_id=playlist_id)

song_list= []
artist_list = []
album_list = []
release_dates = []

for item in response:
    track = item['track']
    album = track['album']
    song_list.append(track['name'])
    artist_list.append(", ".join([artist['name'] for artist in track['artists']] ))
    album_list.append(album['name'])
    release_dates.append(album['release_date'])


playlist_df = pd.DataFrame({'song': song_list, 'album': album_list, 'artist': artist_list, 'release_date_str': release_dates})
playlist_df['release_date'] = pd.to_datetime(playlist_df['release_date_str'], errors='coerce')
print(playlist_df.shape)
print(playlist_df.head())

naT_rows = playlist_df[playlist_df['release_date'].isna()]

playlist_df.loc[playlist_df['release_date'].isna(), 'release_date'] = pd.to_datetime(naT_rows['release_date_str'], format='%Y', errors='coerce')
naT_rows = playlist_df[playlist_df['release_date'].isna()]


playlist_df.loc[playlist_df['release_date'].isna(), 'release_date'] = pd.to_datetime(naT_rows['release_date_str'], format='%Y-%d', errors='coerce')
naT_rows = playlist_df[playlist_df['release_date'].isna()]
                       
# Display the rows with NaT values
print(naT_rows)
print(playlist_df.head())



import pandas as pd
import matplotlib.pyplot as plt
import math

song_counts_by_year = playlist_df.groupby(playlist_df['release_date'].dt.year)['song'].size()

# Plot the count of songs released over time
plt.figure(figsize=(10, 6))
plt.bar(song_counts_by_year.index, song_counts_by_year, width=1, align='center')
plt.title('Count of Songs Released Over Time')
plt.xlabel('Release Date')
plt.ylabel('Count')
min_year = math.floor(song_counts_by_year.index.min() / 5) * 5
max_year = math.ceil(song_counts_by_year.index.max() / 5) * 5
plt.xticks(range(min_year, max_year + 1, 5), rotation=45)
plt.gca().set_axisbelow(True)
plt.grid(alpha=0.3)
plt.show()
