import sys # System-specific parameters and functions
import os # Operating system Library
import numpy as np # Numerical computing library
from collections import  Counter # Counter is a dict subclass for counting hashable objects

# User Interface Libraries
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QLabel, QPushButton, QHBoxLayout, QGridLayout, QFrame, QSplitter, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent

import pandas as pd # Data manipulation library

# Gets the resource path for the file when exporting
def get_resource_path(relative_path):
    """Get the absolute path to a resource, considering PyInstaller bundling."""
    if hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Constants
N_GUESSES = 6 # The number of guesses in a wordle game
DICT_FILE = 'words.parquet' # The file containing a dictionary of all correct words in wordle
DICT_FILE_ALL = 'all_words.parquet' # The file containing a dictionary of all words in wordle
CACHE_DIR = get_resource_path("cache2") # Path to the cache directory
WORD_LEN = 5 # Length of a word guess in wordle

"""
The Wordle Button class is a custom QPushButton representation that denotes a grid in a wordle game.
example:
[◻️] [◻️] [◻️] [◻️] [◻️] : Empty Grid
[🟩] [🟩] [🟩] [🟩] [🟩] : Correct Grid
[🟨] [🟨] [🟨] [🟨] [🟨] : Present Grid
[🔳] [🔳] [🔳] [🔳] [🔳] : Absent Grid
"""
class WordleButton(QPushButton):
    # Constructor
    def __init__(self, text=""):
        super().__init__(text)
        # Set the style of the button
        self.setFixedSize(60, 60) # Size
        self.setFont(QFont('Arial', 20, QFont.Weight.Bold)) # Font size, font weight and bold
        self.setText(text.upper()) # Upper case
        self._state = "empty" # Default state is empty
        self.updateStyle() # Update the style of the button to reflect the state
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Fixed size policy for the button to ensure proper alignment
    
    # Accessor methods for the object
    # Setter
    def setState(self, state):
        self._state = state
        self.updateStyle()
    # Getter
    def getState(self):
        return self._state
    
    # Handles state change of a rows grid cell if clicked
    def mousePressEvent(self, event):
        if self.text(): # If the cell is not empty
            states = ["empty", "correct", "present", "absent"] # Possible states
            current_state = self._state # Current state is the state of the cell
            next_state = states[(states.index(current_state) + 1) % len(states)] # Next state is the next state in the list of states
            self.setState(next_state) # Set the state of the cell to the next state
        super().mousePressEvent(event) # Call the parent class method (Handles every other button on our interface)
    
    # Updates the style of the button based on the state of the button
    def updateStyle(self):
        colors = {
            "empty": ("#ffffff", "#000000"),
            "correct": ("#6aaa64", "#ffffff"),
            "present": ("#c9b458", "#ffffff"),
            "absent": ("#787c7e", "#ffffff"),
        }
        bg_color, text_color = colors.get(self._state, colors["empty"]) # Get the background and text color based on the state of the button
        self.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid #d3d6da;
                background-color: {bg_color};
                color: {text_color};
                margin: 0px;
                padding: 0px;
            }}
        """)

# Main Window Class sets up the user interface for the wordle game and handles the logic of the game (Including the entropy calculation)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() # Calls the parent class constructor
        self.setWindowTitle("Wordle Guessing Assistant")
        self.setGeometry(100, 100, 1000, 800)
        
        # Initialize game state
        self.current_row = 0 # Current row in the wordle game
        self.current_col = 0
        self.grid_buttons = [] # holds the grid buttons 
        self.current_word = "" # current word being guessed
        self.suggestions_labels = [] # holds the suggestion labels

        # Initialize game data
        self.word_list = [] # List of all words in the wordle game
        self.pattern_cache = {} # Cache for storing the pattern of a word
        self.all_words = set() # Set of all words in the wordle game
        self.load_game_data() # load the game data using the files in our constants
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.init_ui() # Initialize the user interface

    # Loads our game data from the files
    def load_game_data(self):
        """Load word list and initialize pattern cache"""
        os.makedirs(CACHE_DIR, exist_ok=True) # Create the cache directory if it does not exist
        
        FILE_LOC_ALL = os.path.join(CACHE_DIR, DICT_FILE_ALL) # File location for the all words dictionary

        if os.path.exists(FILE_LOC_ALL): # If the file exists
            df = pd.read_parquet(FILE_LOC_ALL) # Read the parquet file
        else: # If the file does not exist
            print("Parquet file not found. Generating from text file...") 
            with open(DICT_FILE_ALL, 'r') as f: # Generate the parquet file from the text file
                words = [line.strip() for line in f.readlines()]
            df = pd.DataFrame({"Word": words})
            df.to_parquet(FILE_LOC_ALL)

        self.word_list = df['Word'].tolist() # Get the list of words from the data frame
        self.all_words = set(self.word_list) # Set the all words set to the word list
        print(f'Loaded dictionary with {len(self.word_list)} words...') # Print the number of words loaded

    def calculate_pattern(self, guess, answer):
        """Optimized pattern calculation"""
        if (guess, answer) in self.pattern_cache: # If the pattern is in the cache, return the pattern
            return self.pattern_cache[(guess, answer)]
        
        print(f"Calculating pattern for guess: {guess}, answer: {answer}")
        pattern = [0] * WORD_LEN # Initialize the pattern to 0s
        guess_chars = list(guess) # Convert the guess to a list of characters
        answer_chars = list(answer) # Convert the answer to a list of characters
        
        # Mark correct positions
        for i in range(WORD_LEN):
            if guess_chars[i] == answer_chars[i]:
                pattern[i] = 2
                guess_chars[i] = answer_chars[i] = None
        
        # Mark present positions
        remaining_answer = Counter(c for c in answer_chars if c is not None)
        for i in range(WORD_LEN):
            if guess_chars[i] is not None and remaining_answer[guess_chars[i]] > 0:
                pattern[i] = 1
                remaining_answer[guess_chars[i]] -= 1
        
        result = tuple(pattern)
        self.pattern_cache[(guess, answer)] = result
        print(f"Pattern for {guess} vs {answer}: {result}")
        return result


    def calculate_entropy(self, guess, possible_words):
        """Calculate entropy for a guess"""
        print(f"Calculating entropy for guess: {guess}")
        pattern_counts = Counter() # Counter for the pattern counts i.e. how many patterns are in the pattern_counts dictionary
        for answer in possible_words: # For each answer in possible words
            pattern = self.calculate_pattern(guess, answer) # Calculate the pattern for the answer and the guess
            pattern_counts[pattern] += 1 # Increment the pattern count for the pattern
            if len(pattern_counts) % 100 == 0:  # Log progress every 100 words
                print(f"Processed {len(pattern_counts)} patterns for {guess}...")
        
        total = len(possible_words) # Total number of possible words
        entropy = 0 # Initialize entropy to 0
        for count in pattern_counts.values(): # for each count in the pattern counts
            prob = count / total # Calculate the probability of the pattern (count / total)
            entropy -= prob * np.log2(prob) # E = -Σ p(x) * log2(p(x))
        
        print(f"Entropy for {guess}: {entropy:.2f}")
        return entropy

    
    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Wordle grid and keyboard
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)  # Add spacing between elements

        # Title
        title = QLabel("WORDLE ENTROPY ASSISTANT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        left_layout.addWidget(title)

        # Wordle grid
        grid_frame = QFrame()
        grid_frame.setFrameStyle(QFrame.Shape.Box)
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(5)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        for i in range(6):
            row_buttons = []
            for j in range(5):
                btn = WordleButton()
                grid_layout.addWidget(btn, i, j, Qt.AlignmentFlag.AlignCenter)
                row_buttons.append(btn)
            self.grid_buttons.append(row_buttons)

        left_layout.addWidget(grid_frame)

        # Virtual keyboard
        keyboard_layout = self.create_keyboard()
        left_layout.addLayout(keyboard_layout)

        # Enter and Backspace buttons
        control_layout = QHBoxLayout()
        enter_btn = QPushButton("ENTER")
        enter_btn.clicked.connect(self.handle_enter)
        backspace_btn = QPushButton("⌫")
        backspace_btn.clicked.connect(self.handle_backspace)

        for btn in [enter_btn, backspace_btn]:
            btn.setFixedHeight(50)
            btn.setFont(QFont('Arial', 14))
            control_layout.addWidget(btn)

        left_layout.addLayout(control_layout)
        left_widget.setLayout(left_layout)

        # Right side - Suggestions sidebar
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        suggestions_label = QLabel("Top Suggestions")
        suggestions_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        right_layout.addWidget(suggestions_label)

        self.suggestions_labels = []
        for i in range(5):
            label = QLabel()
            label.setFont(QFont('Arial', 14))
            right_layout.addWidget(label)
            self.suggestions_labels.append(label)

        right_widget.setLayout(right_layout)

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Set up main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)

        # Initialize suggestions
        self.update_suggestions()
    
    def create_keyboard(self):
        keyboard_layout = QVBoxLayout()
        keyboard_layout.setSpacing(5)  # Add spacing between rows
        rows = [
            'QWERTYUIOP',
            'ASDFGHJKL',
            'ZXCVBNM'
        ]
        
        for row in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)  # Add spacing between buttonss
            for letter in row:
                btn = QPushButton(letter)
                btn.setFixedSize(40, 40)
                btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
                btn.clicked.connect(lambda checked, l=letter: self.handle_letter(l))
                row_layout.addWidget(btn)
            keyboard_layout.addLayout(row_layout)
        
        return keyboard_layout

    def update_suggestions(self):
        """Update suggestions based on current possible words"""
        print("Updating suggestions...")
        if not self.all_words:
            self.all_words = set(self.word_list)
        
        # Only use precomputed best words for the first guess
        if self.current_row == 0:
            print("Using precomputed best words for the first guess.")
            top_words = [("TARES", 4.29), ("LARES", 4.26), ("RALES", 4.24),
                        ("RATES", 4.23), ("TERAS", 4.21)]
        else:
            # After the first guess, calculate entropy for remaining words
            print(f"Calculating suggestions from {len(self.all_words)} possible words...")
            if len(self.all_words) <= 100:
                candidates = list(self.all_words)
            else:
                print("Sampling from word list...")
                sample_size = min(100, len(self.all_words))
                possible_sample = np.random.choice(list(self.all_words), 
                                                size=sample_size // 2, 
                                                replace=False)
                full_sample = np.random.choice(self.word_list, 
                                            size=sample_size // 2, 
                                            replace=False)
                candidates = list(set(possible_sample) | set(full_sample))
            
            print(f"Calculating entropy for {len(candidates)} candidates...")
            entropies = {}
            for word in candidates:
                entropies[word] = self.calculate_entropy(word, self.all_words)
                print(f"Entropy calculated for {word}: {entropies[word]:.2f} bits")
            top_words = sorted(entropies.items(), key=lambda x: x[1], reverse=True)[:5]
    
        # Update the labels
        for i, (word, entropy_val) in enumerate(top_words):
            print(f"Suggestion {i+1}: {word.upper()} ({entropy_val:.2f} bits)")
            self.suggestions_labels[i].setText(f"{word.upper()}: {entropy_val:.2f} bits")

    def handle_enter(self):
        if self.current_col == 5 and self.current_word.lower() in self.word_list:
            # Get pattern from user-selected button states
            pattern = []
            for btn in self.grid_buttons[self.current_row]:
                state = btn.getState()
                if state == "correct":
                    pattern.append(2)
                elif state == "present":
                    pattern.append(1)
                else:  # "absent" or "empty"
                    pattern.append(0)
            
            print(f"Observed pattern for {self.current_word}: {pattern}")

            # Find words consistent with the pattern
            filtered_words = {
                possible_word
                for possible_word in self.all_words
                if self.calculate_pattern(self.current_word.lower(), possible_word) == tuple(pattern)
            }
            
            # Intersect with the current set of possible words
            self.all_words &= filtered_words  # Intersect with the current possible words
            print(f"Filtered possible words: {len(self.all_words)} remaining.")

            # Update suggestions
            self.current_row += 1
            self.update_suggestions()
            self.update()  # This forces a refresh of the UI.

            
            # Move to the next row
            self.current_col = 0
            self.current_word = ""

            
    def handle_backspace(self):
        if self.current_col > 0:
            self.current_col -= 1
            self.grid_buttons[self.current_row][self.current_col].setText("")
            self.current_word = self.current_word[:-1]

    def handle_letter(self, letter):
        if self.current_row < 6 and self.current_col < 5:
            current_button = self.grid_buttons[self.current_row][self.current_col]
            current_button.setText(letter)
            current_button.setState("empty")  # Explicitly set state when adding letter
            self.current_word += letter
            self.current_col += 1
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input"""
        key = event.text().upper()
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.handle_enter()
        elif event.key() == Qt.Key.Key_Backspace:
            self.handle_backspace()
        elif key.isalpha() and len(key) == 1:
            self.handle_letter(key)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
