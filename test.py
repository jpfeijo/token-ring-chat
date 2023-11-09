import socket
import queue
import threading
import binascii
import random
from time import *

#leitura do arquivo de configuração
with open('config.txt') as f:
    lines = f.readlines()

#atualiza as variaveis com os valores do arquivo de configuração
# neighborIP = lines[0].strip().split(':')[0]
# neighborPort = int(lines[0].strip().split(':')[1])
# userName = lines[1].strip()
tokenExpirationTime = int(lines[2].strip())
# userHasToken = lines[3].strip().lower() == "true"
# userStartedWithTokek = userHasToken
# userIP = input("Enter your IP: ")
# userPort = int(input("Enter neighbor port: "))

#variaveis para testar localmente
userIP = ""
userPort = int(input("Enter your port: "))
userHasToken = input("do you have the toker (true/false)") == "true"
userName = input("Enter your name: ")
userStartedWithToken = userHasToken
neighborIP = userIP
neighborPort = int(input("Enter neighbor port: "))
#-------------------------------------------------------------

messageSent = False #variavel para verificar se a mensagem foi enviada
tokenReceivedTime = 0 #variavel para verificar o tempo que último token foi recebido

if userHasToken: #se o usuario tiver o token, ele atualiza as variáveis de controle do token
    minNextTokenTime = int(input("Enter min next token time: "))
    timeOutTime = int(input("Enter the time out time: "))

removeToken = False #variavel para verificar se o token deve ser removido





dataMessages = queue.Queue() #fila para armazenar as mensagens a serem enviadas

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #cria o socket
s.bind((userIP, userPort))

if userHasToken: 
    print('Você tem o token')
    print()


def startRing(): #se o usuario começa com o token, ele envia o token para o vizinho
    global tokenReceivedTime
    if userHasToken and not dataMessages.empty(): #se tiver mensagem para enviar, envia a mensagem
        sendMessages()
        print('Mensagem enviada')
    if userHasToken: #se não, apenas repassa o token
        sleep(tokenExpirationTime)
        tokenReceivedTime = time() #atualiza o tempo que o token foi recebido
        passAlongToken()


def receive(): #função em loop para receber as mensagens
    while True:
        message, _ = s.recvfrom(1024)
        handleMessage(message) #quando recebe, chama a função para tratar a mensagem


def handleMessage(messageRaw):
    global tokenReceivedTime, userStartedWithToken, messageSent, userHasToken, dataMessages, messageBeingProcessed, removeToken

    message = messageRaw.decode()#decode da mensagem recebida
    sleep(tokenExpirationTime)#tempo de timeOut

    if message.startswith("9000"): #se receber o token

        if userStartedWithToken:
            if time() - tokenReceivedTime < minNextTokenTime:
                #se o usuario faz o controle do token e recebeu o token antes do tempo minimo,
                #   ele envia o token de volta para a rede
                print()
                print("----------------------------------------------------------")
                print(' Token recebido antes do tempo minimo, 2 tokens na rede')
                print("----------------------------------------------------------")
                print()
                return
            

# precisa disso?
        if messageSent: #se recebeu um token enquanto esperava um ack, ele apenas retorna
            print('Token recebido mas esperando por ACK')
            return

        userHasToken = True 
        tokenReceivedTime = time()

        if dataMessages.empty(): 
            #se não tiver mensagem para enviar, ele apenas repassa o token
            print('Token recebido mas nenhuma mensagem para ser enviada')
            print()
            sleep(tokenExpirationTime)
            if not removeToken: 
                passAlongToken()
            else: #se removeToken for true, ele remove o token do anel
                removeToken = False
            return

        messageSent = True #se tiver mensagem para enviar, ele envia a mensagem e espera uma resposta
        sendMessages()
        print('Token recebido e mensagem enviada -- Esperando por resposta')
        print()
        return

    if message.startswith("7777"): #se receber um pacote de dados
        errorControl, source, destination, crc, messageContent = unpackPackage(
            message)

        if destination == userName: #se o destino for o usuario
            calculatedCrc = str(binascii.crc32( #calcula o crc da mensagem recebida e envia o ack ou nack
                messageContent.encode()) & 0xFFFFFFFF)
            if calculatedCrc != crc:
                print('Mensagem recebida, porem CRC não confere')
                print()
                passAlongMessages(forwardMessage(
                    "NACK", source, destination, crc, messageContent).encode())
                return
            else:
                print('Mensagem recebida corretamente: ', messageContent)
                print()
                passAlongMessages(forwardMessage(
                    "ACK", source, destination, crc, messageContent).encode())
                return

        elif source == userName: #se o usuario for o remetente, ele verifica o controle de erro
            if errorControl == "ACK": #em caso de ACK, retira a mensagem da fila e repassa o token
                print('ACK recebido')
                print()
                messageSent = False
                dataMessages.get()
                if not removeToken:
                    passAlongToken()
                else: #se removeToken for true, ele remove o token do anel
                    removeToken = False
                return

            elif errorControl == "NACK": #em caso de NACK, mantem a mensagem na fila e repassa o token
                print(
                    'NACK recebido (Mensagem sera enviada na proxima rodada)')
                print()
                messageSent = False
                if not removeToken:
                    passAlongToken()
                else: #se removeToken for true, ele remove o token do anel
                    removeToken = False

            elif errorControl == "naoexiste": #em caso de naoexiste, ele retira a mensagem da fila
                if destination != 'TODOS':
                    print(
                        'Destinatario nao existe ou esta desligado')
                    print()
                    messageSent = False
                    dataMessages.get()
                    if not removeToken:
                        passAlongToken()
                    else:
                        removeToken = False
                else:
                    print('Mensagem enviada para todos os usuarios')
                    print()
                    messageSent = False
                    dataMessages.get()
                    if not removeToken:
                        passAlongToken()
                    else: #se removeToken for true, ele remove o token do anel
                        removeToken = False
                    return

        else: #se a mensagem não é pra mim
            errorControl, source, destination, crc, messageContent = unpackPackage(
                message)
            if destination == 'TODOS': #se a mensagem for broadcast, ele printa e repassa a mensagem
                print('(Broadcast):', messageContent)
                passAlongMessages(message.encode())
                return
            elif source != userName and errorControl == "naoexiste": #se a mensagem for para outro usuario
                newMessageContent = messageContent
                if random.randint(0, 100) < 10: #10% de chance de corromper a mensagem
                    print("gerando erro")
                    newMessageContent = messageContent + ' (corrompida)'

                passAlongMessages(forwardMessage(
                    errorControl, source, destination, crc, newMessageContent).encode())
                #repassa a mensagem

    messageBeingProcessed = False


def passAlongMessages(message): #função para repassar a mensagem para o proximo do anel
    s.sendto(message, (neighborIP, neighborPort))


def passAlongToken(): #função para repassar o token para o proximo do anel
    global userHasToken
    print('Passando o token')
    print()
    s.sendto('9000'.encode(), (neighborIP, neighborPort))
    userHasToken = False


def sendMessages(): #função para enviar as mensagens
    message = dataMessages.queue[0]

    if message.startswith('@'): #se a mensagem for privada, ele atualiza o destino e a mensagem
        destination = message.split(' ')[0][1:]
        print('Mensagem privada para', destination)
        print()
        messageContent = message.split(' ', 1)[1]
        package = packPackage("naoexiste", userName,
                              destination, messageContent)

    else:
        package = packPackage("naoexiste", userName, "TODOS", message) #se a mensagem for broadcast, ele atualiza a mensagem

    s.sendto(package.encode(), (neighborIP, neighborPort))


def packPackage(errorControl, source, destination, message): #função para empacotar a mensagem
    crc = str(binascii.crc32(message.encode()) & 0xFFFFFFFF)
    package = f"7777:{errorControl};{source};{destination};{crc};{message}"
    return package


def forwardMessage(errorControl, source, destination, crc, message): #função para empacotar a mensagem recebendo crc como parametro
    package = f"7777:{errorControl};{source};{destination};{crc};{message}"
    return package


def unpackPackage(package): #função para desencapsular a mensagem
    partes = package.split(':')[1].split(';')
    if len(partes) == 5:
        controle_erro, origem, destino, crc, mensagem = partes
        return controle_erro, origem, destino, crc, mensagem
    return None


def writeMessages(): #função para escrever as mensagens
    global removeToken
    while True:
        message = input("")
        if message == "!gerarToken": #comando para gerar um novo token no anel
            passAlongToken()
            return
        if message == "!removeToken":  #comando para remover um token no anel
            removeToken = True
            return
        if dataMessages.qsize() < 10: #se a fila não estiver cheia, ele adiciona a mensagem na fila
            dataMessages.put(message)
        else:
            print("Fila cheia, espere para enviar mais mensagens")

def check_time(): #função para cuidar do tempo de timeout
    global tokenReceivedTime, userStartedWithToken
    if userStartedWithToken:
        while True:
            if time() - tokenReceivedTime > timeOutTime:
                print("No token received for a while, generating a new one")
                print()
                tokenReceivedTime = time()
                passAlongToken()
            sleep(1)
    else:
        return

startRing() #inicia o anel

threading.Thread(target=receive).start() #thread para receber as mensagens
threading.Thread(target=writeMessages).start() #thread para escrever as mensagens
threading.Thread(target=check_time).start() #thread para cuidar do tempo de timeout
