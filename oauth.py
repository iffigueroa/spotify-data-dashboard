from datetime import datetime
from flask import Flask, redirect, request, jsonify, session
import requests
import urllib.parse

import os
from dotenv import load_dotenv
import secrets
load_dotenv()

# CLIENT CREDENTIAL FLOW 
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET= os.getenv("CLIENT_SECRET")
REDIRECT_URI = 'http://localhost:5000/callback'

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe() 


AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'>Login with Spotify</a>"


@app.route('/login')
def login():
    # scope of permissions we need from user
    scope = 'user-read-private user-read-email'
    # pass to spotify call
    params = {
        'client_id': CLIENT_ID, 
        'response_type': 'code',
        'scope': scope, 
        'redirect_uri': REDIRECT_URI, 
        'show_dialog': True # is false by default 
    }

    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    return redirect(auth_url)



@app.route("/callback")
def callback():
    if 'error' in request.args:
        app.logger.debug("GOT ERROR")
        return jsonify({'error': request.args['error']})
    
    if 'code' in request.args:
        app.logger.debug("GOT CODE")
        #build up request body to get access token
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code', 
            'redirect_uri': REDIRECT_URI, 
            'client_id': CLIENT_ID, 
            'client_secret': CLIENT_SECRET,
        }
    
        response = requests.post(TOKEN_URL, data=req_body)
        # we'll care about token_info['access_token'], 'refresh_token', 'expires_in'
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token'] 
        session['expires_at'] = datetime.now().timestamp() + 10 #token_info['expires_in']
        app.logger.info(f"EXPIRES AT {session['expires_at']}")
        return redirect('/playlists')
    
@app.route('/playlists')
def get_playlists():
    app.logger.debug("Requesting playlists")
    # Check if access token in session
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    # MAke request to retrieve playlist 
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
    }
    response = requests.get(API_BASE_URL+'me/playlists', headers=headers)
    playlists = response.json()
    app.logger.debug("Requesting complete")
    return jsonify(playlists)

@app.route('/refresh-token')
def refresh_token():
    app.logger.debug("Refreshing token")
    if 'refresh_token' not in session:
        return redirect('/login')
    
    # Confirm it's actually expired
    if datetime.now().timestamp() > session['expires_at']:
        app.logger.info("Refreshing token")
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'], 
            'client_id': CLIENT_ID, 
            'client_secret': CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=request_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')
    



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)