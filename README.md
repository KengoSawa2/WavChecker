# WavChecker
　wav data comparison check for the video industry that supports QT/MXF/wav(PCM only)

![WavChecker_ok](https://github.com/KengoSawa2/WavChecker/blob/main/ss/wavchecker_ok.png "WavChecker_ok")

## Overview
WavChecker is a wav comparison and diff tool for post-production.

##Usage and fucntion

- Checks if the wav attached to the specified QuickTime(QT) or MXF file is "same wavdata".  
- Comparison between wavs is also possible.
- Comparison between QT and MXF.
- Silence check mode for phase inversion check assistance

There are several modes for checking, though,  
All scenarios are designed for [L'espaceVision](https://www.lespace.co.jp/) post-production workflow.  
This tool is in-house tool.
Try it out and see if it has the features you need:)

## wavChecker Process features
If there is a difference, it displays the difference in each frame based on TC.  
This is not　"wave inversion check."  
Complete binary check is performed. No misjudgment will occur except for bugs.  
Checking process is very fast, because it does not perform any wav decoding process,  
so it can check in a few minutes even if the length of the file is longer than 2 hours.  

## Support Formats
QuickTime(QT) with PCM wav.  
MXF with PCM wav.  
wav with PCM. 16bit,24bit,32bit,LittleEndian,BigEndian,44100hz,48khz,96khz
wav64  

## Support OS
macOS(Windows doesn't test)

## License
[GPL v3.0]

## to Build and Run
download ffmpeg and ffprobe　commands at WavChecker.py folder
https://ffmpeg.org/

### required Python Library
xxhash  
timecode  
wave-bwf-rf64  
PySide2  

### Error(differ detected) example
![WavChecker_error](https://github.com/KengoSawa2/WavChecker/blob/main/ss/wavchecker_error.png "WavChecker_error")
