# TTS Dataset Creator
This tool helps you to create datasets for text to speech tasks. It shows you single sentences that you read out loud. Your voice
is recorded, trimmed and saved along with the sentence as text file in a specific folder.

## Installation
Create a conda environment from the yml file

- conda env create --file environment.yml

Run the main_generator.py

- python main_generator.py


## Usage
The console application guides you through the process.

1. Select the microphone you want to use for recording
2. Select a folder where you want to store your samples.
3. Select a language. The texts presented are in that given language. The application comes with English and German texts so far. Feel free to contribute.
4. You will then see a text in magenta. Read it out loud. When done, press n (next) and the next sentence is shown. If you are not satisfied with your reading, press d (discard) and the text is repeaded. When you think you generated enough samples, press e (exit). You find the wav and txt files in the folder you specified in 2.

## Generate readable text
If you need more texts to read (what will most certainly be the case), then you can use the text collector.

- python main_text_collector.py

This tool collects texts from wikipedia for any language and stores those texts in the texts folder in the application directory.

1. select a language (default de)
2. select the number of articles to download (default 100)

## Contribute
If you'd like to see a specific language to be supported feel free to create text files containing (royalty free) stories and create a pull request.

Furthermore, I'd be super happy if you support me on pateron (https://www.patreon.com/padmalcom)