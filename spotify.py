import os
import time
import subprocess
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
from logger import setup_logger

logger = setup_logger()

load_dotenv()

device_id = os.getenv("DEVICE_ID")

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

scope=(
            "user-follow-read "
            "playlist-read-private "
            "playlist-read-collaborative "
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-read-recently-played "
            "user-library-read "
        )

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                    client_secret=client_secret, redirect_uri=redirect_uri,
                    scope=scope))

# Spotify functions

def launch_spotify_before_agent():
    """
    Pre-agent function to ensure Spotify device is ready.
    Prompts user for device selection if needed.
    """
    try:
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])

        if not devices:
            print("No active devices found.")
            use_default = input("Should default device be used? (y/n): ").strip().lower()
            if use_default == 'y':
                launch_spotify()
                #sp.start_playback(device_id=device_id)
                print("Spotify launching...")
                return True
            else:
                choice = input("Provide a device_id of your liking or type 'q' to quit: ").strip().lower()
                if choice == "q":
                    print("Exiting...")
                    return None
                else:
                    print("Evaluating device_id given...")
                    if choice == device_id:
                        print("ID given is equal to default one.")
                        launch_spotify()
                        #sp.start_playback(device_id=device_id)
                        return True
                    else:
                        print(f"Using ID {choice}...")
                        try:
                            sp.start_playback(device_id=choice)
                            return True
                        except SpotifyException as e:
                            if e.http_status == 404:
                                raise ValueError(f"Device ID '{choice}' not found. Please check and try again.") from e
                            else:
                                raise  # re-raise other Spotify errors
        else:
            active_device = next((d for d in devices if d.get('is_active')), None)
            if active_device:
                print(f"Active device name: {active_device['name']} - ID: {active_device['id']}")
                print("Starting playback")
                sp.start_playback(device_id=active_device['id'])
                return True
            else:
                print("No active device found.\nListing all devices:")
                for i, d in enumerate(devices, start=1):
                    print(f"{i}. Name: {d['name']} | Type: {d['type']} | ID: {d['id']}")
                
                while True:
                    choice = input("\nEnter the number of the device you want to use (or 'q' to quit): ").strip().lower()
                    if choice == "q":
                        print("Exiting...")
                        return None
                    try:
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(devices):
                            selected_device = devices[choice_idx]
                            print(f"Starting playback on: {selected_device['name']} (ID: {selected_device['id']})")
                            sp.start_playback(device_id=selected_device['id'])
                            return True
                        else:
                            print(f"Invalid number. Please enter a number between 1 and {len(devices)}.")
                    except ValueError:
                        print("Invalid input. Please enter a valid number or 'q' to quit.")

    except Exception as e:
        logger.error(f"Error initializing Spotify: {e}")
        return None

def add_song_to_queue(song_uri: str):
    try:
        # Extract track ID from URI (format: spotify:track:TRACK_ID)
        track_id = song_uri.split(':')[-1]
        
        # Get track details
        track_info = sp.track(track_id)
        song_name = track_info['name']
        artists = ', '.join([artist['name'] for artist in track_info['artists']])
        
        # Add to queue
        sp.add_to_queue(song_uri)
        
        #logger.info(f"Added to queue: {artists} - {song_name}")
        return f"Added to queue: {artists} - {song_name}"
    except Exception as e:
        logger.error(f"Error adding track to queue: {e}")
        return "Error adding track to queue"

def find_song_by_name(name: str):
    try:
        results = sp.search(q=name, type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])

        if not tracks:
            print(f"No tracks found for name: '{name}'")
            return None

        track = tracks[0]
        song_uri = track['uri']
        track_id = song_uri.split(':')[-1]
        song_name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])

        print(f"Found: '{song_name}' by {artists}")
        print(f"URI: {track_id}")

        return (song_uri, song_name)

    except Exception as e:
        logger.error(f"Error finding song by name '{name}': {e}")
        return None

def find_song_by_lyrics(lyrics: str):
    try:
        results = sp.search(q=f"lyrics:{lyrics}", type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])

        if not tracks:
            logger.warning(f"No matching tracks found for lyrics: {lyrics}")
            return None

        track = tracks[0]
        song_uri = track['uri']
        track_id = song_uri.split(':')[-1]
        song_name = track['name']
        song_artist = ", ".join(artist['name'] for artist in track['artists'])

        print(f"Found song '{song_name}' with lyrics '{lyrics}' | Artist: {song_artist} | URI: {track_id}")
        return song_uri

    except Exception as e:
        logger.error(f"Error finding song by lyrics '{lyrics}': {e}")
        return None

def add_song_to_queue_by_song_name(song_name: str):
    result = find_song_by_name(song_name)
    if not result:
        logger.warning(f"No matching track found for song name: {song_name}")
        return "No matching tracks found"

    song_uri, track_display_name = result

    try:
        add_song_to_queue(song_uri) 
        msg = f"Added to queue: {track_display_name}"
        #print(msg)
        return msg
    except Exception as e:
        logger.error(f"Unexpected error adding '{track_display_name}' to queue: {e}")
        return f"Unexpected error: {e}"

def add_song_to_queue_by_lyrics(lyrics: str):
    song_uri = find_song_by_lyrics(lyrics)
    if song_uri:
        add_song_to_queue(song_uri)

        # Fetch song details using the Spotify API
        track_info = sp.track(song_uri)
        track_name = track_info['name']
        artist_name = ", ".join(artist['name'] for artist in track_info['artists'])

        #print(f"Added to queue: {track_name} — {artist_name}")
        return (f"Added to queue: {track_name} — {artist_name}")
    else:
        logger.warning(f"No matching track found for lyrics: {lyrics}")
        return "No matching tracks found"

def start_playing_song_by_name(song_name: str):
    result = find_song_by_name(song_name)
    if result:
        song_uri, track_display_name = result
        try:
            sp.start_playback(uris=[song_uri])
            print(f"Now playing: {track_display_name}")
            return f"Started playing: {track_display_name}"
        except Exception as e:
            logger.error(f"Error starting playback for '{song_name}': {e}")
            return "Couldn't play song. Error."
    else:
        logger.warning(f"Song not found: {song_name}")
        return "Couldn't play song. Not found."

def start_playing_song_by_lyrics(lyrics: str):
    song_uri = find_song_by_lyrics(lyrics)
    if song_uri:
        try:
            sp.start_playback(uris=[song_uri])
            return f"Started playing song with lyrics: {lyrics}"
        except Exception as e:
            logger.error(f"Error starting playback for lyrics '{lyrics}': {e}")
            return f"Couldn't play song. Error"
    else:
        logger.warning(f"No track found for lyrics: {lyrics}")
        return f"Couldn't play song. Not found."

def start_playlist_by_name(playlist_name: str):
    try:
        search_queries = [
            playlist_name,
            f"{playlist_name} playlist",
            f"This Is {playlist_name}",
            f"{playlist_name} Mix",
        ]
        
        playlist_uri = None
        playlist_title = None
        playlist_owner = None
        playlist_track_count = None
        
        for query in search_queries:
            results = sp.search(q=query, type='playlist', limit=3)
            
            # Check if results exist and have items
            if results and results.get('playlists') and results['playlists'].get('items'):
                items = results['playlists']['items']
                
                # Loop through items to find the first non-None playlist
                for playlist in items:
                    if playlist is not None:
                        playlist_uri = playlist['uri']
                        playlist_title = playlist['name']
                        playlist_owner = playlist.get('owner', {}).get('display_name', 'Unknown')
                        playlist_track_count = playlist.get('tracks', {}).get('total', 0)
                        break
                
                # If we found a valid playlist, stop searching
                if playlist_uri and playlist_title:
                    break
        
        if playlist_uri and playlist_title:
            sp.start_playback(context_uri=playlist_uri)
            logger.info(f"Started playlist '{playlist_title}' by {playlist_owner} ({playlist_track_count} tracks) -> {playlist_uri}")
            return f"Started playlist: {playlist_title} by {playlist_owner} ({playlist_track_count} tracks)"
        else:
            logger.warning(f"Playlist not found: {playlist_name}")
            return f"No playlist found for '{playlist_name}'. Try being more specific."
            
    except Exception as e:
        logger.error(f"Error starting playlist '{playlist_name}': {e}")
        return "Error starting playlist"

def pause_music():
    try:
        sp.pause_playback()
        return "Playback paused"
    except Exception as e:
        logger.error(f"Error pausing playback: {e}")
        return "Error pausing playback"

def next_track():
    try:
        sp.next_track()
        return "Successfully skipped to the next track"
    except Exception as e:
        logger.error(f"Error skipping track: {e}")
        return "Error occurred while skipping track"

def previous_track():
    try:
        sp.previous_track()
        return "Successfully went back to the previous track"
    except Exception as e:
        logger.error(f"Error going back track: {e}")
        return "Error occurred while going back a track"

def current_user_playing_track():
    try:
        current_track = sp.current_user_playing_track()
        if not current_track or not current_track.get("item"):
            return "No track is currently playing."

        track_info = current_track["item"]

        # Song info
        song_name = track_info.get("name")
        artists = track_info.get("artists", [])
        artist_names = ", ".join([artist.get("name", "") for artist in artists])
        album_name = track_info.get("album", {}).get("name")
        release_date = track_info.get("album", {}).get("release_date")
        track_url = track_info.get("external_urls", {}).get("spotify")

        # Return nicely formatted string
        return (
            f"Song: {song_name}\n"
            f"Artist: {artist_names}\n"
            f"Album: {album_name}\n"
            f"Release date: {release_date}\n"
            f"Spotify URL: {track_url}"
        )
        
    except Exception as e:
        logger.error(f"Error getting current track info: {e}")
        return "Error getting current track info"


def repeat(state: str):
    try:
        if state == 'track':
            sp.repeat(state='track')
            return "This track will be repeated"
        elif state == 'context':
            sp.repeat(state='context')
            return "All tracks will be repeated"
        else:
            sp.repeat(state='off')
            return "Repeat is off"
    except Exception as e:
        logger.error(f"Error repating tracks: {e}")
        return "Error repeating tracks"

def shuffle(state: bool):
    try:
        if state == True:
            sp.shuffle(state=True)
            return "Track shuffling is on"
        else:
            sp.shuffle(state=False)
            return "Track shuffling is off"
    except Exception as e:
        logger.error(f"Error shuffling tracks: {e}")
        return "Error shuffling tracks"

def seek_track(position_ms: int):
    try:
        if position_ms:
            sp.seek_track(position_ms)
            return f"Track moved to {position_ms} ms"
    except Exception as e:
        logger.error(f"Error moving track: {e}")
        return(f"Error moving track to {position_ms} ms")

def current_user():
    """
    Fetch the current Spotify user's information and return as a formatted string.
    """
    try:
        user_info = sp.current_user()
        
        display_name = user_info.get("display_name", "Unknown")
        user_id = user_info.get("id", "Unknown")
        user_type = user_info.get("type", "Unknown")
        followers = user_info.get("followers", {}).get("total", 0)
        spotify_url = user_info.get("external_urls", {}).get("spotify", "N/A")
        images = user_info.get("images", [])
        #image_urls = ", ".join(img.get("url") for img in images) if images else "No images"
        
        # Return formatted string
        return (
            f"User: {display_name}\n"
            f"ID: {user_id}\n"
            f"Type: {user_type}\n"
            f"Followers: {followers}\n"
            f"Spotify URL: {spotify_url}\n"
            #f"Images: {image_urls}"
        )
        
    except Exception as e:
        logger.error(f"Error fetching current user info: {e}")
        return "Error receiving current user information"

def current_user_followed_artists():
    """
    Fetch and return the current user's followed artists as a formatted string.
    """
    try:
        after = None
        all_artists = []

        while True:
            result = sp.current_user_followed_artists(limit=50, after=after)
            items = result["artists"]["items"]

            # Collect artists
            for item in items:
                all_artists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "followers": item["followers"]["total"]
                })

            # Get cursor for next page
            after = result["artists"]["cursors"].get("after")
            if after is None:
                break  # No more pages

        if not all_artists:
            return "You are not following any artists."

        # Build formatted string
        formatted_artists = []
        for i, artist in enumerate(all_artists, start=1):
            formatted_artists.append(
                f"{i}. {artist['name']} (ID: {artist['id']}) — Followers: {artist['followers']}"
            )

        return "Followed Artists:\n" + "\n".join(formatted_artists)

    except Exception as e:
        logger.error(f"Error fetching followed artists: {e}")
        return "Error receiving artists."

def current_user_playlists(limit: int = 50):
    """
    Fetch and return the current user's playlists as a formatted string.
    """
    try:
        offset = 0
        all_playlists = []

        while True:
            results = sp.current_user_playlists(limit=limit, offset=offset)
            items = results["items"]

            # Collect playlists
            for pl in items:
                all_playlists.append({
                    "id": pl["id"],
                    "name": pl["name"],
                    "tracks": pl["tracks"]["total"],
                    "owner": pl["owner"]["display_name"]
                })

            # Check if fewer than 'limit' items → done
            if len(items) < limit:
                break

            offset += limit

        if not all_playlists:
            return "You have no playlists."

        # Build formatted string
        formatted_playlists = []
        for i, pl in enumerate(all_playlists, start=1):
            formatted_playlists.append(
                f"{i}. {pl['name']} (ID: {pl['id']}) — Owner: {pl['owner']}, Tracks: {pl['tracks']}"
            )

        return "Your Playlists:\n" + "\n".join(formatted_playlists)

    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        return "Error receiving playlists."

def current_user_recently_played(limit: int = 10, after: int = None, before: int = None):
    """
    Fetch and return the current user's recently played tracks as a formatted string.
    
    Parameters:
        limit (int): Number of tracks to return (max 50 per Spotify API)
        after (int): Unix timestamp in milliseconds to return tracks played after
        before (int): Unix timestamp in milliseconds to return tracks played before
    """
    try:
        results = sp.current_user_recently_played(limit=limit, after=after, before=before)
        items = results.get("items", [])

        if not items:
            return "No recently played tracks found."

        formatted_tracks = []
        for i, item in enumerate(items, start=1):
            track = item.get("track", {})
            track_name = track.get("name", "Unknown")
            artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
            album = track.get("album", {}).get("name", "Unknown")
            played_at = item.get("played_at", "Unknown time")
            track_url = track.get("external_urls", {}).get("spotify", "N/A")

            formatted_tracks.append(
                f"{i}. '{track_name}' by {artists} — Album: {album} — Played at: {played_at}\n   Spotify URL: {track_url}"
            )

        return "Recently Played Tracks:\n" + "\n".join(formatted_tracks)

    except Exception as e:
        logger.error(f"Error fetching recently played tracks: {e}")
        return "Error receiving recently played tracks."

def current_user_saved_albums(limit: int = 50, offset: int = 0, market: str = None):
    """
    Fetch and return the current user's saved albums as a formatted string.

    Parameters:
        limit (int): Number of albums to return per request (max 50)
        offset (int): Index of the first album to return
        market (str): Optional ISO 3166-1 alpha-2 country code
    """
    try:
        all_albums = []

        while True:
            results = sp.current_user_saved_albums(limit=limit, offset=offset, market=market)
            items = results.get("items", [])

            for item in items:
                album = item.get("album", {})
                album_name = album.get("name", "Unknown")
                artists = ", ".join([artist.get("name") for artist in album.get("artists", [])])
                total_tracks = album.get("total_tracks", 0)
                album_id = album.get("id", "N/A")
                release_date = album.get("release_date", "Unknown")
                album_url = album.get("external_urls", {}).get("spotify", "N/A")

                all_albums.append({
                    "name": album_name,
                    "artists": artists,
                    "tracks": total_tracks,
                    "id": album_id,
                    "release_date": release_date,
                    "url": album_url
                })

            # Break if fewer than 'limit' returned → done
            if len(items) < limit:
                break

            offset += limit

        if not all_albums:
            return "No saved albums found."

        formatted_albums = []
        for i, album in enumerate(all_albums, start=1):
            formatted_albums.append(
                f"{i}. '{album['name']}' by {album['artists']} — Tracks: {album['tracks']}, "
                f"Release date: {album['release_date']} — ID: {album['id']}\n   Spotify URL: {album['url']}"
            )

        return "Your Saved Albums:\n" + "\n".join(formatted_albums)

    except Exception as e:
        logger.error(f"Error fetching saved albums: {e}")
        return "Error receiving saved albums."

#def current_user_saved_albums_add():

def current_user_saved_tracks():
    try:
        sp.current_user_saved_tracks(limit=50)
        #logger.info("Info about users saved tracks")
        return "Users saved tracks"
    except Exception as e:
        logger.error(f"Error with users saved tracks: {e}")
        return "Error receiving users saved tracks"

def current_user_top_artists():
    try:
        sp.current_user_top_artists(limit=50)
        #logger.info("Info about users top artists")
        return "Users top artists"
    except Exception as e:
        logger.error(f"Error with users top artists: {e}")
        return "Error receiving users top artists"

def current_user_top_tracks():
    try:
        sp.current_user_top_tracks(limit=50)
        #logger.info("Info about users top tracks")
        return "Users top tracks"
    except Exception as e:
        logger.error(f"Error with users top tracks: {e}")
        return "Error receiving users top tracks"

def start_playing_artist(artist_name: str):
    try:
        # Step 1. Search for the artist
        results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
        if not results["artists"]["items"]:
            return f"No artist found matching '{artist_name}'."

        artist_id = results["artists"]["items"][0]["id"]

        # Step 2. Get the artist's top tracks (most popular songs)
        top_tracks = sp.artist_top_tracks(artist_id)["tracks"]
        if not top_tracks:
            return f"No top tracks found for '{artist_name}'."

        # Step 3. Pick a random one
        random_track = random.choice(top_tracks)
        uri = random_track["uri"]

        # Step 4. Start playback
        sp.start_playback(uris=[uri])

        #logger.info(f"Playing track '{random_track['name']}' by {artist_name}")
        return f"Playing '{random_track['name']}' by {artist_name}."
    except Exception as e:
        logger.error(f"Error playing artist {artist_name}: {e}")
        return f"Failed to play music by {artist_name}: {e}"

#def recommendation_genre_seeds():
#    genres = sp.recommendation_genre_seeds()
#    return genres
    
#seed_genres = []

def recommendations(seed_genres: list):
    try:
        sp.recommendations(seed_genres=seed_genres)
        #logger.info("Get a list of recommended tracks")
        return "A list of recommended tracks"
    except Exception as e:
        logger.error(f"Error with users recommended tracks: {e}")
        return "Error receiving users recommended tracks"

def queue():
    try:
        sp.queue()
        #logger.info("Get current user's queue")
        return "Current user's queue"
    except Exception as e:
        logger.error(f"Error with users queue: {e}")
        return "Error receiving users queue"

def start_playback(device_id=device_id):
    try:
        sp.start_playback(device_id=device_id)
        #logger.info("Start playback")
        return f"Playback started"
    except SpotifyException as e:
        logger.error(f"Error starting playback: {e}")

'''
def start_playback(device_id: str):
    try:
        sp.start_playback(device_id=device_id)
        #logger.info("Start playback")
        return f"Playback starting with device_id"
    except SpotifyException as e:
        logger.error(f"Error starting playback: {e}")
        
        if e.http_status == 404:
            print("Device not found. Launching Spotify...")
            launch_spotify()
            time.sleep(15)
            
            # Retry up to 2 times
            for attempt in range(2):
                try:
                    sp.start_playback(device_id=device_id)
                    print("Playback started after launching Spotify.")
                    return "Playback started successfully after launching Spotify"
                except SpotifyException as e2:
                    print(f"Retry attempt {attempt + 1} failed ({e2.http_status}): {e2}")
                    logger.error(f"Retry attempt {attempt + 1} failed: {e2}")
                    if attempt < 1:  # If not the last attempt, wait before retrying
                        print(f"Waiting 5 seconds before retry {attempt + 2}...")
                        time.sleep(5)
                    else:
                        print("All retry attempts exhausted.")
                        return "Error receiving users playback after multiple attempts"
        else:
            print(f"Spotify error ({e.http_status}): {e}")
            return "Error receiving users playback"
'''
def devices():
    try:
        results = sp.devices()  # get the actual device data
        devices = results.get("devices", [])
        if not devices:
            return "No devices found."
        
        # Format for agent
        device_list = [
            f"Device name: {d['name']} - Id: {d['id']}, Type: ({d['type']}) - {'Status: Active' if d['is_active'] else 'Inactive'}"
            for d in devices
        ]
        return "\n".join(device_list)
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return f"Error receiving devices: {e}"

def is_spotify_running():
    """Check if Spotify process is currently active."""
    result = subprocess.run(["pgrep", "-f", "/snap/bin/spotify"], stdout=subprocess.PIPE)
    return result.returncode == 0

def launch_spotify():
    """
    Launch Spotify.
    - detach=True: Spotify stays open after script ends
    - detach=False: tied to this script
    """
    if is_spotify_running():
        print("Spotify is already running.")
        return None
    try:
        process = subprocess.Popen(["/snap/bin/spotify"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp  # detaches Spotify from the script
                )
        return "Spotify launched."
    except Exception as e:
        print(f"Error opening Spotify: {e}")


def close_spotify():
    """
    Close Spotify gracefully if it's running.
    Uses pkill (simplest, safe for Snap version).
    """
    try:
        subprocess.run(["pkill", "-f", "spotify"], check=False)
        return "Spotify closed."
    except Exception as e:
        print(f"Error closing Spotify: {e}")