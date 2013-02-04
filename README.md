ConsoleMotionRecorder
=====================

A simple motion data recording tool for the Leap

## Platforms

This should work under Windows, Linux and Mac, though only Windows was tested yet.
The only platform dependent code is the *getChar* function used in main().

## Requirements

This tool requires a python 2.x installation and a Leap Motion device (www.leapmotion.com) with installed Leap app.
Alongside with the source file *ConsoleMotionRecorder.py* the Leap python API should be provided in the same directory:

* *Leap.py*
* *_LeapPython.pyd*
* *Leap.dll*

## Usage

After starting the tool, the following key tokens are available:

* **[h]**		track hand data
* **[f]**		track finger data
* **[enter]**		track what moved last
* **[p]**		record position *(toggle)*
* **[v]**		record velocity *(toggle)*
* **[x]**		record x component *(toggle)*
* **[y]**		record y component *(toggle)*
* **[z]**		record z component *(toggle)*
* **[t]**		record timestamp *(toggle)*
* **[e]**		generate export file *(toggle)*
* **[SPACE]**		start/stop recording
* **[m]**		mark current frame *(while recording)*
* **[q/ESC]**		quit

As soon as the Leap device is plugged in and the Leap app is running, the tool recognizes hand/finger (depends on tracking selection) movement and prints them out.

If desired, an export file can be generated. The filename has the following format: *LeapMotionRecord_YYYYMMDD_mmss.txt*.
During recording, the current frame can be marked. This will add a *1* after the last column in that specific line.

### Recording

To record a certain object do the following:

1. Plug in the Leap device and start the Leap app.
2. Try to only move the desired hand/finger.
3. Press **ENTER** to confirm tracking the last moved object.
4. Press **SPACE** to start recording.
5. If desired, mark a specific recording frame with **m** during recording.
6. press **SPACE** again to stop recording.

### Settings

The following settings are default:

* track finger
* record position *and* velocity
* record y axis
* don't record timestamp
* generate an export file

So, one data packet looks like this:
`ID	Y: 	position		velocity`

After closing the recording tool, these settings are stored in the file *settings.dat*. If this file is present in the working directory of the tool at startup, the tool will load the initial settings from this file instead of generation a new default set. 
