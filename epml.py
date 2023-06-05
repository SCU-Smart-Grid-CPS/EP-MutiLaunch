# epml.py (epgui.py)
# EnergyPlus MultiLaunch Script
# Author(s):    Brian Woo-Shem
# Version:      0.50
# Last Updated: 2023-06-05


# Import
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
import webbrowser
import time
from configparser import ConfigParser
import subprocess
import os
import csv
import sys #for logging
#from tkinter import *


# File & String Manipulation Functions

# Convert tuple to string where each entry is a new line
# Input: t = tuple containing one or more strings
# Returns: s = string where each entry is on a new line
def tuple2str(t):
	s = ''
	for i in t:
		s = s + '\n' + i
	return s

#Remove specified file extension if it is present from a string representing the output file name
# Input:
#	c = string with filename
#	ext = file extension as a string (ex. '.txt')
# Returns: string with filename but no extension
# Examples:
# 1. remExt('myfile.txt','.txt') => 'myfile'
# 2. remExt('myfile','.txt') => 'myfile'
def remExt(c, ext):
	if c[len(c)-len(ext): len(c)] == ext: c = c[:len(c)-len(ext)]
	return c

# Get file path from a string, assumes string contains filepath
#prev is a way to handle if fs is not valid
def getPath(fs,prev):
	# returns index of last instance of '/' character, or -1 if '/' not found
	try:
		i = fs.rindex('/')
		#handle windows filesystems.
		if i == -1:
			i = fs.rindex('\\')
			if i == -1:
				print('Warning: new path not found from the following string; using previous instead')
				print(fs)
				return prev
	except (ValueError):
		print('Warning: new path not found from the following string; using previous instead')
		print(fs)
		return prev
	return str(fs[:i])

# Extract only the name of a file from a filepath
# Input: 
#	String fs
#	String ext = the file extension
# Returns: String containing just the file name
# Dependencies: remExt(c, ext)
# Example: getFileName('/home/random/directories/myfile.txt', '.txt') => 'myfile'
def getFileName(fs,ext):
	#Attempting to handle Windows vs Linux file delimiter issues
	fs = fs.replace('\\','/')
	i = fs.rindex('/')
	if i == -1:
		i = fs.rindex('\\')
	return remExt(str(fs[i+1:]),ext)


#Format a string from typical code text box entry to format that can be stored in .ini file
# issue is ', ", \, newline, tab will cause formatting errors when reading .ini
# PROBLEMS
# .ini does not support multiline variables. 
# https://stackoverflow.com/questions/33930852/how-to-insert-multi-line-value-using-configparser
# https://stackoverflow.com/questions/11399665/new-lines-with-configparser
# Either need to convert them into single line - this creates new problem if the user
# inputs a string like 
#    print('one\ntwo')
# which gets stored as
#	 print('one
#	 two')
# and cannot be converted back easily
# OR need to save it as something with a tab on each subsequent line
# example:
# 	variable = print('one')
#		print('two')
#
# TODO [high priority]: Find a workaround to this bug
# - worst case, can change it so each pre/postcode variable saves to a different text file, which would allow reading mutiline without any conversions

def text_to_ini(s):
	#several attempts that don't work
	
	# ini does not support triple quote method
	#s = '\'\'\'' + s + '\'\'\''
	
	#Tried splitting by other newline characters, problem is both true new line and new line within a user
	# created string both use '\n' and there's no good way to differentiate. 
	'''
	ss = s.split('\u2028')
	s2 = ''
	for line in ss:
		s2 = s2 + line + '\u2028\t'
	'''
	
	#buggy - if you insert a 
	# Newline character
	s = s.replace('\n','\\n')
	# Tab to "\t"
	s = s.replace('\t','\\t')
	# Put a backslash in front of every quote mark in the code
	s = s.replace('\'',"\\'")
	s = s.replace('\"','\\"')
	#s = s.replace('\\','\\\\')
	
	return s

#Undo formatting in text_to_ini()
def ini_to_text(s):
	#s = s[3:len(s)-3]
	
	# Newline character
	s = s.replace('\\n','\n')
	# Tab to "\t"
	s = s.replace('\\t','\t')
	# Put a backslash in front of every quote mark in the code
	s = s.replace("\\'",'\'')
	s = s.replace('\\"','\"')
	#s = s.replace('\\\\','\\')
	
	return s


# Load settings =============================================================================================
cp = ConfigParser()
setfile = 'ep_multilaunch_settings.ini'
cp.read(setfile)
try:
	sp = cp.get('general','sp')
	dtime = int(cp.get('general','dtime'))
	ep_dir = cp.get('general','ep_dir')
	fpath_select_idf = cp.get('filepaths','fpath_select_idf')
	fpath_select_epw = cp.get('filepaths','fpath_select_epw')
	fpath_folder = cp.get('filepaths','fpath_folder')
	fpath_queue = cp.get('filepaths','fpath_queue')
	precode = ini_to_text(cp.get('general','preprocessing_code'))
	postcode = ini_to_text(cp.get('general','postprocessing_code'))
	precodepy = ini_to_text(cp.get('general','preprocessing_code_python'))
	postcodepy = ini_to_text(cp.get('general','postprocessing_code_python'))
	useLogTemp = cp.get('general','use_log_file')
	if 'T' in useLogTemp: useLog = True
	else: useLog = False
except (NameError, ValueError, KeyError, IOError): #note ConfigParser.NoOptionError is not catchable. could use Exception
	print("Warning: Could not get settings from ",setfile," \n Using default settings")
	sp = 'parallel'
	dtime = 30
	ep_dir = 'C:\EnergyPlusV9-4-0\energyplus'
	fpath_select_idf = '/'
	fpath_select_epw = '/'
	fpath_folder = '/'
	fpath_queue = '/'
	precode = ''
	postcode = ''
	precodepy = ''
	postcodepy = ''
	useLog = False

# Set up ability to switch output between log file or console
# https://stackoverflow.com/questions/11124093/redirect-python-print-output-to-logger#11124247
# https://stackoverflow.com/questions/59255738/how-to-toggle-sys-stdout-between-a-file-and-terminal
console = sys.stdout
log = open('epml_out.log','w')

# Function to save all settings that go in the .ini file
# Called whenever new directory is selected to save filepath & whenever advanced settings are applied
def saveSettings():
	global sp
	global dtime
	global ep_dir
	settings_str = '[general]\nsp = '+sp+'\ndtime = '+str(dtime)+'\nep_dir = '+ep_dir+'\n'
	
	global precode
	global postcode
	global precodepy
	global postcodepy
	# Handle log vs console setting
	global useLog
	#print('\nAll output will be written to epml_out.log. Please check log for any errors\n')
	if useLog:
		sys.stdout = log
	else:
		sys.stdout = console
	
	#Replace() is for handling new line: .ini can't read a true newline, but can write literal "\n" in a string
	process_code_str = '\n' + 'preprocessing_code = ' + text_to_ini(precode) + '\npostprocessing_code = ' + text_to_ini(postcode) + '\npreprocessing_code_python = ' + text_to_ini(precodepy) + '\npostprocessing_code_python = ' + text_to_ini(postcodepy) +  '\nuse_log_file = ' + str(useLog) + '\n'
	#process_code_str = '\n' + 'preprocessing_code = ' + text_to_ini(precode) + '\npostprocessing_code = ' + postcode.replace('\n','\\n') + '\npreprocessing_code_python = ' + precodepy.replace('\n','\\n') + '\npostprocessing_code_python = ' + postcodepy.replace('\n','\\n') +  '\nuse_log_file = ' + str(useLog) + '\n'
	
	# Get file paths stored in global variables
	global fpath_select_idf
	global fpath_select_epw
	global fpath_folder
	global fpath_queue
	
	fpath_str = '\n[filepaths]\nfpath_select_idf = '+fpath_select_idf+'\nfpath_select_epw = '+fpath_select_epw+'\nfpath_folder = '+fpath_folder+'\nfpath_queue = '+fpath_queue+'\n'
	
	# Combine strings
	set_contents = settings_str + process_code_str + fpath_str
	
	# Overwrite settings ini file with new settings and filepaths
	global setfile
	stxt = open(setfile, "w")
	stxt.write(set_contents)
	stxt.close()
	
	print('saved settings as:\n',set_contents)
	

# Functions for running simulations ==========================================================================

def searchfolder(folderpath):
	idffiles = []
	idfpaths = []
	epwpaths = []
	weatherfile = 'NONE'
	# Perform search to detect all .idf files in the parent and subdirectories
	#  and get their full directory paths
	for root, dirs, files in os.walk(folderpath):
		for file in files:
			#Find all .idf files. Autoignores "failsafe.idf" file used as a backup when another fails.
			if file.endswith('.idf') and 'failsafe' not in file:
				idfpaths.append(os.path.join(root,file))
				idffiles.append(file)
			#Find all .epw files
			elif file.endswith('.epw'):
				epwpaths.append(os.path.join(root,file))

	# Get number of simulations
	numSims = len(idffiles)
	print('Found ', numSims, ' .idf simulation files.')
	print(idffiles)

	# Alphabetize the list of simulations (they are random otherwise)
	simtuples = [(idffiles[i], idfpaths[i]) for i in range(0, numSims)]
	simsSorted = sorted(simtuples, key=lambda s: s[0])
	
	# handles if it finds more than 1 .epw file
	if len(epwpaths) > 1:
		print('WARNING: Detected multiple weather files, using first one.')
	# save weather file
	if len(epwpaths) > 0:
		weatherfile = epwpaths[0]
	
	# Throw error if no epw file found
	if weatherfile == 'NONE' or len(epwpaths) < 1:
		print('ERROR: No .epw file found!')
	else: #Got valid weather file
		print('Using weather file: ', weatherfile)
	
	return [idfpaths, weatherfile]

# sims2run and wfiles are lists of strings
def run_ep_series(sims2run,wfiles):
	print("Queued ", len(sims2run), " E+ sims:")
	folderDelim = '/'
	errorcount = 0
	worked = True

	for sim,wfile in zip(sims2run,wfiles):
		if not len(sim) == 0:
			# Create run command
			runcmd = ep_dir + ' --readvars --output-directory \"' + remExt(sim,'.idf') + '\" -w \"' + wfile + '\" \"' + sim + '\"'

			print(runcmd)

			#Launch subprocess in the shell
			epproc = subprocess.run(runcmd, capture_output=True, shell=True)
			print(epproc.stdout)
			print(epproc.stderr)

			#Display result. 0 = success; else failure
			print(" returned: ", epproc.returncode)
			# Detect error
			if epproc.returncode != 0:
				errorcount = errorcount + 1
				worked = False
				if epproc.returncode == 1:
					print('ERROR: Incorrect filepath for output-directory, weather, and/or sim ', sim)
				else:
					print('WARNING: Simulation ', sim, ' has errors, check .err file!')
			#else: #Successful run, now do postprocessing
				#epoutfilename = remExt(sim,'.idf') + folderDelim + 'eplusmtr.csv'
	
	return worked

def run_ep_parallel(sims2run,wfiles):
	# Folder delimiter
	folderDelim = '/'
	pn = 0
	global ep_dir
	global dtime

	#Initialize a list to hold all subprocesses, each which runs one simulation
	simprocesses = []
	simp_out = []
	
	# "Launch code" from which simulation will be launched in Python -> Command line
	# run_PPPP.py - change port number = PPPP, filenames for .idf and .epw
	# uses a "template" launch code file called run_TEMPLATE.py and changes a few things.
	run_template = "run_TEMPLATE.py"
	runtempfile = open(run_template, 'r')
	run_contents = runtempfile.read()
	
	# create directory to put launchcodes
	if not os.path.exists("launchcodes"):
		os.makedirs("launchcodes")
	
	#Create launch code for each simulation
	for sim,wfile in zip(sims2run,wfiles):
		if not len(sim) == 0:
			# This part needs to be in loop for all simulations
			run_filename = "launchcodes" + folderDelim + "run_" + str(pn) + ".py"
			runfile = open(run_filename, "a")
			runfile.truncate(0) #delete existing contents
			# Replace variables (keystrings) from the template with their actual values for this simulation
			print('sim = ',sim)
			print('simname = ',getFileName(sim,'.idf'))
			runtowrite = run_contents.replace("PPPP",getFileName(sim,'.idf'))
			#don't replace to avoid errors
			runtowrite = runtowrite.replace("SIMULATION_FILENAME",sim.replace('\\','/'))
			runtowrite = runtowrite.replace("WEATHER_FILENAME",wfile.replace('\\','/'))
			runtowrite = runtowrite.replace("ENERGYPLUS_DIRECTORY",ep_dir)
			runtowrite = runtowrite.replace("OUTPUT_DIRECTORY",remExt(sim,'.idf'))
			
			runfile.write(runtowrite)
			runfile.close()
			pn = pn + 1
	
	last = pn
	pn = 0
	
	# Iteratively start codes to run each simulation in parallel
	# each run_####.py code is needed to handle the relaunch and the parallelization
	# time.sleep(seconds) is a delay to prevent crashing the computer during warmup/initialization
	while pn < last:
		#edit - changed to launchcodes\run####.py folder
		pname = "Py launchcodes" + folderDelim + "run_" + str(pn) + ".py"
		print("Launching: ", pname)
		p = subprocess.Popen(pname, shell=True)
		#TODO [Low priority]: make outputs fromm the run_####.py go to log not command line when useLog = True
		# https://stackoverflow.com/questions/2502833/store-output-of-subprocess-popen-call-in-a-string
		#p = subprocess.Popen(pname, stdout=subprocess.PIPE)
		simprocesses.append(p)
		#out,err = p.communicate()
		#simp_out.append(out)
		time.sleep(dtime)
		pn = pn+1

	# At this point, all simulations are running in parallel
	print('\nAll simulations launched! Please wait while simulations run.\n')

	# Wait for all simulations to complete
	for sp in simprocesses:
		sp.wait()
	
	worked = True
	errorcount = 0
	'''
	for so in sim_out:
		if 'ERROR' in so or 'failsafe' in so:
			worked = False
			errorcount = errorcount + 1
	'''
	# All simulations complete
	print("Done running simulations!\n")
	
	return worked

# Run preprocessing code
def runBefore():
	global precode
	global precodepy
	
	# Bash cannot handle multiline commands. It only runs the first line
	'''
	execute_bash = subprocess.run(precode, capture_output=True, shell=True)
	print(execute_bash.stdout)
	print(execute_bash.stderr)
	'''
	precode_list = precode.split('\n')
	
	for line in precode_list:
		print('Run >> ', line)
		execute_bash = subprocess.run(line, capture_output=True, shell=True)
		print(execute_bash.stdout)
		print(execute_bash.stderr)
	
	# Run Python. 
	# Python can handle multiline including loops, etc. 
	exec(precodepy)
	
	'''
	precode_list = precode.split('\n')
	
	for line in precode_list:
		execute_code = subprocess.run(line, capture_output=True, shell=True)
	
	precodepy_list = precodepy.split('\n')
	
	for line in precodepy_list:
		exec(line)
	'''

# Run postprocessing code
def runAfter():
	global postcode
	global postcodepy
	
	# Run Bash code, one line at a time.
	postcode_list = postcode.split('\n')
	
	for line in postcode_list:
		print('Run >> ', line)
		execute_bash = subprocess.run(line, capture_output=True, shell=True)
		print(execute_bash.stdout)
		print(execute_bash.stderr)
	
	# Run Python. 
	# Python can handle multiline including loops, etc. 
	exec(postcodepy)


# Create GUI in Tkinter ======================================================================================
# Root window
w = tk.Tk()
# Set size
# - Needed to control size of scrolledtext elements in Advanced Settings (tab5) otherwise window will overflow the monitor
# - TODO [low priority]: devise a method that considers current screen resolution/size so it's not giant on low resolution monitors or tiny on 4k screens. 
w.geometry("800x600")

# Window title
w.title('EnergyPlus MultiLaunch')
'''
icon_16 = tk.PhotoImage(file='epgui_16.png')
icon_32 = tk.PhotoImage(file='epgui_32.png')
icon_128 = tk.PhotoImage(file='epgui_128.png')
w.iconphoto(False, icon_128, icon_32) #, icon_16)
'''
w.iconbitmap('epgui_icon.ico')

# Create tabs
tabs = ttk.Notebook(w)
tab1 = ttk.Frame(tabs)
tab2 = ttk.Frame(tabs)
tab3 = ttk.Frame(tabs)
tab4 = ttk.Frame(tabs)
tab5 = ttk.Frame(tabs)
tabs.add(tab1, text='Select Files to Run')
tabs.add(tab2, text='Autodetect in Folder')
tabs.add(tab3, text='Queue File')
tabs.add(tab4, text='Advanced Settings')
tabs.add(tab5, text='About')
tabs.pack(expand = 1, fill="both")


# background color
w.config(background = "white")

# Status messages
status_running = 'Running simulations, please wait...\nThis window may show (Not Responding) while simulations run.\n Do not close this window! It will respond again when simulations are complete.'
status_success = 'Simulations Completed Successfully!'
status_ready = 'Simulations Ready!'
status_failed = 'Error: Simulations Failed! Please check log and .err files.'
# Status message colors #Extra Note is colorname in Brian's custom palette
color_select = '#e5fbff' #FaintBlueTint
color_ready = '#95e0ff' #BrightSkyBlue
color_failed = '#c81a1d' #Bread
color_running = '#ffd900' #LemonDrop
color_success = '#3ed75f' #CRG_Growing_Green

# 1 - Manual select =======================================================================================
epwfilename = ''
numIDF = 0
# Function to select any number of .idf files
# Based on
# https://www.geeksforgeeks.org/file-explorer-in-python-using-tkinter/
# https://www.pythontutorial.net/tkinter/tkinter-open-file-dialog/
def select_idfs():
	
	global fpath_select_idf
	
	filetypes = (
		('idf files','*.idf'),
		('text files', '*.txt'),
		('All files', '*.*')
	)

	filenames = fd.askopenfilenames(
		title='Browse files',
		initialdir=fpath_select_idf,
		filetypes=filetypes
	)
	
	global numIDF
	for fi in range(len(filenames)):
		opened_files_box.insert(1,filenames[fi])
		opened_files_box.itemconfig(fi, bg = 'gray')
		numIDF = numIDF + 1
		
	# Save current filepath to .idf file
	fpath_select_idf = getPath(filenames[0],fpath_select_idf)
	print('Next .idf files directory: ',fpath_select_idf)
	saveSettings()
	
	global epwfilename
	if epwfilename == '':
		status1.config(text = 'Select .epw above.', background=color_select, foreground='black')
	else:
		status1.config(text = status_ready, background=color_ready, foreground='black')
	

def select_epw():
	# Get filepath last used. 
	global fpath_select_epw
	
	filetypes = (
		('EnergyPlus Weather files','*.epw'),
		('Text files', '*.txt'),
		('All files', '*.*')
	)
	
	global epwfilename
	epwfilename = fd.askopenfilename(
		title='Browse files',
		initialdir=fpath_select_epw,
		filetypes=filetypes
	)
	print('Got: ', epwfilename)
	selected_epw.delete('1.0',tk.END)
	selected_epw.insert(tk.END, epwfilename)
	
	# Save current filepath to .epw file
	fpath_select_epw = getPath(epwfilename,fpath_select_epw)
	print('Next epw file directory: ',fpath_select_epw)
	saveSettings()
	
	if numIDF < 1:
		status1.config(text = 'Select .idf above.', background=color_select, foreground='black')
	else:
		status1.config(text = status_ready, background=color_ready, foreground='black')


# From https://www.pythontutorial.net/tkinter/tkinter-listbox/
def remove_opened_files_selected():
	i_select = opened_files_box.curselection()
	selected_filenames = []
	global numIDF
	for i in i_select:
		print('i = ',i)
		selected_filenames.append(opened_files_box.get(i))
		print('Removing: ', opened_files_box.get(i))
		opened_files_box.delete(i)
		numIDF = numIDF - 1
		
	if numIDF < 1:
		if epwfilename == '':
			status1.config(text = 'Select .idf and .epw above.', background=color_select, foreground='black')
		else:
			status1.config(text = 'Select .idf above.', background=color_select, foreground='black')


# instructions
i1 = 'Select one or more EnergyPlus .idf files'
instructions = tk.Label(tab1, text = i1)

i2 = 'Select the EnergyPlus Weather .epw file'
instructions2 = tk.Label(tab1, text = i2)

# open file select
button_select_idfs = tk.Button(tab1, text = 'Select .idf files', command = select_idfs)

button_select_epw = tk.Button(tab1, text = 'Select .epw file', command = select_epw)

selected_epw = tk.Text(tab1,bg='white',height=1)

# list opened files
opened_files_box = tk.Listbox(tab1, selectmode='multiple')#,yscrollcommand=yscrollbar.set)

yscrollbar = ttk.Scrollbar(tab1,orient=tk.VERTICAL,command=opened_files_box.yview)

opened_files_box['yscrollcommand'] = yscrollbar.set

button_remove_idfs = tk.Button(tab1, text='Remove selected files', command=remove_opened_files_selected)

# Very clunky workaround for problem where the config() methods only update at the end of a function
# something about tkinter's order of execution
# using solution from:
# https://stackoverflow.com/questions/30561071/item-config-in-tkinter-execute-together
# https://pythonassets.com/posts/tk-after-function-tkinter/
def run_simulations_select():
	status1.config(text = status_running, background=color_running, foreground='black')
	w.after(10, lambda: run_simulations_select_2())

def run_simulations_select_2():
	runBefore()
	global numIDF
	if not epwfilename == '' and numIDF > 0:
		print('Run simulations via select files method')
		#messages before the sleep don't show up.
		#status1.config(text = 'Running simulations, please wait...', background='#ffd900', foreground='black')
		#status_running()
		
		#another attempt to get a popup message
		#problem is it stalls simulations until the box is clicked
		#tk.messagebox.showinfo('EnergyPlus Parallel Launch Simulation in Progress','Simulations in progress. Please wait.\nEnergyPlus Parallel Launch window may say (Not Responding), this is normal and it will respond again once simulations are complete.')
		
		# generate list of current simulations
		idfs_manual = []
		epw_manual = []
		for i in range(numIDF):
			idfs_manual.append(opened_files_box.get(i))
			epw_manual.append(epwfilename)
		
		res1 = False
		if sp == 'parallel':
			print('run parallel')
			res1 = run_ep_parallel(idfs_manual,epw_manual)
		else:
			print('run series')
			res1 = run_ep_series(idfs_manual,epw_manual)
		#time.sleep(2) #only for testing
		#only the last status1 message appears, after the sleep
		if res1 == True:
			runAfter()
			status1.config(text = status_success, background=color_success, foreground='black')
		else:
			status1.config(text = status_failed, background=color_failed, foreground='white')
	else:
		status1.config(text = 'Error: Invalid .idf filenames inputted. Could not run anything.', background=color_failed, foreground='white')

run1 = tk.Button(tab1, text='Run Simulations', command=run_simulations_select)

status1 = tk.Label(tab1, text = 'Select .idf and .epw above.', background=color_select, foreground='black',borderwidth=2,height=3)

# set up grid
#tab1.grid_rowconfigure(0,weight=1)
tab1.grid_columnconfigure(0,weight=1)
tab1.grid_columnconfigure(1,weight=1)
tab1.grid_rowconfigure(3,weight=2)
#tab1.grid_rowconfigure(7,weight=1)

instructions.grid(column=0,row=1,columnspan=3,sticky='ew')
button_select_idfs.grid(column=0,row=2,sticky='ew')
opened_files_box.grid(column=0,row=3,sticky='nsew',columnspan=2)
yscrollbar.grid(column=2,row=3,sticky='ns')
#button_remove_idfs.grid(column=0,row=4)
button_remove_idfs.grid(column=1,row=2,sticky='ew')
instructions2.grid(column=0,row=4,sticky='ew')
button_select_epw.grid(column=1,row=4,sticky='ew')
selected_epw.grid(column=0,row=5,columnspan=3,sticky='ew')
status1.grid(column=0,row=6,columnspan=3,sticky='ew')
run1.grid(column=1,row=7,sticky='ew')

# 2 - Autodetect =====================================================================================
i_auto_str = 'Automatically detects all .idf files and the .epw file from the selected directory and all subdirectories.'
i_auto = tk.Label(tab2, text = i_auto_str)
#i_auto_2 = tk.Label(tab2, text = 'Select folder')

selected_folder = tk.Text(tab2,bg='white',height=1)

folderpath = ''
list_idf_autodetect = []
epw_autodetect = []
list_epw_autodetect = []

def select_folder():
	global fpath_folder
	
	folderpath = str(fd.askdirectory(initialdir=fpath_folder))
	print('Got: ', folderpath)
	
	selected_folder.delete('1.0',tk.END)
	selected_folder.insert(tk.END, folderpath)
	
	list_idf_epw = searchfolder(folderpath)
	# list_idf_epw = [ [list of idf files] [epw filename] ]
	global list_idf_autodetect
	list_idf_autodetect = list_idf_epw[0]
	global epw_autodetect
	epw_autodetect = list_idf_epw[1]
	
	#Clear listbox
	opened_files_2.delete(0,tk.END)
	#Insert detected files into listbox
	for fi in range(len(list_idf_autodetect)):
		opened_files_2.insert(1,list_idf_autodetect[fi])
		opened_files_2.itemconfig(fi, bg = 'gray')
	
	selected_epw_2.delete('1.0',tk.END)
	selected_epw_2.insert(tk.END, epw_autodetect)
	
	if len(list_idf_autodetect) < 1:
		print('ERROR: None/Invalid .idf in folder selected!')
		status2.config(text = 'Error: No .idf files found in selected folder!', background=color_failed, foreground='white')
	elif epw_autodetect == 'NONE':
		print('ERROR: No .epw found in selected folder!')
		status2.config(text = 'Error: No .epw file found in selected folder!', background=color_failed, foreground='white')
	else:
		# Expand epw_autodetect into list to be compatible
		global list_epw_autodetect
		for i in range(len(list_idf_autodetect)):
			list_epw_autodetect.append(epw_autodetect)
		
		# Save current folder path to settings file
		fpath_folder = getPath(folderpath,fpath_folder)
		print('Next folder search directory: ',fpath_folder)
		saveSettings()
		
		status2.config(text = status_ready, background=color_ready, foreground='black')

button_select_folder = tk.Button(tab2, text = 'Browse Folder', command = select_folder)

def run_simulations_folder():
	status2.config(text = status_running, background=color_running, foreground='black')
	w.after(10, lambda: run_simulations_folder_2())

def run_simulations_folder_2():
	runBefore()
	global list_epw_autodetect
	global list_idf_autodetect
	if len(list_epw_autodetect) > 0 and len(list_idf_autodetect) > 0:
		print('Run simulations via select folder method')
		
		#fix all file delimiters
		for i in range(len(list_idf_autodetect)):
			list_idf_autodetect[i] = list_idf_autodetect[i].replace('\\','/')
		
		#status2.config(text = status_running, background=color_running, foreground='black')
		if sp == 'parallel':
			print('run parallel')
			res2 = run_ep_parallel(list_idf_autodetect,list_epw_autodetect)
		else:
			print('run series')
			res2 = run_ep_series(list_idf_autodetect,list_epw_autodetect)
		
		#Interpret and return result message
		if res2 == True:
			runAfter()
			status2.config(text = status_success, background=color_success, foreground='black')
		else:
			status2.config(text = status_failed, background=color_failed, foreground='white')
	else:
		status2.config(text = 'Error: Invalid folderpath. Could not run anything.', background=color_failed, foreground='white')

run2 = tk.Button(tab2, text='Run Simulations', command=run_simulations_folder)

status2 = tk.Label(tab2, text = 'Select folder above.', background=color_select, foreground='black',borderwidth=2,height=3)
# list opened files
opfiles2_label = tk.Label(tab2, text = 'Input Simulation Files (.idf)')
opened_files_2 = tk.Listbox(tab2, selectmode='multiple')#,yscrollcommand=yscrollbar.set)

yscrollbar2 = ttk.Scrollbar(tab2,orient=tk.VERTICAL,command=opened_files_2.yview)

opened_files_2['yscrollcommand'] = yscrollbar2.set
selepw2_label = tk.Label(tab2, text = 'Weather file (.epw)')
selected_epw_2 = tk.Text(tab2,bg='white',height=1)

# Tab 2 grid
#tab2.grid_rowconfigure(0,weight=1)
tab2.grid_columnconfigure(0,weight=1)
tab2.grid_columnconfigure(1,weight=2)
tab2.grid_rowconfigure(4,weight=1)

i_auto.grid(column=0,row=1,columnspan=3,sticky='ew')
button_select_folder.grid(column=0,row=2,sticky='ew')
selected_folder.grid(column=1,row=2,columnspan=2,sticky='ew')
opfiles2_label.grid(column=0,row=3,columnspan=3,sticky='ew')
opened_files_2.grid(column=0,row=4,sticky='nsew',columnspan=2)
yscrollbar2.grid(column=2,row=4,sticky='ns')
selepw2_label.grid(column=0,row=5,columnspan=3,sticky='ew')
selected_epw_2.grid(column=0,row=6,columnspan=3,sticky='ew')
status2.grid(column=0,row=7,columnspan=3,sticky='ew')
run2.grid(column=1,row=8,sticky='ew')

# 3 - Queue ==========================================================================================
i_q_str = 'Run the specified .idf files with their .epw weather files from the queue .csv file.'
i_q = tk.Label(tab3, text = i_q_str)

queue_file_text = tk.Text(tab3,bg='white',height=1)

queue_file = ''

def select_queue():
	global queue_file
	global fpath_queue
	
	queue_file = str(fd.askopenfilename(title='Browse Queue File',initialdir=fpath_queue))
	print('Got: ', queue_file)
	
	queue_file_text.delete('1.0',tk.END)
	queue_file_text.insert(tk.END, queue_file)
	
	# Save current filepath to queue file
	fpath_queue = getPath(queue_file,fpath_queue)
	print('Next queue file directory: ',fpath_queue)
	saveSettings()
	
	#TODO [medium priority]: Move reading of queue file to here & display the input files and weather file before running like in Autodetect mode
	
	status3.config(text = status_ready, background=color_ready, foreground='black')

button_select_queue = tk.Button(tab3, text = 'Browse Queue File', command = select_queue)

def run_simulations_queue():
	status3.config(text = status_running, background=color_running, foreground='black')
	w.after(10, lambda: run_simulations_queue_2())

def run_simulations_queue_2():
	runBefore()
	global queue_file
	if not queue_file == '':
		try:
			list_idf_queue = []
			list_epw_queue = []
			#read csv with headers
			with open(queue_file) as csvfile:
				readCSV = csv.DictReader(csvfile, delimiter=',')
				for row in readCSV:
					list_idf_queue.append(row['Filepath'])
					list_epw_queue.append(row['Weather'])
			print('Run simulations via queue method')
			#status3.config(text = status_running, background=color_running, foreground='black')
			if sp == 'parallel':
				print('run parallel')
				res3 = run_ep_parallel(list_idf_queue,list_epw_queue)
			else:
				print('run series')
				res3 = run_ep_series(list_idf_queue,list_epw_queue)
			
			#Interpret and return result message
			if res3 == True:
				runAfter
				status3.config(text = status_success, background=color_success, foreground='black')
			else:
				status3.config(text = status_failed, background=color_failed, foreground='white')
		except (KeyError):
			status3.config(text = 'Error: Invalid queue_file. Could not run anything.', background=color_failed, foreground='white')
	else:
		status3.config(text = 'Error: Invalid queue_file. Could not run anything.', background=color_failed, foreground='white')

run3 = tk.Button(tab3, text='Run Simulations', command=run_simulations_queue)

status3 = tk.Label(tab3, text = 'Select queue file .csv above.', background=color_select, foreground='black',borderwidth=2, height=5)

# Tab 3 grid
tab3.grid_columnconfigure(0,weight=1)
tab3.grid_columnconfigure(1,weight=2)
tab3.grid_rowconfigure(4,weight=1)

i_q.grid(column=0,row=1,columnspan=3,sticky='ew')
button_select_queue.grid(column=0,row=2,sticky='ew')
#i_auto_2.grid(column=0,row=2,sticky='ew')
queue_file_text.grid(column=1,row=2,columnspan=2,sticky='ew')
status3.grid(column=0,row=3,columnspan=3,sticky='ew')
run3.grid(column=1,row=4,sticky='ew')


# 4 - Advanced Settings
i_seriesparallel_str = 'Run simulations in series or parallel?'
i_seriesparallel = tk.Label(tab4, text = i_seriesparallel_str)

sp_tk = tk.StringVar()
rb_series = ttk.Radiobutton(tab4, text='Series', value='series', variable=sp_tk)
rb_parallel = ttk.Radiobutton(tab4, text='Parallel', value='parallel', variable=sp_tk)
sp_tk.set(sp)

dtime_tk = tk.StringVar()
dtime_tk.set(str(dtime))
dtime_entry = tk.Entry(tab4, textvariable = dtime_tk)

dtime_label = tk.Label(tab4, text = 'Wait time between launches in seconds')

ep_dir_label = tk.Label(tab4, text = 'EnergyPlus installation directory')
ep_dir_tk = tk.StringVar()
ep_dir_tk.set(ep_dir)
ep_dir_entry = tk.Entry(tab4, textvariable = ep_dir_tk)

uselog_label = tk.Label(tab4, text = 'Output to Log File (epml_out.log) or Console/Terminal/Command Prompt Window')
uselog_tk = tk.BooleanVar()
uselog_true = ttk.Radiobutton(tab4, text='Log File', value=True, variable=uselog_tk)
uselog_false = ttk.Radiobutton(tab4, text='Console (for debugging)', value=False, variable=uselog_tk)
uselog_tk.set(useLog)

# Entry won't allow multiline
'''
precode_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Console/Bash code')
precode_tk = tk.Entry(tab4, text = precode)
postcode_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Console/Bash code')
postcode_tk = tk.Entry(tab4, text = postcode)

precodepy_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Python code')
precodepy_tk = tk.Entry(tab4, text = precodepy)
postcodepy_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Python code')
postcodepy_tk = tk.Entry(tab4, text = postcodepy)
'''

'''
precode_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Console/Bash code')
precode_tk = tk.Text(tab4,height=24)
precode_tk.insert(tk.END, precode)

postcode_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Console/Bash code')
postcode_tk = tk.Text(tab4,height=24)
postcode_tk.insert(tk.END, postcode)

precodepy_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Python code')
precodepy_tk = tk.Text(tab4,height=24)
precodepy_tk.insert(tk.END, precodepy)
postcodepy_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Python code')
postcodepy_tk = tk.Text(tab4,height=24)
postcodepy_tk.insert(tk.END, postcodepy)
'''
#TODO [High priority]: the text boxes appear way too large, and there isn't an obvious way to fix it using grid. --Done
# Solution:
# https://stackoverflow.com/questions/14887610/specify-the-dimensions-of-a-tkinter-text-box-in-pixels
precode_subframe = tk.Frame(tab4,height=50,width=400)
precode_subframe.grid_propagate(False)
precode_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Console/Bash code')
precode_tk = tk.Text(precode_subframe)
# replace is to convert newline stored as literal string "\n" to an actual new line - see saveSettings function for explanation
precode_tk.insert(tk.END, ini_to_text(precode))
precode_ysb = ttk.Scrollbar(precode_subframe,orient=tk.VERTICAL,command=precode_tk.yview)
precode_tk['yscrollcommand'] = precode_ysb.set

precode_tk.pack(side='left', fill='both', expand=True)
precode_ysb.pack(side='right',fill='y')
'''
precode_subframe.grid_columnconfigure(0,weight=1)
precode_tk.grid(column=0,row=1,sticky='nsew')
precode_ysb.grid(column=1,row=1,sticky='ns')
'''

# Easier method is using scrolledtext.
# Both seem to get the same end result
# TODO [low priority]: Change all of these to scrolledtext for consistency
precodepy_subframe = tk.Frame(tab4,height=50)
precodepy_subframe.grid_propagate(False)
precodepy_label = tk.Label(tab4, text = 'Preprocessing code to execute before all simulations - Python code')
#precodepy_tk = tk.Text(tab4,height=24)
precodepy_tk = tk.scrolledtext.ScrolledText(precodepy_subframe)
precodepy_tk.insert(tk.END, ini_to_text(precodepy))
precodepy_tk.pack(side='left', fill='both', expand=True)
#precodepy_tk.grid(column=0,row=1,sticky='nsew')

postcode_subframe = tk.Frame(tab4,height=50)
postcode_subframe.grid_propagate(False)
postcode_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Console/Bash code')
#postcode_tk = tk.Text(tab4,height=24)
postcode_tk = tk.scrolledtext.ScrolledText(postcode_subframe)
#postcode_tk.insert(tk.END, postcode.replace('\\n','\n'))
postcode_tk.insert(tk.END, ini_to_text(postcode))
postcode_tk.pack(side='left', fill='both', expand=True)

postcodepy_subframe = tk.Frame(tab4,height=50)
postcodepy_subframe.grid_propagate(False)
postcodepy_label = tk.Label(tab4, text = 'Postprocessing code to execute after all simulations complete - Python code')
#postcodepy_tk = tk.Text(tab4,height=24)
postcodepy_tk = tk.scrolledtext.ScrolledText(postcodepy_subframe)
#postcodepy_tk.insert(tk.END, postcodepy.replace('\\n','\n'))
postcodepy_tk.insert(tk.END, ini_to_text(postcodepy))
postcodepy_tk.pack(side='left', fill='both', expand=True)

# When "Apply Settings" button pushed, get the new settings from the various widgets.
def getSettings():
	# Modifies each of the global variables that correspond to the settings.
	global sp
	sp = sp_tk.get()
	
	global dtime
	try:
		dtime_temp = dtime
		dtime = int(dtime_tk.get())
	except (ValueError):
		dtime = dtime_temp
		dtime_tk.set(str(dtime))
	
	global ep_dir
	ep_dir = ep_dir_tk.get()
	
	global useLog
	useLog = uselog_tk.get()
	
	global precode
	precode = precode_tk.get("1.0", "end-1c")
	global precodepy
	precodepy = precodepy_tk.get("1.0", "end-1c")
	global postcode
	postcode = postcode_tk.get("1.0", "end-1c")
	global postcodepy
	postcodepy = postcodepy_tk.get("1.0", "end-1c")
	
	#Call saveSettings function to save these variables
	saveSettings()
	
	return tk.messagebox.showinfo('Settings Saved','Settings Saved Successfully!')
	'''
	#rewrite settings ini file
	global setfile
	stxt = open(setfile, "w")
	new_settings_str = '[general]\nsp = '+sp+'\ndtime = '+str(dtime)+'\nep_dir = '+ep_dir
	stxt.write(new_settings_str)
	stxt.close()
	
	print('saved settings as: sp = ',sp,'\tdtime = ', dtime,'\tep_dir = ',ep_dir)
	'''

button_save_settings = tk.Button(tab4, text = 'Apply', command = getSettings)

tab4.grid_columnconfigure(0,weight=1)
tab4.grid_columnconfigure(1,weight=1)
tab4.grid_columnconfigure(2,weight=1)
tab4.grid_rowconfigure(8,weight=1)
tab4.grid_rowconfigure(10,weight=1)
tab4.grid_rowconfigure(12,weight=1)
tab4.grid_rowconfigure(14,weight=1)
#tab4.grid_rowconfigure(16,weight=1)

i_seriesparallel.grid(column=0,row=1,sticky='w')
rb_parallel.grid(column=1,row=1,sticky='ew')
rb_series.grid(column=2,row=1,sticky='ew')
dtime_label.grid(column=0,row=3,sticky='w')
dtime_entry.grid(column=1,row=3,columnspan=2,sticky='ew')
ep_dir_label.grid(column=0,row=4,sticky='w')
ep_dir_entry.grid(column=1,row=4,columnspan=2,sticky='ew')
uselog_label.grid(column=0,row=5,columnspan=3,sticky='w')
uselog_true.grid(column=0,row=6,sticky='ew')
uselog_false.grid(column=1,row=6,sticky='ew')

#TODO [High priority]: the text boxes appear way too large, and there isn't an obvious way to fix it using grid. -- resolved
# height, sticky, and ipady are all getting ignored. 
precode_label.grid(column=0,row=7,columnspan=3,sticky='w')
#precode_tk.grid(column=0,row=8,columnspan=3,sticky='nsew',ipady=20) #ipady=50
precode_subframe.grid(column=0,row=8,columnspan=3,sticky='nsew')
precodepy_label.grid(column=0,row=9,columnspan=3,sticky='w')
precodepy_subframe.grid(column=0,row=10,columnspan=3,sticky='nsew')
postcode_label.grid(column=0,row=11,columnspan=3,sticky='w')
postcode_subframe.grid(column=0,row=12,columnspan=3,sticky='nsew')
postcodepy_label.grid(column=0,row=13,columnspan=3,sticky='w')
postcodepy_subframe.grid(column=0,row=14,columnspan=3,sticky='nsew')
'''
postcode_label.grid(column=0,row=11,columnspan=3,sticky='w')
postcode_tk.grid(column=0,row=12,columnspan=3,sticky='ew')
postcodepy_label.grid(column=0,row=13,columnspan=3,sticky='w')
postcodepy_tk.grid(column=0,row=14,rowspan=2,columnspan=3,sticky='ew')
'''

button_save_settings.grid(column=2,row=16,sticky='ew')


# 5 - About
i_about_title = tk.Label(tab5, text = 'EnergyPlus MultiLaunch',font=('Arial',18,'bold'))
i_about_str = '\nSuperlauncher for running many EnergyPlus simulations in series or parallel.\n\nVersion: 0.50   Updated: 2023-06-05\n\nLicensed under the GNU General Public License v3\nCreated by Brian Woo-Shem\nSanta Clara University, School of Engineering, Department of Mechanical Engineering\n'
i_about = tk.Label(tab5, text = i_about_str)
i_copyrights = tk.Label(tab5, text = '\nEnergyPlus is a trademark of the US Department of Energy. \nEnergyPlus MultiLaunch is an independent project and is not affiliated nor endorsed by the US Department of Energy.')

# link to documentation that is a clickable url
def callback(url):
	webbrowser.open(url)

i_url = tk.Label(tab5, text = 'https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch', fg='blue', cursor='hand2')
i_url.bind("<Button-1>", lambda e: callback("https://github.com/SCU-Smart-Grid-CPS/EP-MutiLaunch"))

tab5.grid_columnconfigure(0,weight=1)
i_about_title.grid(column=0,row=1,sticky='ew')
i_about.grid(column=0,row=2,sticky='ew')
i_url.grid(column=0,row=3,sticky='ew')
i_copyrights.grid(column=0,row=4,sticky='ew')


# Starts GUI and waits for user input
w.mainloop()


