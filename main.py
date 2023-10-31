import socket
import datetime
from threading import Thread
import time

def tokenn():
    global token
    global free
    global s
    global remove
    token=1
    msg="ttt"+ip
    msg=bytes(msg,"utf-8")
    s.sendto(msg,(ip_next,send))
    time.sleep(1)
    token=0
    if remove==0:
        msg=bytes("token"+str(free),"utf-8")
        s.sendto(msg,(ip_next,send))
    else:
        remove=0
        print("Extra token successfully purged")
    #print("My IP: "+ip+" My receiving port: "+str(listen)+" Neighbour's IP: "+ip_next+" Neighbour's receiving port: "+str(send))

def sendd():
    global s
    global token
    global free
    global ip_next
    global send
    while True:
        msg,adr=map(str,input().split())
        ttl="5"
        msg+="@"+ttl+adr
        msg=bytes(msg,"utf-8")
        while token!=1: time.sleep(1)
        if free==1:
            s.sendto(msg,(ip_next,send))
            free=0
            print("Message sent")

def respond():
    global s
    global ss
    global token
    global free
    global setfree
    global ip_next
    global ip
    global send
    global remove
    while True:
        data,addr=s.recvfrom(1024)
        data=data.decode("utf-8")
        if data=="new":
            msg="new_acc ip:"+ip_next+"port:"+str(send)
            msg=bytes(msg,"utf-8")
            s.sendto(msg,(addr[0],addr[1]))
            ip_next=addr[0]
            send=addr[1]
        if "new_acc" in data:
            t=0
            ipp=""
            pport=""
            for i in range(len(data)-1):
                if data[i]==":" and t==0:
                    t=1
                    j=i+1
                    while data[j]!="p":
                        ipp+=data[j]
                        j+=1
                    i+=1
                if data[i]==":" and t==1: t=2
                if t==2: pport+=data[i+1]
            ip_next=ipp
            send=int(pport)
        if "@" in data:
            t=0
            addrr=""
            ttl=0
            for i in range(len(data)-2):
                if data[i]=="@":
                    t=1
                    ttl=int(data[i+1])
                if t==1: addrr+=data[i+2]
            msg,trash=map(str,data.split("@"))
            if addrr==ip:
                setfree=1
                print("Message received: "+msg)
            else:
                ttl-=1
                msg=bytes(msg+"@"+str(ttl)+addrr,"utf-8")
                if ttl>0: s.sendto(msg,(ip_next,send))
                else:
                    setfree=1
                    print("Message couldn't be delivered, removing from network")
        if "ttt" in data:
            addrr=""
            for i in range(3,len(data)): addrr+=data[i]
            if addrr!=ip and token==1: remove=1
            if addrr!=ip and token==0:
                msg=bytes(data,"utf-8")
                s.sendto(msg,(ip_next,send))
        if "token" in data:
            free=int(data[5])
            if setfree==1:
                free=1
                setfree=0
            #print("token"+ip+str(datetime.datetime.now())+"free: "+str(free))
            Thread(target=tokenn).start()
            msg="token received, ID: "+id+", DATE: "+str(datetime.datetime.now())
            msg=bytes(msg,"utf-8")
            ss.sendto(msg,(multi,multi_port))

id=str(datetime.datetime.now())+"ID"
print("Port:")
listen=int(input())
print("Neighbour's port:")
send=int(input())
print("IP:")
ip=input()
print("Neighbour IP:")
ip_next=input()
print("Token (0 or 1):")
token=int(input())
multi="239.192.0.100"
multi_port=10000
remove=0
free=0
setfree=0

s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((ip,listen))
ss=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
ss.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,2)
t=Thread(target=tokenn)
if token==1:
    free=1
    t.start()
msg=bytes("new","utf-8")
s.sendto(msg,(ip_next,send))
t2=Thread(target=respond)
t2.start()
t3=Thread(target=sendd)
t3.start()