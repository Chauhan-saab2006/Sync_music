# Sync Music

Stream your Windows PC audio to any device on your network through a browser. No apps to install, no drivers needed.

## What It Does

- Captures system audio using WASAPI loopback (or Stereo Mix)
- Streams to phones, tablets, or other PCs via WebSocket
- Multiple devices can listen simultaneously
- Auto-reconnects if connection drops

## Requirements

- Windows OS
- Python 3.x

## Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**

   ```bash
   python server.py
   ```

   Or use `sexy audio.bat` for auto-restart on crash.

3. **Connect from any device:**
   Open `http://<your-pc-ip>:5000` in a browser and hit Play.

## How It Works

| Layer         | Tech                 | Purpose                            |
| ------------- | -------------------- | ---------------------------------- |
| Audio Capture | sounddevice + WASAPI | Grabs system audio output          |
| Server        | Flask + WebSockets   | Serves UI and streams audio        |
| Client        | WebAudio API         | Decodes and plays audio in browser |

**Ports:** HTTP on `5000`, WebSocket on `8765`

## Troubleshooting

**No audio?**  
Enable Stereo Mix in Windows Sound settings (Recording tab → Show Disabled Devices).

**Can't connect?**  
Allow port 5000 through Windows Firewall.

## Files

```
server.py        # Audio capture and streaming server
client.html      # Browser-based player UI
sexy audio.bat   # Auto-restart wrapper script
requirements.txt # Python dependencies
```

## License

MIT

I'm actively building AI, automation & networking tools.  
Reach out if you’d like to collaborate or contribute.

<div align="left">

<a href="https://github.com/mayurkoli8" target="_blank">
<img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" />
</a>

<a href="https://www.linkedin.com/in/mayur-koli-484603215/" target="_blank">
<img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" />
</a>

<a href="https://instagram.com/mentesa.live" target="_blank">
<img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" />
</a>

<a href="mailto:kolimohit9595@gmail.com">
<img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" />
</a>

</div>

---

### 💬 Want to improve this project?

Open an issue or start a discussion — PRs welcome ⚡
