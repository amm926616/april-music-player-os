import json
import os
from cryptography.fernet import Fernet
import inspect
from _utils.colors import printCyan, printYellow


def rewrite_credentials(input_file):
    with open(input_file, 'r') as file:
        data = json.load(file)

    file.close()

    if "auth_type" in data and data["auth_type"] == 1:
        data["type"] = "AUTHENTICATION_STORED_SPOTIFY_CREDENTIALS"
        del data["auth_type"]

    if "auth_data" in data:
        data["credentials"] = data.pop("auth_data")

    with open(input_file, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Modifed credentials saved to {input_file}")


class EasyJson:
    _instance = None  # Class variable to store the single instance

    def __new__(cls, *args, **kwargs):
        # Check if an instance already exists, if not, create it
        if cls._instance is None:
            cls._instance = super(EasyJson, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent reinitialization
            self.ej_path = os.path.dirname(os.path.abspath(__file__))
            self.april_config_path = self.get_april_config_path()
            self.home_script_path = None

            self.default_values = {
                "english_font": os.path.join(self.ej_path, "fonts", "PositiveForward.otf"),
                "korean_font": os.path.join(self.ej_path, "fonts", "NotoSerifKR-ExtraBold.ttf"),
                "japanese_font": os.path.join(self.ej_path, "fonts", "NotoSansJP-Bold.otf"),
                "chinese_font": os.path.join(self.ej_path, "fonts", "NotoSerifKR-ExtraBold.ttf"),
                "lrc_font_size": 24,
                "sync_threshold": 0.3,
                "early_sync_time": 0.2,
                "lyrics_color": "white",
                "show_lyrics": True,
                "play_song_at_startup": False,
                "playback_states": {"shuffle": False, "loop": False,"repeat": False},
                "buttons_all_default": True,
                "previous_loop": False,
                "previous_shuffle": False,
                "music_directories": {self.get_user_default_folder("Music"): True},
                "last_played_song": {},
                "lyrics_downloaders": {'lrcdl': True, 'syrics': False},
                "selected_music_downloader": 'zotify',
                "active_subscription": False,
                "time_to_expire": None,
                "previous_login_time": None,
                "running_system": self.check_os(),
                "config_path": self.april_config_path,
                "config_file": str(os.path.join(self.get_april_config_path(), "configs", "config.april")),
                "script_path": os.path.dirname(os.path.abspath(__file__)),
                "songtable_json_file": os.path.join(self.get_april_config_path(), "table_data.json"),
                "default_image_folder": self.get_user_default_folder("Pictures"),
                "volume": 0.8
            }

            self.zotify_credential_path = self.get_zotify_credential_file_path()

            self.config_file = os.path.join(self.get_april_config_path(), "configs", "config.april")
            self.key = "pNtpUh6JNDtoUpMnQ1b73BSKeABITKHC7JzumILCE2g="
            self.data = self.load_json()
            self.initialized = True  # Mark the instance as initialized
            self.icon_path = os.path.join(self.ej_path, "media-icons")

    def set_home_script_path(self, path):
        self.home_script_path = path
        printCyan(f"home_script_path: {self.home_script_path}")

    def check_evalution_used(self):
        """return true if the user has used his evaluation"""
        proof_file = os.path.join(self._get_config_path(), ".mavenCoreNoFile")
        if os.path.exists(proof_file):
            return True
        return False

    def create_evaluation_proof(self, file_path=None):
        proof_file = os.path.join(self._get_config_path(), ".mavenCoreNoFile")
        try:
            with open(proof_file, "w") as file:
                file.write("loving is caring!")
            # Ensure file permissions are secure (600: owner can read/write)
            os.chmod(file_path, 0o600)
        except Exception as e:
            print("failed to create proof file")

    def check_evaluation(self):
        proof_file = os.path.join(self._get_config_path(), ".mavenCoreNoFile")
        try:
            with open(proof_file, "r") as file:
                for line in file:
                    if line == "loving is caring!":
                        return True
        except Exception as e:
            print(f"Failed to read credentials: {e}")
            return None

    def get_user_default_folder(self, folder_type: str) -> str:
        """
        Returns the path to the user's default folder based on the given folder type.

        Args:
            folder_type (str): Name of the default folder (e.g., "Music", "Pictures", "Documents").

        Returns:
            str: The full path to the requested folder.

        Raises:
            ValueError: If folder_type is empty or invalid.
        """
        if not folder_type or not isinstance(folder_type, str):
            raise ValueError("folder_type must be a non-empty string.")

        user_home = os.getenv("USERPROFILE") if os.name == "nt" else os.path.expanduser("~")
        if not user_home:
            raise EnvironmentError("Could not determine the user's home directory.")

        return os.path.join(user_home, folder_type)

    def check_os(self):
        """Check the OS type and return the correct config path."""
        if os.name == "nt":
            return "windows"
        else:
            return "unix"

    def get_zotify_config_folder_path(self) -> str:
        if self.check_os() == "windows":
            return os.path.join(self._get_config_path(), "Zotify")
        else:
            return os.path.join(os.path.expanduser("~"), ".local", "share", "zotify")


    def get_zotify_credential_file_path(self):
        if self.check_os() == "windows":
            return os.path.join(self.get_zotify_config_folder_path(), "credentials.json")
        else:
            return os.path.join(self.get_zotify_config_folder_path(), "credentials.json")

    def _get_config_path(self):
        if self.check_os() == "windows":
            return os.getenv("APPDATA")
        else: # for unix like systems
            return os.path.join(os.path.expanduser("~"), '.config')

    def get_april_config_path(self):
        if self.check_os() == "windows":
            return os.path.join(self._get_config_path(), "April Music Player")
        else:
            return os.path.join(self._get_config_path(), "april-music-player")

    def setupBackgroundImage(self):
        default_image_path = os.path.join(self.ej_path, "background-images", "default.jpg")
        self.edit_value("background_image", default_image_path)
        return default_image_path

    def setupLyricsColor(self):
        self.edit_value("lyrics_color", "white")

    # Encrypt the JSON file
    def encrypt_json(self, data):
        # Convert the JSON data to a string and then encode to bytes
        json_data = json.dumps(data)
        byte_data = json_data.encode('utf-8')

        # Create a Fernet object with the key
        cipher_suite = Fernet(self.key)

        # Encrypt the data
        encrypted_data = cipher_suite.encrypt(byte_data)

        return encrypted_data

    def decrypt_json(self):
        # Try to read the encrypted data and decrypt it
        try:
            # Read the encrypted data
            with open(self.config_file, "rb") as f:
                encrypted_data = f.read()

            # Create a Fernet object with the key
            cipher_suite = Fernet(self.key)

            # Decrypt the data
            decrypted_data = cipher_suite.decrypt(encrypted_data)

            # Convert the decrypted byte data back to a string and load it into a dictionary
            json_data = decrypted_data.decode('utf-8')
            data = json.loads(json_data)

            return data  # Return the decrypted data if successful

        except (Exception, json.JSONDecodeError) as e:
            print(f"Error while decrypting or parsing the file: {e}")
            print("Returning default values.")
            return self.default_values  # Return default values if an error occurs

    def load_json(self):
        """Load the JSON file and return the data as a dictionary."""
        if not os.path.exists(self.config_file):
            return self.default_values  # Return an empty dictionary if the file doesrunning_platformn't exist
        try:
            return self.decrypt_json()
        except (json.JSONDecodeError, IOError):
            print(f"Error: Unable to read or decode {self.config_file}. Returning empty config.")
            return {}

    def save_json(self):
        """Save the current data to the JSON file."""
        # Capture caller information
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        caller_file = caller_frame.f_code.co_filename
        caller_line = caller_frame.f_lineno

        print(f"edit_value called by '{caller_name}' in '{caller_file}' at line {caller_line}")

        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "wb") as f:
                f.write(self.encrypt_json(self.data))
                print("Saved encrypted data")
        except IOError as e:
            print(f"Error: Failed to write to file {self.config_file}. {e}")

    def get_value(self, key):
        """Retrieve the value of a key from the JSON data."""
        return self.data.get(key, None)

    def edit_value(self, key, value):
        """Edit the value of a key in the JSON data."""
        self.data[key] = value
        # Capture caller information
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        caller_file = caller_frame.f_code.co_filename
        caller_line = caller_frame.f_lineno

        print(f"edit_value called by '{caller_name}' in '{caller_file}' at line {caller_line}")
        # self._save_json()

    def setup_default_values(self, fresh_config=False):
        if fresh_config:
            self.data = self.default_values  # Replace with default values
            self.save_json()
        else:
            # Add any missing default values
            for key, default_value in self.default_values.items():
                if key not in self.data:
                    self.data[key] = default_value
            self.save_json()

    def check_zotify_credential_format(self):
        """Return True if the file exists and the format is correct."""

        required_keys = {
            "username": str,
            "type": str,
            "credentials": str
        }

        # Check if file exists
        if not os.path.isfile(self.zotify_credential_path):
            print(self.zotify_credential_path)
            print("File not found. Proceeding with alternative method.")
            return False

        try:
            with open(self.zotify_credential_path, 'r') as file:
                data = json.load(file)

            # Check that all required keys are present and of the correct type
            for key, value_type in required_keys.items():
                if key not in data:
                    print(f"Missing key: {key}. Proceeding with alternative method.")
                    return False
                if not isinstance(data[key], value_type):
                    print(
                        f"Incorrect type for key: {key}. Expected {value_type.__name__}. Proceeding with alternative method.")
                    return False

            # Additional check for specific value in 'type' field
            if data["type"] != "AUTHENTICATION_STORED_SPOTIFY_CREDENTIALS":
                print("Invalid 'type' value. Proceeding with alternative method.")
                return False

            print("credentials.json file found and format is correct.")
            return True

        except json.JSONDecodeError:
            print("File is not a valid JSON. Proceeding with alternative method.")
            return False

    def ensure_config_file(self):
        if not os.path.exists(self.config_file):
            self.setup_default_values(fresh_config=True)  # fresh setup default config
        else:
            self.setup_default_values()

    def save_data_when_quit(self):
        self.save_json()

