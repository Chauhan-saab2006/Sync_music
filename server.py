# server.py — System audio capture + WS stream + HTTP UI (multi-client safe)
import socket, sys, asyncio, queue as q_module
import numpy as np
from threading import Thread
from flask import Flask, send_from_directory
import sounddevice as sd
import websockets
import time
import struct

SAMPLE_RATE = 44100
CHANNELS    = 2
BLOCK       = 1024
PORT_HTTP   = 5000
PORT_WS     = 8765

# ------------------ HTTP SERVER ------------------
app = Flask(__name__)
@app.route('/')
def index():
    return send_from_directory('.', 'client.html')

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

HOST = get_ip()

# ------------------ AUDIO DEVICE PICK ------------------
audio_queue = q_module.Queue(maxsize=100)
captured_channels = CHANNELS

def audio_callback(indata, frames, time_info, status):
    capture_time = time.time()
    try:
        audio_queue.put_nowait((indata.copy(), capture_time))
    except q_module.Full:
        pass  # Drop frames if the processing loop is too slow

def list_devs():
    devs = sd.query_devices()
    print("\n--- Devices ---")
    for i, d in enumerate(devs):
        print(i, d['name'], "| out:", d['max_output_channels'], "in:", d['max_input_channels'])
    return devs

def try_wasapi(idx):
    dev_info = sd.query_devices(idx)
    # Try the device's native channel count as well as 2 and 1
    for ch in sorted({dev_info['max_output_channels'], 2, 1}, reverse=True):
        if ch <= 0:
            continue
        try:
            print(f"  WASAPI loopback dev={idx} ch={ch}")
            try:
                ws_settings = sd.WasapiSettings(loopback=True)
            except Exception:
                ws_settings = None
            s = sd.InputStream(
                device=idx, samplerate=SAMPLE_RATE,
                channels=ch, blocksize=BLOCK,
                dtype="int16", extra_settings=ws_settings,
                callback=audio_callback
            )
            s.start()
            print(f"  WASAPI loopback OK dev={idx} ({dev_info['name']}) ch={ch}")
            return s, ch
        except Exception as e:
            print(f"  failed ch={ch}: {e}")
    return None, None

def try_input_device(idx, dev_info):
    ch = min(dev_info['max_input_channels'], CHANNELS)
    if ch <= 0:
        return None, None
    try:
        print(f"  Input dev={idx} ({dev_info['name']}) ch={ch}")
        s = sd.InputStream(
            device=idx, samplerate=SAMPLE_RATE,
            channels=ch, blocksize=BLOCK,
            dtype="int16", callback=audio_callback
        )
        s.start()
        print(f"  Input OK dev={idx}")
        return s, ch
    except Exception as e:
        print(f"  failed: {e}")
        return None, None

devs = list_devs()

# 1. Try WASAPI loopback on every output device
stream = None
print("\n--- Trying WASAPI loopback ---")
for idx, d in enumerate(devs):
    if d['max_output_channels'] > 0:
        stream, captured_channels = try_wasapi(idx)
        if stream:
            break

# 2. Prefer Stereo Mix by name, then fall back to any input device
if not stream:
    print("\nLoopback failed → trying input devices (Stereo Mix preferred)")
    # Sort: explicit "stereo mix" first
    input_devs = sorted(
        [(i, d) for i, d in enumerate(devs) if d['max_input_channels'] > 0],
        key=lambda x: (0 if "stereo mix" in x[1]['name'].lower() else 1)
    )
    for idx, d in input_devs:
        stream, captured_channels = try_input_device(idx, d)
        if stream:
            break

if not stream:
    print("No audio source found. Enable Stereo Mix or WASAPI loopback in Windows sound.")
    sys.exit(1)

print(f"\nCapturing with {captured_channels} channel(s) at {SAMPLE_RATE} Hz")

# ------------------ MULTI-CLIENT WS STREAM ------------------
clients = set()

async def audio_broadcast():
    """Dequeue captured audio frames and broadcast to all connected clients."""
    loop = asyncio.get_event_loop()
    while True:
        # get() blocks until a frame arrives — run in executor to keep event loop free
        frames, capture_time = await loop.run_in_executor(None, audio_queue.get)

        # If mono, duplicate to stereo so client always receives 2-channel data
        if captured_channels == 1:
            frames = np.repeat(frames, 2, axis=1)

        raw = frames.tobytes()
        packet = struct.pack('<d', capture_time) + raw

        if clients:
            dead = set()
            
            async def send_to_client(ws):
                try:
                    await ws.send(packet)
                except Exception:
                    dead.add(ws)
            
            await asyncio.gather(*(send_to_client(ws) for ws in list(clients)))
            
            clients.difference_update(dead)

async def ws_handler(websocket, *args, **kwargs):
    """Client connects – add to client set, keep alive until disconnect."""
    clients.add(websocket)
    print("Client connected:", websocket.remote_address)
    try:
        async for message in websocket:
            if isinstance(message, str) and message.startswith("ping:"):
                # Handle time sync ping
                parts = message.split(":")
                if len(parts) >= 2:
                    client_ts = parts[1]
                    server_ts = time.time() * 1000 # Send back milliseconds
                    await websocket.send(f"pong:{client_ts}:{server_ts}")
    except Exception:
        pass
    print("Client disconnected:", websocket.remote_address)
    clients.discard(websocket)

async def ws_main():
    print(f"WS: ws://{HOST}:{PORT_WS}")
    server = websockets.serve(ws_handler, "0.0.0.0", PORT_WS, max_size=None)
    await asyncio.gather(server, audio_broadcast())

def http_start():
    print(f"HTTP: http://{HOST}:{PORT_HTTP}")
    app.run(host="0.0.0.0", port=PORT_HTTP)

# ------------------ START ------------------
if __name__ == "__main__":
    Thread(target=http_start, daemon=True).start()
    asyncio.run(ws_main())
