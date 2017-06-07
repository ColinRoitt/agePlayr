import json
from flask import Flask, request, redirect, g, render_template, session
import requests
import base64
import urllib
import spotipy
import datetime

# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.

app = Flask(__name__)
app.secret_key = 'asdjhu3ad3hu'

#  Client Keys
CLIENT_ID = "62bfab0e397541528d6616594c7fab29"
CLIENT_SECRET = "cfc206dfcc8c4ecfb67f423d6e2c3b08"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.route("/")
def initPg():
    return render_template("index.html")

@app.route("/n")
def index():
    session['yearOfBirth'] = request.args.get("year")
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    currentYear = datetime.datetime.now().year
    years = []
    YOB = session['yearOfBirth']
    year = int(YOB)
    tracksToAdd = []
    tracksToShow = []
    while (year <= currentYear):
        years.append(year)
        year += 1
    sp = spotipy.Spotify(auth=access_token)
    username = str(sp.current_user()['id'])
    returnString = ''
    for i in years:
        results = sp.search(q='year:' + str(i), type='track', limit = 1)
        track = results['tracks']['items'][0]['name']
        artist = results['tracks']['items'][0]
        uri = results['tracks']['items'][0]
        #returnString += str(results) + ' || '
        returnString = 'year: ' + str(i) + ' ' + track + ' BY ' + artist['artists'][0]['name'] + ' URI = ' + uri['uri']
        tracksToAdd.append(uri['uri'])
        tracksToShow.append(returnString)

    #create playist and get its ID
    sp.user_playlist_create(username, str(YOB) + ' to ' + str(currentYear), public=True)
    playlistId = str(sp.user_playlists(username)['items'][0]['uri'])
    #add each track to a playlist
    sp.user_playlist_add_tracks(username, playlistId, tracksToAdd)

    return render_template("display.html",sorted_array=tracksToShow)


if __name__ == "__main__":
    app.run(debug=True,port=PORT)
