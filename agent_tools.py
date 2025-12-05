from langchain.tools import tool
import os
from dotenv import load_dotenv
from spotify import (add_song_to_queue_by_song_name,
                    add_song_to_queue_by_lyrics, start_playing_song_by_name, start_playing_song_by_lyrics,
                    start_playlist_by_name, pause_music, next_track, previous_track, start_playing_artist,
                    format_artist_albums, start_playing_artist_album, start_playing_album_by_name, 
                    current_user_playing_track, 
                    repeat, shuffle, seek_track, current_user,
                    current_user_followed_artists, current_user_playlists, current_user_recently_played,
                    current_user_saved_albums, current_user_saved_tracks, current_user_top_artists_short_term,
                    current_user_top_tracks, queue, start_playback, volume, transfer_playback, devices,
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

@tool("start_playback", return_direct=False)
def start_playback_tool():
    """Starts or resumes Spotify playback on the first available device."""
    result = start_playback()
    return result if result else "Playback started"

@tool("pause_music", return_direct=False)
def pause_music_tool():
    """Pauses the current Spotify playback."""
    result = pause_music()
    return result if result else "Music paused"

@tool("next_track", return_direct=False)
def next_track_tool():
    """Skips to the next track in the Spotify queue."""
    result = next_track()
    return result if result else "Skipped to next track"

@tool("previous_track", return_direct=False)
def previous_track_tool():
    """Goes back to the previous track in the playback history."""
    result = previous_track()
    return result if result else "Went to previous track"

@tool("repeat", return_direct=False)
def repeat_tool(state: str):
    """Sets the repeat mode for Spotify playback."""
    result = repeat(state)
    return result if result else f"Repeat set to {state}"

@tool("shuffle", return_direct=False)
def shuffle_tool(state: bool):
    """Turns shuffle mode on or off for Spotify playback."""
    result = shuffle(state)
    status = "on" if state else "off"
    return result if result else f"Shuffle turned {status}"

@tool("seek_track", return_direct=False)
def seek_track_tool(position_ms: int):
    """Seeks to a specific position in the currently playing track."""
    result = seek_track(position_ms)
    return result if result else f"Seeked to {position_ms}ms"

@tool("start_playing_artist", return_direct=False)
def start_playing_artist_tool(artist_name: str):
    """Plays a random popular song from the specified artist."""
    result = start_playing_artist(artist_name)
    return result if result else f"Playing music by {artist_name}"

@tool("format_artist_albums", return_direct=False)
def format_artist_albums_tool(artist_name: str):
    """Get all the albums from the specified artist."""
    result = format_artist_albums(artist_name)
    return result if result else f"Albums by {artist_name}"

@tool("start_playing_artist_album", return_direct=False)
def start_playing_artist_album_tool(artist_name: str):
    """Plays a random popular album from the specified artist."""
    result = start_playing_artist_album(artist_name)
    return result if result else f"Playing album by {artist_name}"

@tool("start_playing_album_by_name", return_direct=False)
def start_playing_album_by_name_tool(album_name: str):
    """Searches for a specific album by name and starts playing it immediately."""
    result = start_playing_album_by_name(album_name)
    return result if result else f"Now playing album: {album_name}"

@tool("add_song_to_queue_by_song_name", return_direct=False)
def add_song_to_queue_by_song_name_tool(song_name: str):
    """Finds a song by its name and adds it to the Spotify queue."""
    result = add_song_to_queue_by_song_name(song_name)
    return result if result else f"Added '{song_name}' to queue"

@tool("add_song_to_queue_by_lyrics", return_direct=False)
def add_song_to_queue_by_lyrics_tool(lyrics: str):
    """Finds a song by matching lyrics and adds it to the Spotify queue."""
    result = add_song_to_queue_by_lyrics(lyrics)
    return result if result else f"Added song with lyrics '{lyrics}' to queue"

@tool("start_playing_song_by_name", return_direct=False)
def start_playing_song_by_name_tool(song_name: str):
    """Searches for a specific song by name and starts playing it immediately."""
    result = start_playing_song_by_name(song_name)
    return result if result else f"Now playing: {song_name}"

@tool("start_playing_song_by_lyrics", return_direct=False)
def start_playing_song_by_lyrics_tool(lyrics: str):
    """Finds a song by matching lyrics and starts playing it immediately."""
    result = start_playing_song_by_lyrics(lyrics)
    return result if result else f"Playing song with lyrics: '{lyrics}'"

@tool("start_playlist_by_name", return_direct=False)
def start_playlist_by_name_tool(playlist_name: str):
    """Searches for a playlist and starts playing it on Spotify."""
    result = start_playlist_by_name(playlist_name)
    return result if result else f"Now playing playlist: {playlist_name}"

@tool("queue", return_direct=False)
def queue_tool():
    """Retrieves and displays the current Spotify playback queue."""
    result = queue()
    return result if result else "Queue is empty or unavailable"

@tool("current_user", return_direct=False)
def current_user_tool():
    """Fetches the current Spotify user's profile information."""
    result = current_user()
    return result if result else "Unable to fetch user profile"

@tool("current_user_playing_track", return_direct=False)
def current_user_playing_track_tool():
    """Returns detailed information about the currently playing Spotify track."""
    result = current_user_playing_track()
    return result if result else "No track currently playing"

@tool("current_user_followed_artists", return_direct=False)
def current_user_followed_artists_tool():
    """Gets the complete list of artists the current user follows on Spotify."""
    result = current_user_followed_artists()
    return result if result else "No followed artists found"

@tool("current_user_playlists", return_direct=False)
def current_user_playlists_tool():
    """Lists all Spotify playlists owned or followed by the user."""
    result = current_user_playlists()
    return result if result else "No playlists found"

@tool("current_user_recently_played", return_direct=False)
def current_user_recently_played_tool():
    """Fetches the user's recently played tracks on Spotify."""
    result = current_user_recently_played()
    return result if result else "No recently played tracks found"

@tool("current_user_saved_albums", return_direct=False)
def current_user_saved_albums_tool():
    """Retrieves all albums saved in the user's Spotify library."""
    result = current_user_saved_albums()
    return result if result else "No saved albums found"

@tool("current_user_saved_tracks", return_direct=False)
def current_user_saved_tracks_tool():
    """Gets all tracks saved or liked by the user in their Spotify library."""
    result = current_user_saved_tracks()
    return result if result else "No saved tracks found"

@tool("current_user_top_artists_short_term", return_direct=False)
def current_user_top_artists_short_term_tool():
    """Returns the user's top 20 Spotify artists based on the last 4 weeks of listening."""
    result = current_user_top_artists_short_term()
    return result if result else "No top artists data available"

@tool("current_user_top_tracks", return_direct=False)
def current_user_top_tracks_tool():
    """Returns the user's top 20 most played tracks based on long-term listening history."""
    result = current_user_top_tracks()
    return result if result else "No top tracks data available"

@tool("volume", return_direct=False)
def volume_tool(volume_percent: int = None, change: int = None):
    """Adjusts Spotify volume either to an absolute level or by a relative change."""
    result = volume(volume_percent=volume_percent, change=change)
    if result:
        return result
    elif volume_percent is not None:
        return f"Volume set to {volume_percent}%"
    else:
        return f"Volume adjusted by {change}"

@tool("transfer_playback", return_direct=False)
def transfer_playback_tool(device_id: str, force_play=True):
    """Change playing device."""
    result = transfer_playback(device_id, force_play=True)
    return result if result else f"Transferred playback to device {device_id}"

@tool("devices", return_direct=False)
def devices_tool():
    """Lists all available Spotify playback devices with their status."""
    result = devices()
    return result if result else "No devices found"

@tool("launch_spotify", return_direct=False)
def launch_spotify_tool():
    """Launches the Spotify application if it isn't already running."""
    result = launch_spotify()
    return result if result else "Spotify launched"

@tool("close_spotify", return_direct=False)
def close_spotify_tool():
    """Closes or quits the Spotify application gracefully."""
    result = close_spotify()
    return result if result else "Spotify closed"

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
                        start_playing_album_by_name_tool, start_playback_tool, volume_tool, 
                        transfer_playback_tool, devices_tool,
                        launch_spotify_tool, close_spotify_tool,
                        ]

