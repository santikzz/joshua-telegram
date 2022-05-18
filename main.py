import telebot
import json
import re
#import threading

from functions import *

bot = telebot.TeleBot("telegram-token", parse_mode=None)
print('Ready!')

@bot.message_handler(commands=['start'])
def start(message):
	uid = message.from_user.id
	user_data = { 'uid': str(message.from_user.id), 'name': message.from_user.first_name }
	user_data = json.dumps(user_data)
	create(bot, uid, user_data)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
	
	args = message.text.split()
	cmd = args.pop(0).lower()
	
	uid = message.chat.id
	card_path = f'./userdata/{uid}/cards.json'

	userdata = load(uid, 'data')

	if cmd == 'saldo':

		if args[0] == 'sumo':
			saldo_sumo(bot, message, userdata)
		elif args[0] == 'comedor':
			saldo_comedor(bot, message, userdata)

	elif cmd == 'track':

		#track(message, args[0], args[1])
		track(bot, message, args)

	elif cmd == 'ping':
		bot.send_message(message.chat.id, 'Pong.')



bot.infinity_polling()