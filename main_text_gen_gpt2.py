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

from spacy.lang.de import German
from spacy.lang.en import English
from spacy.lang.fr import French

from transformers import pipeline


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

def normlize_text(text, lang, nlp):

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
	
	return sentence	

if __name__ == '__main__':

	console = Console()
	
	app_folder = os.path.dirname(os.path.realpath(__file__))
	texts_folder = os.path.join(app_folder, "texts")
	
	table = Table()
	table.add_column("TSS GPT Text Generator", style="cyan")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	table.add_row("This tool generates texts using GPT-2 language models.")
	
	# Select language
	default_lang = 'de'
	console.print("Please select a [red]language[/red] to collect data for (default [i]%s[/i])." % default_lang)
	in_lang = input()
	if not in_lang:
		in_lang = default_lang
		
	if not in_lang in ['de', 'en', 'fr']:
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
	console.print("Please specify if you want to [red]normalize (n)[/red] texts. (default [i]none[/i]).")
	normalize_and_clean = input()
	normalize_text = 'n' in normalize_and_clean
	console.print("Normlize text? [red]%r[/red]." % normalize_text)
	
	# split texts by sentences
	if in_lang == 'de':
		nlp = German()
		#pipe = pipeline('text-generation', model="benjamin/gerpt2-large", tokenizer="benjamin/gerpt2-large", device = 0)
		pipe = pipeline('text-generation', model='Tanhim/gpt2-model-de', tokenizer='Tanhim/gpt2-model-de')
		text = pipe("Der Sinn des Lebens ist es", max_length=100)[0]["generated_text"]
	elif in_lang == 'en':
		nlp = English()
		pipe = pipeline('text-generation', model="gpt2", device = 0)
		text = pipe("The meaning of life is", max_length=100)[0]["generated_text"]
	elif in_lang == 'fr':
		nlp = French()
		pipe = pipeline('text-generation', model="antoiloui/belgpt2", tokenizer="antoiloui/belgpt2", device = 0)
		text = pipe("Le sens de la vie est", max_length=100)[0]["generated_text"]		
	else:
		console.print("The language %s is not supported yet. Please create a github issue." % in_lang)
		sys.exit(0)
	
	nlp.add_pipe('sentencizer')
	
	# Get all sentences from text except the first one
	doc = nlp(text)
	
	# Keep sentences with a proper ending
	all_sentences = [str(sent).strip() for sent in doc.sents if str(sent).strip().endswith(('.', '!', '?'))]
	
	# If there are enough sentences, remove the one used for generation
	if len(all_sentences) > 1:
		all_sentences = all_sentences[1:]
		
	gen_sentence = ' '.join(all_sentences)
	console.print("Initial text: [magenta]%s" % gen_sentence)
	
	# Generate as much text as desired
	files_written = 0
	#for n in track(range(in_file_count), description="Processing..."):
	n = 0
	while n < in_file_count:
		
		console.print("(%d/%d) Processing sentence ..." % ((n+1), in_file_count))
		
		# Generate new sentences based on the last n characters
		prefix = gen_sentence[-min(300, len(gen_sentence)):]
		#console.print("Using prefix [green]%s[/green] of text [green]%s[/green] for generation." % (prefix, gen_sentence))
		gen_result = pipe(prefix, max_length=150)
		if len(gen_result) > 0:
			text = pipe(prefix, max_length=150)[0]["generated_text"]
		else:
			continue
			
		if len(text) == 0:
			print("No valid output was generated. Please restart.")
			sys.exit(0)
		
		# cut the prefix
		text = text[len(prefix):]
		doc = nlp(text)
		all_new_sentences = [str(sent).strip() for sent in doc.sents if str(sent).strip().endswith(('.', '!', '?'))]
		
		# If there are enough sentences, remove the one used for generation
		if len(all_new_sentences) > 1:
			all_new_sentences = all_new_sentences[1:]
			
		gen_sentence = ' '.join(all_new_sentences)
		console.print("Generated sentence(s): %s" % gen_sentence)

		if normalize_text:
			gen_sentence = normlize_text(gen_sentence, in_lang, nlp)
			
		# remove brackets
		gen_sentence = re.sub(".*?\((.*?)\).*?", "", gen_sentence)
		gen_sentence = re.sub(".*?\[(.*?)\].*?", '', gen_sentence)
		
		# replace linebreaks and tabs
		gen_sentence = gen_sentence.replace("\n", " ")
		gen_sentence = gen_sentence.replace("\t", " ")
		
	
		i = 0
		while os.path.exists(os.path.join(texts_folder, in_lang + "_gpt" + str(i) + ".txt")):
			i += 1
			
		text_file_path = os.path.join(texts_folder, in_lang + "_gpt" + str(i) + ".txt")
		text_file = open(text_file_path, 'a', encoding = 'utf-8')
		text_file.write(gen_sentence)
		text_file.close()
		files_written += 1
		n += 1
	
	console.print("%d files were written." % files_written)
		
	