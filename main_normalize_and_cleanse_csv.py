from rich import print
from rich.console import Console
from rich.table import Table

import glob
import os
import sys
import csv

c_map_de = {
	'€': 'euro',
	'$': 'dollar',
	'mr.': 'Mister',
	'mrs.': 'Mistress',
	'mme': 'Madame',
	'etc.': 'et cetera',
	'usw.': 'und so weiter',
	
	
	'“': '"',
	'„': '"'
}

def cleanse(text, lang):
	# todo
	return text

if __name__ == '__main__':

	console = Console()
		
	table = Table()
	table.add_column("CSV text normalizer", style="cyan")
	table.add_row("Normalizes a metadata.csv by looking at the second column and normalizing numbers and abreviations.")
	table.add_row("2021 - padmalcom")
	table.add_row("www.stonedrum.de")
	
	
	console.print(table)
		
	# Select a project folder
	app_folder = os.path.dirname(os.path.realpath(__file__))
	project_directories = glob.glob(os.path.join(app_folder, 'project*/'))
	
	if len(project_directories) == 0:
		console.print("There are no project directories. Create a folder starting with 'project' that contains a 'metadata.csv'. This works best using main_generate_csv.py.")
		sys.exit(0)
		
	console.print("Please select a [red]project folder[/red] by entering its id (default 0 (%s))" % project_directories[0])
	for index, pd in enumerate(project_directories):
		console.print("%d: %s" % (index, pd))
	
	in_folder_id = input()
	if not in_folder_id:
		in_folder_id = 0
	project_folder = project_directories[int(in_folder_id)]
	
	metadata_csv_file = os.path.join(project_folder, 'metadata.csv')
	if not os.path.exists(metadata_csv_file):
		console.print("Project folder does not contain a metadata.csv file. Exiting.")
		sys.exit(0)
	
	console.print("Project folder is [red]%s" % project_folder)
	
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
	
	with open(metadata_csv_file, encoding = "utf-8") as csv_file:
			csv_reader = csv.reader(csv_file, delimiter='|')
			csv_data = list(csv_reader)
			
	console.print("Found %d sentences." % len(csv_data))

	if len(csv_data) == 0:
		console.print("You need to add some sentences to your text files first. Exiting.")
		sys.exit(0)
		
	metadata_csv_file_normalized = os.path.join(project_folder, 'metadata_normalized.csv')
	csv_out = open(metadata_csv_file_normalized, 'wb')
	writer = csv.writer(csv_out, delimiter='|')
	
	i = 0
	while i < len(csv_data):
		# clean missing wav files
		if os.path.exists(os.path.join(project_folder, csv_data[i][0])):
		
			# normlize
			cleansed = cleanse(csv_data[i], in_lang)
			writer.write([csv_data[i][0], csv_data[i][1], cleansed])
		i += 1
	csv_out.close()
		
	os.rename(metadata_csv_file, os.path.join(project_folder, 'metadata_original.csv'))
	os.rename(metadata_csv_file_normalized, metadata_csv_file)
	console.print("Done")
	
	