from langchain.tools import tool
import os
from dotenv import load_dotenv
from spotify import (add_song_to_queue, find_song_by_name, find_song_by_lyrics, add_song_to_queue_by_song_name,
                    add_song_to_queue_by_lyrics, start_playing_song_by_name, start_playing_song_by_lyrics,
                    start_playlist_by_name, pause_music, next_track, previous_track, start_playing_artist,
                    current_user_playing_track, repeat, shuffle, seek_track, current_user,
                    current_user_followed_artists, current_user_playlists, current_user_recently_played,
                    current_user_saved_albums, current_user_saved_tracks, current_user_top_artists,
                    current_user_top_tracks, queue, start_playback, devices)

from spotify_launcher import (is_spotify_running, launch_spotify, close_spotify)
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()
device_id = os.getenv("DEVICE_ID")

duckduckgo = DuckDuckGoSearchRun()

@tool("web_search", return_direct=False)
def web_search_tool(query: str) -> str:
    """
    Search the web for up-to-date factual information.
    Useful for retrieving band member names, biographies, or background info
    that Spotify's API doesn't include.
    """
    results = duckduckgo.run(query)
    return results

@tool("start_playback", return_direct=True)
def start_playback_tool(device_id: str = device_id):
    """
    Starts or resumes Spotify playback on the user's active device.

    Use this tool when the user requests to play or resume music or podcasts.
    If no device_id is provided, the default active device will be used.

    Args:
        device_id (str, optional): Spotify device ID to start playback on.

    Returns:
        str: Confirmation that playback has started.
    """
    return start_playback(device_id)

@tool("pause_music", return_direct=True)
def pause_music_tool():
    """
    Pauses the current Spotify playback.

    Use this tool when the user says things like "pause", "stop", or "hold the music".
    """
    return pause_music()

@tool("next_track", return_direct=True)
def next_track_tool():
    """
    Skips to the next track in the Spotify queue.

    Use when the user says "next song", "skip", or "play the next track".
    """
    return next_track()

@tool("previous_track", return_direct=True)
def previous_track_tool():
    """
    Goes back to the previous Spotify track.

    Use when the user says "go back", "previous song", or "play the last one again".
    """
    return previous_track()

@tool("repeat", return_direct=True)
def repeat_tool(state: str):
    """
    Sets the repeat mode for Spotify playback.

    Use when the user requests to repeat a song or playlist.
    Valid options for 'state' are:
        - 'track': repeat the current song
        - 'context': repeat the whole playlist/album
        - 'off': turn off repeat
    """
    return repeat(state)

@tool("shuffle", return_direct=True)
def shuffle_tool(state: bool):
    """
    Turns shuffle mode on or off for Spotify playback.

    Use when the user says "shuffle my music" or "turn off shuffle".
    """
    return shuffle(state)

@tool("seek_track", return_direct=True)
def seek_track_tool(position_ms: int):
    """
    Seeks to a specific position in the currently playing track.

    Use when the user says things like "fast-forward 30 seconds" or "go back 10 seconds".
    The position is provided in milliseconds.
    """
    return seek_track(position_ms)

@tool("start_playing_artist", return_direct=True)
def start_playing_artist_tool(artist_name: str):
    """
    Starts playing a random popular song from the given artist on Spotify.

    Use this when the user requests to play music by a specific artist 
    without naming a particular song or playlist.

    Args:
        artist_name (str): The artist's name (e.g., "Drake", "Taylor Swift").

    Returns:
        str: Confirmation message that a random song from the artist is playing.
    """
    return start_playing_artist(artist_name)

@tool("add_song_to_queue", return_direct=True)
def add_song_to_queue_tool(song_uri: str):
    """
    Adds a specific song to the Spotify queue using its Spotify URI.

    Use this when the user provides a Spotify link or URI.
    Example URI: "spotify:track:4uLU6hMCjMI75M1A2tKUQC"
    """
    return add_song_to_queue(song_uri)

@tool("add_song_to_queue_by_song_name", return_direct=True)
def add_song_to_queue_by_song_name_tool(song_name: str):
    """
    Finds a song by name and adds it to the Spotify queue.

    Use when the user says "add [song name] to my queue".
    """
    return add_song_to_queue_by_song_name(song_name)

@tool("add_song_to_queue_by_lyrics", return_direct=True)
def add_song_to_queue_by_lyrics_tool(lyrics: str):
    """
    Finds a song by its lyrics and adds it to the Spotify queue.

    Use when the user remembers part of a song's lyrics and wants it queued.
    """
    return add_song_to_queue_by_lyrics(lyrics)

@tool("find_song_by_name", return_direct=True)
def find_song_by_name_tool(name: str):
    """
    Searches for a song on Spotify by name and returns its URI.

    Use when the user asks for a song title, e.g., "find 'Bohemian Rhapsody'".
    """
    return find_song_by_name(name)

@tool("find_song_by_lyrics", return_direct=True)
def find_song_by_lyrics_tool(lyrics: str):
    """
    Searches Spotify for a song based on its lyrics.

    Use when the user provides a lyric fragment to identify a song.
    """
    return find_song_by_lyrics(lyrics)

@tool("start_playing_song_by_name", return_direct=True)
def start_playing_song_by_name_tool(song_name: str):
    """
    Starts playing a specific song on Spotify by its name.

    Use when the user says "play [song name]".
    """
    return start_playing_song_by_name(song_name)

@tool("start_playing_song_by_lyrics", return_direct=True)
def start_playing_song_by_lyrics_tool(lyrics: str):
    """
    Starts playing a Spotify song found by matching given lyrics.

    Use when the user recalls lyrics but not the song title.
    """
    return start_playing_song_by_lyrics(lyrics)

@tool("start_playlist_by_name", return_direct=True)
def start_playlist_by_name_tool(playlist_name: str):
    """
    Starts playing a Spotify playlist by its name.

    Use when the user says "play my [playlist name] playlist".
    """
    return start_playlist_by_name(playlist_name)

@tool("queue", return_direct=True)
def queue_tool():
    """
    Retrieves the current Spotify playback queue.

    Use when the user asks "what's next" or "show me my queue".
    """
    return queue()

@tool("current_user", return_direct=True)
def current_user_tool():
    """Fetches the current Spotify user’s profile information."""
    return current_user()

@tool("current_user_playing_track", return_direct=True)
def current_user_playing_track_tool():
    """
    Returns details about the currently playing Spotify track.

    Use when the user asks "what’s playing" or "what song is this?".
    """
    return current_user_playing_track()

@tool("current_user_followed_artists", return_direct=True)
def current_user_followed_artists_tool():
    """Gets the list of artists followed by the current user."""
    return current_user_followed_artists()

@tool("current_user_playlists", return_direct=True)
def current_user_playlists_tool():
    """Lists all Spotify playlists owned or followed by the user."""
    return current_user_playlists()

@tool("current_user_recently_played", return_direct=True)
def current_user_recently_played_tool():
    """Fetches the user's recently played tracks on Spotify."""
    return current_user_recently_played()

@tool("current_user_saved_albums", return_direct=True)
def current_user_saved_albums_tool():
    """Retrieves the user's saved albums from Spotify."""
    return current_user_saved_albums()

@tool("current_user_saved_tracks", return_direct=True)
def current_user_saved_tracks_tool():
    """Gets the user's saved or liked tracks."""
    return current_user_saved_tracks()

@tool("current_user_top_artists", return_direct=True)
def current_user_top_artists_tool():
    """Returns the user's top Spotify artists based on listening history."""
    return current_user_top_artists()

@tool("current_user_top_tracks", return_direct=True)
def current_user_top_tracks_tool():
    """Returns the user's most played tracks on Spotify."""
    return current_user_top_tracks()

@tool("devices", return_direct=True)
def devices_tool():
    """
    Lists all available Spotify playback devices.
    Use when the user asks "what devices are connected" or "where can I play music".
    """
    return devices()

@tool("is_spotify_running", return_direct=True)
def is_spotify_running_tool():
    """Checks if the Spotify application is currently running on the system."""
    return is_spotify_running()

@tool("launch_spotify", return_direct=True)
def launch_spotify_tool():
    """Launches the Spotify application if it isn’t already running."""
    return launch_spotify()

@tool("close_spotify", return_direct=True)
def close_spotify_tool():
    """Closes or quits the Spotify application."""
    return close_spotify()


#@tool("start_music", return_direct=True)
#def start_music_tool(playlist_name: str):
#    """Start Spotify playback."""
#    return start_music(playlist_name)

#@tool("currently_playing", return_direct=True)
#def currently_playing_tool():
#    """Current Spotify track information."""
#    return currently_playing()

#@tool("recommendations", return_direct=True)
#def recommendations_tool(seed_genres: list):
#    """Get user recommendations."""
#    return recommendations(seed_genres)

spotify_agent_tools = [web_search_tool, add_song_to_queue_tool, find_song_by_name_tool, find_song_by_lyrics_tool,
                        add_song_to_queue_by_song_name_tool, add_song_to_queue_by_lyrics_tool,
                        start_playing_song_by_name_tool, start_playing_song_by_lyrics_tool,
                        start_playlist_by_name_tool, pause_music_tool,
                        next_track_tool, previous_track_tool, current_user_playing_track_tool,
                        repeat_tool, shuffle_tool, seek_track_tool, current_user_tool,
                        current_user_followed_artists_tool, current_user_playlists_tool,
                        current_user_recently_played_tool, current_user_saved_albums_tool,
                        current_user_saved_tracks_tool, current_user_top_artists_tool,
                        current_user_top_tracks_tool, queue_tool, start_playing_artist_tool,
                        start_playback_tool, devices_tool,
                        is_spotify_running_tool, launch_spotify_tool, close_spotify_tool]
