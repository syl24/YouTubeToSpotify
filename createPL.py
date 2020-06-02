import json
import identifications
import os
import requests

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl


class CreatePL:

    # Initialize YT client
    # Create dict of songs
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    # Creation of YT client, from copied directly from Google's API docs
    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    # Using client, get videos from playlist, used Google's API docs
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )

        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]
            self.all_song_info[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,
                "spotify_url": self.get_spotify_url(song_name, artist)
            }

    # Used Spotify API information to create dumps and query
    def create_playlist(self):

        request_body = json.dumps({
            "name": "Youtube Music Liked Videos",
            "description": "Liked Videos",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(identifications.spotify_userID)

        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(identifications.spotify_token)
            }
        )
        response_json = response.json()
        return response_json["id"]

    # Used Spotify API docs to conduct query
    def get_spotify_url(self, song_name, artist):

        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )

        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(identifications.spotify_token)
            }
        )

        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use first song on search
        uri = songs[0]["uri"]

        return uri

    # Putting it all together to
    def get_songs(self):
        # population of songs
        self.get_liked_videos()

        # collect uri
        uri = []
        for song, info in self.all_song_info.items():
            uri.append(info["spotify_uri"])

        # create new playlist
        playlist_id = self.create_playlist()

        # add all songs into this new playlist
        request_data = json.dumps(uri)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(identifications.spotify_token)
            }
        )

        response_json = response.json

        return response_json

# Run
if __name__ == '__main__':
    cp = CreatePL()
    cp.get_songs()
