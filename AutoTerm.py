#!/usr/bin/env python3
#title           :AutoTerm.py
#description     :AutoTerm is a serial port terminal. This terminal will automagically reconnect to the serial port when it is plugged in again.
#author          :Spudmn
#date            :16/09/2018
#version         :0.6
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

import os

if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))
        
  

class SerialThread(threading.Thread):
    def __init__(self, queue,sPort_Name,lb_Status):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sPort_Name = sPort_Name
        self.lb_Status = lb_Status
        self.state = 0
        self.Serial_Port = None

    def Is_Comport_Present(self,sComport):
        for port, _desc, _hwid in comports():
            if port == sComport:
#                 print "Found " + str(port)
                return True
        return False
        
    def run(self):
        while True:
            if self.state == 0:

                if self.Is_Comport_Present(self.sPort_Name):
                    
                    try:
                        self.Serial_Port = serial.Serial(self.sPort_Name,115200)
                        self.state = 1
                        self.lb_Status.config(text= "Status: Online",fg="black")
                    except :
                        self.lb_Status.config(text= "Status: Can not open port", fg="red")
                        if self.Serial_Port != None:
                            self.Serial_Port.close()
                            self.Serial_Port = None
                        #print "Port Error"
                else:
                    self.lb_Status.config(text= "Status: Offline", fg="red")
                    # Wait for 5 m seconds
                    time.sleep(.500)

            else:  # State == 1
                try:
                      
                    data = self.Serial_Port.read(1)
                    if data is None or data == "":
#                         print "Return"
                        if self.Serial_Port != None:
                            self.Serial_Port.close()
                            self.Serial_Port = None
                        self.state = 0
                        continue
                    self.queue.put(data)
                except :
#                     print "Serial Error"
                    if self.Serial_Port != None:
                        self.Serial_Port.close()
                        self.Serial_Port = None
                    self.state = 0
                    


class App(object):
    
    def __init__(self,parent,sComport):
        
        self.parent=parent
        self.sComport = sComport
        self.parent.title("AutoTerm V0.6")
        

       
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
        
        
        self.queue = queue.Queue()
        self.thread = SerialThread(self.queue,self.sComport,self.lb_Status)
        self.thread.daemon = True;  #this will cuase the serial thread to close on exit
        self.thread.start()
        self.process_serial()


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
        while self.queue.qsize():
            try:
                if self.text.dlineinfo('end-1chars') != None:
                    self.text.insert('end', self.queue.get())    #if the scroll bar is at the bottom then output string and shift to keep the new line in view
                    self.text.see('end')
                else:
                    self.text.insert('end', self.queue.get())
                      
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
