#!/bin/python
import psutil
from time import sleep
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
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
        self.run(int(self.polling_interval))

    def getConfig(self):
        try:
            config = ConfigParser.ConfigParser()
            config.read(CONFIG_FILE)

            for s in config.sections():
                if s=="general":
                    for i in config.items(s):
                        setattr(self,i[0],i[1])
                    self.set_logger()
                else:
                    myprops={"name":s,
                             "last_check":None,
                             "status":None,
                             "last_ok":None,
                             "alert_sent":None,
                             }

                    for i in config.items(s):
                        myprops[i[0]]=i[1]

                    if myprops["prog"] not in self.progs:
                        logger.debug("creation prog entry for %s" % myprops["prog"] )
                        self.progs[myprops["prog"]]=[myprops]
                    else :
                        self.progs[myprops["prog"]].append(myprops)
        except Exception:
            print "could not load config %s" % CONFIG_FILE
            logger.exception(Exception)
            sys.exit(2)


    def set_logger(self):
        logger.setLevel(getattr(logging,self.log_level))
        formater=logging.Formatter("%(asctime)s - %(levelname)7s - %(message)s")
        rHandler=TimedRotatingFileHandler(self.log_file, when='d', interval=1, backupCount=7)
        rHandler.setFormatter(formater)
        logger.addHandler(rHandler)

        if self.log_streamhandler in ["true","True","1"]:
            sh=logging.StreamHandler()
            sh.setFormatter(formater)
            logger.addHandler(sh)


    def run(self,polling_interval):
        while True:
            try:
                self.check()
                sleep(polling_interval)
            except Exception:
                logger.exception(Exception)
                sleep(polling_interval)


    def check(self):
        check_tstamp=datetime.datetime.now()
        hours_paused= self.alert_hour_paused.split(',')
        if str(check_tstamp.hour) in hours_paused:
            logging.info("we are actual in paused time, nothing to do : %s time:%s" %(hours_paused,check_tstamp.hour))
        else :
            logging.info("start checking services (not in paused time): %s time:%s" %(hours_paused,check_tstamp.hour))
            process_list=psutil.process_iter()
            for i in process_list:
                process_name=i.name()
                process_cmdline=i.cmdline()
                logger.debug("process=%s \n cmdline=%s" % (process_name,process_cmdline))
                if process_name in self.progs: #process is in list
                    for p in self.progs[process_name]:
                        if p["cmdline"] in process_cmdline or p["cmdline"]=="None":
                            logger.debug("found match in progs : %s" % p)
                            p["last_check"]=check_tstamp
                            self.all_ok(p)

            self.process_unchecked(check_tstamp)

    def process_unchecked(self,check_tstamp):
        for p in self.progs:
            logger.debug("myprog= %s" % p)
            for v in self.progs[p]:
                logger.debug("cmdline in list=%s" % v)
                if v["last_check"]!=check_tstamp: #service was not running
                    v["status"]="nok"
                    v["last_check"]=check_tstamp
                    self.alert(v)

    def alert(self,props):
        if props["alert_sent"]== None:
            logger.error( "Service %s:%s is NOT running --> Creating alert" % (props["name"],props["cmdline"]))
            alert_result=self.send_alert("service %s [NOK]" % (props["name"]))
            if alert_result==True:
                props["alert_sent"]=datetime.datetime.now()
        else:
            logger.error("Service %s:%s is NOT running, alert already fired" % (props["name"],props["cmdline"]))

    def all_ok(self,props):
        if props["alert_sent"]!=None: #there was an alert
            logger.error("service %s:%s is again available --> send all_ok" % (props["name"],props["cmdline"]))
            props["alert_sent"]=None
            self.send_alert("service %s [OK] again available " % (props["name"]))

        else :
            logger.info("Service %s:%s is running" % (props["name"],props["cmdline"]))

        props["status"]="ok"
        props["last_ok"]=props["last_check"]


    def send_alert(self,txt):
        try:
            msg = MIMEText(txt.encode('utf-8'), 'plain', 'utf-8')
            msg['Subject'] = self.alert_prefix +txt
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
    if len(sys.argv)!=2:
        print "specify config file as first argument sysarg=%s" % sys.argv
        sys.exit(2)
    CONFIG_FILE=sys.argv[1]
    logger = logging.getLogger('')
    service_checker()
