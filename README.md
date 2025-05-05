# April Music Player

<img src="./icons/april-logo.png" alt="logo" width="400"/>

## 🌐 Official Website

Check out the official website for April Music Player:  
[April Music Player's Official Website](https://april-music-player.github.io/)

---

## 🎵 About

April Music Player is an interactive music player with lyric syncing and note-taking capabilities, designed to enhance
lyric memorization and language learning. Its features include:

- **Customizable Lyrics Display**: Perfect for language learners.
- **Note-Taking and Vocabulary Tools**: Take notes and keep personal vocabulary collections.
- **Interactive Features**: Engage deeply with your favorite songs.

This project was inspired by a personal wish for a tool to practice Korean lyrics and is now shared with everyone to
enjoy.  
**Presented to you by Aiden.**

---

## 📸 Screenshots

Here’s a glimpse of April Music Player in action:

<div align="center">
  <img src="./screenshots/0001.png" width="600"/>
  <img src="./screenshots/0002.png" width="600"/>
  <img src="./screenshots/0003.png" width="600"/>
  <img src="./screenshots/0004.png" width="600"/>
  <img src="./screenshots/0005.png" width="600"/>
  <img src="./screenshots/0006.png" width="600"/>
  <img src="./screenshots/0007.png" width="600"/>
  <img src="./screenshots/0008.png" width="600"/>
  <img src="./screenshots/0009.png" width="600"/>
  <img src="./screenshots/0010.png" width="600"/>
</div>

---

## 📂 Preparation: Music and Lyrics Files

To get started, download your songs and lyrics beforehand. Recommended tools:

- **Music Downloader**: [Zotify](https://github.com/zotify-dev/zotify)
- **Lyrics File Tools**:
    - [LrcGet](https://github.com/tranxuanthang/lrcget)
    - [Syrics](https://github.com/akashrchandran/syrics)
    - [SongSync](https://github.com/Lambada10/SongSync)

The tools listed above help you grab songs or LRC lyrics files easily.

---

## 🛠 Installation

### Option 1: Use Windows Installer

An outdated Windows installer is available:
[Download Windows Installer](https://github.com/amm926616/april-music-player-os/releases/download/windows-installers/april-open-source-v1.1-setup.exe)

_**Note:** Major updates only receive a new installer. For frequent updates, use the Python-based setup._

---

### Option 2: Run With Python

1. Clone or download the repository:
    ```bash
    git clone https://github.com/amm926616/april-music-player.git
    cd april-music-player
    ```

2. **(Optional)** Create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    .venv\Scripts\activate  # Windows
    ```

3. Install required dependencies:
    - For Windows:
      ```bash
      pip install -r requirements/requirements-windows.txt
      ```
    - For Linux:
      ```bash
      pip install -r requirements/requirements-linux.txt
      ```

4. Run the application:
    ```bash
    python main.py
    ```

5. Optionally, create a shortcut or script for easier launching in the future.

---

## 🎹 Keyboard Shortcuts

Navigate the app effortlessly with these bindings:

### 🔗 General (Main UI & Playlist)

#### Playback Control

- `Space`: Play/Pause
- `Ctrl+Right`: Seek forward
- `Ctrl+Left`: Seek backward
- `Right`: Seek forward
- `Left`: Seek backward
- `0 / Home`: Return to start of song
- `Ctrl+P`: Stop song
- `Shift+Alt+R`: Restart current song
- `Ctrl+Alt+R`: Reload directories (update database)

#### Navigation & Playlist

- `Ctrl+R`: Play random song
- `Ctrl+T`: Play song at the top of the playlist
- `Ctrl+G`: Scroll to currently playing row
- `Enter`: Play selected song (playlist focused)
- `Del`: Remove selected song(s) from the playlist
- `Ctrl+C`: Copy file path of selected song
- `Ctrl+D`: Restore table (reset filters) in the playlist search mode. 

#### Search & Focus

- `Ctrl+F`: Focus playlist search bar
- `Ctrl+Shift+F`: Focus main search bar
- `Ctrl+J`: Focus playlist (no search)

#### Lyrics & Metadata

- `Ctrl+L`: Activate LRC display
- `Ctrl+I`: Toggle lyric sync on/off
- `F2`: Edit selected song metadata

#### Playback Modes

- `Ctrl+1`: Toggle playlist loop
- `Ctrl+2`: Toggle repeat (current song)
- `Ctrl+3`: Toggle shuffle

#### UI & Actions

- `F11`: Toggle fullscreen
- `Ctrl+S`: Save playlist
- `Ctrl+Q`: Quit application
- `Esc`: Close current dialog or sub-window

---

### 📜 Lyrics (LRC) View

#### Playback & Navigation

- `Space`: Play/Pause
- `Left`/`Right`: Seek backward/forward
- `D`: Jump to start of current lyric
- `Up`/`Down`: Previous/next lyric line (interactive only)
- `R`: Restart song

#### Tools & UI

- `F`: Toggle fullscreen
- `Ctrl+D`: Open dictionary
- `E`: Open lyrics notebook
- `Ctrl+C`: Copy current lyric text

---

### 📔 Lyrics Notebook

- `Ctrl+S`: Save text
- `Esc` / `Ctrl+W`: Close without saving

---

### 📚 Personal Dictionary

Explore my stand-alone app for vocabulary
management ([Personal Dictionary](https://github.com/amm926616/sqlite-personal-dictionary)):

- **Search System**: Mimics neuronal connections for exploring similar-sounding words.

Use within the April Music Player:

- `Ctrl+S`: Search word
- `Ctrl+Q`: Delete selected entry
- `Enter` (word box): Search
- `Enter` (meaning box): Save entry
- `Esc` / `Ctrl+W`: Close window
