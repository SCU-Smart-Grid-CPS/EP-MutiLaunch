# run_template.py
# Author(s):    Brian Woo-Shem
# Version:      2.3
# Last Updated: 2023-05-11
# Code to run a single EnergyPlus sim, with repetition in case of warmup anomaly errors and failsafe for total .idf implosion.
# Intended for use with epgui EP Parallel Launch

#Simulation Name
sn = 'PPPP'

print("run_" + str(sn) + ".py ===>")

import subprocess

# === Directories used ===
ep_dir = 'ENERGYPLUS_DIRECTORY'

wfile = 'WEATHER_FILENAME'

simfile = 'SIMULATION_FILENAME'

outdir = 'OUTPUT_DIRECTORY'

# === Create run command ===
runcmd = ep_dir + ' --readvars --output-directory \"' + outdir + '\" -w \"' + wfile + '\" \"' + simfile + '\"'

#print("Sim ", sn, " running: ")
print(runcmd)

# === Initial run ===
#Launch subprocess in the shell
epproc = subprocess.run(runcmd, capture_output=True, shell=True)

#Display result. 0 = success; else failure
print(sn, " returned: ", epproc.returncode)

# === Re-attempt to run the simulation if it crashed ===
# There is probably a more elegant way to combine this with above run, but this works well enough

#Sanity check to ensure it does not have infinite loop of crashing
insanity = 1

# If previous run was not successful and it ran fewer than 10 times, run it again
while epproc.returncode!=0 and insanity < 11:
	epproc = subprocess.run(runcmd, capture_output=True, shell=True)
	print("Warning: ", sn, " failed -> rerunning")
	print(sn, " returned: ", epproc.returncode)
	insanity = insanity + 1

# === Display result to user ===
if insanity < 11:
	print(sn, " success!")
else:
	print("ERROR: ", sn, " Failed repeatedly, using default sim.")
	
	#Use failsafe sim so the entire system doesn't get stuck
	# Clumsy way to copy a file
	import os #don't import until now to speed up nominal operation
	import platform
	
	failsafesim = "failsafe.idf"
	fsfile = open(failsafesim, 'r')
	failsafe_contents = fsfile.read()
	catchallfile = str(sn) + '\failsafe.idf'
	cfile = open(catchallfile, "a")
	cfile.truncate(0)
	cfile.write(failsafe_contents)
	cfile.close()
	fsfile.close()
	
	while epproc.returncode!=0 and insanity < 13:
		print(sn, ' running failsafe to protect overall simulation')
		runcmd = ep_dir + ' --readvars --output-directory ' + str(sn) + ' -w ' + wfile + ' ' + catchallfile
		epproc = subprocess.run(runcmd, capture_output=True, shell=True)
		print(sn, " returned: ", epproc.returncode)
		insanity = insanity + 1
	
	if insanity < 13:
		print(sn, " failsafe only success!")
	else:
		print("ERROR: ", sn, " Failed repeatedly in failsafe -> giving up.\n\nUse CTRL+C to kill the simulation code.")
		exit()
