#!/usr/bin/env python
'''
Example of CBTM Client.
'''
import socket
import ssl
import curses
from curses.textpad import Textbox, rectangle
import string
import sys

class CBTClient(object):

    def __init__(self):
        '''
            Instantiates the CBTM Client, calling the 
            methods to build the interface and holding
            the data structures necessary to interpret
            the commands entered by the user.
        '''
        #self.host = '134.226.55.212'
        self.host = '127.0.0.1'
        self.port = 5006

        self.commands={'ru':'request_unit',
                       'rl':'release_unit',
                       'gs':'grid_status',
                       'us':'unit_status',
                       'su':'start_unit',
                       'sdu':'shutdown_unit',
                       'rbu':'restart_unit',
                       'sp':'set_port',
                       'sh':'set_host',
                       'q':'quit'}

        ignore_list = ['\n']

        self.pr = [ord(k) for k in string.printable if not(k in ignore_list)]

        self.build_inter()


    def build_inter(self):
        '''
            Builds the interface of the client, using the package curses
        '''
        head_y = 5
        instruct_y = 1
        text_y = 10
        resp_y = 1
        rf_y = 20

        width = 500

        header_msg = 'CBTClient v0.1'


        main_scr = curses.initscr()
        curses.noecho()
        curses.curs_set(0)
        main_scr.keypad(1)

        tot_y = sum((head_y, instruct_y, text_y, resp_y, rf_y))

        main_scr.resize(tot_y,width)

        max_y, max_x = main_scr.getmaxyx()
        y=0


        header = main_scr.subwin(head_y,max_x,y,0)
        header.box(ord('#'), ord('='))
        header.addstr(int(head_y/2),int(max_x/2)-int(len(header_msg)/2),header_msg)
        y += head_y


        instruct = main_scr.subwin(instruct_y,max_x,y,0)
        instruct.addstr('Enter command (press enter to send):')
        y += instruct_y


        text_field = main_scr.subwin(text_y,max_x-2,y,1)
        text_field.border()
        text_field.move(1,1)
        y += text_y


        resp_label = main_scr.subwin(resp_y,max_x,y,0)
        resp_label.addstr('Response:')
        y += resp_y


        rf = main_scr.subwin(rf_y,max_x-2,y,1)
        rf.border()

        main_scr.refresh()

        self.scrs={'main':main_scr,
                   'head':header,
                   'instruct':instruct,
                   'text':text_field,
                   'label':resp_label,
                   'resp':rf}


    def _reset(self, scr):
        '''
            Resets the interface displayed to the user
        '''
        self.scrs[scr].clear()
        self.scrs[scr].border()
        self.scrs[scr].move(1,1)
        self.scrs[scr].refresh()


    def _show(self, scr, msg):
        '''
            Displays the interface to the user
        '''
        self.scrs[scr].clear()
        y, x = self.scrs[scr].getyx()
        for m in range(len(msg)):
            if not(y==1+m and x==1):
                self.scrs[scr].move(1+m,1)
            self.scrs[scr].addstr(msg[m])
        self.scrs[scr].border()
        self.scrs[scr].refresh()


    def show_response(self,msg):
        self._show('resp',msg)


    def text_reset(self):
        self._reset('text')


    def get_text(self, pad):
        msg = pad.gather().split('\n')[1][1:][:-1].strip()
        self.text_reset()
        return str(msg)


    def show_text(self, msg):
        self._show('text',[msg,])


    def inter_loop(self):
        start_y, start_x = self.scrs['text'].getyx()

        pad = Textbox(self.scrs['text'])
        pad.stripspaces = True

        msg = ['Welcome to CBTM Client.','List of accepted commands(separate '+\
        'the commands and the arguments with ","):']
        for k,v in self.commands.items():
            msg.append('%s -- %s'%(k,v))
        data = ''
        while True:
            self.show_response(msg)
            msg = []
            #Get user input
            while True:
                ch = self.scrs['text'].getch()

                if ch in self.pr:
                    self.scrs['text'].echochar(ch)
                else:
                    if ch == ord('\n'):
                        data = self.get_text(pad)
                        break
                    elif ch == 14:
                        continue
                    elif ch == 16:
                        self.show_text(data)
                        self.scrs['text'].move(1,1+len(data))
                    elif ch == 263:
                        tmp = self.get_text(pad)[:-1]
                        self.show_text(tmp)
                        self.scrs['text'].move(1,1+len(tmp))
                    else:
                        # self.show_text(str(ch))
                        pad.do_command(ch)
                        y,x = self.scrs['text'].getyx()
                        if x < start_x:
                            self.text_reset()

            #Separate the text entered by the user on commas
            args = data.split(',') 
            try:
                #Get the first argument (Code for command)
                code = args.pop(0) 
            except IndexError:
                code = -1

            #Interprets the command
            try: 
                command = self.commands[code]
            except KeyError:
                msg.append('Code not recognized: '+code)
                msg.append('Try:')
                for k,v in self.commands.items():
                    msg.append('%s -- %s'%(k,v))
                continue

            if command == 'quit':
                break
            elif command =='set_port':
                #Execute set port
                self.port = int(args[0])
                msg.append('Port for CBTM communication set to %d'%self.port)
                continue
            elif command =='set_host':
                #Execute set host
                self.host = str(args[0])
                msg.append('CBTM host set to %s'%self.host)
                continue
            elif code in ['rl','us','su','sdu','rbu']:
                # Checks for number of arguments
                if len(args) != 1:
                    msg.append('The requested command needs one argument.')
                    continue
            elif code in ['ru']:
                # Checks for number of arguments
                if len(args) != 4:
                    msg.append('The requested command needs 4 arguments.')
                    continue

            msg.append('Message from CBTM:')
            try:
                # Send command to CBTM Server
                rp = self.send(self.structure(command, args))
                msg.extend(rp.split('\n'))
            except socket.error:
                msg = ['No server active on port %d'%self.port,]


    def interact(self):
        try:
            self.inter_loop()
        finally:
            curses.endwin()


    def send(self, msg):
        '''
            Establishes connection to CBTM Server (with SSL authentication)
            and send the commands.
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wrapped_sock = ssl.wrap_socket(s,keyfile='../resources/cbtm_key.pem',
                                        certfile='../resources/cbtm_cert.pem')
        wrapped_sock.connect((self.host, self.port))
        wrapped_sock.sendall(msg)
        return wrapped_sock.recv(1024)


    def structure(self, command, args):
        '''
            Translate the commands to CBTP format.
        '''
        if command == 'grid_status':
            msg = 'grid_status:get'
        elif command == 'get_group_list':
            msg = 'get_group_list:get'
        elif command =='request_unit':
            msg = command +':'+','.join(args)
        elif command == 'start_unit':
            msg = command + ':'+','.join(args)
        elif command == 'shutdown_unit':
            msg = command + ':'+','.join(args)
        elif command == 'restart_unit':
            msg = command + ':'+','.join(args)
        else:
            msg = command +':'+' '.join(args)

        return msg




if __name__ == '__main__':
    test = CBTClient()
    test.interact()
