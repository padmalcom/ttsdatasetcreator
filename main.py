from rich import print
import glob
import os
from spacy.lang.de import German
import time
import pyaudio
import keyboard
from rich.progress import Progress
from rich.progress import track
import wave
from datetime import datetime

chunk = 1024
sample_format = pyaudio.paInt16
channels = 1
frame_rate = 22050
timeout = 60



if __name__ == '__main__':
	print("Hello, [magenta]World[/magenta]! [u]is[/u] a [i]way[/i]")
	
	# Initialisiere pyaudio
	pyaudio = pyaudio.PyAudio()
	
	# select input device
	info = pyaudio.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount')
	for i in range(0, numdevices):
		if (pyaudio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
			print ("Input Device id ", i, " - ", pyaudio.get_device_info_by_host_api_device_index(0, i).get('name'))
	in_mic_id = int(input())
	print("You have selected %s as input device." % pyaudio.get_device_info_by_host_api_device_index(0, in_mic_id).get('name'))
	
	
	# 0. select folder to save wavs
	app_folder = os.path.dirname(os.path.realpath(__file__))
	project_folder = os.path.join(app_folder, "sample_" + datetime.now().strftime("%d.%m.%Y"))
	print("Please select a folder to save your current session to (default %s)." % project_folder)
	in_folder = input()
	if not in_folder:
		in_folder = project_folder
	if not os.path.exists(in_folder):
		os.mkdir(in_folder)
	print("wavs and transcripts will be saved in %s" % in_folder)
	
	
	# 0.1 select languages
	print("Please select a language (default %s)." % 'de')
	in_lang = input()
	if not in_lang:
		in_lang = 'de'
	print("Language is set to %s." % in_lang)
	
	lang_text_files = glob.glob(os.path.join(app_folder, 'texts', in_lang + '*.txt'))
	print("Found %d text files for %s" % (len(lang_text_files), in_lang))
	
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


	

	
	# 1.1 Hit Space to skip to save+next, hit backspace to discard
	print("[green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording.")
	i = 0
	cancelled = False
	while i < len(all_sentences):
		print("[magenta]" + all_sentences[i] + "[/magenta]")
		print("[green]n[/green] = next sentence, [yellow]d[/yellow] = discard and repeat last recording, [red]e[/red] = exit recording.")
		
		start_time = time.time()
		current_time = time.time()
		frames = []
		stream = pyaudio.open(input_device_index = in_mic_id, format=sample_format, channels=channels, rate=frame_rate, frames_per_buffer=chunk, input=True)
		
		with Progress() as recording_progress:
			recording_task = recording_progress.add_task("[red]Recording...", total=timeout)
			
			#recording_progress.start_task(recording_task)
			#recording_progress.update(recording_task, advance = 60)
			
			#while (current_time - start_time) < timeout:
			while not recording_progress.finished:
				recording_progress.update(recording_task, completed = current_time - start_time)
			
				
				#print((current_time - start_time) - timeout)
				
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