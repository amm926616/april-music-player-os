SHORTCUTS = """
        <h2>🎹 <b>Keyboard Shortcuts</b></h2>
        <p>Master these shortcuts to navigate and control the app effortlessly:</p>

        <h3>📝 <b>Getting Started</b></h3>
        <ul>
            <li>Start by <strong>double-clicking</strong> on an item in the left layout's tree list:</li>
            <ul>
                <li>Double-click an <strong>artist name</strong> to load all songs by that artist into the playlist.</li>
                <li>Double-click an <strong>album name</strong> to load all songs from that album.</li>
                <li>Double-click a <strong>single song</strong> to add just that song to the playlist.</li>
            </ul>
        </ul>

        <h3>🔗 <b>General (Main UI & Playlist)</b></h3>
        <h4>Playback Control</h4>
        <ul>
            <li><strong>Space</strong>: Play/Pause</li>
            <li><strong>Ctrl + Shift + Right Arrow</strong>: Play next song</li>
            <li><strong>Ctrl + Left Arrow</strong>: Seek backward</li>
            <li><strong>Right Arrow</strong>: Seek forward</li>
            <li><strong>Left Arrow</strong>: Seek backward</li>
            <li><strong>0 / Home</strong>: Return to start of song</li>
            <li><strong>Ctrl + P</strong>: Stop song</li>
            <li><strong>Shift + Alt + R</strong>: Restart current song</li>
            <li><strong>Ctrl + Alt + R</strong>: Reload directories (update database)</li>
        </ul>
        <h4>Navigation & Playlist</h4>
        <ul>
            <li><strong>Ctrl + R</strong>: Play random song</li>
            <li><strong>Ctrl + T</strong>: Play song at top of playlist</li>
            <li><strong>Ctrl + G</strong>: Scroll to currently playing row</li>
            <li><strong>Enter</strong>: Play selected song (when playlist focused)</li>
            <li><strong>Del</strong>: Remove selected song(s) from playlist</li>
            <li><strong>Ctrl + C</strong>: Copy file path of selected song</li>
            <li><strong>Ctrl + D</strong>: Restore table (reset filters)</li>
        </ul>
        <h4>Search & Focus</h4>
        <ul>
            <li><strong>Ctrl + F</strong>: Focus playlist search bar</li>
            <li><strong>Ctrl + Shift + F</strong>: Focus main search bar</li>
            <li><strong>Ctrl + J</strong>: Focus playlist (without search)</li>
        </ul>
        <h4>Lyrics & Metadata</h4>
        <ul>
            <li><strong>Ctrl + L</strong>: Activate LRC display</li>
            <li><strong>Ctrl + I</strong>: Toggle lyrics sync on/off</li>
            <li><strong>F2</strong>: Edit selected song’s metadata</li>
        </ul>
        <h4>Playback Modes</h4>
        <ul>
            <li><strong>Ctrl + 1</strong>: Toggle playlist loop</li>
            <li><strong>Ctrl + 2</strong>: Toggle repeat (current song)</li>
            <li><strong>Ctrl + 3</strong>: Toggle shuffle</li>
        </ul>
        <h4>UI & Actions</h4>
        <ul>
            <li><strong>F11</strong>: Toggle fullscreen</li>
            <li><strong>Ctrl + S</strong>: Save playlist</li>
            <li><strong>Ctrl + Q</strong>: Quit application</li>
            <li><strong>Esc</strong>: Close active dialog/sub-window</li>
        </ul>

        <h3>📜 <b>Lyrics (LRC) View</b></h3>
        <h4>Playback & Navigation</h4>
        <ul>
            <li><strong>Space</strong>: Play/Pause</li>
            <li><strong>Left Arrow / Right Arrow</strong>: Seek backward/forward</li>
            <li><strong>D</strong>: Jump to start of current lyric</li>
            <li><strong>Up Arrow / Down Arrow</strong>: Previous/next lyric line (if interactive)</li>
            <li><strong>R</strong>: Restart song</li>
        </ul>
        <h4>Tools & UI</h4>
        <ul>
            <li><strong>F</strong>: Toggle fullscreen</li>
            <li><strong>Ctrl + D</strong>: Open dictionary</li>
            <li><strong>E</strong>: Open lyrics notebook</li>
            <li><strong>Ctrl + C</strong>: Copy current lyric text</li>
            <li><strong>Ctrl + Y</strong>: Create lyrics animation</li>
        </ul>

        <h3>📔 <b>Lyrics Notebook</b></h3>
        <ul>
            <li><strong>Ctrl + S</strong>: Save text</li>
            <li><strong>Esc / Ctrl + W</strong>: Close without saving</li>
        </ul>

        <h3>📚 <b>Personal Dictionary</b></h3>
        <ul>
            <li><strong>Ctrl + S</strong>: Search word</li>
            <li><strong>Ctrl + Q</strong>: Delete selected entry</li>
            <li><strong>Enter</strong> (in word box): Search</li>
            <li><strong>Enter</strong> (in meaning box): Save new entry</li>
            <li><strong>Esc / Ctrl + W</strong>: Close window</li>
        </ul>

        <p style="font-style:italic;">Tip: Use these shortcuts to streamline your workflow and enhance your music experience!</p>
        """

PREPARATION = """<b>Before using the player, you'll need to download your songs and lyrics in advance. I use Zotify
        to download songs from Spotify, and for LRC lyrics files, I recommend using LRCGET, Syrics on your laptop,
        or SongSync on Android. There are also various websites where you can download music with embedded metadata
        and lyrics.<br></b><br> - <a href="https://github.com/zotify-dev/zotify">Zotify</a><br> - <a
        href="https://github.com/tranxuanthang/lrcget">LRCGET</a><br> - <a
        href="https://github.com/akashrchandran/syrics">Syrics</a><br> - <a
        href="https://github.com/Lambada10/SongSync">SongSync</a><br><br> <b>For the program to easily match and grab
        files, ensure that the music file and the LRC file have the same name, plus in the same directory. I will
        figure out for better file management in the future.</b>"""


FROMME = """
        <b>🎵 April Music Player - More Than Just a Player</b><br><br>

        April Music Player is not just another music player - it's a comprehensive language learning companion. 
        Designed with special features for navigation, note-taking, dictionary, and interactive learning, 
        it helps you enjoy music while mastering new languages.<br><br>

        <b>🌟 Key Features:</b>
        • Synchronized lyrics display for active learning
        • Built-in note-taking and vocabulary tools
        • Customizable interface for personalized learning
        • Special functions to enhance lyric memorization<br><br>

        <b>🌐 Learn more:</b> <a href="https://april-landing-react.vercel.app/">Visit our official website</a><br>
        <b>💡 Suggestions?</b> Contact the developer on Telegram: <a href="https://t.me/Adamd178">@Adamd178</a><br>
        <b>⭐ Love it?</b> Star us on <a href="https://github.com/amm926616/April-Music-Player">GitHub</a> to support the project!<br><br>

        <small>Created with ❤️ by Aiden (AD178)</small>
        """