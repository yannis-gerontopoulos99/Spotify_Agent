import subprocess
import os
import signal
import time

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
