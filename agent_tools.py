from langchain.tools import tool
from spotify import (add_song_to_queue, find_song_by_name, find_song_by_lyrics, add_song_to_queue_by_song_name,
                    add_song_to_queue_by_lyrics, start_playing_song_by_name, start_playing_song_by_lyrics,
                    start_playlist_by_name, start_music, pause_music, next_track, previous_track,
                    currently_playing, repeat, shuffle, seek_track, current_user)

@tool("add_song_to_queue", return_direct=True)
def add_song_to_queue_tool(song_uri: str):
    """Add a song to the Spotify queue using its URI."""
    return add_song_to_queue(song_uri)

@tool("find_song_by_name", return_direct=True)
def find_song_by_name_tool(name: str):
    """Find a song's Spotify URI by name."""
    return find_song_by_name(name)

@tool("find_song_by_lyrics", return_direct=True)
def find_song_by_lyrics_tool(lyrics: str):
    """Find a song's Spotify URI by lyrics."""
    return find_song_by_lyrics(lyrics)

@tool("add_song_to_queue_by_song_name", return_direct=True)
def add_song_to_queue_by_song_name_tool(song_name: str):
    """Add a song to queue by song name."""
    return add_song_to_queue_by_song_name(song_name)

@tool("add_song_to_queue_by_lyrics", return_direct=True)
def add_song_to_queue_by_lyrics_tool(lyrics: str):
    """Add a song to queue by song lyrics."""
    return add_song_to_queue_by_lyrics(lyrics)

@tool("start_playing_song_by_name", return_direct=True)
def start_playing_song_by_name_tool(song_name: str):
    """Start playing a Spotify song by its name."""
    return start_playing_song_by_name(song_name)

@tool("start_playing_song_by_lyrics", return_direct=True)
def start_playing_song_by_lyrics_tool(lyrics: str):
    """Start playing a Spotify song by its lyrics."""
    return start_playing_song_by_lyrics(lyrics)

@tool("start_playlist_by_name", return_direct=True)
def start_playlist_by_name_tool(playlist_name: str):
    """Start playing a Spotify song by its lyrics."""
    return start_playlist_by_name(playlist_name)

@tool("start_music", return_direct=True)
def start_music_tool(playlist_name: str):
    """Start Spotify playback."""
    return start_music(playlist_name)

@tool("pause_music", return_direct=True)
def pause_music_tool():
    """Pause Spotify playback."""
    return pause_music()

@tool("next_track", return_direct=True)
def next_track_tool():
    """Next Spotify track."""
    return next_track()

@tool("previous_track", return_direct=True)
def previous_track_tool():
    """Previous Spotify track."""
    return previous_track()

@tool("currently_playing", return_direct=True)
def currently_playing_tool():
    """Current Spotify track information."""
    return currently_playing()

@tool("repeat", return_direct=True)
def repeat_tool(state: str):
    """Repeat current song, all songs or turn off repeat Spotify track.
    If the state=track then the current song will only be repeated.
    If the state =context then all songs will be repeated.
    if the state is=off the repeat is turned off."""
    return repeat(state)

@tool("shuffle", return_direct=True)
def shuffle_tool(state: bool):
    """Shuffle or turn off shuffle tracks."""
    return shuffle(state)

@tool("seek_track", return_direct=True)
def seek_track_tool(position_ms: int):
    """Fastforward or backwards the current track using miliseconds as input."""
    return seek_track(position_ms)

@tool("current_user", return_direct=True)
def current_user_tool():
    """SGet current Spotify user information."""
    return current_user()

spotify_agent_tools = [add_song_to_queue_tool, find_song_by_name_tool, find_song_by_lyrics_tool,
                        add_song_to_queue_by_song_name_tool, add_song_to_queue_by_lyrics_tool,
                        start_playing_song_by_name_tool, start_playing_song_by_lyrics_tool,
                        start_playlist_by_name_tool, start_music_tool, pause_music_tool,
                        next_track_tool, previous_track_tool, currently_playing_tool,
                        repeat_tool, shuffle_tool, seek_track_tool, current_user_tool]


