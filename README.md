# TTS Dataset Creator
This tool helps you to create datasets for text to speech tasks. It shows you single sentences that you read out loud. Your voice
is recorded, trimmed and saved along with the sentence as text file in a specific folder.

<a href="https://www.buymeacoffee.com/padmalcom" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

## Installation
Create a conda environment from the yml file

- conda env create --file environment.yml

## Usage
There are 5 applications in this repository:

1. main_text_gen_gpt2.py - Use a gpt-2 model to generate readable texts
2. main_text_gen_wiki.py - Download texts from wikipedia
3. main_generate_csv.py - Collects texts from 1 and/or 2 and creates a metadata.csv file by splitting all texts in sentences and generate the according wav name.
4. main_generator.py - Reads a metadata.csv, display sentence by sentence and records your reading.
5. main_cleaner.py - Cleans a directory with wavs and a metadata.csv. All entries that have no wav file are deleted.


### main_generator.py
The console application guides you through the process.

1. Select the microphone you want to use for recording
2. Select a folder where you want to store your samples.
3. Select a language. The texts presented are in that given language. The application comes with English and German texts so far. Feel free to contribute. We support pdf and txt files.
4. You will then see a text in magenta. Read it out loud. When done, press n (next) and the next sentence is shown. If you are not satisfied with your reading, press d (discard) and the text is repeaded. When you think you generated enough samples, press e (exit). You find the wav and txt files in the folder you specified in 2.


### main_text_gen_wiki.py
- python main_text_gen_wiki.py

This tool collects texts from wikipedia for any language and stores those texts in the texts folder in the application directory.

1. select a language (default de)
2. select the number of articles to download (default 100, max is 500)
3. select if the text should be normalized ($=>Dollar, 10=ten, 1.=first) and cleansed (an nlp model that is trained to repair sentences is applied, this is an experimental feature).

### main_text_gen_gpt2.py
GPT-2 is a pretrained language model that can be used to generate text.

- python main_text_gen_gpt2.py

This tool generates sentences of ~400 characters.

1. select a langauge (default de)
2. select the number of files to create (default 100)
3. select if the text should be normalized ($=>Dollar, 10=ten, 1.=first)


### main_generate_csv.py
tbd

### main_cleaner.py
tbc

## Contribute
If you'd like to see a specific language to be supported feel free to create text files containing (royalty free) stories and create a pull request.

Furthermore, I'd be super happy if you support me on pateron (https://www.patreon.com/padmalcom)

## Text sources
###German
- https://deutschestextarchiv.de/download
- https://german-nlp-group.github.io/projects/gc4-corpus.html#download
- https://github.com/tblock/10kGNAD
