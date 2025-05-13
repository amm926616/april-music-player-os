#!/usr/bin/env python

import re
import pyperclip

class Decryptor:
    ELEMENTS_MAP = {
        "a": "u3Y$", "b": "+b0P", "c": "~Cp6", "d": "O^d8", "e": "^e5B",
        "f": "Rw4~", "g": "n2N^", "h": "c@T8", "i": "_dG6", "j": "9G&o",
        "k": "w+W3", "l": "Gx@4", "m": "L4b@", "n": "+3zI", "o": "O6r!",
        "p": "D2p#", "q": "Wg&3", "r": "3Jj&", "s": "E6&e", "t": "X~3g",
        "u": "^eO6", "v": "J4+o", "w": "h@6K", "x": "q#W4", "y": "Bm5^",
        "z": "+3Ip"
    }

    INVERSION_MAP = {'~': '1', '!': '2', '@': '3', '#': '4', '$': '5', '^': '6', '&': '7', '*': '8', '_': '9', '+': '0'}
    INVERSION_KEYS = tuple(INVERSION_MAP.keys())
    INVERSION_VALUES = tuple(INVERSION_MAP.values())

    def __init__(self, hint):
        self.hint = hint
        self.shuffle_index = hint.index('#')
        self.extract_index = hint.index('@')
        self.inversion_index = hint.index('$')
        self.cleaned_hint = self._clean_hint()
        self.hint_chars = tuple(self.cleaned_hint)
        self.passcode = self._generate_passcode()

    def _clean_hint(self):
        """Remove special symbols and numbers from the hint."""
        return re.sub(r'\d+', '', self.hint.replace('#', '').replace('@', '').replace('$', ''))

    def _generate_passcode(self):
        """Generate the initial passcode from the hint characters."""
        return ''.join(self.ELEMENTS_MAP[char] for char in self.hint_chars)

    def _shuffle_passcode(self):
        """Shuffle passcode characters based on a predefined pattern."""
        shuffle_patterns = (
            (0, 1, 3, 2), (1, 0, 3, 2), (2, 1, 0, 3), (0, 3, 1, 2),
            (1, 0, 2, 3), (3, 0, 2, 1), (3, 2, 0, 1), (0, 2, 3, 1)
        )
        pattern = shuffle_patterns[self.shuffle_index]
        self.hint_chars = tuple(self.hint_chars[i] for i in pattern)

    def _extract_characters(self):
        """Extract and modify characters based on extraction rules."""
        if self.extract_index in (0, 1):
            method_index = 0
        elif self.extract_index in (2, 3):
            method_index = 1
        elif self.extract_index in (4, 5):
            method_index = 2
        else:
            method_index = 3

        extracted_chars = ''.join(self.ELEMENTS_MAP[self.hint_chars[i]][method_index] for i in range(4))
        remaining_chars = ''.join(
            self.ELEMENTS_MAP[self.hint_chars[i]].replace(self.ELEMENTS_MAP[self.hint_chars[i]][method_index], '')
            for i in range(4)
        )
        self.passcode = remaining_chars + extracted_chars

    def _invert_passcode(self):
        """Apply inversion transformations to the passcode."""
        inverted_passcode = ''
        for char in self.passcode:
            if char.isalpha():
                inverted_passcode += char.swapcase()
            elif char in self.INVERSION_VALUES:
                index = self.INVERSION_VALUES.index(char)
                inverted_passcode += self.INVERSION_KEYS[index]
            elif char in self.INVERSION_KEYS:
                index = self.INVERSION_KEYS.index(char)
                inverted_passcode += str(self.INVERSION_VALUES[index])
            else:
                inverted_passcode += char
        self.passcode = inverted_passcode

    def decrypt(self):
        """Perform decryption by shuffling, extracting, and inverting the passcode."""
        self._shuffle_passcode()
        self.passcode = self._generate_passcode()
        self._extract_characters()
        self._invert_passcode()
        return self.passcode

def clean_string(input_string):
    # Regular expression to keep only a-z, 0-9, and @#$
    pattern = r'[^a-z0-9@#$]'
    # Replace all characters that don't match the pattern with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    return cleaned_string

if __name__ == "__main__":
    key = input("Enter key: ")
    password = Decryptor(clean_string(key)).decrypt()
    pyperclip.copy(password)
    print("auto copied to the clipboard.")
    print(password)
