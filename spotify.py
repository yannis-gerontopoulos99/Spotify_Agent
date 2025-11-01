import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from logger import setup_logger

logger = setup_logger()

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                    client_secret=client_secret, redirect_uri=redirect_uri))

# Spotify functions

def add_song_to_queue(song_uri: str):
    try:
        sp.add_to_queue(song_uri)
        logger.info(f"Added track to queue: {song_uri}")
        return "Added track to queue successfully"
    except Exception as e:
        logger.error(f"Error adding track to queue: {e}")
        return "Error adding track to queue"

def find_song_by_name(name: str):
    try:
        results = sp.search(q=name, type='track')
        if results:
            song_uri = results['tracks']['items'][0]['uri']
            logger.info(f"Found song '{name}' -> URI: {song_uri}")
            return song_uri
        else:
            logger.warning(f"No tracks found for name: {name}")
            return None
    except Exception as e:
        logger.error(f"Error finding song by name '{name}': {e}")
        return None

def find_song_by_lyrics(lyrics: str):
    try:
        results = sp.search(q=f"lyrics:{lyrics}", type='track')
        if results and results['tracks']['items']:
            song_uri = results['tracks']['items'][0]['uri']
            logger.info(f"Found song with lyrics '{lyrics}' -> URI: {song_uri}")
            return song_uri
        else:
            logger.warning(f"No matching tracks found for lyrics: {lyrics}")
            return None
    except Exception as e:
        logger.error(f"Error finding song by lyrics '{lyrics}': {e}")
        return None

def add_song_to_queue_by_song_name(song_name: str):
    song_uri = find_song_by_name(song_name)
    if song_uri:
        return add_song_to_queue(song_uri)
    else:
        logger.warning(f"No matching track found for song name: {song_name}")
        return "No matching tracks found"

def add_song_to_queue_by_lyrics(lyrics: str):
    song_uri = find_song_by_lyrics(lyrics)
    if song_uri:
        return add_song_to_queue(song_uri)
    else:
        logger.warning(f"No matching track found for lyrics: {lyrics}")
        return "No matching tracks found"

def start_playing_song_by_name(song_name: str):
    song_uri = find_song_by_name(song_name)
    if song_uri:
        try:
            sp.start_playback(uris=[song_uri])
            logger.info(f"Started playing song '{song_name}'")
            return f"Started playing song {song_name}"
        except Exception as e:
            logger.error(f"Error starting playback for '{song_name}': {e}")
            return f"Couldn't play song. Error"
    else:
        logger.warning(f"Song not found: {song_name}")
        return f"Couldn't play song. Not found."

def start_playing_song_by_lyrics(lyrics: str):
    song_uri = find_song_by_lyrics(lyrics)
    if song_uri:
        try:
            sp.start_playback(uris=[song_uri])
            logger.info(f"Started playing song with lyrics '{lyrics}'")
            return f"Started playing song with lyrics: {lyrics}"
        except Exception as e:
            logger.error(f"Error starting playback for lyrics '{lyrics}': {e}")
            return f"Couldn't play song. Error"
    else:
        logger.warning(f"No track found for lyrics: {lyrics}")
        return f"Couldn't play song. Not found."

def start_playlist_by_name(playlist_name: str):
    try:
        results = sp.search(q=playlist_name, type='playlist', limit=1)
        if results and results['playlists']['items']:
            playlist_uri = results['playlists']['items'][0]['uri']
            sp.start_playback(context_uri=playlist_uri)
            logger.info(f"Started playlist '{playlist_name}' -> {playlist_uri}")
            return f"Playlist started: {playlist_name}"
        else:
            logger.warning(f"Playlist not found: {playlist_name}")
            return "Playlist not found"
    except Exception as e:
        logger.error(f"Error starting playlist '{playlist_name}': {e}")
        return "Error starting playlist"

def start_music():
    try:
        sp.start_playback()
        logger.info("Playback started")
        return "Playback started"
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        return "Error starting playback"

def pause_music():
    try:
        sp.pause_playback()
        logger.info("Playback paused")
        return "Playback paused"
    except Exception as e:
        logger.error(f"Error pausing playback: {e}")
        return "Error pausing playback"

def next_track():
    try:
        sp.next_track()
        logger.info("Skipped to next track")
        return "Successfully skipped to the next track"
    except Exception as e:
        logger.error(f"Error skipping track: {e}")
        return "Error occurred while skipping track"

def previous_track():
    try:
        sp.previous_track()
        logger.info("Went back to previous track")
        return "Successfully went back to the previous track"
    except Exception as e:
        logger.error(f"Error going back track: {e}")
        return "Error occurred while going back a track"

def currently_playing():
    try:
        current_track = sp.currently_playing() #current_user_playing_track()
        logger.info(f"Current track info: {current_track}")
        return "Current track info: {current_track}"
    except Exception as e:
        logger.error(f"Error getting current track info: {e}")
        return "Error getting current track info"

def repeat(state: str):
    try:
        if state == 'track':
            sp.repeat(state='track')
            logger.info("This track will be repeated")
            return "This track will be repeated"
        elif state == 'context':
            sp.repeat(state='context')
            logger.info("All tracks will be repeated")
            return "All tracks will be repeated"
        else:
            sp.repeat(state='off')
            logger.info("Repeat is off")
            return "Repeat is off"
    except Exception as e:
        logger.error(f"Error repating tracks: {e}")
        return "Error repeating tracks"

def shuffle(state: bool):
    try:
        if state == True:
            sp.shuffle(state=True)
            logger.info("Track shuffling is on")
            return "Track shuffling is on"
        else:
            sp.shuffle(state=False)
            logger.info("Track shuffling is off")
            return "Track shuffling is off"
    except Exception as e:
        logger.error(f"Error shuffling tracks: {e}")
        return "Error shuffling tracks"

def seek_track(position_ms: int):
    try:
        if position_ms:
            sp.seek_track(position_ms)
            logger.info(f"Track moved to {position_ms} ms")
            return f"Track moved to {position_ms} ms"
    except Exception as e:
        logger.error(f"Error moving track: {e}")
        return(f"Error moving track to {position_ms} ms")

def current_user():
    try:
        sp.current_user()
        logger.info("Info about current user")
        return "Current user information"
    except Exception as e:
        logger.error(f"Error with current user: {e}")
        return "Error receving curretn user information"