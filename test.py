import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotify import (add_song_to_queue, find_song_by_name, find_song_by_lyrics, add_song_to_queue_by_song_name,
                    add_song_to_queue_by_lyrics, start_playing_song_by_name, start_playing_song_by_lyrics,
                    start_playlist_by_name, start_music, pause_music, next_track, previous_track,
                    currently_playing, repeat, shuffle, seek_track, current_user)


load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
scope = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-currently-playing",
    "streaming"
)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                    client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

#add_song_to_queue('6j0MEtClnzHKW6YLusvlfC') 
#find_song_by_name('Hello')
#find_song_by_lyrics('οσα περιμενα για να στα πω')
#add_song_to_queue_by_song_name('Youngblood')
#add_song_to_queue_by_lyrics('οσα περιμενα για να στα πω') 
#start_playing_song_by_name('Pump it') 
#start_playing_song_by_lyrics('οσα περιμενα για να στα πω')
#start_playlist_by_name('CALM') 
#start_music() 
#pause_music() 
#next_track() 
#previous_track() #Error if no previous track
#currently_playing() 
#repeat('off') #track, context
#shuffle(False)
#seek_track(15) 
#current_user()