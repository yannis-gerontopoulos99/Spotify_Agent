from langchain.tools import tool
import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from spotify import (add_song_to_queue, find_song_by_name, find_song_by_lyrics, add_song_to_queue_by_song_name,
                    add_song_to_queue_by_lyrics, start_playing_song_by_name, start_playing_song_by_lyrics,
                    start_playlist_by_name, pause_music, next_track, previous_track, start_playing_artist,
                    format_artist_albums, start_playing_artist_album, start_playing_album_by_name, 
                    current_user_playing_track, 
                    repeat, shuffle, seek_track, current_user,
                    current_user_followed_artists, current_user_playlists, current_user_recently_played,
                    current_user_saved_albums, current_user_saved_tracks, current_user_top_artists_short_term,
                    current_user_top_tracks, queue, start_playback, volume, devices,
                    is_spotify_running, launch_spotify, close_spotify)

from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()
device_id = os.getenv("DEVICE_ID")

duckduckgo = DuckDuckGoSearchRun()

@tool("web_search", return_direct=False)
def web_search_tool(query: str) -> str:
    """
    Search the web for up-to-date factual information not available in Spotify's API.
    
    Use this when you need:
    - Band member names, biographies, or artist background information
    - Release dates, album details, or music history
    - Song meanings, lyrics explanations, or music trivia
    - Any factual information about artists, songs, or music that Spotify doesn't provide
    
    Args:
        query (str): The search query (e.g., "who are the members of Radiohead")
    
    Returns:
        str: Search results containing the requested information
    """
    results = duckduckgo.run(query)
    return results

@tool("start_playback", return_direct=True)
def start_playback_tool():
    """
    Starts or resumes Spotify playback on the first available device.
    
    Use this when the user says:
    - "play music", "start playing", "resume"
    - "unpause", "continue playing"
    
    This will resume paused playback or start playing on an available device.
    Does NOT require a specific song - just starts/resumes whatever was last playing.
    
    Returns:
        str: Confirmation that playback has started
    """
    return start_playback()

@tool("pause_music", return_direct=True)
def pause_music_tool():
    """
    Pauses the current Spotify playback.
    
    Use this when the user says:
    - "pause", "pause the music"
    - "stop", "stop playing"
    - "hold the music", "hold on"
    
    Returns:
        str: Confirmation that playback is paused
    """
    return pause_music()

@tool("next_track", return_direct=True)
def next_track_tool():
    """
    Skips to the next track in the Spotify queue.
    
    Use this when the user says:
    - "next song", "skip this song"
    - "play the next track", "skip"
    - "next one", "move on"
    
    Returns:
        str: Confirmation that the track was skipped
    """
    return next_track()

@tool("previous_track", return_direct=True)
def previous_track_tool():
    """
    Goes back to the previous track in the playback history.
    
    Use this when the user says:
    - "go back", "previous song"
    - "play the last one again", "previous track"
    - "back", "rewind to the last song"
    
    Returns:
        str: Confirmation that playback returned to the previous track
    """
    return previous_track()

@tool("repeat", return_direct=True)
def repeat_tool(state: str):
    """
    Sets the repeat mode for Spotify playback.
    
    Use this when the user wants to repeat songs.
    
    Parameters:
    - state (str): Must be one of:
        * 'track' - Repeat the current song on loop
        * 'context' - Repeat the entire playlist/album
        * 'off' - Turn off repeat mode
    
    Examples:
    - "repeat this song" → state='track'
    - "repeat the playlist" → state='context'
    - "stop repeating" → state='off'
    - "loop this track" → state='track'
    
    Returns:
        str: Confirmation of the repeat mode setting
    """
    return repeat(state)

@tool("shuffle", return_direct=True)
def shuffle_tool(state: bool):
    """
    Turns shuffle mode on or off for Spotify playback.
    
    Use this when the user wants to randomize or order their music.
    
    Parameters:
    - state (bool): 
        * True - Turn shuffle ON (randomize playback order)
        * False - Turn shuffle OFF (play in original order)
    
    Examples:
    - "shuffle my music" → state=True
    - "turn on shuffle" → state=True
    - "turn off shuffle" → state=False
    - "play in order" → state=False
    
    Returns:
        str: Confirmation of the shuffle mode setting
    """
    return shuffle(state)

@tool("seek_track", return_direct=True)
def seek_track_tool(position_ms: int):
    """
    Seeks to a specific position in the currently playing track.
    
    Use this when the user wants to move to a different timestamp in the song or restart it.
    
    Parameters:
    - position_ms (int): The target position in milliseconds
        * 1 second = 1000 ms
        * 30 seconds = 30000 ms
        * 1 minute = 60000 ms
    
    Examples:
    - "skip ahead 30 seconds" → Calculate current position + 30000 ms
    - "go back 10 seconds" → Calculate current position - 10000 ms
    - "go to 2 minutes" → position_ms=120000
    - "start from the beginning" → position_ms=1
    - "start the song again" → position_ms=1
    - "replay - restart song" → position_ms=1
    
    IMPORTANT: You need to get the current playback position first, then calculate 
    the new position based on the user's request (forward/backward).
    
    Returns:
        str: Confirmation of the new track position
    """
    return seek_track(position_ms)

@tool("start_playing_artist", return_direct=True)
def start_playing_artist_tool(artist_name: str):
    """
    Plays a random popular song from the specified artist.
    
    Use this when the user wants to listen to an artist without specifying a particular song.
    This tool searches for the artist, retrieves their top tracks, and plays one randomly.
    
    Use this for requests like:
    - "play some Drake"
    - "play music by Taylor Swift"
    - "I want to hear The Beatles"
    - "put on some Radiohead"
    
    DO NOT use this if the user specifies a song name - use start_playing_song_by_name instead.
    
    Args:
        artist_name (str): The artist's name (e.g., "Drake", "Taylor Swift", "The Beatles")
    
    Returns:
        str: Confirmation message with the song name that's now playing
    """
    return start_playing_artist(artist_name)

@tool("format_artist_albums", return_direct=True)
def format_artist_albums_tool(artist_name: str):
    """
    Get all the albums from the specified artist.
    
    Use this when the user asks about the albums of a specific artist.
    You can also use this for getting inforamtion only for specific album.
    This tool searches for the artist, retrieves all their albums, and gets information about them such as
    album name, release data, and album type.
    
    Use this for requests like:
    - "what are Drake's albums"
    - "do you know the albums by Taylor Swift"
    
    DO NOT use this if the user specifies an album name to be played - use start_playing_album_by_name instead.
    
    Args:
        artist_name (str): The artist's name (e.g., "Drake", "Taylor Swift", "The Beatles")
    
    Returns:
        str: Confirmation message with all the album names or the specific one requested
    """
    return format_artist_albums(artist_name)

@tool("start_playing_artist_album", return_direct=True)
def start_playing_artist_album_tool(artist_name: str):
    """
    Plays a random popular album from the specified artist.
    
    Use this when the user wants to listen to an artists album without specifying a particular album.
    This tool searches for the artist, retrieves their top albums, and plays one randomly.
    
    Use this for requests like:
    - "play Drakes album"
    - "play an album by Taylor Swift"
    
    DO NOT use this if the user specifies an album name - use start_playing_album_by_name instead.
    
    Args:
        artist_name (str): The artist's name (e.g., "Drake", "Taylor Swift", "The Beatles")
    
    Returns:
        str: Confirmation message with the albums name that's now playing
    """
    return start_playing_artist_album(artist_name)

@tool("start_playing_album_by_name", return_direct=True)
def start_playing_album_by_name_tool(album_name: str):
    """
    Searches for a specific album by name and starts playing it immediately.
    
    Use this when the user wants to play a specific album right now.
    This will interrupt current playback and start the requested album.
    
    Use for requests like:
    - "play [album name]"
    - "play the album [album name]"
    - "I want to hear [album name] album"
    
    Args:
        album_name (str): The name of the album (e.g., "Dangerous Woman", "EVERYONE'S a STAR")
    
    Returns:
        str: Confirmation message that the song is now playing
    """
    return start_playing_album_by_name(album_name)

#@tool("add_song_to_queue", return_direct=True)
#def add_song_to_queue_tool(song_uri: str):
#    """
#    Adds a specific song to the Spotify queue using its Spotify URI.
#
#    Use this when the user provides a Spotify link or URI.
#    Example URI: "spotify:track:4uLU6hMCjMI75M1A2tKUQC"
#    """
#    return add_song_to_queue(song_uri)

#@tool("find_song_by_name", return_direct=True)
#def find_song_by_name_tool(name: str):
#    """
#    Searches for a song on Spotify by name and returns its URI.
#
#    Use when the user asks for a song title, e.g., "find 'Bohemian Rhapsody'".
#    """
#    return find_song_by_name(name)

#@tool("find_song_by_lyrics", return_direct=True)
#def find_song_by_lyrics_tool(lyrics: str):
#    """
#    Searches Spotify for a song based on its lyrics.
#
#    Use when the user provides a lyric fragment to identify a song.
#    """
#    return find_song_by_lyrics(lyrics)

@tool("add_song_to_queue_by_song_name", return_direct=True)
def add_song_to_queue_by_song_name_tool(song_name: str):
    """
    Finds a song by its name and adds it to the Spotify queue.
    
    Use this when the user wants to queue a song without immediately playing it.
    The song will be added to play after the current track and other queued songs.
    
    Use for requests like:
    - "add [song name] to my queue"
    - "queue up [song name]"
    - "add [song name] to play later"
    - "put [song name] in the queue"
    
    Args:
        song_name (str): The name of the song to queue (e.g., "Bohemian Rhapsody")
    
    Returns:
        str: Confirmation message with the song name and artist that was added to queue
    """
    return add_song_to_queue_by_song_name(song_name)

@tool("add_song_to_queue_by_lyrics", return_direct=True)
def add_song_to_queue_by_lyrics_tool(lyrics: str):
    """
    Finds a song by matching lyrics and adds it to the Spotify queue.
    
    Use this when the user remembers part of a song's lyrics but not the title.
    The song will be queued, not played immediately.
    
    Use for requests like:
    - "queue the song that goes '[lyrics]'"
    - "add that song with the lyrics '[lyrics]' to my queue"
    - "queue up the song that says '[lyrics]'"
    
    Args:
        lyrics (str): A memorable phrase or line from the song (e.g., "is this the real life")
    
    Returns:
        str: Confirmation message with the song name and artist that was added to queue
    """
    return add_song_to_queue_by_lyrics(lyrics)

@tool("start_playing_song_by_name", return_direct=True)
def start_playing_song_by_name_tool(song_name: str):
    """
    Searches for a specific song by name and starts playing it immediately.
    
    Use this when the user wants to play a specific song right now.
    This will interrupt current playback and start the requested song.
    
    Use for requests like:
    - "play [song name]"
    - "play the song [song name]"
    - "I want to hear [song name]"
    - "put on [song name]"
    
    Args:
        song_name (str): The name of the song (e.g., "Imagine", "Blinding Lights")
    
    Returns:
        str: Confirmation message that the song is now playing
    """
    return start_playing_song_by_name(song_name)

@tool("start_playing_song_by_lyrics", return_direct=True)
def start_playing_song_by_lyrics_tool(lyrics: str):
    """
    Finds a song by matching lyrics and starts playing it immediately.
    
    Use this when the user remembers lyrics but not the song title and wants to play it now.
    This will interrupt current playback.
    
    Use for requests like:
    - "play the song that goes '[lyrics]'"
    - "play that song with '[lyrics]' in it"
    - "I want to hear the song that says '[lyrics]'"
    
    Args:
        lyrics (str): A memorable phrase or line from the song (e.g., "sweet dreams are made of this")
    
    Returns:
        str: Confirmation message that the song is now playing
    """
    return start_playing_song_by_lyrics(lyrics)

@tool("start_playlist_by_name", return_direct=True)
def start_playlist_by_name_tool(playlist_name: str):
    """
    Searches for a playlist and starts playing it on Spotify.
    
    This tool searches for playlists by name and tries multiple query variations:
    - Exact name match
    - "[name] playlist"
    - "This Is [artist name]" (Spotify's official artist playlists)
    - "[name] Mix"
    
    Use for requests like:
    - "play my [playlist name] playlist"
    - "play a [genre] playlist" (e.g., "play a jazz playlist")
    - "play a playlist with [artist name]"
    - "play the [mood] playlist" (e.g., "play the chill playlist")
    
    Args:
        playlist_name (str): The playlist name, genre, artist name, or mood (e.g., "Discover Weekly", "jazz", "Beyoncé")
    
    Returns:
        str: Confirmation message with the playlist name, owner, and track count
    """
    return start_playlist_by_name(playlist_name)

@tool("queue", return_direct=True)
def queue_tool():
    """
    Retrieves and displays the current Spotify playback queue.
    
    Shows what's currently playing (marked as track 0) and all upcoming queued tracks.
    Each track includes song name, artist(s), and album information.
    
    Use when the user asks:
    - "what's in my queue"
    - "what's playing next"
    - "show me my queue"
    - "what songs are coming up"
    - "what's queued"
    
    Returns:
        str: Formatted list showing currently playing track and all queued tracks
    """
    return queue()

@tool("current_user", return_direct=True)
def current_user_tool():
    """
    Fetches the current Spotify user's profile information.
    
    Returns user details including display name, user ID, account type, 
    follower count, and Spotify profile URL.
    
    Use when the user asks:
    - "what's my Spotify username"
    - "show me my profile"
    - "what's my user info"
    - "who am I logged in as"
    
    Returns:
        str: Formatted user profile information
    """
    return current_user()

@tool("current_user_playing_track", return_direct=True)
def current_user_playing_track_tool():
    """
    Returns detailed information about the currently playing Spotify track.
    
    Provides song name, artist(s), album name, release date, and Spotify URL.
    
    Use when the user asks:
    - "what's playing", "what song is this"
    - "what am I listening to"
    - "who's this by", "who sings this"
    - "what's the name of this song"
    - "when was this released"
    
    Returns:
        str: Formatted track details including song, artist, album, release date, and URL
    """
    return current_user_playing_track()

@tool("current_user_followed_artists", return_direct=True)
def current_user_followed_artists_tool():
    """
    Gets the complete list of artists the current user follows on Spotify.
    
    Returns all followed artists with their names, IDs, and follower counts.
    Uses pagination to retrieve the complete list.
    
    Use when the user asks:
    - "who do I follow"
    - "show me my followed artists"
    - "what artists am I following"
    - "list my artists"
    
    Returns:
        str: Formatted list of all followed artists with details
    """
    return current_user_followed_artists()

@tool("current_user_playlists", return_direct=True)
def current_user_playlists_tool():
    """
    Lists all Spotify playlists owned or followed by the user.
    
    Returns playlist names, IDs, track counts, and owner information.
    Includes both user-created playlists and playlists they follow.
    
    Use when the user asks:
    - "show me my playlists"
    - "what playlists do I have"
    - "list my playlists"
    - "what playlists am I following"
    
    Returns:
        str: Formatted list of all playlists with names, owners, and track counts
    """
    return current_user_playlists()

@tool("current_user_recently_played", return_direct=True)
def current_user_recently_played_tool():
    """
    Fetches the user's recently played tracks on Spotify.
    
    Returns the last 10 tracks played with song names, artists, albums, 
    timestamps of when they were played, and Spotify URLs.
    
    Use when the user asks:
    - "what did I listen to recently"
    - "show me my recent tracks"
    - "what have I been playing"
    - "what was I listening to earlier"
    
    Returns:
        str: Formatted list of recently played tracks with timestamps
    """
    return current_user_recently_played()

@tool("current_user_saved_albums", return_direct=True)
def current_user_saved_albums_tool():
    """
    Retrieves all albums saved in the user's Spotify library.
    
    Returns album names, artists, track counts, release dates, IDs, and Spotify URLs.
    Uses pagination to fetch the complete collection.
    
    Use when the user asks:
    - "show me my saved albums"
    - "what albums do I have"
    - "list my albums"
    - "show me my album collection"
    
    Returns:
        str: Formatted list of all saved albums with complete details
    """
    return current_user_saved_albums()

@tool("current_user_saved_tracks", return_direct=True)
def current_user_saved_tracks_tool():
    """
    Gets all tracks saved or liked by the user in their Spotify library.
    
    Returns song names, artists, albums, release dates, IDs, and Spotify URLs.
    Uses pagination to retrieve the complete collection (starts with first 20).
    
    Use when the user asks:
    - "show me my liked songs"
    - "what songs do I have saved"
    - "list my favorite tracks"
    - "show me my saved music"
    
    Returns:
        str: Formatted list of all saved tracks with complete details
    """
    return current_user_saved_tracks()

@tool("current_user_top_artists_short_term", return_direct=True)
def current_user_top_artists_short_term_tool():
    """
    Returns the user's top 20 Spotify artists based on the last 4 weeks of listening.
    
    Provides artist names, follower counts, popularity scores, genres, and Spotify URLs.
    This reflects recent listening trends and newly discovered artists.
    
    Use when the user asks:
    - "who are my top artists lately"
    - "what artists have I been listening to recently"
    - "show me my recent top artists"
    - "who have I been playing the most this month"
    
    Returns:
        str: Formatted list of top 20 artists with popularity metrics and genres
    """
    return current_user_top_artists_short_term()

@tool("current_user_top_tracks", return_direct=True)
def current_user_top_tracks_tool():
    """
    Returns the user's top 20 most played tracks based on long-term listening history.
    
    Provides song names, artists, albums, popularity scores, IDs, and Spotify URLs.
    This reflects the user's all-time favorite songs over several years.
    
    Use when the user asks:
    - "what are my top songs"
    - "show me my most played tracks"
    - "what's my favorite music"
    - "what do I listen to the most"
    
    Returns:
        str: Formatted list of top 20 tracks with complete details
    """
    return current_user_top_tracks()

@tool("volume", return_direct=True)
def volume_tool(volume_percent: int = None, change: int = None):
    """
    Adjusts Spotify volume either to an absolute level or by a relative change.
    
    CRITICAL: Use ONLY ONE parameter at a time, never both together.
    
    Parameters:
    - volume_percent (int): Set volume to exact percentage (0-100). Use when user specifies 
    a number like "set volume to 50" or "make it 75%"
    
    - change (int): Adjust volume relative to current level. Use for vague requests:
        * "a bit/slightly/a little higher/lower" → ±5
        * "higher/up/increase/louder/raise" → +10
        * "lower/down/decrease/quieter/reduce" → -10
        * "much higher/lower/way up/way down" → ±20
    
    Examples:
    - "set volume to 50" → volume_percent=50, change=None
    - "turn it up" → volume_percent=None, change=10
    - "a little lower" → volume_percent=None, change=-5
    - "much louder" → volume_percent=None, change=20
    - "volume 80%" → volume_percent=80, change=None
    
    IMPORTANT: For relative changes, you don't need to know the current volume - 
    the function automatically calculates it and applies the change.
    
    Returns:
        str: Confirmation showing the volume change (e.g., "Volume changed from 45% to 55%")
    """
    return volume(volume_percent=volume_percent, change=change)

@tool("devices", return_direct=True)
def devices_tool():
    """
    Lists all available Spotify playback devices with their status.
    
    Shows device names, IDs, types (computer, smartphone, speaker), and whether 
    they're currently active or inactive.
    
    Use when the user asks:
    - "what devices are available"
    - "where can I play music"
    - "show me my devices"
    - "what devices are connected to Spotify"
    
    Returns:
        str: Formatted list of all devices with names, types, IDs, and active status
    """
    return devices()

@tool("is_spotify_running", return_direct=True)
def is_spotify_running_tool():
    """
    Checks if the Spotify application is currently running on the system.
    
    Use this to verify Spotify's status before attempting other operations.
    
    Use when the user asks:
    - "is Spotify running"
    - "is Spotify open"
    - "check if Spotify is on"
    
    Returns:
        bool: True if Spotify is running, False if not
    """
    return is_spotify_running()

@tool("launch_spotify", return_direct=True)
def launch_spotify_tool():
    """
    Launches the Spotify application if it isn't already running.
    
    Opens Spotify as a detached process that continues running after the script ends.
    If Spotify is already running, returns a message saying so.
    
    Use when the user says:
    - "open Spotify"
    - "launch Spotify"
    - "start Spotify"
    - "turn on Spotify"
    
    Returns:
        str: Confirmation that Spotify launched, or notification that it's already running
    """
    return launch_spotify()

@tool("close_spotify", return_direct=True)
def close_spotify_tool():
    """
    Closes or quits the Spotify application gracefully.
    
    Terminates the Spotify process using pkill. This will stop all playback.
    
    Use when the user says:
    - "close Spotify"
    - "quit Spotify"
    - "shut down Spotify"
    - "exit Spotify"
    
    Returns:
        str: Confirmation that Spotify was closed
    """
    return close_spotify()

# A helper mapping and a tool to execute multi-step plans (JSON)
tool_function_map = {
    "web_search": web_search_tool,
    "start_playback": start_playback_tool,
    "pause_music": pause_music_tool,
    "next_track": next_track_tool,
    "previous_track": previous_track_tool,
    "repeat": repeat_tool,
    "shuffle": shuffle_tool,
    "seek_track": seek_track_tool,
    "start_playing_artist": start_playing_artist_tool,
    "add_song_to_queue_by_song_name": add_song_to_queue_by_song_name_tool,
    "add_song_to_queue_by_lyrics": add_song_to_queue_by_lyrics_tool,
    "start_playing_song_by_name": start_playing_song_by_name_tool,
    "start_playing_song_by_lyrics": start_playing_song_by_lyrics_tool,
    "start_playlist_by_name": start_playlist_by_name_tool,
    "format_artist_albums": format_artist_albums_tool,
    "start_playing_artist_album": start_playing_artist_album_tool,
    "start_playing_album_by_name": start_playing_album_by_name_tool,
    "queue": queue_tool,
    "current_user": current_user_tool,
    "current_user_playing_track": current_user_playing_track_tool,
    "current_user_followed_artists": current_user_followed_artists_tool,
    "current_user_playlists": current_user_playlists_tool,
    "current_user_recently_played": current_user_recently_played_tool,
    "current_user_saved_albums": current_user_saved_albums_tool,
    "current_user_saved_tracks": current_user_saved_tracks_tool,
    "current_user_top_artists_short_term": current_user_top_artists_short_term_tool,
    "current_user_top_tracks": current_user_top_tracks_tool,
    "volume": volume_tool,
    "devices": devices_tool,
    "is_spotify_running": is_spotify_running_tool,
    "launch_spotify": launch_spotify_tool,
    "close_spotify": close_spotify_tool,
}

@tool("execute_plan", return_direct=True)
def execute_plan_tool(plan: Any) -> str:
    """
    Execute a plan consisting of a JSON array of steps:
        [ {"tool": "<tool_name>", "args": { ... }}, ... ]
    Executes steps sequentially, continues on error, and returns a combined summary.
    """
    try:
        # Accept either a JSON string or Python list
        if isinstance(plan, str):
            steps = json.loads(plan)
        else:
            steps = plan

        if not isinstance(steps, list):
            return "Plan must be a JSON list of steps."

        # Safety: limit steps to avoid runaway plans
        MAX_STEPS = 20
        if len(steps) > MAX_STEPS:
            return f"Plan too long ({len(steps)} steps). Max allowed is {MAX_STEPS}."

        results: List[str] = []
        for i, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                results.append(f"Step {i}: invalid step (not an object).")
                continue

            tool_name = step.get("tool")
            args = step.get("args", {}) or {}

            fn = tool_function_map.get(tool_name)
            if fn is None:
                results.append(f"Step {i}: tool not found: {tool_name}")
                continue

            try:
                # Prefer kwargs; fall back to single-arg call if args is not a dict
                if isinstance(args, dict):
                    res = fn(**args)
                elif args is None:
                    res = fn()
                else:
                    res = fn(args)
                results.append(f"Step {i} ({tool_name}): {res}")
            except Exception as e:
                results.append(f"Step {i} ({tool_name}) failed: {e}")

        return "Plan executed:\n" + "\n".join(results)

    except json.JSONDecodeError:
        return "Invalid JSON plan."
    except Exception as e:
        return f"Error executing plan: {e}"

spotify_agent_tools = [web_search_tool, add_song_to_queue_by_song_name_tool, add_song_to_queue_by_lyrics_tool,
                        start_playing_song_by_name_tool, start_playing_song_by_lyrics_tool,
                        start_playlist_by_name_tool, pause_music_tool,
                        next_track_tool, previous_track_tool, current_user_playing_track_tool,
                        repeat_tool, shuffle_tool, seek_track_tool, current_user_tool,
                        current_user_followed_artists_tool, current_user_playlists_tool,
                        current_user_recently_played_tool, current_user_saved_albums_tool,
                        current_user_saved_tracks_tool, current_user_top_artists_short_term_tool,
                        current_user_top_tracks_tool, queue_tool, start_playing_artist_tool,
                        format_artist_albums_tool, start_playing_artist_album_tool, 
                        start_playing_album_by_name_tool, start_playback_tool, volume_tool, devices_tool,
                        is_spotify_running_tool, launch_spotify_tool, close_spotify_tool,
                        execute_plan_tool]
