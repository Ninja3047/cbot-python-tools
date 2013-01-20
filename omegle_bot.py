
import urllib2 as url
import urllib
import httplib as http
from lib import cleverbot

import datetime
import time
from lib.gdata_sp import gspread_log 

#This simply cuts the extra characters to isolate the ID
def fmtId( string ):
    return string[1:len( string ) - 1]


#Talk to people
def talk(id,req, msg):

    #Show the server that we're typing
    typing = url.urlopen('http://omegle.com/typing', '&id='+id)
    typing.close()

    #Show the user that we can write now
    #msg = str(raw_input('> '))

    #Send the string to the stranger ID
    msgReq = url.urlopen('http://omegle.com/send', '&msg='+msg+'&id='+id)

    #Close the connection
    msgReq.close()


#This is where all the magic happens, we listen constantly to the page for events
def listenServer( id, req , log):
	s = cleverbot.cbot_Session()
	t=time.time()
	status = 0

	pstring = str(datetime.datetime.now()).split('.')[0] +' [Stranger disconnected, finding new session]'
	print pstring
	log.clear_rt()
	log.write(pstring)	
	closelist = ["bitly", "tyoyu"]
	while True:
		if not status and time.time() - t > 10:
			break
		site = url.urlopen(req)

		#We read the HTTP output to get what's going on
		rec = site.read()
		if 'waiting' in rec:
			t = time.time()
			status = 0
			#print("Waiting...")

		elif 'connected' in rec:
			print
			status = 0
			t = time.time()
			
			#Since this isn't threaded yet, it executes the talk function (yeah, turn by turn)
			talk(id,req,"hi")
			pstring = str(datetime.datetime.now()).split('.')[0] +" Cleverbot : " + "hi"
			#print pstring
			#log.write(pstring)
			
		elif 'strangerDisconnected' in rec:
			#pstring =  str(datetime.datetime.now()).split('.')[0] +' [Stranger disconnected]'
			print "disconnect..."
			#log.write(pstring)
			#We start the whole process again
			#omegleConnect()
			break
			
		elif 'typing' in rec:
			status = 1
			print "[ Stranger is typing ]"
			'''
			print "[ Stranger is typing ]"
			log.write("[ Stranger is typing ]")
			'''

		#When we receive a message, print it and execute the talk function            
		elif 'gotMessage' in rec:
			status = 1
			resp = rec[17:len( rec ) - 3]
			br = 0
			for phrase in closelist:
				if phrase in resp:
					br = 1
			if br:
				break
			pstring = str(datetime.datetime.now()).split('.')[0] + " Stranger : "+ resp
			print pstring
			log.write(pstring)
			try:
				msg = s.Ask(resp)
				msg.replace(' m ', ' f ')
				msg.replace('/m/','/f/')
			except:
				pass
			pstring = str(datetime.datetime.now()).split('.')[0] +" Cleverbot : " + msg
			print pstring
			log.write(pstring)
			talk(id,req, msg)
			status = 0
			t = time.time()+10


#Here we listen to the start page to acquire the ID, then we "clean" the string to isolate the ID
def omegleConnect(id_, log):
    try:
	site = url.urlopen('http://omegle.com/start','')
	id = fmtId( site.read() )
	
	if id != id_:
		#print(id)
		req = url.Request('http://omegle.com/events', urllib.urlencode( {'id':id}))

		listenServer(id,req, log)
    except:
	print "[connection error]"

    return id


if __name__ == "__main__":

	id = 0.    
	google_id = "fubar@gmail.com"
	google_pwd = "12345"
	s_sheet_name = "cleverbot omegle log"
	log = gspread_log(google_id, google_pwd, s_sheet_name)
	#log.clear_perm()
	while True:
		id = omegleConnect(id, log)
		#print id
		time.sleep(2)
