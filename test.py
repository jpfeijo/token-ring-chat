import socket
import queue
import threading
import binascii

with open('config.txt') as f:
    lines = f.readlines()

userIP = lines[0].strip().split(':')[0]
userPort = int(lines[0].strip().split(':')[1])
userName = lines[1].strip()
tokenExpirationTime = int(lines[2].strip())
userHasToken = lines[3].strip().lower() == "true"

messageSent = False

neighborIP = input("Enter neighbor IP: ")
neighborPort = int(input("Enter neighbor port: "))
neighborName = input("Enter neighbor name: ")

dataMessages = queue.Queue()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((userIP, userPort))


def receive():
    while True:
        message, _ = s.recvfrom(1024)
        messageDecoded = message.decode()

        if messageDecoded.startswith("9000"):  # token
            # userHasToken = True
            pass

        if messageDecoded.startswith("7777"):
            errorControl, source, destination, crc, messageContent = unpackPackage(
                messageDecoded)

        if source == userName:
            passAlongToken()
            # passa o token, pois a mensgem enviada já deu a volta


def handleMessage(message, address):
    global messageSent, userHasToken, dataMessages

    if message.startswith("9000"):
        if messageSent:
            print('Token recebido mas esperando por ACK')
            return

        userHasToken = True
        if dataMessages.empty():
            print('Token recebidom mas nenhuma mensagem para ser enviada')
            passAlongToken()
            return

        messageSent = True
        sendMessages()
        print('Token recebido e mensagem enviada -- Esperando por ACK')
        return

    if message.startswith("7777"):
        errorControl, source, destination, crc, messageContent = unpackPackage(
            messageDecoded)

        pass


def passAlongMessages():
    isMessageForMe = True  # variavel mocada

    while True:
        message, _ = s.recvfrom(1024)
        messageDecoded = message.decode()
        if isMessageForMe:
            print(message.decode())

        s.sendto(message, (neighborIP, neighborPort))


def passAlongToken():
    global userHasToken
    s.sendto('9000'.encode(), (neighborIP, neighborPort))
    userHasToken = False


def sendMessages():
    message = dataMessages[0]
    package = packPackage("naoexiste", userName, neighborName, message)
    s.sendto(package.encode(), (neighborIP, neighborPort))


def packPackage(errorControl, source, destination, message):
    crc = str(binascii.crc32(message.encode()) & 0xFFFFFFFF)
    package = f"7777:{errorControl};{source};{destination};{crc};{message}"
    return package


def unpackPackage(package):
    if package.startswith("7777:"):
        partes = package[5:].split(';')
        if len(partes) == 5:
            controle_erro, origem, destino, crc, mensagem = partes
            return controle_erro, origem, destino, crc, mensagem
    return None


def writeMessages():
    while True:
        message = input("")
        dataMessages.put(message)
        print(dataMessages.queue)


t1 = threading.Thread(target=receive)
t1.daemon = True
t1.start()

# t2 = threading.Thread(target=passAlongMessages)
# t2.daemon = True
# t2.start()

# t3 = threading.Thread(target=sendMessages)
# t3.daemon = True
# t3.start()

t4 = threading.Thread(target=writeMessages)
t4.daemon = True
t4.start()

# t3.join()
t4.join()
