#!/bin/python
import psutil
from time import sleep
import datetime
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import smtplib
import ConfigParser
from email.mime.text import MIMEText

class service_checker:
    def __init__(self):
        self.last_check=None
        self.progs=[]
        self.services={}
        self.progs={}

        self.getConfig()

    def getConfig(self):
        config = ConfigParser.ConfigParser()
        config.read("config.cfg")

        for s in config.sections():
            if s=="general":
                for i in config.items(s):
                    print i
                    setattr(self,i[0],i[1])

            else:
                myprops={
                                    "last_check":None,
                                    "status":None,
                                    "last_ok":None,
                                    "alert_sent":None,
                                    }

                for i in config.items(s):
                    myprops[i[0]]=i[1]

                self.services[s]=myprops

                if self.progs[myprops["prog"]]== None :
                    self.progs[myprops["prog"]]== {s:myprops}
                else:
                    self.progs[myprops["prog"]][s]=myprops


    def run(self,polling_interval):
        while True:
            try:
                self.check()
                sleep(polling_interval)
            except Exception:
                logger.exception(Exception)
                sleep(polling_interval)


    def check(self):
        logger.info("start checking services")
        check_tstamp=datetime.datetime.now()
        process_list=psutil.process_iter()
        for i in process_list:
            process_name=i.name
            #logger.debug(process_name)
            if process_name in self.progs: #process is in list
                if i.cmdline in self.progs[i] or self.progs[]:
                    props["last_check"]=check_tstamp
                    self.all_ok(process_name,props)

        for k,v in self.services.items():
            if v["last_check"]!=check_tstamp: #service was no running
                v["status"]="nok"
                v["last_check"]=check_tstamp
                self.alert(k,v)

    def alert(self,serviceName,props):
        if props["alert_sent"]== None:
            logger.error( "Service %s:%s is NOT running --> Creating alert" % (serviceName,props["cmdline"]))
            alert_result=self.send_alert("[NOK] service %s:%s is NOT running" % (serviceName,props["cmdline"]))
            if alert_result==True:
                props["alert_sent"]=datetime.datetime.now()
        else:
            logger.error("Service %s:%s is NOT running, alert already fired" % (serviceName,props["cmdline"]))

    def all_ok(self,serviceName,props):
        if props["alert_sent"]!=None: #there was an alert
            logger.error("service %s:%s is again available --> send all_ok" % (serviceName,props["cmdline"]))
            props["alert_sent"]=None
            self.send_alert(self.alert_prefix +"service %s:%s is again available [ok]" % (serviceName,props["cmdline"]))

        else :
            logger.info("Service %s:%s is running" % (serviceName,props["cmdline"]))

        props["status"]="ok"
        props["last_ok"]=props["last_check"]


    def send_alert(self,txt):
        try:
            msg = MIMEText(txt.encode('utf-8'), 'plain', 'utf-8')
            msg['Subject'] = txt
            msg['From'] = self.alert_from
            msg['To'] = self.alert_to


            s = smtplib.SMTP(self.smtp_server)
            s.ehlo()
            s.starttls()
            s.login(self.smtp_user,self.smtp_password)
            logger.debug(txt)
            s.sendmail(self.alert_from, self.alert_to, msg.as_string())
            s.quit()
            logger.info("alert sent to %s" % self.alert_to)
            return True

        except Exception:
            logger.error("alert could not be sent")
            logger.exception(Exception)
            return False

if __name__ == '__main__':
    LOGFILE=os.path.basename(__file__)+'.log'
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    formater=logging.Formatter("%(asctime)s - %(levelname)7s - %(message)s")
    rHandler=TimedRotatingFileHandler(LOGFILE, when='d', interval=1, backupCount=7)
    rHandler.setFormatter(formater)
    logger.addHandler(rHandler)

    sh=logging.StreamHandler()
    sh.setFormatter(formater)
    logger.addHandler(sh)
    service_checker().run(10)