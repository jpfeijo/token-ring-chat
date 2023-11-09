import socket
import queue
import threading
import binascii
import random
from time import *

with open('config.txt') as f:
    lines = f.readlines()

# neighborIP = lines[0].strip().split(':')[0]
# neighborPort = int(lines[0].strip().split(':')[1])
# userName = lines[1].strip()
tokenExpirationTime = int(lines[2].strip())
# userHasToken = lines[3].strip().lower() == "true"
# userStartedWithTokek = userHasToken
# userIP = input("Enter your IP: ")
# userPort = int(input("Enter neighbor port: "))

messageSent = False
tokenReceivedTime = 0
minNextTokenTime = int(input("Enter min next token time: "))

removeToken = False


userIP = ""
userPort = int(input("Enter your port: "))
userHasToken = input("do you have the toker (true/false)") == "true"
userName = input("Enter your name: ")
userStartedWithToken = userHasToken

neighborIP = userIP
neighborPort = int(input("Enter neighbor port: "))


dataMessages = queue.Queue()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((userIP, userPort))

if userHasToken:
    print('Você tem o token')


def userStartedWithToken():
    global tokenReceivedTime
    if userHasToken and not dataMessages.empty():
        sendMessages()
        print('Mensagem enviada')
    if userHasToken:
        sleep(tokenExpirationTime)
        tokenReceivedTime = time()
        passAlongToken()


def receive():
    while True:
        message, _ = s.recvfrom(1024)
        handleMessage(message)


def handleMessage(messageRaw):
    global tokenReceivedTime, userStartedWithToken, messageSent, userHasToken, dataMessages, messageBeingProcessed, removeToken

    message = messageRaw.decode()
    sleep(tokenExpirationTime)

    if message.startswith("9000"):

        if userStartedWithToken:
            if time() - tokenReceivedTime < minNextTokenTime:
                print('Token recebido antes do tempo minimo, 2 tokens na rede')
                return
            


        if messageSent:
            print('Token recebido mas esperando por ACK')
            return

        userHasToken = True
        tokenReceivedTime = time()

        if dataMessages.empty():
            print('Token recebido mas nenhuma mensagem para ser enviada')
            sleep(tokenExpirationTime)
            if not removeToken:
                passAlongToken()
            else:
                removeToken = False
            return

        messageSent = True
        sendMessages()
        print('Token recebido e mensagem enviada -- Esperando por ACK')
        return

    if message.startswith("7777"):
        errorControl, source, destination, crc, messageContent = unpackPackage(
            message)

        if destination == userName:
            calculatedCrc = str(binascii.crc32(
                messageContent.encode()) & 0xFFFFFFFF)
            if calculatedCrc != crc:
                print('CRC nao confere')
                passAlongMessages(forwardMessage(
                    "NACK", source, destination, crc, messageContent).encode())
                return
            else:
                print('Mensagem recebida: ', messageContent)
                passAlongMessages(forwardMessage(
                    "ACK", source, destination, crc, messageContent).encode())
                return

        elif source == userName:
            if errorControl == "ACK":
                print('ACK recebido')
                messageSent = False
                dataMessages.get()
                if not removeToken:
                    passAlongToken()
                else:
                    emoveToken = False
                return

            elif errorControl == "NACK":
                print(
                    'NACK recebido (Mensagem sera enviada na proxima rodada)')
                messageSent = False
                if not removeToken:
                    passAlongToken()
                else:
                    removeToken = False

            elif errorControl == "naoexiste":
                if destination != 'TODOS':
                    print(
                        'Destinatario nao existe ou esta desligado')
                    messageSent = False
                    dataMessages.get()
                    if not removeToken:
                        passAlongToken()
                    else:
                        removeToken = False
                else:
                    print('Mensagem enviada para todos os usuarios')
                    messageSent = False
                    dataMessages.get()
                    if not removeToken:
                        passAlongToken()
                    else:
                        removeToken = False
                    return

        else:
            errorControl, source, destination, crc, messageContent = unpackPackage(
                message)
            if destination == 'TODOS':
                print('(Broadcast):', messageContent)
                passAlongMessages(message.encode())
                return
            # esse else tava quebrando e a mensagem sempre caia aqui ================
            elif source != userName and errorControl == "naoexiste":
                newMessageContent = messageContent
                if random.randint(0, 100) < 10:
                    print("gerando erro")
                    newMessageContent = messageContent + ' (corrompida)'

                passAlongMessages(forwardMessage(
                    errorControl, source, destination, crc, newMessageContent).encode())

    messageBeingProcessed = False


def passAlongMessages(message):
    s.sendto(message, (neighborIP, neighborPort))


def passAlongToken():
    global userHasToken
    print('Passando o token')
    s.sendto('9000'.encode(), (neighborIP, neighborPort))
    userHasToken = False


def sendMessages():
    message = dataMessages.queue[0]

    if message.startswith('@'):
        destination = message.split(' ')[0][1:]
        print('Mensagem privada para', destination)
        messageContent = message.split(' ', 1)[1]
        package = packPackage("naoexiste", userName,
                              destination, messageContent)

    else:
        package = packPackage("naoexiste", userName, "TODOS", message)

    s.sendto(package.encode(), (neighborIP, neighborPort))


def packPackage(errorControl, source, destination, message):
    crc = str(binascii.crc32(message.encode()) & 0xFFFFFFFF)
    package = f"7777:{errorControl};{source};{destination};{crc};{message}"
    return package


def forwardMessage(errorControl, source, destination, crc, message):
    package = f"7777:{errorControl};{source};{destination};{crc};{message}"
    return package


def unpackPackage(package):
    partes = package.split(':')[1].split(';')
    if len(partes) == 5:
        controle_erro, origem, destino, crc, mensagem = partes
        return controle_erro, origem, destino, crc, mensagem
    return None


def writeMessages():
    global removeToken
    while True:
        message = input("")
        if message == "!gerarToken":
            passAlongToken()
            return
        if message == "!removeToken":
            removeToken = True
            return
        if dataMessages.qsize() < 10:
            dataMessages.put(message)
        else:
            print("Fila cheia, espera para enviar mais mensagens")


userStartedWithToken()

threading.Thread(target=receive).start()
threading.Thread(target=writeMessages).start()
