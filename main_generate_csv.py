from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.progress import track
from rich.table import Table

import pdfplumber

from spacy.lang.de import German
from spacy.lang.en import English
from spacy.lang.fr import French
from spacy.lang.it import Italian

import glob
import os
import re
import sys

from datetime import datetime, timedelta

replacement_map = {
	'«': '"',
	'»': '"',
	'“': '"',
	'„': '"'
}

if __name__ == '__main__':

	console = Console()
		
	table = Table()
	table.add_column("TSS CSV Generator", style="cyan")
	table.add_row("This tool extracts texts from the sample folder, splits them into sentence and creates a metadata.csv to be used with the generator.")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	
	console.print(table)
	
	app_folder = os.path.dirname(os.path.realpath(__file__))
	
	now = datetime.now()
	project_folder = os.path.join(app_folder, 'project_' + now.strftime("%d%m%Y_%H%M%S"))
	console.print("Please select a [red]project folder[/red] (default [i]%s[/i])." % project_folder)
	in_project_folder = input()
	if not in_project_folder:
		in_project_folder = project_folder
	project_folder = in_project_folder
	if not os.path.exists(project_folder):
		os.mkdir(project_folder)
		
	console.print("Project folder is %s" % project_folder)
	
	# Select languages
	console.print("Please select a [red]language[/red] (default [i]%s[/i])." % 'de')
	in_lang = input()
	if not in_lang:
		in_lang = 'de'
	console.print("Language is set to [red]%s[/red]." % in_lang)
	
	# Select file types to read
	console.print("Please select the file types you want to load (t=text, p=pdf, tp=both) (default [i]tp[/i])")
	in_file_types = input()
	if not in_file_types:
		in_file_types = "tp"
	if not 't' in in_file_types and not 'p' in in_file_types:
		in_file_types = "tp"
		
	# Display number of text files
	if 't' in in_file_types:
		text_files = glob.glob(os.path.join(app_folder, 'texts', in_lang + '*.txt'))
		console.print("Found %d text files for %s" % (len(text_files), in_lang))
		
		# 1. Read text files
		all_texts = ''
		for tf in text_files:
			f = open(tf, "r", encoding= 'utf-8')
			all_texts += f.read() + '\n'
		
	# Display number of pdf files
	if 'p' in in_file_types:
		pdf_files = glob.glob(os.path.join(app_folder, 'texts', in_lang + '*.pdf'))
		console.print("Found %d pdf files for %s" % (len(pdf_files), in_lang))

		for pdf_file in pdf_files:
			with pdfplumber.open(pdf_file) as pdf:
				for page in pdf.pages:
					page_text = page.extract_text()
					if page_text:
						all_texts +=  page_text + '\n'
					
	# split texts by sentences
	if in_lang == 'de':
		nlp = German()
	elif in_lang == 'en':
		nlp = English()
	elif in_lang == 'fr':
		nlp = French()
	elif in_lang == 'it':
		nlp = Italian()
	else:
		console.print("The language %s is not supported yet. Please create a github issue." % in_lang)
		sys.exit(0)
	
	nlp.add_pipe('sentencizer')

	# Split every 100000 characters
	split_text = [all_texts[i:i+100000] for i in range(0, len(all_texts), 100000)]
	all_sentences = []
	for st in split_text:
		doc = nlp(st)
		all_sentences.extend([str(sent).strip() for sent in doc.sents])

	console.print("Found %d sentences." % len(all_sentences))

	# Write metadata.csv
	csv_file_name = 'metadata.csv'
	csv_file_path = os.path.join(project_folder, csv_file_name)
	csv_file = open(csv_file_path, 'a', encoding = 'utf-8')
	# todo cleanse text
	for index, sentence in enumerate(all_sentences):
		sentence = sentence.replace("\n", " ")
		sentence = sentence.replace("\t", " ")
		
		# clean text
		cleansed_sentence = sentence
		
		for character, replacement in replacement_map.items():
			cleansed_sentence = cleansed_sentence.replace(character, replacement)
		
		wav_file_name = (str(index) + '.wav').rjust(12, '0')
		
		if len(cleansed_sentence) > 5:
			csv_file.write(wav_file_name + "|" + sentence + "|" + cleansed_sentence + '\n')
	
	csv_file.close()		
	
	duration_in_seconds = len(all_sentences) * 4
	duration = timedelta(seconds=duration_in_seconds)
	
	console.print("%d sentence written to %s. These are approximately %s of audio." % (len(all_sentences), csv_file_name, duration))