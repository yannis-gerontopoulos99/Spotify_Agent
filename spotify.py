import os
import time
import subprocess
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
from datetime import datetime
from logger import setup_logger
import psutil
import platform

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
            "user-top-read "

        )

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                    client_secret=client_secret, redirect_uri=redirect_uri,
                    scope=scope))

# Spotify functions

# Pre-agent function to ensure Spotify device is ready and prompts user for device selection if needed
def launch_spotify_before_agent():
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
            # Find active device from available devices
            active_device = next((d for d in devices if d.get('is_active')), None)
            if active_device:
                print(f"Active device name: {active_device['name']} - ID: {active_device['id']}")
                
                # Check if something is currently playing on the active device
                current_playback = sp.current_playback()
                if current_playback and current_playback.get('is_playing') and current_playback.get('device', {}).get('id') == active_device['id']:
                    track = current_playback.get("item")
                    if track:
                        song_name = track.get("name", "Unknown Song")
                        artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
                        print(f"Currently playing: {song_name} - {artists}")
                    else:
                        print("Playback is active, but no track info is available.")
                else:
                    print("Starting playback...")
                    sp.start_playback(device_id=active_device['id'])
                    
                return True

            else:
                # No active device found, prompt user to select one
                print("No active device found.\nListing all available devices:")
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

# Helper function
# Returns detailed information about the currently playing track
def current_user_playing_track_info_helper():
    try:
        current_track = sp.current_user_playing_track()
        if not current_track or not current_track.get("item"):
            return None
        
        track = current_track["item"]

        # Track info
        track_name = track.get("name")
        track_id = track.get("id")
        track_uri = track.get("uri")

        # Artists info
        artists = track.get("artists", [])
        artist_names = ", ".join(a.get("name", "") for a in artists)
        artist_ids = ", ".join(a.get("id", "") for a in artists)
        artist_uris = ", ".join(a.get("uri", "") for a in artists)

        # Album info
        album = track.get("album", {})
        album_name = album.get("name")
        album_id = album.get("id")
        album_uri = album.get("uri")

        return (track_name, track_id, artist_names, artist_ids, album_name, album_id
        )
    except Exception as e:
        logger.error(f"Error getting current track info: {e}")
        return "Error getting current track info"

# Helper function
# Adds a song to the Spotify queue using its URI and returns confirmation with track details
def add_song_to_queue_helper(song_uri: str, device_id: str):
    try:
        # Extract track ID from URI (format: spotify:track:TRACK_ID)
        track_id = song_uri.split(':')[-1]
        
        # Get track details
        track_info = sp.track(track_id)
        song_name = track_info['name']
        artists = ', '.join([artist['name'] for artist in track_info['artists']])
        
        # Add to queue
        sp.add_to_queue(song_uri, device_id)
        
        #logger.info(f"Added to queue: {artists} - {song_name}")
        return f"Added to queue: {artists} - {song_name}"
    except Exception as e:
        logger.error(f"Error adding track to queue: {e}")
        return "Error adding track to queue"

# Helper function
# Searches Spotify for a track by name and returns its URI and name
def find_song_by_name_helper(name: str):
    try:
        results = sp.search(q=name, type='track', limit=5)
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

# Helper function
# Searches Spotify for a track by lyrics fragment and returns its URI
def find_song_by_lyrics_helper(lyrics: str):
    try:
        results = sp.search(q=f"lyrics:{lyrics}", type='track', limit=5)
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
        return (song_uri, song_name)

    except Exception as e:
        logger.error(f"Error finding song by lyrics '{lyrics}': {e}")
        return None

# Finds a song by name and adds it to the queue
def add_song_to_queue_by_song_name(song_name: str):
    try:
        # Check what's currently playing
        current_info = current_user_playing_track_info_helper()
        
        # Find the requested song
        result = find_song_by_name_helper(song_name)
        if not result:
            logger.warning(f"Song not found: {song_name}")
            return "Couldn't play song. Not found."

        song_uri, track_display_name = result
        requested_track_id = song_uri.split(':')[-1]

        # Check if the requested song is already playing
        if current_info and current_info != "Error getting current track info":
            current_track_id = current_info[1]
                
            if current_track_id == requested_track_id:
                return f"'{track_display_name}' is already playing"

        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        # Queue the song
        add_song_to_queue_helper(song_uri, device_id) 
        msg = f"Added to queue: {track_display_name}"
        return msg
        
    except Exception as e:
        logger.error(f"Unexpected error adding '{song_name}' to queue: {e}")
        return f"Unexpected error: {e}"

# Finds a song by lyrics fragment and adds it to the queue
def add_song_to_queue_by_lyrics(lyrics: str):
    try:
        # Check what's currently playing
        current_info = current_user_playing_track_info_helper()
        
        # Find the song by lyrics
        result = find_song_by_lyrics_helper(lyrics)
        if not result:
            logger.warning(f"No matching track found for lyrics: {lyrics}")
            return "No matching tracks found"
        
        song_uri, track_display_name = result
        requested_track_id = song_uri.split(':')[-1]
        
        # Check if the requested song is already playing
        if current_info and current_info != "Error getting current track info":
            current_track_id = current_info[1]
            
            if current_track_id == requested_track_id:
                return f"'{track_display_name}' is already playing"
        
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        # Queue the song
        add_song_to_queue_helper(song_uri, device_id)
        msg = f"Added to queue: {track_display_name}"
        return msg
        
    except Exception as e:
        logger.error(f"Error adding song with lyrics '{lyrics}' to queue: {e}")
        return "Error adding track to queue"

# Finds a song by name and starts playing it immediately
def start_playing_song_by_name(song_name: str):
    try:
        # Check what's currently playing
        current_info = current_user_playing_track_info_helper()
        
        # Find the requested song
        result = find_song_by_name_helper(song_name)
        if not result:
            logger.warning(f"Song not found: {song_name}")
            return "Couldn't play song. Not found."
        
        song_uri, track_display_name = result
        
        # Check if the requested song is already playing
        if current_info and current_info != "Error getting current track info":
            current_track_id = current_info[1]
            requested_track_id = song_uri.split(':')[-1]
            
            if current_track_id == requested_track_id:
                #print(f"'{track_display_name}' is already playing")
                return f"'{track_display_name}' is already playing"
        
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        # Start playback
        sp.start_playback(device_id, uris=[song_uri])
        print(f"Now playing: {track_display_name}")
        return f"Started playing: {track_display_name}"
    except Exception as e:
        logger.error(f"Error starting playback for '{song_name}': {e}")
        return "Couldn't play song. Error."

# Finds a song by lyrics fragment and starts playing it immediately
def start_playing_song_by_lyrics(lyrics: str):
    try:
        # Check what's currently playing
        current_info = current_user_playing_track_info_helper()
        
        result = find_song_by_lyrics_helper(lyrics)
        if not result:
            logger.warning(f"Song with lyrics not found: {lyrics}")
            return "Couldn't play song. Not found."
        
        song_uri, track_display_name = result
        
        # Check if the requested song is already playing
        if current_info and current_info != "Error getting current track info":
            current_track_id = current_info[1]
            requested_track_id = song_uri.split(':')[-1]
            
            if current_track_id == requested_track_id:
                #print(f"'{track_display_name}' is already playing")
                return f"'{track_display_name}' is already playing"
        
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        # Start playback
        sp.start_playback(device_id, uris=[song_uri])
        #print(f"Now playing: {track_display_name}")
        return f"Started playing: {track_display_name}"
    except Exception as e:
        logger.error(f"Error starting playback for lyrics: '{lyrics}': {e}")
        return "Couldn't play song from lyrics. Error."

# Searches for a playlist by name and starts playing it
def start_playlist_by_name(playlist_name: str):
    try:
        # Try multiple search query variations to find the playlist
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
            # Check active device for app launch scenario
            devices_response = sp.devices()
            devices = devices_response.get('devices', [])
            if not devices:
                return "No devices found."
            
            devices = sp.devices().get("devices", [])
            if not devices:
                print("No devices found.")
                return None
            # Return the ID of the first device
            device_id = devices[0].get("id")
            
            sp.start_playback(device_id, context_uri=playlist_uri)
            #logger.info(f"Started playlist '{playlist_title}' by {playlist_owner} ({playlist_track_count} tracks) -> {playlist_uri}")
            return f"Started playlist: {playlist_title} by {playlist_owner} ({playlist_track_count} tracks)"
        else:
            logger.warning(f"Playlist not found: {playlist_name}")
            return f"No playlist found for '{playlist_name}'. Try being more specific."
            
    except Exception as e:
        logger.error(f"Error starting playlist '{playlist_name}': {e}")
        return "Error starting playlist"

# Pauses the current playback
def pause_music():
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        sp.pause_playback(device_id)
        return "Playback paused"
    except Exception as e:
        error_message = str(e)
        
        # Spotify sends this when there's no previous track or the command is disallowed
        if "403" in error_message and "Restriction violated" in error_message:
            return "There is no track available to pause."
        
        logger.error(f"Error pausing track: {e}")
        return "Error occurred while pausing track"

# Skips to the next track in the queue
def next_track():
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        sp.next_track(device_id)
        return "Successfully skipped to the next track"
    
    except Exception as e:
        error_message = str(e)
        
        # Spotify sends this when there's no previous track or the command is disallowed
        if "403" in error_message and "Restriction violated" in error_message:
            return "There is no next track available."
        
        logger.error(f"Error skipping track: {e}")
        return "Error occurred while skipping track"

# Goes back to the previous track
def previous_track():
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        sp.previous_track(device_id)
        return "Successfully went back to the previous track"

    except Exception as e:
        error_message = str(e)

        # Spotify sends this when there's no previous track or the command is disallowed
        if "403" in error_message and "Restriction violated" in error_message:
            return "There is no previous track available."

        # fallback for all other errors
        logger.error(f"Error going back track: {e}")
        return "Error occurred while going back a track"

# Returns detailed information about the currently playing track
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
        duration_ms = track_info.get("duration_ms", 0)
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        
        # Return nicely formatted string
        return (
            f"Song: {song_name}\n"
            f"Artist: {artist_names}\n"
            f"Album: {album_name}\n"
            f"Release date: {release_date}\n"
            f"Spotify URL: {track_url}\n"
            f"Song duration: {minutes}:{seconds:02d} minutes"
        )
    except Exception as e:
        logger.error(f"Error getting current track info: {e}")
        return "Error getting current track info"

# Sets repeat mode: 'track' (repeat one song), 'context' (repeat all), or 'off'
def repeat(state: str):
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        if state == 'track':
            sp.repeat(state='track', device_id=device_id)
            return "This track will be repeated"
        elif state == 'context':
            sp.repeat(state='context', device_id=device_id)
            return "All tracks will be repeated"
        else:
            sp.repeat(state='off', device_id=device_id)
            return "Repeat is off"
    except Exception as e:
        logger.error(f"Error repeating tracks: {e}")
        return "Error repeating tracks"

# Toggles shuffle mode on or off
def shuffle(state: bool):
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        sp.shuffle(state=state, device_id=device_id)
        status = "on" if state else "off"
        return f"Track shuffling is {status}"
    except Exception as e:
        logger.error(f"Error shuffling tracks: {e}")
        return "Error shuffling tracks"

# Seeks to a specific position in the current track (in milliseconds)
def seek_track(position_ms: int):
    try:
        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        if position_ms:
            sp.seek_track(device_id, position_ms)
            return f"Track moved to {position_ms} ms"
    except Exception as e:
        logger.error(f"Error moving track: {e}")
        return(f"Error moving track to {position_ms} ms")

# Fetches and returns the current Spotify user's profile information
def current_user():
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

# Fetches and returns all artists the current user follows as a formatted string
def current_user_followed_artists():
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

# Fetches and returns all playlists owned or followed by the current user
def current_user_playlists(limit: int = 50):
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

# Fetches recently played tracks with optional time filters (after/before timestamps in ms)
def current_user_recently_played(limit: int = 10, after: int = None, before: int = None):
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

# Fetches all albums saved in the user's library with pagination support
def current_user_saved_albums(limit: int = 50, offset: int = 0, market: str = None):
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

# Fetches all tracks saved in the user's library with pagination support
def current_user_saved_tracks(limit: int = 20, offset: int = 0, market: str = None):
    try:
        all_tracks = []

        while True:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset, market=market)
            items = results.get("items", [])

            for item in items:
                track = item.get("track", {})

                track_name = track.get("name", "Unknown")
                artists = ", ".join(a.get("name") for a in track.get("artists", []))
                track_id = track.get("id", "N/A")
                track_url = track.get("external_urls", {}).get("spotify", "N/A")
                album_name = track.get("album", {}).get("name", "Unknown")
                release_date = track.get("album", {}).get("release_date", "Unknown")

                all_tracks.append({
                    "name": track_name,
                    "artists": artists,
                    "album": album_name,
                    "release_date": release_date,
                    "id": track_id,
                    "url": track_url
                })

            # Stop if Spotify returned less than `limit`
            if len(items) < limit:
                break

            offset += limit

        if not all_tracks:
            return "No saved tracks found."

        formatted = []
        for i, tr in enumerate(all_tracks, start=1):
            formatted.append(
                f"{i}. '{tr['name']}' — {tr['artists']}\n"
                f"   Album: {tr['album']} | Release: {tr['release_date']}\n"
                f"   ID: {tr['id']}\n"
                f"   URL: {tr['url']}"
            )

        return "Your Saved Tracks:\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error fetching saved tracks: {e}")
        return "Error receiving saved tracks."

# Returns the user's top 20 artists from the last 4 weeks (short term)
def current_user_top_artists_short_term(limit: int = 20, time_range: str = 'short_term'):
    try:
        results = sp.current_user_top_artists(limit=limit, offset=0, time_range=time_range)
        items = results.get("items", [])

        if not items:
            return "No top artists found."

        formatted = []
        for i, artist in enumerate(items, start=1):
            name = artist.get("name", "Unknown")
            genres = ", ".join(artist.get("genres", []))
            popularity = artist.get("popularity", 0)
            url = artist.get("external_urls", {}).get("spotify", "N/A")
            followers = artist.get("followers", {}).get("total", 0)

            formatted.append(
                f"{i}. {name}\n"
                f"   Followers: {followers} | Popularity: {popularity}\n"
                f"   Genres: {genres}\n"
                f"   URL: {url}"
            )

        return "Your Short Term Top Artists (Top 20):\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error fetching top artists: {e}")
        return "Error receiving top artists."

# Returns the user's top 20 artists from several years of listening history (long term)
def current_user_top_artists_long_term(limit: int = 20, time_range: str = 'long_term'):
    try:
        results = sp.current_user_top_artists(limit=limit, offset=0, time_range=time_range)
        items = results.get("items", [])

        if not items:
            return "No top artists found."

        formatted = []
        for i, artist in enumerate(items, start=1):
            name = artist.get("name", "Unknown")
            genres = ", ".join(artist.get("genres", []))
            popularity = artist.get("popularity", 0)
            url = artist.get("external_urls", {}).get("spotify", "N/A")
            followers = artist.get("followers", {}).get("total", 0)

            formatted.append(
                f"{i}. {name}\n"
                f"   Followers: {followers} | Popularity: {popularity}\n"
                f"   Genres: {genres}\n"
                f"   URL: {url}"
            )

        return "Your Long Term Top Artists (Top 20):\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error fetching top artists: {e}")
        return "Error receiving top artists."

# Returns the user's top tracks based on time range (short_term=4 weeks, medium_term=6 months, long_term=years)
def current_user_top_tracks(limit: int = 20, time_range: str = 'long_term'):
    try:
        results = sp.current_user_top_tracks(
            limit=limit,
            offset=0,
            time_range=time_range
        )

        items = results.get("items", [])
        if not items:
            return "No top tracks found."

        formatted = []
        for i, track in enumerate(items, start=1):
            name = track.get("name", "Unknown")
            artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
            album = track.get("album", {}).get("name", "Unknown")
            popularity = track.get("popularity", 0)
            url = track.get("external_urls", {}).get("spotify", "N/A")
            track_id = track.get("id", "N/A")

            formatted.append(
                f"{i}. {name} — {artists}\n"
                f"   Album: {album}\n"
                f"   Popularity: {popularity}\n"
                f"   ID: {track_id}\n"
                f"   URL: {url}"
            )

        return "Your Top Tracks (Top 20):\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error fetching top tracks: {e}")
        return "Error receiving top tracks."

# Searches for an artist and plays a random track from their top tracks
def start_playing_artist(artist_name: str):
    try:
        # Step 1. Search for the artist
        results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
        if not results["artists"]["items"]:
            return f"No artist found matching '{artist_name}'."

        artist_id = results["artists"]["items"][0]["id"]

        # Step 2. Get the artist's top tracks
        top_tracks = sp.artist_top_tracks(artist_id)["tracks"]
        if not top_tracks:
            return f"No top tracks found for '{artist_name}'."

        # Get currently playing track ID
        current_info = current_user_playing_track_info_helper()
        current_track_id = current_info[1] if current_info else None

        # Step 3. Pick a random track that is NOT the currently playing track
        available_tracks = [t for t in top_tracks if t["id"] != current_track_id]

        # If all tracks match the current one (rare but possible)
        if not available_tracks:
            # Just play something anyway (fallback)
            random_track = random.choice(top_tracks)
        else:
            random_track = random.choice(available_tracks)

        uri = random_track["uri"]

        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")
        
        # Step 4. Start playback
        sp.start_playback(device_id, uris=[uri])

        return f"Playing '{random_track['name']}' by {artist_name}."

    except Exception as e:
        logger.error(f"Error playing artist {artist_name}: {e}")
        return f"Failed to play music by {artist_name}: {e}"

# Helper function
# Finds all albums by the specified artist
def find_artist_albums_helper(artist_name: str):
    try:
        results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
        if not results["artists"]["items"]:
            return [], f"No artist found matching '{artist_name}'."

        artist_id = results["artists"]["items"][0]["id"]

        albums = sp.artist_albums(
            artist_id=artist_id,
            include_groups=['album', 'single'],
            limit=50
        )["items"]

        full_albums = []

        for item in albums:
            album_id = item["id"]
            full = sp.album(album_id)

            full_albums.append({
                "album_id": full["id"],
                "album_name": full["name"],
                "release_date": full["release_date"],
                "popularity": full.get("popularity", 0),
                "album_type": full["album_type"],
                "artist_name": full["artists"][0]["name"],
                "uri": full["uri"],
                "full": full
            })

        return full_albums, None

    except Exception as e:
        return [], str(e)

# Formats and returns a list of albums by the specified artist
def format_artist_albums(artist_name: str):
    albums, error = find_artist_albums_helper(artist_name)

    if error:
        return error

    formatted = []

    for i, a in enumerate(albums, start=1):
        name = a["artist_name"]
        album = a["album_name"]
        release = a["release_date"]
        album_type = a["album_type"]

        formatted.append(
            f"{i}. {name}\n"
            f"   Album: {album}\n"
            f"   Release Date: {release}\n"
            f"   Type: {album_type}"
        )

    return f"Albums for '{artist_name}':\n\n" + "\n\n".join(formatted)

# Searches for an artist and plays a random album from their discography
def start_playing_artist_album(artist_name: str):
    try:
        # 1. Check currently playing album
        current_info = current_user_playing_track_info_helper()
        current_album_id = None
        if current_info:
            # unpack: track_name, track_id, artist_names, artist_ids, album_name, album_id
            _, _, _, _, _, current_album_id = current_info
        
        # 2. Get albums
        albums, error = find_artist_albums_helper(artist_name)

        if error:
            print(error)
            return

        if not albums:
            print("No albums found.")
            return

        # 3. Sort by popularity
        albums = sorted(albums, key=lambda x: x["popularity"], reverse=True)

        # 4. Take top 10
        top_10 = albums[:2]

        # 5. Remove current album from top_10 if it's there
        top_10 = [a for a in top_10 if a["album_id"] != current_album_id]

        if not top_10:
            return f"The top album by {artist_name} is already playing."

        # 6. Pick random from remaining
        chosen = random.choice(top_10)

        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")

        # 7. Start playback
        sp.start_playback(device_id, context_uri=chosen["uri"])

        return (
            f"Now Playing Album:\n"
            f"   Album: {chosen['album_name']}\n"
            f"   Artist: {chosen['artist_name']}\n"
            f"   Release Date: {chosen['release_date']}\n"
            f"   Type: {chosen['album_type']}"
        )

    except Exception as e:
        logger.error(f"Error playing artist album {artist_name}: {e}")
        print(f"Failed to play album by {artist_name}: {e}")

# Search for an album by its name and play the most relevant match.
def start_playing_album_by_name(album_name: str):
    try:
        # 1. Check currently playing album
        current_info = current_user_playing_track_info_helper()
        current_album_id = None
        if current_info:
            # unpack: track_name, track_id, artist_names, artist_ids, album_name, album_id
            _, _, _, _, _, current_album_id = current_info

        # 2. Search Spotify for albums
        results = sp.search(q=f"album:{album_name}", type="album", limit=10)

        albums = results.get("albums", {}).get("items", [])
        if not albums:
            return f"No album found with name '{album_name}'."

        # 3. Best match (Spotify ranks by relevance)
        album = albums[0]

        album_id = album["id"]
        found_name = album["name"]
        artist_name = album["artists"][0]["name"]
        release_date = album.get("release_date")
        album_type = album.get("album_type")

        # 4. Check if already playing
        if current_album_id == album_id:
            return (
                f"The album '{found_name}' by {artist_name} "
                f"is already playing."
            )

        # Check active device for app launch scenario
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        devices = sp.devices().get("devices", [])
        if not devices:
            print("No devices found.")
            return None
        # Return the ID of the first device
        device_id = devices[0].get("id")

        # 5. Start playback
        sp.start_playback(device_id, context_uri=f"spotify:album:{album_id}")

        return (
            f"Now Playing Album:\n"
            f"   Album: {found_name}\n"
            f"   Artist: {artist_name}\n"
            f"   Release Date: {release_date}\n"
            f"   Type: {album_type}"
        )

    except Exception as e:
        logger.error(f"Error playing album '{album_name}': {e}")
        return f"Failed to play album '{album_name}': {e}"

# Returns the current queue showing what's playing now and what's coming up next
def queue():
    try:
        data = sp.queue()
        if not data:
            return "No queue data found."

        formatted = []

        # Currently playing
        current = data.get("currently_playing")
        if current:
            name = current.get("name", "Unknown Song")
            artists = ", ".join(a.get("name", "") for a in current.get("artists", []))
            album = current.get("album", {}).get("name", "Unknown Album")
            formatted.append(f"0. 🎧 CURRENTLY PLAYING: {name} — {artists}\n   Album: {album}")

        # Upcoming tracks
        queue_items = data.get("queue", [])
        if not queue_items:
            formatted.append("No upcoming tracks in queue.")
        else:
            for i, track in enumerate(queue_items, start=1):
                name = track.get("name", "Unknown Song")
                artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
                album = track.get("album", {}).get("name", "Unknown Album")
                formatted.append(f"{i}. {name} — {artists}\n   Album: {album}")

        return "Your Spotify Queue:\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error fetching queue: {e}")
        return "Error retrieving Spotify queue."

# Starts playback on the first available device
def start_playback():
    try:
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        if not devices:
            return "No devices found."
        
        try:
            devices = sp.devices().get("devices", [])
            if not devices:
                print("No devices found.")
                return None
            # Return the ID of the first device
            device_id = devices[0].get("id")
        except Exception as e:
            print(f"Error getting device ID: {e}")
            return None
        
        sp.start_playback(device_id=device_id)    
        #logger.info("Start playback")
        return f"Playback started"
    except SpotifyException as e:
        logger.error(f"Error starting playback: {e}")

# Adjusts Spotify volume either to an absolute level or by a relative change
def volume(volume_percent: int = None, change: int = None):
    try:
        devices = sp.devices().get("devices", [])
        if not devices:
            return {"error": "No devices found"}
        device_id = devices[0]["id"]
        playback = sp.current_playback()
        if not playback:
            return {"error": "No active playback"}
        current_volume = playback["device"].get("volume_percent", 50)
        if change is not None:
            new_volume = max(0, min(100, current_volume + change))
        else:
            new_volume = max(0, min(100, volume_percent))
        sp.volume(new_volume, device_id)
        return f"Volume changed from {current_volume}% to {new_volume}%"
    except Exception as e:
        return {"error": str(e)}

# Transfers to a different device using it's id
def transfer_playback(device_id: str, force_play=True):
    try:
        # Transfer playback to the new device
        sp.transfer_playback(device_id=device_id, force_play=force_play)

        # Get currently active device info
        current_playback = sp.current_playback()
        if current_playback and current_playback.get("device"):
            device = current_playback["device"]
            device_name = device.get("name", "Unknown")
            device_type = device.get("type", "Unknown")
            is_active = device.get("is_active", False)

            device_info = (
                f"Current device details:\n"
                f"Name: {device_name}\n"
                f"Type: {device_type}\n"
                f"Active: {is_active}"
            )
        else:
            device_info = "No active device found after transfer."

        return f"Changed to device with Id: {device_id}\n{device_info}"

    except Exception as e:
        logger.error(f"Error transferring devices: {e}")
        return f"Error transferring devices: {e}"

# Returns a formatted list of all available Spotify devices with their status
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

# Checks if Spotify process is currently running on the system
def is_spotify_running():
    try:
        target = "spotify"

        for process in psutil.process_iter(['name']):
            
            try:
                if target in process.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue    
        return False
    except Exception as e:
        logger.error(f"Error checking if device is running: {e}")
        return f"Error checking running device: {e}"

# Launches Spotify application if it's not already running (detached from script process)
def launch_spotify():
    current_os = platform.system()
    target = "spotify"

    try:
        if current_os == "Windows":
            # On Windows, 'start' can open apps by name
            subprocess.run(["start", f"{target}.exe"], shell=True)
            return "Spotify Opened"
        elif current_os == "Darwin":
            # On Mac, 'open -a' opens applications by name
            subprocess.run(["open", "-a", target])
            return "Spotify Opened"
        elif current_os == "Linux":
            # On Linux, 'xdg-open' is the standard way to open apps/files
            subprocess.run(["xdg-open", target])
            return "Spotify Opened"
        
    except Exception as e:
        print(f"Error opening Spotify: {e}")

# Closes Spotify application gracefully using pkill
def close_spotify():
    current_os = platform.system()
    target = "spotify"
    
    try:
        if current_os == "Windows":
            # /F forces the process to close, /IM specifies the image name
            # We add .exe for Windows just in case
            name = target if target.endswith(".exe") else f"{target}.exe"
            subprocess.run(["taskkill", "/F", "/IM", name], check=True, capture_output=True)
            return("Spotify Closed")
        elif current_os == "Darwin":  # macOS
            # 'pkill' is standard on Mac to terminate by name
            subprocess.run(["pkill", "-x", target], check=True)
            return("Spotify Closed")
        elif current_os == "Linux":
            # 'pkill' or 'killall' works on most Linux distros
            subprocess.run(["pkill", target], check=True)
            return("Spotify Closed")
        print(f"Successfully closed {target}")

    except Exception as e:
        print(f"Error closing Spotify: {e}")

# Get todays date
def get_todays_date():
    try:
        # Get today's date
        today = datetime.today()
        
        # Format the date (customize if needed)
        formatted_date = today.strftime("%Y-%m-%d")
        
        return f"Today's date is {formatted_date}"
    
    except Exception as e:
        logger.error(f"Error getting today's date: {e}")
        return "Error occurred while calculating today's date"