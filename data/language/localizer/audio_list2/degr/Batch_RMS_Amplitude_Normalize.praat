#################################################################
#								#
# Batch script for normalizing RMS amplitude of .wav files	#
# 								#
# To run this script, open it in Praat and press "Ctrl+R" 	#
# or go to the "Run" menu and select "Run"			#
#								#
# Written by Tyler Perrachione tkp@mit.edu 			#
# with some code shamelessly pilfered from Robert Daland	#
# 13-Jan-2009							#
#								#
#################################################################

form RMSNormalize
	comment Enter source directory (if other than local directory)
	sentence sourceDir ./
	comment Enter target directory (if other than local directory)
	sentence targetDir ./
	comment Enter the target RMS amplitude (in dB)
	real target_intensity 70.0
endform

Create Strings as file list... list 'sourceDir$'*.wav
numberOfFiles = Get number of strings
number = 1
for ifile from 1 to numberOfFiles
	select Strings list
	fileName$ = Get string... ifile
	Read from file... 'sourceDir$''fileName$'
	Scale intensity... target_intensity
	Write to WAV file... 'targetDir$''fileName$'
	number = number + 1
endfor
select Strings list
Remove