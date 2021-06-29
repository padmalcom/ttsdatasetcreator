from rich import print
from rich.console import Console
import glob
import os
from spacy.lang.de import German
from spacy.lang.en import English
from spacy.lang.fr import French
import time
import pyaudio
import keyboard
from rich.progress import Progress
from rich.progress import track
from rich.table import Table
import wave
from datetime import datetime
import librosa
import struct
import numpy as np
import webrtcvad
from scipy.ndimage.morphology import binary_dilation
import soundfile
import sys


chunk = 1024
sample_format = pyaudio.paInt16
channels = 1
frame_rate = 22050
timeout = 60

# For silence trimming
vad_moving_average_width = 8
int16_max = (2 ** 15) - 1
vad_window_length = 30
sample_rate = 16000
vad_max_silence_length = 6
	
	
def trim_long_silences(wav):
	
	# Compute the voice detection window size
	samples_per_window = (vad_window_length * sample_rate) // 1000
    
	# Trim the end of the audio to have a multiple of the window size
	wav = wav[:len(wav) - (len(wav) % samples_per_window)]
    
	# Convert the float waveform to 16-bit mono PCM
	pcm_wave = struct.pack("%dh" % len(wav), *(np.round(wav * int16_max)).astype(np.int16))
    
	# Perform voice activation detection
	voice_flags = []
	vad = webrtcvad.Vad(mode=3)
	for window_start in range(0, len(wav), samples_per_window):
		window_end = window_start + samples_per_window
		voice_flags.append(vad.is_speech(pcm_wave[window_start * 2:window_end * 2], sample_rate=sample_rate))
	voice_flags = np.array(voice_flags)
    
    # Smooth the voice detection with a moving average
	def moving_average(array, width):
		array_padded = np.concatenate((np.zeros((width - 1) // 2), array, np.zeros(width // 2)))
		ret = np.cumsum(array_padded, dtype=float)
		ret[width:] = ret[width:] - ret[:-width]
		return ret[width - 1:] / width
    
	audio_mask = moving_average(voice_flags, vad_moving_average_width)
	audio_mask = np.round(audio_mask).astype(np.bool)

	# Dilate the voiced regions
	audio_mask = binary_dilation(audio_mask, np.ones(vad_max_silence_length + 1))
	audio_mask = np.repeat(audio_mask, samples_per_window)

	return wav[audio_mask == True]


if __name__ == '__main__':

	console = Console()
	
	table = Table()
	table.add_column("TSS Dataset Creator", style="cyan")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	
	
	console.print(table)
	
	console.print("\nPlease select your [red]microphone[/red] (enter the device number).")
	# Initialisiere pyaudio
	pyaudio = pyaudio.PyAudio()
	
	# select input device
	info = pyaudio.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount')
	for i in range(0, numdevices):
		if (pyaudio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
			print ("Input Device id ", i, " - ", pyaudio.get_device_info_by_host_api_device_index(0, i).get('name'))
	in_mic_id = int(input())
	console.print("You have selected [red]%s[/red] as input device." % pyaudio.get_device_info_by_host_api_device_index(0, in_mic_id).get('name'))
	
	
	# 0. select folder to save wavs
	app_folder = os.path.dirname(os.path.realpath(__file__))
	project_folder = os.path.join(app_folder, "sample_" + datetime.now().strftime("%d.%m.%Y"))
	console.print("Please select a [red]folder[/red] to save your current session to (default [i]%s[/i])." % project_folder)
	in_folder = input()
	if not in_folder:
		in_folder = project_folder
	if not os.path.exists(in_folder):
		os.mkdir(in_folder)
	console.print("wavs and transcripts will be saved in [red]%s[/red]" % in_folder)
	
	
	# 0.1 select languages
	console.print("Please select a [red]language[/red] (default [i]%s[/i])." % 'de')
	in_lang = input()
	if not in_lang:
		in_lang = 'de'
	console.print("Language is set to [red]%s[/red]." % in_lang)
	
	# Save to csv or txt?
	console.print("Save to [red]csv[/red] or to single [red]txt[/red] file(s)?  (default [i]csv[/i]).")
	in_text_format = input()
	if not in_text_format:
		in_text_format = 'csv'
	if not in_text_format == 'txt':
		in_text_format = 'csv'
	console.print("Format set to [red]%s[/red]." % in_text_format)
	
	# Display files found
	lang_text_files = glob.glob(os.path.join(app_folder, 'texts', in_lang + '*.txt'))
	console.print("Found %d text files for %s" % (len(lang_text_files), in_lang))
	
	if len(lang_text_files) == 0:
		console.print("Please select another language or create text files starting with %s in the [red]texts[/red] folder. Exiting." % in_lang)
		sys.exit(0)
				
	# 1. Show text, sentence by sentence
	all_texts = ''
	for tf in lang_text_files:
		f = open(tf, "r", encoding= 'utf-8')
		all_texts += f.read() + '\n'
				
	# split texts by sentences
	if in_lang == 'de':
		nlp = German()
	elif in_lang == 'en':
		nlp = English()
	elif in_lang == 'fr':
		nlp = French()
	else:
		console.print("The language %s is not supported yet. Please create a github issue." % in_lang)
		sys.exit(0)
	
	nlp.add_pipe('sentencizer')

	doc = nlp(all_texts)
	all_sentences = [str(sent).strip() for sent in doc.sents]

	console.print("Found %d sentences." % len(all_sentences))

	if len(all_sentences) == 0:
		console.print("You need to add some sentences to your text files first. Exiting.")
		sys.exit(0)
	
	# 1.1 Hit Space to skip to save+next, hit backspace to discard
	console.print("[green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording.")
	
	console.print("Ready?", style="green")
	input("Press any key to start")
	
	i = 0
	cancelled = False
	while i < len(all_sentences):
		console.clear()
		console.print("\n\n" + all_sentences[i] + "\n\n", style = "black on white", justify="center")
		console.print("(%d/%d) [green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording." % ((i+1), len(all_sentences)))
		
		start_time = time.time()
		current_time = time.time()
		frames = []
		stream = pyaudio.open(input_device_index = in_mic_id, format=sample_format, channels=channels, rate=frame_rate, frames_per_buffer=chunk, input=True)
		
		with Progress() as recording_progress:
			recording_task = recording_progress.add_task("[red]Recording...", total=timeout)
						
			#while (current_time - start_time) < timeout:
			while not recording_progress.finished:
				recording_progress.update(recording_task, completed = current_time - start_time)
							
				data = stream.read(chunk)
				frames.append(data)
				current_time = time.time()

					
				if keyboard.is_pressed('n'):
					i += 1
					data = stream.read(chunk)
					frames.append(data)
					stream.close()
					wav_file_name = (str(i) + '.wav').rjust(10, '0')
					wf = wave.open(os.path.join(project_folder, wav_file_name), 'wb')
					wf.setnchannels(channels)
					wf.setsampwidth(pyaudio.get_sample_size(sample_format))
					wf.setframerate(frame_rate)										
					wf.writeframes(b''.join(frames))
					wf.close()
					
					# trim silence?
					wav, source_sr = librosa.load(str(os.path.join(project_folder, wav_file_name)), sr=None)
					wav = trim_long_silences(wav)
					soundfile.write(str(os.path.join(project_folder, wav_file_name)), wav, source_sr)
										
					# Write the transcript
					if in_text_format == 'txt':
						text_file_name = (str(i) + '.txt').rjust(10, '0')
						text_file_path = os.path.join(project_folder, text_file_name)
						if os.path.exists(text_file_path):
							os.remove(text_file_path)
						text_file = open(text_file_path, 'a')
						text_file.write(all_sentences[i])
						text_file.close()
					else:
						csv_file_path = os.path.join(project_folder, 'metadata.csv')
						csv_file = open(csv_file_path, 'a')
						# todo cleanse text
						csv_file.write(wav_file_name + "," + all_sentences[i] + "," + all_sentences[i] + '\n')
						csv_file.close()
					break
				elif keyboard.is_pressed("d"):
					stream.close()
					break
				elif keyboard.is_pressed("e"):
					stream.close()
					cancelled = True
					break
					
			if cancelled:
				break
		

	pyaudio.terminate()