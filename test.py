import socket
import queue
import threading
import binascii
import random
from time import sleep

with open('config.txt') as f:
    lines = f.readlines()

userIP = lines[0].strip().split(':')[0]
userPort = int(lines[0].strip().split(':')[1])
userName = lines[1].strip()
tokenExpirationTime = int(lines[2].strip())
userHasToken = lines[3].strip().lower() == "true"
userStartedWithTokek = userHasToken

messageSent = False
messageBeingProcessed = False

neighborIP = input("Enter neighbor IP: ")
neighborPort = int(input("Enter neighbor port: "))
neighborName = input("Enter neighbor name: ")

dataMessages = queue.Queue()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((userIP, userPort))

if userHasToken:
    print('Você tem o token')


def userStartedWithToken():
    if userHasToken and not dataMessages.empty():
        sendMessages()
        print('Mensagem enviada')
    if userHasToken:
        sleep(tokenExpirationTime)
        print('Token expirado -- Repassando token')
        passAlongToken()


def receive():
    while True:
        message, _ = s.recvfrom(1024)
        handleMessage(message)


def handleMessage(messageRaw):

    message = messageRaw.decode()
    sleep(tokenExpirationTime)
    global messageSent, userHasToken, dataMessages, messageBeingProcessed

    if messageBeingProcessed:
        print('Message is already being processed')
        return

    messageBeingProcessed = True

    if message.startswith("9000"):
        if messageSent:
            print('Token recebido mas esperando por ACK')
            return

        userHasToken = True

        if dataMessages.empty():
            print('Token recebido mas nenhuma mensagem para ser enviada')
            sleep(tokenExpirationTime)
            passAlongToken()
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
            # testar se o crc esta certo, caso esteja, enviar ack - caso nao esteja, enviar nack
        else:
            if destination == 'TODOS':
                print('(Broadcast):', message)
                passAlongMessages(message.encode())
            else:
                newMessageContent = messageContent
                if random.randint(0, 100) < 10:
                    newMessageContent = messageContent + ' (corrompida)'

                passAlongMessages(forwardMessage(
                    errorControl, source, destination, crc, newMessageContent).encode())

        if source == userName:
            if errorControl == "ACK":
                print('ACK recebido - Repassando token')
                messageSent = False
                dataMessages.get()
                passAlongToken()
                return

            elif errorControl == "NACK":
                print(
                    'NACK recebido - Repassando token (Mensagem sera enviada na proxima rodada)')
                messageSent = False
                passAlongToken()

            elif errorControl == "naoexiste":
                if destination != 'TODOS':
                    print(
                        'Destinatario nao existe ou esta desligado - Repassando token')
                    messageSent = False
                    passAlongToken()
                else:
                    print('Mensagem enviada para todos os usuarios - Repassando token')
                    messageSent = False
                    dataMessages.get()
                    passAlongToken()
                    return

    messageBeingProcessed = False


def passAlongMessages(message):
    s.sendto(message, (neighborIP, neighborPort))


def passAlongToken():
    global userHasToken
    s.sendto('9000'.encode(), (neighborIP, neighborPort))
    userHasToken = False


def sendMessages():
    message = dataMessages.queue[0]
    package = packPackage("naoexiste", userName, neighborName, message)
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
    while True:
        message = input("")
        if dataMessages.qsize() < 10:
            dataMessages.put(message)
        else:
            print("Fila cheia, espera para enviar mais mensagens")


userStartedWithToken()

threading.Thread(target=receive).start()
threading.Thread(target=writeMessages).start()
