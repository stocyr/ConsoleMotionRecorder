'''
ConsoleMotionRecorder

Copyright (C) 2013  Cyril Stoller
Except for _Getch, _GetchUnix, _GetchWindows and _GetchMacCarbon
--> Source: http://code.activestate.com/recipes/134892/

ConsoleMotionRecorder is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
'''

import Leap, time, pickle, os


class _Getch:
    """
    Gets a single character from standard input.  Does not echo to
    the screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except(AttributeError, ImportError):
                self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys, termios # import termios now or else you'll get the Unix version on the Mac

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


class _GetchMacCarbon:
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned.  The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """
    def __init__(self):
        import Carbon
        Carbon.Evt #see if it has this (in Unix, it doesn't)

    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0]==0: # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg & 0x000000FF)



def print_help():
    print ""
    print "############################"
    print " ConsoleMotionRecorder v1.0 "
    print "############################"
    print ""
    print "Usage:"
    print "----------------------"
    print ""
    print " [h]     track hand data"
    print " [f]     track finger data"
    print " [enter] track what moved last"
    print ""
    print " [p]     record position (toggle)"
    print " [v]     record velocity (toggle)"
    print " [x]     record x component (toggle)"
    print " [y]     record y component (toggle)"
    print " [z]     record z component (toggle)"
    print " [s]     record special custom data (toggle)"
    print ""
    print " [t]     record timestamp (toggle)"
    print " [e]     generate export file (toggle)"
    print ""
    print " [SPACE] start/stop recording"
    print " [m]     mark current frame (while recording)"
    print " [q/ESC] quit"
    print ""


def generate_format(settings, no_tab=False):
    format_string = "frame"
    component = ""
    if settings['record_timestamp']: format_string += "\ttimestamp"
    if settings['record_position']: component += " position"
    if settings['record_velocity']: component += "\tvelocity"
    if settings['record_x']: format_string += "\tX:" + component
    if settings['record_y']: format_string += "\tY:" + component
    if settings['record_z']: format_string += "\tZ:" + component
    if settings['special_data']: format_string += "\tSpecialData"
    
    if no_tab:
        format_string = format_string.replace("\t", "  ")
    
    return format_string


class RecorderListener(Leap.Listener):
    average_fps = 0
    leap_connected = False
    FPS_HISTORY = 10
    THRESHOLD_MOVEMENT = 200
    settings = {}
    mark_frame_flag = False
    recording = False
    file = None
    moving_id = 0
    tracking_id = 0
    
    def on_connect(self, controller):
        self.leap_connected = True
        print "INFO: Leap connected"

    def on_disconnect(self, controller):
        self.leap_connected = False
        print "INFO: Leap disconnected"
    
    def update(self, settings):
        self.settings = settings
    
    def record_start(self, settings, filename):
        self.settings = settings
        if self.settings['export_file']:
            self.file = open(filename,'w')
            self.file.write("Leap ConsoleMotionRecorder Export File\n")
            self.file.write("\n")
            self.file.write("Average FPS: %.2f\n" % self.average_fps)
            self.file.write("\n")
            self.file.write(generate_format(self.settings) + '\n')
        self.recording = True
    
    def record_stop(self):
        self.recording = False
        if self.settings['export_file']:
            self.file.close()
        print ""  
        print "" 
        print_help()     

    def mark_frame(self):
        self.mark_frame_flag = True
    
    def track_last(self):
        self.tracking_id = self.moving_id

    def on_frame(self, controller):
        frame = controller.frame()
        
        # determine average FPS
        if controller.frame(self.FPS_HISTORY).is_valid:
            self.average_fps =  float(1000000.0*self.FPS_HISTORY/(frame.timestamp - controller.frame(self.FPS_HISTORY).timestamp))

        # am I recording?
        if self.recording:
            velocity = Leap.Vector()
            position = Leap.Vector()
            
            # search for the ID stored earlier
            if self.settings['track_hand'] and frame.hand(self.tracking_id).is_valid:
                # if object was found, copy raw data
                velocity = frame.hand(self.tracking_id).palm_velocity
                position = frame.hand(self.tracking_id).palm_position
                
            elif not self.settings['track_hand'] and frame.pointable(self.tracking_id).is_valid:
                # if object was found, copy raw data
                velocity = frame.pointable(self.tracking_id).tip_velocity
                position = frame.pointable(self.tracking_id).tip_position
            else:
                # ID not found - abort
                print "ERROR: tracking ID not found - aborting"
                if self.settings['export_file']:
                    self.file.write("ERROR: tracking ID not found - aborting")
                self.record_stop()
                
            if self.recording:
                # not aborted yet? gather data
                data = "%d" % frame.id
                if self.settings['record_timestamp']:
                    data += "\t%d" % frame.timestamp
                if self.settings['record_x']:
                    if self.settings['record_position']:
                        data += "\t%f" % position.x
                    if self.settings['record_velocity']:
                        data += "\t%f" % velocity.x
                if self.settings['record_y']:
                    if self.settings['record_position']:
                        data += "\t%f" % position.y
                    if self.settings['record_velocity']:
                        data += "\t%f" % velocity.y
                if self.settings['record_z']:
                    if self.settings['record_position']:
                        data += "\t%f" % position.z
                    if self.settings['record_velocity']:
                        data += "\t%f" % velocity.z
                if self.settings['special_data']:
                    data += "\t"
                    ###################################################
                    ## HERE YOU CAN PUT YOUR OWN CUSTOM EXPORT VALUE ##
                    ###################################################
                    ## EXAMPLE: finger width                         ##
                    data += "%f" % frame.pointable(self.tracking_id).width
                    ##                                               ##
                    ###################################################
                if self.mark_frame_flag:
                    # does the current frame has to be marked?
                    data += "\t1"
                    self.mark_frame_flag = False    # YOMO - you only mark once
                
                # output data
                print data
                if self.settings['export_file']:
                    self.file.write(data + '\n')
        else:
            # not recording? -> movement detection only -> needed for object identification
            if self.settings['track_hand'] and not frame.hands.empty:
                for hand in frame.hands:
                    # search through every hand: big movement and not same ID as before?
                    if hand.palm_velocity.magnitude > self.THRESHOLD_MOVEMENT and self.moving_id != hand.id:
                        self.moving_id = hand.id
                        print "movement of hand ID %d - press [ENTER] to track it" % hand.id
            elif not self.settings['track_hand'] and not frame.pointables.empty:
                for pointable in frame.pointables:
                    # search though every finger: big movement and not same ID as before?
                    if pointable.tip_velocity.magnitude > self.THRESHOLD_MOVEMENT and self.moving_id != pointable.id:
                        self.moving_id = pointable.id
                        print "movement of finger ID %d - press [ENTER] to track it" % pointable.id


def main():
    # initialize a native getch function
    getChar = _Getch()
    
    # check if there already exists a settings file:
    if not os.path.exists("settings.dat"):
        # initialize the settings dictionary
        settings = {'track_hand': False,
                    'record_position': True,
                    'record_velocity': True,
                    'record_x': False,
                    'record_y': True,
                    'record_z': False,
                    'special_data': False,
                    'record_timestamp': False,
                    'export_file': True}
        
    else:
        # loads the settings from the file
        settings_file = open("settings.dat", "r")
        settings = pickle.load(settings_file)
        settings_file.close()


    # Create a listener and controller
    listener = RecorderListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    listener.update(settings)
    
    # print help
    print_help()

    # main keyboard process loop
    while True:
        # read key token
        inputchar = getChar()
        inputchar = inputchar.lower()
        
        # H:
        if inputchar == 'h':
            settings['track_hand'] = True
            print "tracking hand"
        # F:
        elif inputchar == 'f':
            settings['track_hand'] = False
            print "tracking finger"
        # [ENTER]:
        elif inputchar == '\x0d':   # = ENTER
            if listener.leap_connected:
                listener.track_last()
                if settings['track_hand']:
                    print "tracking hand with ID %d" % listener.tracking_id
                else:
                    print "tracking finger with ID %d" % listener.tracking_id
        # V:
        elif inputchar == 'v':
            if settings['record_position'] or not settings['record_velocity']:
                settings['record_velocity'] = not settings['record_velocity']
            print generate_format(settings, True)
        # P:
        elif inputchar == 'p':
            if settings['record_velocity'] or not settings['record_position']:
                settings['record_position'] = not settings['record_position']
            print generate_format(settings, True)
        # X:
        elif inputchar == 'x':
            if settings['record_y'] or settings['record_z'] or not settings['record_x']:
                settings['record_x'] = not settings['record_x']
            print generate_format(settings, True)
        # Y:
        elif inputchar == 'y':
            if settings['record_x'] or settings['record_z'] or not settings['record_y']:
                settings['record_y'] = not settings['record_y']
            print generate_format(settings, True)
        # Z:
        elif inputchar == 'z':
            if settings['record_x'] or settings['record_y'] or not settings['record_z']:
                settings['record_z'] = not settings['record_z']
            print generate_format(settings, True)
        # S:
        elif inputchar == 's':
            settings['special_data'] = not settings['special_data']
            print generate_format(settings, True)
        # E:
        elif inputchar == 'e':
            settings['export_file'] = not settings['export_file']
            if settings['export_file']:
                print "generating export file"
            else:
                print "generating no export file"
        # T:
        elif inputchar == 't':
            settings['record_timestamp'] = not settings['record_timestamp']
            print generate_format(settings, True)
        # [SPACE]:
        elif inputchar == ' ':
            if listener.leap_connected == False:
                print "ERROR: Leap not connected / Leap app not running"
            elif listener.tracking_id == 0:
                print "ERROR: no ID selected (press [ENTER] to track the last moving object)"
            else:
                if listener.recording:
                    listener.record_stop()
                else:
                    # generate time stamp for filename and start recording
                    filename = time.strftime("LeapMotionRecord_%Y%m%d_%H%M%S.txt")
                    listener.record_start(settings, filename)            
        # M:
        elif inputchar == 'm':
            if listener.recording:
                listener.mark_frame()
        # Q or [ESC]:
        elif inputchar == 'q' or inputchar == '\x1b': # = ESC
            break
        
        # transmit these changed settings to the listener class
        if not listener.recording:
            listener.update(settings)
    
    print "Exiting..."
    
    # app closes: Remove the listener
    controller.remove_listener(listener)
    
    # store the settings
    settings_file = open("settings.dat", "w")
    pickle.dump(settings, settings_file)
    settings_file.close()


if __name__ == "__main__":
    main()
