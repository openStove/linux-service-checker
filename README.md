# linux-service-checker

This peace of code, is designed to be sure serveral services are running on the machine. If not, you can specify who is going to get an alert.
- You can also specify in which hours no check is performed (the time where you make your backup for example)
- When the service is running again, an "all ok" mail is sent

To do : 
- Perhaps I would implement an "action", so that you could do something when the service is down, for example restart...


##Install
You need to install psutil, with pipe, oder under ubuntu with apt-get install python-psutil
