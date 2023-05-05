from flask import Flask, jsonify, request, render_template, redirect, session
from flask_session import Session
import os
import requests
import base64
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler

all_songs_sampled = pd.read_csv('songs_clustered.csv')


app = Flask(__name__)

from config import client_id, client_secret, redirect_uri, scope

# Configure the Flask session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

feature_columns = ['danceability', 'energy', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'hot']

# Load the saved scaler and KMeans model
def load(filename = "filename.pickle"): 
    try: 
        with open(filename, "rb") as file: 
            return pickle.load(file) 
    except FileNotFoundError: 
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error loading file: {filename}, Error: {str(e)}")


scaler = load("scaler.pickle")
best_model = load("kmeans_18.pickle")

# Function to preprocess and predict the cluster for the user input song
def predict_cluster(audio_features, hot=0):
    # Convert the audio features into a DataFrame
    audio_features_df = pd.DataFrame([audio_features])

    # Add 'hot' to the audio_features_df with a default value of 0
    audio_features_df['hot'] = hot

    # Scale the audio features using the saved scaler
    audio_features_scaled = scaler.transform(audio_features_df)

    # Predict the cluster using the saved KMeans model
    cluster = best_model.predict(audio_features_scaled)

    return cluster[0]

def get_recommended_songs(cluster, hot):
    recommended_songs = all_songs_sampled[(all_songs_sampled['cluster'] == cluster) & (all_songs_sampled['hot'] == hot)]
    top_songs = recommended_songs.sort_values(by='valence', ascending=False).head()
    song_list = []
    for _, row in top_songs.iterrows():
        song_url = f"https://open.spotify.com/track/{row['id']}"
        song_list.append({'name': row['name'], 'artists': row['artists'], 'url': song_url})
    return song_list



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('term', '')
    results = sp.search(q=query, type='track', limit=10)
    tracks = results['tracks']['items']
    suggestions = [{'label': f"{track['name']} - {track['artists'][0]['name']}", 'value': track['id']} for track in tracks]
    return jsonify(suggestions)

@app.route('/audio_features', methods=['GET'])
def audio_features():
    try:
        song_id = request.args.get('id', '')
        if song_id:
            raw_audio_features = get_audio_features(song_id)
            if raw_audio_features:
                audio_features = {feature: raw_audio_features[feature] for feature in feature_columns if feature != 'hot'}
                cluster = predict_cluster(audio_features, hot=1)  # Adjust the 'hot' value as needed
                return jsonify({"cluster": int(cluster), **audio_features})
        return jsonify({})
    except Exception as e:
        return jsonify({"error": str(e)})





def get_audio_features(spotify_id):
    if spotify_id is None:
        return None
    else:
        audio_features = sp.audio_features([spotify_id])[0]
        # Check if the song id is in the original all_songs_sampled DataFrame and whether hot or not
        if spotify_id in all_songs_sampled['id'].iloc[:69].values:
            audio_features['hot'] = 1
        else:
            audio_features['hot'] = 0
        return audio_features
    

@app.route('/recommended_songs', methods=['GET'])
def recommended_songs():
    song_id = request.args.get('id', '')
    hot = int(request.args.get('hot', '0'))
    if song_id:
        raw_audio_features = get_audio_features(song_id)
        if raw_audio_features:
            audio_features = {feature: raw_audio_features[feature] for feature in feature_columns if feature != 'hot'}
            cluster = predict_cluster(audio_features, hot=hot)
            top_songs = get_recommended_songs(cluster, hot)
            return jsonify(top_songs)
    return jsonify([])


@app.route('/login')
def login():
    auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": auth_token,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    auth_request = requests.post("https://accounts.spotify.com/api/token", data=code_payload, headers=headers)
    auth_response = auth_request.json()
    access_token = auth_response.get("access_token")
    session['access_token'] = access_token
    return redirect('/')

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    # Get the user's ID
    access_token = session['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    user_request = requests.get("https://api.spotify.com/v1/me", headers=headers)
    user_response = user_request.json()
    user_id = user_response['id']

    # Create a new playlist
    playlist_name = "Recommended Songs"
    payload = {
        "name": playlist_name,
        "public": True
    }
    create_playlist_request = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists", data=json.dumps(payload), headers=headers)
    create_playlist_response = create_playlist_request.json()
    playlist_id = create_playlist_response['id']

    # Add the recommended songs to the playlist
    song_ids = request.form.getlist('song_id[]')
    add_tracks_payload = {
        "uris": [f"spotify:track:{song_id}" for song_id in song_ids]
    }
    add_tracks_request = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", data=json.dumps(add_tracks_payload), headers=headers)

    return jsonify({"playlist_url": create_playlist_response["external_urls"]["spotify"]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
