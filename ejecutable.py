import numpy as np
from flask import Flask, request, render_template, json, Response
import time
import socket
import threading
import numpy as np
import os


app = Flask(__name__)


global numeroAnimalMobile
numeroAnimalMobile = 1
global NUMERO_MAXIMO_MODULOS
NUMERO_MAXIMO_MODULOS = 5

global ESTADO_MODULOS
ESTADO_MODULOS = []

global ACTIVIDAD_ACTUAL
global datosCompletos 
global datosTemporales 
ACTIVIDAD_ACTUAL = [] ## una actividad para cada animal con dispositivo
datosCompletos =[]
datosTemporales =[]


for modulo in  range(0,NUMERO_MAXIMO_MODULOS):
	ACTIVIDAD_ACTUAL.append(3)
	ESTADO_MODULOS.append(0)
	datosCompletos.append(  ['','','','','','','','','',''] )

datosTemporales = np.zeros((len(datosCompletos) , 1,6)).tolist()


global LISTA_ACTIVIDADES
global LISTA_LINKS
#### Comiendo = 0
#### Rumiando = 1
#### Caminando = 2
#### Nada = 3
LISTA_ACTIVIDADES = ['Comiendo', 'Rumiando', 'Caminando', 'Nada']
LISTA_LINKS = ['comiendo.png', 'rumia.png', 'caminando.png', 'nada.png']


lock = threading.Lock()

global TIEMPO_INICIO
TIEMPO_INICIO = time.time() #Variable que guarda el tiempo en el que el servidor empezó a correr
global fechaYhora
FECHA_Y_HORA = "" #Variable para etiquetar los datos con fechas y horas
global nuevaLineaDatos
nuevaLineaDatos = [0,0,0,0,0,0,0,0,0,""]

###SWITCH MLC
global estadoLEDMLC
estadoLEDMLC = 0


### hilo para recivir los datos por sockets
def ThreadActualizarSocket():
	global TIEMPO_INICIO
	global ACTIVIDAD_ACTUAL
	global datosCompletos 
	global datosTemporales 
	global nuevaLineaDatos
	global ESTADO_MODULOS
	print("ThreadActualizarSocket Started... ")
	UDP_IP = socket.gethostbyname(socket.gethostname())
	UDP_PORT = 9001 ## Este puerto debe coincidir con el configurado en el módulo wifi para el envío de datos
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((UDP_IP, UDP_PORT))

	while True:
		lock.acquire()
		data, addr = s.recvfrom(1024)
		data = data.decode()
		file = open("datosAccel"+str(TIEMPO_INICIO),"a") #Se activa (crea) el archivo para guardar (escribir) un nuevo dato
		try:
			ArrayData = data.split("#")
			Ax = float(ArrayData[0])
			Ay = float(ArrayData[1])
			Az = float(ArrayData[2])
			Gx = float(ArrayData[3])
			Gy = float(ArrayData[4])
			Gz = float(ArrayData[5])
			IdClient = int(ArrayData[6])-1
			NumeroPaquete = float(ArrayData[7])
			fechaYhora = str(time.strftime("%c"))

			nuevaLineaDatos = [ Ax,Ay,Az,Gx,Gy,Gz,IdClient,NumeroPaquete,ACTIVIDAD_ACTUAL[IdClient], fechaYhora]
			##print ("linea", nuevaLineaDatos)
			datosCompletos[IdClient].append(nuevaLineaDatos)
			datosTemporales[IdClient].append(nuevaLineaDatos[0:6])
			ESTADO_MODULOS[IdClient] = 1
			file.write( ( fechaYhora + " %.1f \t %.5f \t %.5f \t %.5f \t %.5f \t %.5f \t %.5f \t %.5f \t"%(NumeroPaquete, IdClient, Ax, Ay, Az, Gx, Gy, Gz) ) + "	 " + str(ACTIVIDAD_ACTUAL[IdClient]) + "\n" )
			file.close() #Cada vez que el servidor recibe un dato lo guarda adecuamente en el archivo plano de texto
					  	 #para evitar perdidas de datos
		except Exception as e:
			print(e)
			print("Error en dato")
		lock.release()
threading.Thread(target=ThreadActualizarSocket).start()

### hilo para realizar predición de estados
def ThreadMLC():
	global estadoLEDMLC
	global datosTemporales 
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	print("ThreadMLC Started ...")
	######## Machine learnning
	###loaded_model
	# try:
	# 	loaded_model = joblib.load('./model.csv')
	# except Exception as inst:
	# 	print("No se cargó el modelo")
	# 	print(type(inst))    # la instancia de excepción
	# 	print(inst.args)     # argumentos guardados en .args
	# 	print(inst)          # __str__ permite imprimir args directamente,

	# else:
	# 	print("____________________________________________")
	# 	print("MODELO CARGADO")
	# 	print("____________________________________________")
	
	while True:
		if(estadoLEDMLC==1):
			longitudTemporalModuloMayor=0
			for i in range(0,NUMERO_MAXIMO_MODULOS):
				x = len(datosTemporales[i])
				if (x>longitudTemporalModuloMayor):
					longitudTemporalModuloMayor=x
			print("longitudTemporalModuloMayor",longitudTemporalModuloMayor)
			if(longitudTemporalModuloMayor>= 700):
				for animali in range(0,NUMERO_MAXIMO_MODULOS):
					x = len(datosTemporales[animali])
					if not (x== 0): ### si no esta vacio 
						### se realiza la predicion
							datosPredecir = datosTemporales[animali]
							datosPredecir = datosPredecir[len(datosPredecir)-100:len(datosPredecir)] ### Matriz 100 filas, 6 columnas
							predecida = 2
							ACTIVIDAD_ACTUAL[animali]= predecida
							print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL)

					datosTemporales = np.zeros((len(datosCompletos) , 1,6)).tolist()
			else:
				#print("esperar")
				time.sleep(5)

threading.Thread(target=ThreadMLC).start()

@app.route('/')
def indexTemplate():
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	global LISTA_ACTIVIDADES
	global LISTA_LINKS
	global numeroAnimalMobile
	LISTA = zip(LISTA_ACTIVIDADES, LISTA_LINKS, range(0,len(LISTA_ACTIVIDADES)))
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	return render_template( 'index.html' , ListaModulos=ListaModulos,NUMERO_MAXIMO_MODULOS=NUMERO_MAXIMO_MODULOS,LISTA=LISTA  )

@app.route('/mobile')
def indexMobile():
	global LISTA_ACTIVIDADES
	global LISTA_LINKS
	global numeroAnimalMobile
	LISTA = zip(LISTA_ACTIVIDADES, LISTA_LINKS, range(0,len(LISTA_ACTIVIDADES)))
	ACTUAL = ACTIVIDAD_ACTUAL[0]
	return render_template('mobile.html', LISTA=LISTA , ACTUAL=ACTUAL, numeroAnimal=numeroAnimalMobile )
@app.route('/actualizar_estado', methods = ['POST'])
def actualizar_estado():
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	for modulo in  range(0,NUMERO_MAXIMO_MODULOS): 
		ACTIVIDAD_ACTUAL[modulo] = int(request.form['estadoVaca'+str(modulo)])
	print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL)
	##print("xxxxxxxxxxxxxxxxxxx")
	##print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL )
	return ""

### Recibe la información del switch MLC, para así comenzar a predecir
@app.route('/switchMLC', methods = ['POST'])
def switchMLC():
	global estadoLEDMLC
	estadoLEDnuevo = request.form['led']
	print("la nueva accion del LED es : "  + estadoLEDnuevo)
	if(estadoLEDnuevo=='true'):
		estadoLEDMLC=1
	elif(estadoLEDnuevo=='false'):
		estadoLEDMLC=0
	return ""


### Envia la información de los estados de conexion de los modulos
@app.route('/actualizarEstadoModulos', methods=['POST'])
def actualizarEstadoModulos():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global ESTADO_MODULOS
	global datosTemporales
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	for modulo in ListaModulos:
		if(len(datosTemporales[modulo])==0):
			ESTADO_MODULOS[modulo] = 0

	return json.dumps({'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS,'ESTADO_MODULOS':ESTADO_MODULOS, 'ListaModulos':list(ListaModulos)});

### Envia la información de las graficas.
@app.route('/actualizarGraficas', methods=['POST'])
def actualizarGraficas():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global TIEMPO_INICIO
	global nuevaLineaDatos ##[ Ax,Ay,Az,Gx,Gy,Gz,IdClient,NumeroPaquete,ACTIVIDAD_ACTUAL[IdClient], fechaYhora]
	modulo = int(nuevaLineaDatos[6])
	Ax = nuevaLineaDatos[0]
	Ay = nuevaLineaDatos[1]
	Az = nuevaLineaDatos[2]
	Gx = nuevaLineaDatos[3]
	Gy = nuevaLineaDatos[4]
	Gz = nuevaLineaDatos[5]
	tiempo = time.time()-TIEMPO_INICIO
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	return json.dumps({'Ax':Ax ,'Ay':Ay ,'Az':Az ,'Gx':Gx ,'Gy':Gy ,'Gz':Gz ,'tiempo':tiempo, 'modulo':modulo,'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS, 'ListaModulos':list(ListaModulos), 'nuevaLineaDatos':nuevaLineaDatos});

### Envia la información de los estados de los animales
@app.route('/actualizarEstadosVacas', methods=['POST'])
def actualizarEstadosVacas():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global ACTIVIDAD_ACTUAL
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	return json.dumps({'ACTIVIDAD_ACTUAL':ACTIVIDAD_ACTUAL,'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS, 'ListaModulos':list(ListaModulos)});


if __name__ == '__main__':
	app.run(host='0.0.0.0',debug = True ,port= 9001, use_reloader=False, threaded=True)


