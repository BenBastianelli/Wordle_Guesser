Wordle Guesser!
Created By : Ben Bastianelli

Inspired by the video made by '3 Blue 1 Brown'
video link : https://www.youtube.com/watch?v=v68zYyaEmEA&t=937s 

This assitant uses Entropy to calculate the best possible guess to minimise the possible number of words left as quickly and efficiently as possible.
It does this by:
        - loading a file of all 12972 5 letter words in the english language to make sure a users input is valid. 
        - Once this is done the user guesses
        - When the user guesses the list of total words is shortened based on the number of words that are still possible based on the pattern entered of Green,yellow and grey.
        - After this is done it takes a sample of 100 words from the remaining word list and calculates entropy for those words by 
          applying the current function to every possible pattern left for the word:
            **Function**
             E = -Σ  p(x) * log2(p(x))
        - Once this is done the new suggestions are updated and this processed is repeated

This repository contains two versions of the project along with resource files with the data needed to run the program.

If you wish to create an executable for the program you can use the following commands in your terminal to create an executable easily:

  pip install pyinstaller
  pyinstaller "chosen_script".py --onefile --noconsole --add-data SRC:DEST

But if you wish to use it purely from the terminal then ensure you download the appropriate version 
( Denoted by a NE at the end of the file name )
E.G. : Wordle_CMD_NE_Ver1.0.1.py 
[NE stands for "Non Executable" and exists as this version of the script lacks the code to allow you to properly export the script and all its data as 1 executable]



