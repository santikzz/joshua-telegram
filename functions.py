from bs4 import BeautifulSoup as bs
import json
import requests
import re
import os
import time
from threading import Event
from datetime import date

exit = Event() #thread event to sudden terminate tracking

lineas = { "500":"Amarillo", "501":"Rojo", "502":"Blanco", "503":"Azul", "504":"Verde", "505":"Marron", "N/A":"N/A" }

def create(bot, uid, data):	
	path = f'./userdata/{uid}'
	if not os.path.exists(path):
		os.makedirs(path)
		try:
			f = open(f'{path}/data.json', 'w')
			f.write(data)
			f.close()
			bot.send_message(message.chat.id, f'Nuevo usuario: {uid} agregado exitosamente!')
			print(f'User {path}/data.json created!')
		except:
			bot.send_message(message.chat.id, f'Un error ha ocurrido al crear usuario: {uid}')
			print(f'Error creating {path}/data.json')
	else:
		bot.send_message(message.chat.id, f'Usuario: {uid} ya existe!')
		print(f'Error creating {path}/data.json (Already exists!)')

def save(uid, file, data):	
	path = f'./userdata/{uid}'
	try:
		f = open(f'{path}/{file}.json', 'w')
		f.write(data)
		f.close()
		print(f'Saving {path}/{file}.json successful.')
		return True
	except:
		print(f'Error saving {path}/{file}.json')
		return False

def load(uid, file):
	path = f'./userdata/{uid}/{file}.json'
	try:
		f = open(path, 'r')
		data = json.loads(f.read())
		f.close()
		print(f'Loading data from {path}')
		return data
	except:
		print(f'Error opening {path}')
		return 0

def saldo_comedor(bot, message, userdata):

	user = userdata['comedor_user']
	password = userdata['comedor_pass']

	url = 'http://comedortandil.unicen.edu.ar'
	login_route = '/cliente/login_contenido.php'

	login_payload = {
		'b_login':'Ingresar',
		'sis':'cliente',
		'destino':'',
		'xgap_historial':'skip',
		'servidororigen':'10.254.1.182',
		'paginaorigen':'/cliente/login_contenido.php',
		'nick': user,
		'passwd': password
	}

	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0', 'origin': 'http://comedortandil.unicen.edu.arr', 'referer': 'http://comedortandil.unicen.edu.ar/cliente/login_contenido.php'}

	s = requests.session()
	login_request = s.post(url + login_route, headers=headers, data=login_payload)
	cookies = login_request.cookies
	soup = bs(s.get('http://comedortandil.unicen.edu.ar/cliente/ajax_clientesaldo.php?xgap_historial=skip').text, 'lxml')
	raw = soup.text

	saldo = re.findall("\d+\.\d+", raw)[0]

	if('Ingreso al Sistema' in raw):
		bot.send_message(message.chat.id, f'Ha ocurrido un error: datos de sesion invalidos.')
		#return 0
	else:
		bot.send_message(message.chat.id, f'Saldo comedor: ${saldo}')
		#return saldo[0]

def saldo_sumo(bot, message, userdata):

	tarjeta = userdata["tarjeta"]

	html = requests.get(f'http://www.gpssumo.com/movimientos/get_movimientos/{tarjeta}/3').text
	#html = requests.get(f'http://nimrodsolutions.xyz/testws.php').text #debug

	if html == ' 1':
		return 0
	else:
		saldo = re.findall("'\$ (-?\d+.\d+)'", html)[1]
		bot.send_message(message.chat.id, f'Saldo sumo: ${saldo}')
		#return saldo[1]

################## SUMO TRACK SECTION ##################

#chequea si la tarjeta existe en el sistema
def check_card(tarjeta):
	res = requests.get(f'http://www.gpssumo.com/movimientos/get_movimientos/{tarjeta}/3').text
	if res == ' 1':
		return False
	else:
		return True

#devuelve la ultima transaccion de una tarjeta
def get_card_data(tarjeta):
	html = requests.get(f'http://www.gpssumo.com/movimientos/get_movimientos/{tarjeta}/3').text
	#html = requests.get('http://nimrodsolutions.xyz/testws.php').text #debug

	if (html == ' 1') or (html == ' 2') :
		return False
	else:
		last = re.search("{(.*?)},", html)[1]
		#debito = re.search("'DEBITO MONEDA'", last)		
		trans = re.search("\d+", last)[0]
		fecha = re.search("fecha : '(\d{2}\/\d{2}\/\d{4})'", last)[1]
		hora = re.search("hora : '(\d{2}:\d{2}) Hs.'", last)[1]
		linea = re.search("linea : '(\d{3})'", last)[1]

		if not linea:
			linea = 'N/A'

	data = {'last': trans, 'fecha': fecha, 'hora': hora, 'linea': linea }
	return data


def track(bot, message, args):

	uid = message.chat.id
	hoy = date.today()
	ndia = hoy.strftime("%d")
	hoy = hoy.strftime("%d/%m/%Y")

	#si al arg es add, agrego una nueva tarjeta con alias a /userdata/{user}/cards.js
	if args[0] == 'add':

		tarjeta = args[1] #numero de la tarjeta (8 digitos)
		alias = args[2]	#alias/nombre de la tarjeta

		if re.search("\d{7,8}", tarjeta): #chequeo que la tarjeta sea valida (contiene 7 a 8 digitos)

			print(f'{tarjeta} is valid.')
		
			if check_card(tarjeta): #chequeo que la tarjeta exista en el sistema

				print(f'{tarjeta} is registered.')
				tarjetas = load(uid, 'cards') #cargo la lista de tarjetas de /userdata/{user}/cards.js
				tarjetas[alias] = tarjeta #agrego el nuevo item al diccionario
				print(f'adding {tarjeta} as {alias}')	
				tarjetas = json.dumps(tarjetas) #convierto el diccionario a json
				save(uid, 'cards', tarjetas) #guardo el nuevo json en el archivo
				print(f'cards.js updated!')
				bot.send_message(message.chat.id, f'Nueva tarjeta {tarjeta} asignada a \'{alias}\'')

			else:
				print(f'{tarjeta} is valid, but doesn\'t exists!')
				bot.send_message(message.chat.id, f'Tarjeta {tarjeta} es valida, pero no esta registrada en el sistema de SUMO.')

		else:
			print(f'{tarjeta} is invalid!')
			bot.send_message(message.chat.id, f'Tarjeta {tarjeta} invalida!')

	elif args[0] == 'list':

		tarjetas = load(uid, 'cards')
		lista = ''
		for alias, tarjeta in tarjetas.items():
			lista += f'{alias.upper()}: {tarjeta}\n' 
		bot.send_message(message.chat.id, lista)


	elif args[0] == 'stop':
		print('Stoping tracking...')
		stop = True
		exit.set()
		time.sleep(1)
		exit.clear()

	elif args[0] == 'last':

		target = args[1]
		
		if re.search("\d{7,8}", target): #es una tarjeta	
			alias = target
			tarjeta = target
		else:
			tarjetas = load(uid, 'cards')

			if target in tarjetas: #si el alias existe en la lista de tarjetas
				tarjeta = tarjetas[target]
				alias = target
			else:
				print(f'Alias {target} doesn\'t exists')
				bot.send_message(message.chat.id, f'No existe tarjeta asociada para \'{target}\'')
				return None
		
		data_new = get_card_data(tarjeta) #obtengo la ultima transaccion

		if not data_new:
			print(f'No data on {tarjeta}')
			bot.send_message(message.chat.id, f'No hay transacciones de \'{alias}\' en los ultimos 6 meses.')
			return None
		else:
			hora = data_new['hora']
			linea = data_new['linea']
			fecha = data_new['fecha']

			if fecha == hoy:
				fecha = 'Hoy'
			elif (int(ndia) - int(fecha[:2])) == 1:
				fecha = 'Ayer'

			bot.send_message(message.chat.id, f'Ultimo viaje de \'{alias}\':\n{fecha} - {hora} hs - Linea {linea} ({lineas[linea]})')
	#end if args 'last'

	else:
		
		stop = False
		target = args[0]
		
		try:
			mins = args[1]
		except:
			mins = 5

		if re.search("\d{7,8}", target): #es una tarjeta
			
			alias = target
			tarjeta = target

		else:
			
			tarjetas = load(uid, 'cards')

			if target in tarjetas: #si el alias existe en la lista de tarjetas
				tarjeta = tarjetas[target]
				alias = target

			else:
				print(f'Alias {target} doesn\'t exists')
				bot.send_message(message.chat.id, f'No existe tarjeta asociada para \'{target}\'')
				return None

		cardfile = f'track_{tarjeta}'
		
		data_new = get_card_data(tarjeta) #obtengo la ultima transaccion

		if not data_new:
			print(f'No data on {tarjeta}')
			bot.send_message(message.chat.id, f'No hay transacciones de \'{alias}\' en los ultimos 6 meses.')
			return None
		
		#la guardo en el archivo track_{tarjeta}.json
		json_data = json.dumps(data_new)
		save(uid, cardfile, json_data)
		print(f'Track: {cardfile} rewriten.')

		hora = data_new['hora']
		linea = data_new['linea']
		fecha = data_new['fecha']

		if fecha == hoy:
			fecha = 'Hoy'
		elif (int(ndia) - int(fecha[:2])) == 1:
			fecha = 'Ayer'

		bot.send_message(message.chat.id, f'Tracking \'{alias}\' por {mins} mins')
		bot.send_message(message.chat.id, f'Ultimo viaje de \'{alias}\':\n{fecha} - {hora} hs - Linea {linea} ({lineas[linea]})')

		print(f'Track: tracking {tarjeta} ({alias}) for {mins} mins')
		print(f'Track: last data on {tarjeta} => {data_new}')

		for _ in range(0,int(mins)*6): 

			print(f'Track: reading {cardfile}.json')
			data_last = load(uid, cardfile)
			print(f'Fetching data from SUMO ({tarjeta})')
			data_new = get_card_data(tarjeta)

			if data_new['last'] > data_last['last']:
				
				hora = data_new['hora']
				linea = data_new['linea']

				print(f'Track: new data => {data_new}')
				bot.send_message(message.chat.id, f'Nuevo viaje de \'{alias}\'\n {hora} hs - Linea {linea} ({lineas[linea]})')

				json_data = json.dumps(data_new)
				save(uid, cardfile, json_data)

			else:
				print(f'Track: no new data from ({tarjeta}), retrying in 10 seconds...')

			#time.sleep(10) #invervalos de 10seg
			if exit.wait(10):
				break

		print(f'Track: Finish traking {tarjeta}')
		bot.send_message(message.chat.id, f'Tracking de \'{alias}\' finalizado')


################## END SUMO TRACK SECTION ##################