import decimal
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track
import wikipedia
import re
import os
import random
import sys
from num2words import num2words
from transformers import AutoTokenizer, T5ForConditionalGeneration

from spacy.lang.de import German
from spacy.lang.en import English
from spacy.lang.fr import French
from spacy.lang.it import Italian

# Cleansing
tokenizer = AutoTokenizer.from_pretrained("flexudy/t5-base-multi-sentence-doctor")
model = T5ForConditionalGeneration.from_pretrained("flexudy/t5-base-multi-sentence-doctor")

def clean_sentence(text):
	input_text = "repair_sentence: " + text + " context: {}{} </s>"
	input_ids = tokenizer.encode(input_text, return_tensors="pt")
	outputs = model.generate(input_ids, max_length=128, num_beams=1)
	return tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

currencies = {
	'de_$': 'Dollar',
	'de_€': 'Euro',
	'de_₿': 'Bitcoin',
	'de_£': 'Pfund',
	'en_$': 'dollar',
	'en_€': 'euro',
	'en_₿': 'bitcoin',
	'en_£': 'pound',
}

def normlize_text(text, lang, nlp, clean = False):

	# tokenize
	doc = nlp(text)
	res = []
	for token in doc:
		new_token = ''

		# numbers
		if token.like_num:
			try:
				# ordinals
				if token.text.endswith('.'):
					#new_token = num2words(token.text, lang=lang, to = 'ordinal')
					new_token = token
				else:
					new_token = num2words(token.text, lang=lang)
			except NotImplementedError:
				print("Warning, language %s not supported for text normalization." % lang)
				new_token = token.text
		# currencies
		elif token.is_currency:		
			if lang + '_' + token.text in currencies:
				new_token = currencies[lang + '_' + token.text]
			else:
				new_token = token.text
		else:
			new_token = token.text
		res.append(new_token)
	sentence = ' '.join(res)
	
	if clean:
		sentence = clean_sentence(sentence)
	return sentence	


if __name__ == '__main__':
	console = Console()
	
	app_folder = os.path.dirname(os.path.realpath(__file__))
	texts_folder = os.path.join(app_folder, "texts")
	
	table = Table()
	table.add_column("TSS Dataset Collector", style="cyan")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	table.add_row("This tool collects texts from wikipedia and requires internet connection.")
	
	# Select language
	default_lang = 'de'
	console.print("Please select a [red]language[/red] to collect data for (default [i]%s[/i])." % default_lang)
	in_lang = input()
	if not in_lang:
		in_lang = default_lang
		
	if not in_lang in wikipedia.languages():
		console.print("Language [red]%s[/red] is not supported by wikipedia." % in_lang)
		sys.exit(0)
		
	console.print("Language is set to [red]%s[/red]." % in_lang)
	
	# Select amount of files
	default_file_count = 100
	console.print("Please select a [red]file count[/red] (default [i]%d[/i])." % default_file_count)
	in_file_count = input()
	if not in_file_count or not in_file_count.isdigit():
		in_file_count = default_file_count
	in_file_count = int(in_file_count)
	console.print("Will collect [red]%d[/red] files." % in_file_count)
	
	# Normalize and clean text
	console.print("Please specify if you want to [red]normalize (n)[/red] and/or [red]clean (c)[/red] texts (highly experimental). [red](nc)[/red] for both. (default [i]none[/i]).")
	normalize_and_clean = input()
	normalize_text = 'n' in normalize_and_clean
	clean_text = 'c' in normalize_and_clean
	console.print("Clean text? [red]%r[/red], normlize text? [red]%r[/red]." % (clean_text, normalize_text))
	
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
	
	# collect articles
	wikipedia.set_lang(in_lang)
	
	
	files_written = 0
	
	# wikipedia can only get 500 pages at once
	
	topics = []
	while in_file_count > 0:
		new_topics = wikipedia.random(pages = in_file_count)
		print("New topics %d" % len(new_topics))
		topics.extend(new_topics)
		in_file_count -= 500
		
	print("Topics: %d" % len(topics))
	
	for n in track(range(len(topics)), description="Processing..."):
		
		try:
			page = wikipedia.page(topics[n])
		except wikipedia.exceptions.DisambiguationError as e:
			random_topic = random.choice(e.options)
			
			try:
				page = wikipedia.page(random_topic)
			except wikipedia.exceptions.DisambiguationError as e:
				print("Topic [red]%s[/red] is an ambiguity. Skipping" % random_topic)
				continue
		
		console.print("\n(%d/%d) Processing page on %s..." % (n, len(topics), page.title))

		content = page.summary
		
		# clean		
		# remove text in brackets
		pattern1 = r'\(.*?\)'
		content = re.sub(pattern1, '', content)
					
		pattern2 = r'==(.*?)=='
		content = re.sub(pattern2, '', content)
		
		pattern3 = r'\[.*?\]'
		content = re.sub(pattern3, '', content)

		
		if normalize_text:
			content = normlize_text(content, in_lang, nlp, clean_text)
	
		i = 0
		while os.path.exists(os.path.join(texts_folder, in_lang + "_wiki" + str(i) + ".txt")):
			i += 1
			
		text_file_path = os.path.join(texts_folder, in_lang + "_wiki" + str(i) + ".txt")
		text_file = open(text_file_path, 'a', encoding = 'utf-8')
		text_file.write(content)
		text_file.close()
		files_written += 1
	
	console.print("%d files were written." % files_written)
		
	
