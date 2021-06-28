from rich import print
import glob
import os
from spacy.lang.de import German
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
	table = Table()
	table.add_column("TSS Dataset Creator", style="cyan")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	
	print(table)

	print("\nPlease select your [red]microphone[/red] (enter the device number).")
	# Initialisiere pyaudio
	pyaudio = pyaudio.PyAudio()
	
	# select input device
	info = pyaudio.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount')
	for i in range(0, numdevices):
		if (pyaudio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
			print ("Input Device id ", i, " - ", pyaudio.get_device_info_by_host_api_device_index(0, i).get('name'))
	in_mic_id = int(input())
	print("You have selected [red]%s[/red] as input device." % pyaudio.get_device_info_by_host_api_device_index(0, in_mic_id).get('name'))
	
	
	# 0. select folder to save wavs
	app_folder = os.path.dirname(os.path.realpath(__file__))
	project_folder = os.path.join(app_folder, "sample_" + datetime.now().strftime("%d.%m.%Y"))
	print("Please select a [red]folder[/red] to save your current session to (default [i]%s[/i])." % project_folder)
	in_folder = input()
	if not in_folder:
		in_folder = project_folder
	if not os.path.exists(in_folder):
		os.mkdir(in_folder)
	print("wavs and transcripts will be saved in [red]%s[/red]" % in_folder)
	
	
	# 0.1 select languages
	print("Please select a [red]language[/red] (default [i]%s[/i])." % 'de')
	in_lang = input()
	if not in_lang:
		in_lang = 'de'
	print("Language is set to [red]%s[/red]." % in_lang)
	
	lang_text_files = glob.glob(os.path.join(app_folder, 'texts', in_lang + '*.txt'))
	print("Found %d text files for %s" % (len(lang_text_files), in_lang))
	
	if len(lang_text_files) == 0:
		print("Please select another language or create text files starting with %s in the [red]texts[/red] folder. Exiting." % in_lang)
		sys.exit(0)
		
	# 1. Show text, sentence by sentence
	all_texts = ''
	for tf in lang_text_files:
		f = open(tf, "r", encoding= 'utf-8')
		all_texts += f.read() + '\n'
				
	# split texts by sentences
	nlp = German()
	nlp.add_pipe('sentencizer')

	doc = nlp(all_texts)
	all_sentences = [str(sent).strip() for sent in doc.sents]

	print("Found %d sentences." % len(all_sentences))

	if len(all_sentences) == 0:
		print("You need to add some sentences to your text files first. Exiting.")
		sys.exit(0)
	
	# 1.1 Hit Space to skip to save+next, hit backspace to discard
	print("[green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording.")
	i = 0
	cancelled = False
	while i < len(all_sentences):
		print("[magenta]" + all_sentences[i] + "[/magenta]")
		print("(%d/%d) [green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording." % ((i+1), len(all_sentences)))
		
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
					wf = wave.open(os.path.join(project_folder, str(i) + '.wav'), 'wb')
					wf.setnchannels(channels)
					wf.setsampwidth(pyaudio.get_sample_size(sample_format))
					wf.setframerate(frame_rate)										
					wf.writeframes(b''.join(frames))
					wf.close()
					
					# trim silence?
					wav, source_sr = librosa.load(str(os.path.join(project_folder, str(i) + '.wav')), sr=None)
					wav = trim_long_silences(wav)
					soundfile.write(str(os.path.join(project_folder, str(i) + '.wav')), wav, source_sr)
										
					# Write the transcript
					text_file_path = os.path.join(project_folder, str(i) + '.txt')
					if os.path.exists(text_file_path):
						os.remove(text_file_path)
					text_file = open(text_file_path, 'a')
					text_file.write(all_sentences[i])
					text_file.close()
					# save audio
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
		
	# 1.2 Show remaining sentences
	# 1.3 Hit Escape to quit

	# 2. Ask to process wavs
	# 2.1 Remove Pauses
	pyaudio.terminate()