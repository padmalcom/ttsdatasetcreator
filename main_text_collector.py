from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track
import wikipedia
import re
import os
import random
import sys

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
	in_file_count = int(input())
	if not in_file_count:
		in_file_count = default_file_count
	console.print("Will collect [red]%d[/red] files." % in_file_count)	
	
	# collect articles
	wikipedia.set_lang(in_lang)
	
	topics = wikipedia.random(pages = in_file_count)
	files_written = 0
	for n in track(range(len(topics)), description="Processing..."):
		
		try:
			page = wikipedia.page(topics[n])
		except wikipedia.exceptions.DisambiguationError as e:
			page = random.choice(e.options)
		
		console.print("\n(%d/%d) Processing page on %s..." % (n, len(topics), page.title))

		content = page.summary
		
		# clean		
		# remove text in brackets
		pattern1 = r'\(.*?\)'
		content = re.sub(pattern1, '', content)
		
		pattern2 = r'==(.*?)=='
		content = re.sub(pattern2, '', content)
	
		i = 0
		while os.path.exists(os.path.join(texts_folder, in_lang + "_wiki" + str(i) + ".txt")):
			i += 1
			
		text_file_path = os.path.join(texts_folder, in_lang + "_wiki" + str(i) + ".txt")
		text_file = open(text_file_path, 'a', encoding = 'utf-8')
		text_file.write(content)
		text_file.close()
		files_written += 1
	
	console.print("%d files were written." % files_written)
		
	