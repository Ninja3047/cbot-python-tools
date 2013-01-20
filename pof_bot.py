import BeautifulSoup,urllib,urllib2, base64, ClientCookie
from lib.cleverbot import cbot_Session
import shutil, time
from django.utils.encoding import smart_str #fixes some unicode issues

class pof_bot():
    def __init__(self,u,p,pid):
        self.username=u
        self.password=p
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.values = {'username' : self.username,'password':self.password}
        self.base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
        self.headers = { 'User-Agent' : self.user_agent ,"Authorization": "Basic %s" % self.base64string}
        self.dd = urllib.urlencode(self.values)        
        self.pid = pid
        self.frontpage = self.login()
        self.cbot = cbot_Session()    


    def login(self):    
        """
        does programmatic login
        """
        data= self.get("http://www.pof.com/processLogin.aspx")
        return data    
    
    def getThreadsThisPage(self, data, discussions):
        """
        grabs msg thread links on current page
        """
        unread =  data.findAll("div", {"class" : "unread"})
        unread = unread + data.findAll("div", {"class" : "inbox-row"})
        for msg in unread:
            try:
                links = msg.findAll("a")
                profile = "http://www.pof.com/" + links[0]['href']
                msglink = "http://www.pof.com/" + links[2]['href']
                uid = links[0]['href'].split("=")[1]
                discussions[uid] = [uid, profile, msglink]                
            except:
                pass
                #msglink = "http://www.pof.com/" + links[1]['href']
        return discussions
    
    def parseMail(self, page = "http://www.pof.com/inbox.aspx", d = {}):   
        """
        walks through the inbox pages
        """
        data= self.get(page)
        d = self.getThreadsThisPage(data, d)
        np = data.find("span", {"class" : "headline txtGrey size14"})
        if np:
            np = np.find("a")
            if np:
                nextpage = "http://www.pof.com/" + np['href']
                d = self.parseMail(page = nextpage, d = d)
        return d
    
    def checkAllMail(self):
        """
        download all messages, make replies if needed
        """
        f=open('chat.txt', 'w')
        threads = self.parseMail()
        DT=[]
        for uid in threads.keys():
            dt = self.getProfileInfoAndMsg(threads[uid])
            if dt:
                print 
                print dt[0]
                print dt[-1]
                for id_,tx in zip(dt[1],dt[2]):
                    if id_ == self.pid:
                        print "Cleverbot :", tx
                    else:
                        print "Stranger :", tx
                DT.append(dt)
        DT = sorted(DT, reverse = True, key = lambda pair: len(pair[1]))
        for dt in DT:
            f.write('\n')
            f.write('\n')
            f.write('\n')
            f.write(dt[0] + '\n')
            for id_,tx in zip(dt[1],dt[2]):
                f.write('\n')
                if id_ == self.pid:
                    f.write("Cleverbot : "+ tx +'\n')
                else:
                    f.write("Stranger : "+ tx +'\n')
        f.close()
        shutil.copyfile("chat.txt", "chat_backup.txt")
    
    def pullThread(self, msgl):
        """
        gets all messages for a thread
        """
        data= self.get(msgl)
        msgs = data.findAll("span",{"class":"username-inbox"})
        this_id=''
        
        ids,texts = [],[]
        for msg in msgs:
            this_id= msg.find("a")['href'].split("=")[1]
            txt = msg.parent.parent.findAll("div")[1].text
            if "has expressed interest in you" not in txt:
                texts.append(smart_str(txt))
                ids.append(smart_str(this_id))
        for link in data.findAll("a"):
            if "viewallmessages" in link['href'] and not data.find("span", {"class": "text-warning"}):
                newlink =  "http://www.pof.com/" + link['href']
                ids2,texts2 = self.pullThread(newlink)
                ids = ids2 + ids
                texts = texts2 + texts
                break
        if not msgs:
            return [],[]
        else:
            return ids,texts
    
    def getProfileInfoAndMsg(self, member):
        """
        gets basic profile info, message history for a single user. 
        sends replies if needed.
        
        Creates log file, sorted in decreasing order of length of message history
        """
        uid, profile, msgl = member
        
        data= self.get(profile)
        descr=''
        for td in data.findAll("td", {"class":"txtGrey size15"}):
            if "cm)" in td.text:
                descr= td.text.rstrip().replace('\t','')
                descr = smart_str(descr.replace('\r',' ').replace('\n',' ').replace('&quot;','"'))
                break
        data= self.get(msgl)
        descr = ''
        ids, texts = self.pullThread(msgl)
        if len(ids) == 0:
            return None
        if ids[-1] != self.pid: #need reply
            txt = texts[-1]
            txt = smart_str(txt)
            try:
                reply = self.cbot.Ask(txt)
            except: # possible unicode errors. default to something vacuuous
                reply = self.cbot.Ask("hello i like you")
            try: # doesnt always work, but scrub "cleverbot" from replies
                # replace "cleverbot" with "smartchick"
                reply = reply.lower().replace('clever','smart').replace('bot', 'chick')
            except:
                pass
            new_v = self.values.copy()
            form = data.find("form")
            for inp in form.findAll("input"):
                if inp['type'] != "checkbox":
                    new_v[inp['name']] = inp['value']
            new_v["message"] = reply
            self.headers = { 'User-Agent' : self.user_agent ,"Authorization": "Basic %s" % self.base64string}
            dd = urllib.urlencode(new_v)   
            request = urllib2.Request("http://www.pof.com/sendmessage.aspx",dd,self.headers)
            result = ClientCookie.urlopen(request)
            html = result.read()    
            ids.append(self.pid)
            texts.append(reply)
        return descr, ids,texts, msgl
        
    def mycity(self):
        """
        visits all user profiles in current city matching your criteria.
        Increases exposure.
        """
        visited=[]
        for i in xrange(500):
            myc="http://www.pof.com/lastonlinemycity.aspx?page="+str(i)
            data=self.get(myc)
            members=self.strip_members(data)
            for url in members:
                if url not in visited:
                    visited.append(url)
                    self.get(url)
                    print "page",i,"visiting",url
                    member=url[url.index("profile_id=")+11:]
                    self.meet(member)
    
    def visitOnline(self):
        """
        visits all profiles of those on the 'whos online' page.
        Increases exposure.
        """
        visited=[]
        for i in xrange(500):
            p="http://www.pof.com/everyoneonline.aspx?page_id=" + str(i)
            data=self.get(p)
            members=self.strip_members(data)
            for url in members:
                if url not in visited:
                    visited.append(url)
                    self.get(url)
                    print "page",i,"visiting",url
                    member=url[url.index("profile_id=")+11:]
                    self.meet(member)
        
    def visitAll(self):
        """
        Walk through the site, visit all profiles possible.
        Increases exposure.
        """
        visited=[]
        for i in xrange(499):
            p="http://www.pof.com/everyoneonline.aspx?page_id=" + str(i)
            myc="http://www.pof.com/lastonlinemycity.aspx?page="+str(i)
            data1=self.get(myc)
            data2=self.get(p)
            members1=self.strip_members(data1)
            members2=self.strip_members(data2)
            members1.extend(members2)
            for url in members1:
                if url not in visited:
                    visited.append(url)
                    self.get(url)
                    member=url[url.index("profile_id=")+11:]
                    print "page",i,"visiting",member
                    self.meet(member)
    
    
    
    def meet(self,member):
        """
        Submit "yes" for all members on the 'meet me' feature.
        Significantly increases exposure.
        """
        u="http://www.pof.com/meetme.aspx"
        values = {'votea':'1','add_id' : member,'p_Id':member,'nextfive':"13274077,42132650,42287788,42016458,42162693,39390651,42172880,42247856,42172950"}
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
        self.headers = { 'User-Agent' : user_agent ,"Authorization": "Basic %s" % base64string}
        self.dd = urllib.urlencode(values)        
        request = urllib2.Request(u,self.dd,self.headers)
        result = ClientCookie.urlopen(request)
        #html = result.read()            
        #data= BeautifulSoup.BeautifulSoup(html)
        #return data
        return
        
    def get(self,page):
        """
        basic url to source to beautifulsoup method
        """
        request = urllib2.Request(page,self.dd,self.headers)
        result = ClientCookie.urlopen(request)
        html = result.read()            
        data= BeautifulSoup.BeautifulSoup(html)
        return data        
    
    def strip_members(self,data):
        """
        get member ids for page viewing
        """
        urls=[]
        for a in data.findAll("a"):
            s= a["href"]
            if "viewprofile" in s:
                urls.append(''.join(["http://www.pof.com/",s]))
        return urls
        
if __name__=="__main__":
    pof_uname="somechick" #pof username
    pof_pword="12345" #pof pword
    pof_pid="54321" #pof profile id
    bot = pof_bot(pof_uname,pof_pword,pof_pid)
    bot.checkAllMail() # check all messages, reply if needed, create log file
    