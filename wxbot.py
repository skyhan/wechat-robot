#!/usr/bin/env python
# coding: utf-8
# import qrcode
import requests
import json
import xml.dom.minidom
import multiprocessing
import urllib
import time, re, sys, os, random
import subprocess

import msgparser


QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')


def utf82gbk(string):
    return string.decode('utf8').encode('gbk')

def make_unicode(data):
    if not data:
        return data
    result = None
    if type(data) == unicode:
        result = data
    elif type(data) == str:
        result = data.decode('utf-8')
    return result

class WXBot:
    def __init__(self):
        self.DEBUG = False
        self.uuid = ''
        self.base_uri = ''
        self.redirect_uri= ''
        self.uin = ''
        self.sid = ''
        self.skey = ''
        self.pass_ticket = ''
        self.deviceId = 'e' + repr(random.random())[2:17]
        self.BaseRequest = {}
        self.synckey = ''
        self.SyncKey = []
        self.User = []
        self.MemberList = []
        self.ContactList = []
        self.GroupList = []
        self.is_auto_reply = False
        self.syncHost = ''
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5'})

        try:
            with open('auto.json') as f:
                cfg = json.load(f)
                self.auto_reply_url = cfg['url']
                self.auto_reply_key = cfg['key']
        except Exception, e:
            self.auto_reply_url = None
            self.auto_reply_key = None

    def get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time())*1000 + random.randint(1,999),
        }
        r = self.session.get(url, params=params)
        r.encoding = 'utf-8'
        data = r.text
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return code == '200'
        return False

    def gen_qr_code(self):

        global tip

        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(time.time()),
        }

        r = requests.post(url, params)
        #g_info['tip'] = 1
        tip = 1

        with open(QRImagePath, 'wb') as fd:
            for chunk in r.iter_content(512):
                fd.write(chunk)

        if sys.platform.find('darwin') >= 0:
            subprocess.call(['open', QRImagePath])
        elif sys.platform.find('linux') >= 0:
            subprocess.call(['xdg-open', QRImagePath])
        else:
            os.startfile(QRImagePath)

        print('请使用微信扫描二维码以登录')
        # string = 'https://login.weixin.qq.com/l/' + self.uuid
        # qr = qrcode.QRCode()
        # qr.border = 1
        # qr.add_data(string)
        # qr.make(fit=True)
        # img = qr.make_image()
        # img.save('qr.jpg')

    def wait4login(self, tip):
        time.sleep(tip)
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (tip, self.uuid, int(time.time()))
        r = self.session.get(url)
        r.encoding = 'utf-8'
        data = r.text
        param = re.search(r'window.code=(\d+);', data)
        code = param.group(1)

        if code == '201':
            return True
        elif code == '200':
            param = re.search(r'window.redirect_uri="(\S+?)";', data)
            redirect_uri = param.group(1) + '&fun=new'
            self.redirect_uri = redirect_uri
            self.base_uri = redirect_uri[:redirect_uri.rfind('/')]
            return True
        elif code == '408':
            print '[login timeout]'
        else:
            print '[login exception]'
        return False

    def login(self):
        r = self.session.get(self.redirect_uri)
        r.encoding = 'utf-8'
        data = r.text
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
            return False

        self.BaseRequest = {
            'Uin': self.uin,
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
            }
        return True

    def init(self):
        url = self.base_uri + '/webwxinit?r=%i&lang=en_US&pass_ticket=%s' % (int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest
        }
        r = self.session.post(url, json=params)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        self.SyncKey = dic['SyncKey']
        self.User = dic['User']
        self.synckey = '|'.join([ str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List'] ])
        return dic['BaseResponse']['Ret'] == 0

    def status_notify(self):
        url = self.base_uri + '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
        self.BaseRequest['Uin'] = int(self.BaseRequest['Uin'])
        params = {
            'BaseRequest': self.BaseRequest,
            "Code": 3,
            "FromUserName": self.User['UserName'],
            "ToUserName": self.User['UserName'],
            "ClientMsgId": int(time.time())
        }
        r = self.session.post(url, json=params)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        return dic['BaseResponse']['Ret'] == 0

    def get_contact(self):
        url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (self.pass_ticket, self.skey, int(time.time()))
        r = self.session.post(url, json={})
        r.encoding = 'utf-8'
        if self.DEBUG:
            with open('contacts.json', 'w') as f:
                f.write(r.text.encode('utf-8'))
        dic = json.loads(r.text)
        self.MemberList = dic['MemberList']

        ContactList = self.MemberList[:]
        SpecialUsers = [
            'newsapp',
            'fmessage',
            'filehelper',
            'weibo',
            'qqmail',
            'fmessage',
            'tmessage',
            'qmessage',
            'qqsync',
            'floatbottle',
            'lbsapp',
            'shakeapp',
            'medianote',
            'qqfriend',
            'readerapp',
            'blogapp',
            'facebookapp',
            'masssendapp',
            'meishiapp',
            'feedsapp',
            'voip',
            'blogappweixin',
            'weixin',
            'brandsessionholder',
            'weixinreminder',
            'wxid_novlwrv3lqwv11',
            'gh_22b87fa7cb3c',
            'officialaccounts',
            'notification_messages',
            'wxid_novlwrv3lqwv11',
            'gh_22b87fa7cb3c',
            'wxitil',
            'userexperience_alarm',
            'notification_messages']
        for contact in ContactList:
            if contact['VerifyFlag'] & 8 != 0: # public account
                ContactList.remove(contact)
            elif contact['UserName'] in SpecialUsers: # special account
                ContactList.remove(contact)
            elif contact['UserName'].find('@@') != -1: # group
                self.GroupList.append(contact)
                ContactList.remove(contact)
            elif contact['UserName'] == self.User['UserName']: # self
                ContactList.remove(contact)
        self.ContactList = ContactList

        return True

    def batch_get_contact(self):
        url = self.base_uri + '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Count": len(self.GroupList),
            "List": [ {"UserName": g['UserName'], "EncryChatRoomId":""} for g in self.GroupList ]
        }
        r = self.session.post(url, data=params)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        return True

    def test_sync_check(self):
        for host in ['webpush', 'webpush2']:
            self.syncHost = host
            [retcode, selector] = self.sync_check()
            if retcode == '0':
                return True
        return False

    def sync_check(self):
        params = {
            'r': int(time.time()),
            'sid': self.sid,
            'uin': self.uin,
            'skey': self.skey,
            'deviceid': self.deviceId,
            'synckey': self.synckey,
            '_': int(time.time()),
        }
        url = 'https://' + self.syncHost + '.weixin.qq.com/cgi-bin/mmwebwx-bin/synccheck?' + urllib.urlencode(params)
        r = self.session.get(url)
        r.encoding = 'utf-8'
        data = r.text
        pm = re.search(r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', data)
        retcode = pm.group(1)
        selector = pm.group(2)
        return [retcode, selector]

    def sync(self):
        url = self.base_uri + '/webwxsync?sid=%s&skey=%s&lang=en_US&pass_ticket=%s' % (self.sid, self.skey, self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'SyncKey': self.SyncKey,
            'rr': ~int(time.time())
        }
        r = self.session.post(url, json=params)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        if self.DEBUG:
            print json.dumps(dic, indent=4)
        if dic['BaseResponse']['Ret'] == 0:
            self.SyncKey = dic['SyncKey']
            self.synckey = '|'.join([ str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List'] ])
        return dic

    def get_icon(self, id):
        url = self.base_uri + '/webwxgeticon?username=%s&skey=%s' % (id, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'img_'+id+'.jpg'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    def get_head_img(self, id):
        url = self.base_uri + '/webwxgetheadimg?username=%s&skey=%s' % (id, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'img_'+id+'.jpg'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    def get_msg_img(self, msgid):
        url = self.base_uri + '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'img_'+msgid+'.jpg'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    # Not work now for weixin haven't support this API
    def get_video(self, msgid):
        url = self.base_uri + '/webwxgetvideo?msgid=%s&skey=%s' % (msgid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'video_'+msgid+'.mp4'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    def get_voice(self, msgid):
        url = self.base_uri + '/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'voice_'+msgid+'.mp3'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    #Get the NickName or RemarkName of an user by user id
    def get_user_remark_name(self, uid):
        name = 'unknown group' if uid[:2] == '@@' else 'stranger'
        for member in self.MemberList:
            if member['UserName'] == uid:
                name = member['RemarkName'] if member['RemarkName'] else member['NickName']
        return name

    #Get user id of an user
    def get_user_id(self, name):
        for member in self.MemberList:
            if name == member['RemarkName'] or name == member['NickName'] or name == member['UserName']:
                return member['UserName']
        return None

    def auto_reply(self, word):
        if self.auto_reply_key == None or self.auto_reply_url == None:
            return 'hi'

        body = {'key': self.auto_reply_key, 'info':word}
        r = requests.post(self.auto_reply_url, data=body)
        resp = json.loads(r.text)
        if resp['code'] == 100000:
            return resp['text']
        else:
            return None

    def handle_msg(self, r):
        for msg in r['AddMsgList']:
            msgType = msg['MsgType']
            name = self.get_user_remark_name(msg['FromUserName']) #FromUserName is user id
            content = msg['Content'].replace('&lt;','<').replace('&gt;','>')
            msgid = msg['MsgId']
            if msgType == 51: #init message
                pass
            elif msgType == 1:
                if content.find('http://weixin.qq.com/cgi-bin/redirectforward?args=') != -1:
                    r = self.session.get(content)
                    r.encoding = 'gbk'
                    data = r.text
                    pos = self.search_content('title', data, 'xml')
                    print '[Location] %s : I am at %s ' % (name, pos)
                elif msg['ToUserName'] == 'filehelper':
                    print '[File] %s : %s' % (name, content.replace('<br/>','\n'))
                elif msg['FromUserName'] == self.User['UserName']: #self
                    pass
                elif msg['FromUserName'][:2] == '@@':
                    [people, content] = content.split(':<br/>')
                    group = self.get_user_remark_name(msg['FromUserName'])
                    name = self.get_user_remark_name(people)
                    print '[Group] |%s| %s: %s' % (group, name, content.replace('<br/>','\n'))
                else:
                    print '[Text] ', name, ' : ', content
                    # parse message here
                    parse_msg(name, content)

                    if self.is_auto_reply:
                        ans = self.auto_reply(content)
                        if ans:
                            if self.send_msg(msg['FromUserName'], ans):
                                print '[AUTO] Me : ', ans
                            else:
                                print '[AUTO] Failed'
            elif msgType == 3:
                image = self.get_msg_img(msgid)
                print '[Image] %s : %s' % (name, image)
            elif msgType == 34:
                voice = self.get_voice(msgid)
                print '[Voice] %s : %s' % (name, voice)
            elif msgType == 42:
                info = msg['RecommendInfo']
                print '[Recommend] %s : ' % name
                print '========================='
                print '= NickName: %s' % info['NickName']
                print '= Alias: %s' % info['Alias']
                print '= Local: %s %s' % (info['Province'], info['City'])
                print '= Gender: %s' % ['unknown', 'male', 'female'][info['Sex']]
                print '========================='
            elif msgType == 47:
                url = self.search_content('cdnurl', content)
                print '[Animation] %s : %s' % (name, url)
            elif msgType == 49:
                appMsgType = defaultdict(lambda : "")
                appMsgType.update({5:'link', 3:'music', 7:'weibo'})
                print '[Share] %s : %s' % (name, appMsgType[msg['AppMsgType']])
                print '========================='
                print '= title: %s' % msg['FileName']
                print '= desc: %s' % self.search_content('des', content, 'xml')
                print '= link: %s' % msg['Url']
                print '= from: %s' % self.search_content('appname', content, 'xml')
                print '========================='
            elif msgType == 62:
                print '[Video] ', name, ' sent you a video, please check on mobiles'
            elif msgType == 53:
                print '[Video Call] ', name, ' call you'
            elif msgType == 10002:
                print '[Redraw] ', name, ' redraw back a message'
            else:
                print '[Maybe] : %s，maybe image or link' % str(msg['MsgType'])
                print msg

    def proc_msg(self):
        print 'proc start'
        self.test_sync_check()
        while True:
            [retcode, selector] = self.sync_check()
            if retcode == '1100':
                pass
                #print '[*] you have login on mobile'
            elif retcode == '0':
                if selector == '2':
                    r = self.sync()
                    if r is not None:
                        self.handle_msg(r)
                elif selector == '7': # play WeChat on mobile
                    r = self.sync()
                    if r is not None:
                        self.handle_msg(r)
                elif selector == '0':
                    time.sleep(1)

    def send_msg_by_uid(self, word, dst = 'filehelper'):
        url = self.base_uri + '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)
        msg_id = str(int(time.time()*1000)) + str(random.random())[:5].replace('.','')
        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': {
                "Type": 1,
                "Content": make_unicode(word),
                "FromUserName": self.User['UserName'],
                "ToUserName": dst,
                "LocalID": msg_id,
                "ClientMsgId": msg_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        r = self.session.post(url, data = data, headers = headers)
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def send_msg(self, name, word, isfile = False):
        uid = self.get_user_id(name)
        if uid:
            if isfile:
                with open(word, 'r') as f:
                    result = True
                    for line in f.readlines():
                        line = line.replace('\n','')
                        print '-> '+name+': '+line
                        if self.send_msg_by_uid(line, uid):
                            pass
                        else:
                            result = False
                        time.sleep(1)
                    return result
            else:
                if self.send_msg_by_uid(word, uid):
                    return True
                else:
                    return False
        else:
            print '[*] this user does not exist'
            return False
    def search_content(self, key, content, fmat = 'attr'):
        if fmat == 'attr':
            pm = re.search(key+'\s?=\s?"([^"<]+)"', content)
            if pm: return pm.group(1)
        elif fmat == 'xml':
            pm=re.search('<{0}>([^<]+)</{0}>'.format(key),content)
            if pm: return pm.group(1)
        return 'unknown'

    def run(self):
        self.get_uuid()
        print 'get uuid end'
        self.gen_qr_code()
        print 'gen qr code end'
        self.wait4login(1)
        print 'wait4login end'
        self.wait4login(0)
        print 'wait4login end'
        if self.login():
            print 'login succeed'
        else:
            print 'login failed'
            return
        if self.init():
            print 'init succeed'
        else:
            print 'init failed'
            return
        print 'init end'
        self.status_notify()
        print 'status notify end'
        self.get_contact()
        print 'get %d contacts' % len(self.ContactList)

        if raw_input('auto reply?(y/n): ') == 'y':
            self.is_auto_reply = True
            print 'auto reply opened'
        else:
            print 'auto reply closed'

        self.proc_msg()

def main():
    bot = WXBot()
    bot.run()

if __name__ == '__main__':
    main()
