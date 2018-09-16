#!/usr/bin/env python3
#title           :AutoTerm.py
#description     :AutoTerm is a serial port terminal. This terminal will automagically reconnect to the serial port when it is plugged in again.
#author          :Spudmn
#date            :17/09/2018
#version         :0.7
#usage           :python AutoTerm.py COM5   or python AutoTerm.py /dev/ttyUSB0  
#notes           :
#python_version  :3.5.2  
#==============================================================================

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.





import sys
import serial
import threading
import queue
import tkinter as tk
import tkinter.scrolledtext as tkst
import time
from enum import Enum

import os

if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))
        

class Serial_Thread_State(Enum):
    FINDING_PORT = 0
    FOUND_PORT = 1

  

class SerialThread(threading.Thread):
    def __init__(self, Serial_Queue,sPort_Name,lb_Status_Queue):
        threading.Thread.__init__(self)
        self.Serial_Queue = Serial_Queue
        self.sPort_Name = sPort_Name
        self.lb_Status_Queue = lb_Status_Queue
        self.state = Serial_Thread_State.FINDING_PORT
        self.Serial_Port = None

    def Is_Comport_Present(self,sComport):
        for port, _desc, _hwid in comports():
            if port == sComport:
#                 print "Found " + str(port)
                return True
        return False
        
    def run(self):
        while True:
            if self.state == Serial_Thread_State.FINDING_PORT:

                if self.Is_Comport_Present(self.sPort_Name):
                    
                    try:
                        self.Serial_Port = serial.Serial(self.sPort_Name,115200)
                        self.state = Serial_Thread_State.FOUND_PORT
                        self.lb_Status_Queue.put(["Status: Online","black"])
                    except :
                        self.lb_Status_Queue.put(["Status: Can not open port","red"])
                        if self.Serial_Port != None:
                            self.Serial_Port.close()
                            self.Serial_Port = None
                        #print "Port Error"
                else:
                    self.lb_Status_Queue.put(["Status: Offline","red"])
                    # Wait for 5 m seconds
                    time.sleep(.500)

            elif self.state == Serial_Thread_State.FOUND_PORT:
                try:
                      
                    data = self.Serial_Port.read(1)
                    if data is None or data == "":
#                         print "Return"
                        if self.Serial_Port != None:
                            self.Serial_Port.close()
                            self.Serial_Port = None
                        self.state = Serial_Thread_State.FINDING_PORT
                        continue
                    self.Serial_Queue.put(data)
                except :
#                     print "Serial Error"
                    if self.Serial_Port != None:
                        self.Serial_Port.close()
                        self.Serial_Port = None
                    self.state = Serial_Thread_State.FINDING_PORT
            else:
                print ("Error in State")       


class App(object):
    
    def __init__(self,parent,sComport):
        
        self.parent=parent
        self.sComport = sComport
        self.parent.title("AutoTerm V0.7")

       
        self.text = tkst.ScrolledText(self.parent, height=30, width=80,font='Terminal_Ctrl+Hex 9', background="black", foreground="yellow")
               
        self.frame = tk.Frame(self.parent)
        self.frame.pack(side='bottom')


        self.bt_Clear_Screen = tk.Button(self.frame, text="Clear", command = self.On_bt_Clear_Screen_Click)
        self.bt_Clear_Screen.pack( side = 'left')


        self.lb_Comport = tk.Label(self.frame, text="Comport: " + self.sComport)
        self.lb_Comport.pack( side = 'left')

        self.lb_Status = tk.Label(self.frame, text="Status: ")
        self.lb_Status.pack( side = 'left')
        self.lb_Status.config(text= "Status: Offline")
        
        self.text.pack(side='top', fill='y')
        
        self.text.bind("<KeyPress>", self.keydown)
        self.text.bind("<KeyRelease>", self.keyup)
        
        
        
        self.Serial_Queue = queue.Queue()
        self.lb_Status_Queue = queue.Queue()
        self.thread = SerialThread(self.Serial_Queue,self.sComport,self.lb_Status_Queue)
        self.thread.daemon = True;  #this will cuase the serial thread to close on exit
        self.thread.start()
        self.process_serial()
        self.On_Update_GUI_Timer()


    def On_Update_GUI_Timer(self): #Update the GUI
        while self.lb_Status_Queue.qsize():
            try:
                status = self.lb_Status_Queue.get()
                #print(status)
                self.lb_Status.config(text= status[0],fg=status[1])
            except queue.Empty:
                print("lb_Status Que Error")
                pass
        self.parent.after(250, self.On_Update_GUI_Timer) #Update the GUI

    

    def keyup(self,e):
#         print 'up', e.char
        pass
        
    def keydown(self,e):
#         print ('down', e.char)
        if self.thread.Serial_Port != None:
            if self.thread.Serial_Port.isOpen():
                self.thread.Serial_Port.write(e.char.encode())

    def On_bt_Clear_Screen_Click(self):
        self.text.delete(1.0,'end')
        
 
    def process_serial(self):
        while self.Serial_Queue.qsize():
            try:
                if self.text.dlineinfo('end-1chars') != None:
                    self.text.insert('end', self.Serial_Queue.get())    #if the scroll bar is at the bottom then output string and shift to keep the new line in view
                    self.text.see('end')
                else:
                    self.text.insert('end', self.Serial_Queue.get())
                      
            except queue.Empty:
                print("Que Error")
                pass
        self.parent.after(100, self.process_serial)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



def main(argv):
    print(sys.version)
    root = tk.Tk()
    try:
        root.iconbitmap(default=resource_path('app.ico'))
    except Exception:
        pass
    if len(argv) == 0:
        print("Usage: python AutoTerm.py COM5   or python AutoTerm.py /dev/ttyUSB0 ")
        sys.exit(1)
    else:
        sComport = argv[0]
    app = App(root,sComport)
    root.mainloop()



if __name__ == "__main__":
    main(sys.argv[1:])
