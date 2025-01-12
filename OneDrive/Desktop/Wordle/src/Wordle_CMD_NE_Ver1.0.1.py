import os
import pandas as pd
from collections import Counter
import numpy as np

N_GUESSES = 6
DICT_FILE_all = 'all_words.parquet'
DICT_FILE = 'words.parquet'
CACHE_DIR = 'cache2'
WORD_LEN = 5
pattern_cache = {}
WIN = False

# Load our game Data
def load_Game_data():
    print('Loading game data...')
    os.makedirs(CACHE_DIR, exist_ok=True) # Create the cache directory if it does not exist
        
    FILE_LOC_ALL = os.path.join(CACHE_DIR, DICT_FILE_all) # File location for the all words dictionary

    if os.path.exists(FILE_LOC_ALL): # If the file exists
        df = pd.read_parquet(FILE_LOC_ALL) # Read the parquet file
    else: # If the file does not exist
        print("Parquet file not found. Generating from text file...") 
        with open(DICT_FILE_all, 'r') as f: # Generate the parquet file from the text file
            words = [line.strip() for line in f.readlines()]
        df = pd.DataFrame({"Word": words})
        df.to_parquet(FILE_LOC_ALL)

    word_list = df['Word'].tolist() # Get the list of words from the data frame
    all_words = set(word_list) # Set the all words set to the word list
    print(f'Loaded dictionary with {len(word_list)} words...') # Print the number of words loaded
    return word_list, all_words

# Calculates the pattern for a guess and answer
def calculate_pattern(guess, answer):
    """Optimized pattern calculation"""
    if (guess, answer) in pattern_cache: # If the pattern is in the cache, return the pattern
        return pattern_cache[(guess, answer)]
    
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
    pattern_cache[(guess, answer)] = result
    return result

# Calculate the entropy for a guesS
def calculate_entropy(guess, possible_words):
    """Calculate entropy for a guess"""
    print(f"Calculating entropy for guess: {guess}")
    pattern_counts = Counter() # Counter for the pattern counts i.e. how many patterns are in the pattern_counts dictionary
    for answer in possible_words: # For each answer in possible words
        pattern = calculate_pattern(guess, answer) # Calculate the pattern for the answer and the guess
        pattern_counts[pattern] += 1 # Increment the pattern count for the pattern
    
    total = len(possible_words) # Total number of possible words
    entropy = 0 # Initialize entropy to 0
    for count in pattern_counts.values(): # for each count in the pattern counts
        prob = count / total # Calculate the probability of the pattern (count / total)
        entropy -= prob * np.log2(prob) # E = -Σ p(x) * log2(p(x))
    
    print(f"Entropy for {guess}: {entropy:.2f}")
    return entropy

def process_guess(guess,word_list,all_words):
    if guess not in all_words:
                    print("Invalid guess. Try again.")
    else:
        pattern = input("Enter the pattern for this guess (0 for absent, 1 for present, 2 for correct): ")
        if pattern == "22222":
                print("Congratulations! You have guessed the word!")
                WIN = True
        # Find words consistent with the pattern
        filtered_words = {
                possible_word
                for possible_word in all_words
                if calculate_pattern(guess.lower(), possible_word) == tuple(map(int, pattern))
            }
            
        # Intersect with the current set of possible words
        all_words &= filtered_words  # Intersect with the current possible words
        print(f"Filtered possible words: {len(all_words)} remaining.")

    
        # After the first guess, calculate entropy for remaining words
        if len(all_words) <= 100:
            candidates = list(all_words)
        else:
            print("Sampling from word list...")
            sample_size = min(100, len(all_words))
            possible_sample = np.random.choice(list(all_words), 
                                            size=sample_size // 2, 
                                            replace=False)
            full_sample = np.random.choice(word_list, 
                                        size=sample_size // 2, 
                                        replace=False)
            candidates = list(set(possible_sample) | set(full_sample))
        
        entropies = {}
        for word in candidates:
            entropies[word] = calculate_entropy(word, all_words)
        top_words = sorted(entropies.items(), key=lambda x: x[1], reverse=True)[:5]
        return top_words

# Main game loop
def main():
    print("Lets solve this word! >:)")
    word_list, all_words = load_Game_data()
    print("Loaded game data")
    print("Starting game...")
    round =0
    
    for x in range(N_GUESSES):
        print(f"Round {round+1}")
        if(round == 0):
            top_words = [("TARES", 4.29), ("LARES", 4.26), ("RALES", 4.24),
                        ("RATES", 4.23), ("TERAS", 4.21)]
            print(f"The pre-computed best guesses for the first round are: {top_words} ")
            guess = input("Enter your guess: ")
            top_words = process_guess(guess, word_list, all_words)
            if WIN:
                 break
            round +=1
        else:
             print(f"The best words to guess this round are : {top_words}")
             guess = input("Enter your guess: ")
             top_words = process_guess(guess,word_list,all_words)
             if WIN : 
                  break
             round +=1
                  
                
                      
if __name__ == "__main__":
    main()