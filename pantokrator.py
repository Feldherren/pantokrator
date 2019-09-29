import discord
from discord.ext import tasks, commands
import os
import re
import asyncio
from datetime import datetime, timedelta
import sys
import pickle 
import shutil

# TODO: running and checking more than one game at once?

# TODO: opt-in reminder that you haven't taken your turn yet; reminders PM you at 12, 6, 3 and 1 hours before the turn is due
# requires: claiming a nation for the game (spelled correctly or recognisable through the dict below), and opting in to reminders
# independent of watch status, as someone might want one without the other.
#	TODO: make sure claim/unclaim still work with storing user_id now, and that ?who gets the proper nation name
#	TODO: make sure reminder_loop starts properly and runs
#	TODO: generally make it bug-free
#	TODO: see if on_command_error needs to be set for me-only commands
#	TODO: means of setting/resetting turn estimate, in case I extend it (me-only)
#	TODO: means of marking someone as AI-controlled, since the bot can't read that (me-only)
#	TODO: replaced whitespace generics in p_nationstatus with \t for tabs; make sure that still works AND picks up t'ien chi, tir na n'og and anything else with apostrophes and/or spaces
#	TODO: means of starting games from the bot

# TODO: announce new turns for game(s) in specific channel(s); how to make this persistent? See if context can be pickled

TOKEN = ''
SYMBOL = '?'

bot = commands.Bot(command_prefix=commands.when_mentioned_or(SYMBOL))

description = '''Pantokrator, a Dominions 5 bot for raspberry pi and python.'''

SAVEDIR = '/home/pi/.dominions5/savedgames'
DOMCMD_PATH = '/home/pi/.dominions5/domcmd-'}
DATAFILE = 'pantokrator-data'
REMINDER_HOURS = [12, 6, 3, 1]
KEEPCHARACTERS = ['_', '-']
global games
games = {}

seasons = {0: 'early spring', 1: 'spring', 2:'late spring', 3:'early summer', 4:'summer', 5:'late summer', 6:'early fall', 7:'fall', 8:'late fall', 9:'early winter', 10:'winter', 11:'late winter'}
NATIONS_EARLY_IDS = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,36,37,38,39,40]
NATIONS_EARLY = {'arcoscephale':5, 'arco':5, 'ermor':6, 'ulm':7, 'marverni':8, 'sauromatia':9, "t'ien chi'":10, "t'ien":10, 'tien chi':10, 'tien':10, 'machaka':11, 'mictlan':12, 'abysia':13, 'caelum':14, "c'tis":15, 'ctis':15, 'pangaea':16, 'agartha':17, "tir na n'og":18, 'tir na nog':18, 'tir':18, 'fomoria':19, 'vanheim':20, 'helheim':21, 'niefelheim':22, 'rus':24, 'kailasa':25, 'lanka':26, 'yomi':27, 'hinnom':28, 'ur':29, 'berytos':30, 'xibalba':31, 'mekone':32, 'atlantis':36, "r'lyeh":37, 'rlyeh':37, 'pelagia':38, 'oceania':39, 'therodos':40}
NATIONS_MID_IDS = [43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,73,74,75,76,77]
NATIONS_MID = {'arcoscephale':43, 'arco':43, 'ermor':44, 'sceleria':45, 'pythium':46, 'man':47, 'eriu':48, 'ulm':49, 'marignon':50, 'mictlan':51, "t'ien chi'":52, "t'ien":52, 'tien chi':52, 'tien':52, 'machaka':53, 'agartha':54, 'abysia':55, 'caelum':56, "c'tis":57, 'ctis':57, 'pangaea':58, 'asphodel': 59, 'vanheim':60, 'jotunheim':61, 'vanarus':62, 'bandar log':63, 'bandar':63, 'shinuyama':64, 'ashdod':65, 'uruk':66, 'nazca':67, 'xibalba':68, 'phlegra':69, 'phaeacia':70, 'atlantis':73, "r'lyeh":74, 'rlyeh':74, 'pelagia':75, 'oceania':76, 'ys':77}
NATIONS_LATE_IDS = [80,81,82,83,84,85,86,87,89,90,91,92,93,94,95,96,97,98,99,100,101,102,106,107,108]
NATIONS_LATE = {'arcoscephale':80, 'arco':80, 'pythium':81, 'lemuria':82, 'man':83, 'ulm':84, 'marignon':85, 'mictlan':86, "t'ien chi'":87, "t'ien":87, 'tien chi':87, 'tien':87, 'jomon':89, 'agartha':90, 'abysia':91, 'caelum':92, "c'tis":93, 'ctis':93, 'pangaea':94, 'midgard':95, 'utgard':96, 'bogarus':97, 'patala':98, 'gath':99, 'ragha':100, 'xibalba':101, 'phlegra':102, 'atlantis':106, "r'lyeh":107, 'rlyeh':107, 'erytheia':108}
NATIONS_ALL_IDS = []
# TODO: add IDs as aliases
# TODO: add nations to status? Emp figures it'd be bad
NATIONS_ALL_VALID_ALIASES = {
5:"Arcoscephale", 43:"Arcoscephale", 80:"Arcoscephale", 'arco':'Arcoscephale', 'arcoscephale':'Arcoscephale', 
6:"Ermor", 44:"Ermor", 'ermor':'Ermor', 
7:"Ulm", 49:'Ulm', 84:'Ulm', 'ulm':'Ulm',  
8:'Marverni', 'marverni':'Marverni', 
9:"Sauromatia", 'sauromatia':'Sauromatia', 'sauro':'Sauromatia', 
10:"T'ien Ch'i", 52:"T'ien Ch'i", 87:"T'ien Ch'i", "t'ien ch'i":"T'ien Ch'i", "t'ien":"T'ien Ch'i", 'tien chi':"T'ien Ch'i", 'tien':"T'ien Ch'i", 
11:'Machaka', 53:'Machaka', 'machaka':'Machaka', 
12:'Mictlan', 51:'Mictlan', 86:'Mictlan', 'mictlan':'Mictlan', 
13:'Abysia', 55:'Abysia', 91:'Abysia', 'abysia':'Abysia', 
14:'Caelum', 56:'Caelum', 92:'Caelum', 'caelum':'Caelum', 
15:"C'tis", 57:"C'tis", 93:"C'tis", "c'tis":"C'tis", 'ctis':"C'tis", 
16:"Pangaea", 58:'Pangaea', 94:'Pangaea', 'pangaea':"Pangaea", 
17:"Agartha", 54:'Agartha', 90:'Agartha', 'agartha':"Agartha", 
18:"Tir na n'Og", "tir na n'og":"Tir na n'Og", 'tir na nog':"Tir na n'Og", 'tir':"Tir na n'Og", 
19:"Fomoria", 'fomoria':"Fomoria", 
20:"Vanheim", 60:'Vanheim', 'vanheim':"Vanheim", 
21:"Helheim", 'helheim':"Helheim", 
22:"Niefelheim", 'niefelheim':"Niefelheim", 
24:"Rus", 'rus':"Rus", 
25:"Kailasa", 'kailasa':"Kailasa", 
26:"Lanka", 'lanka':"Lanka", 
27:"Yomi", 'yomi':"Yomi", 
28:"Hinnom", 'hinnom':"Hinnom", 
29:"Ur", 'ur':"Ur", 
30:"Berytos", 'berytos':"Berytos", 
31:"Xibalba", 68:'Xibalba', 101:'Xibalba', 'xibalba':"Xibalba", 
32:"Mekone", 'mekone':"Mekone", 
36:"Atlantis", 73:'Atlantis', 106:'Atlantis', 'atlantis':"Atlantis", 
37:"R'lyeh", 74:"R'lyeh", 107:"R'lyeh", "r'lyeh":"R'lyeh", 'rlyeh':"R'lyeh", 
38:"Pelagia", 75:'Pelagia', 'pelagia':"Pelagia", 
39:"Oceania", 76:'Oceania', 'oceania':"Oceania", 
40:"Therodos", 'therodos':"Therodos", 
45:'Sceleria', 'sceleria':'Sceleria', 
46:'Pythium', 81:'Pythium', 'pythium':'Pythium', 
47:'Man', 83:'Man', 'man':'Man', 
48:'Eriu', 'eriu':'Eriu', 
50:'Marignon', 85:'Marignon', 'marignon':'Marignon', 
59:'Asphodel', 'asphodel':'Asphodel',
61:'Jotunheim', 'jotunheim':'Jotunheim',
62:'Vanarus', 'vanarus':'Vanarus',
63:'Bandar Log', 'bandar log':'Bandar Log', 'bandar':'Bandar Log',
64:'Shinuyama', 'shinuyama':'Shinuyama',
65:'Ashdod', 'ashdod':'Ashdod',
66:'Uruk', 'uruk':'Uruk',
67:'Nazca', 'nazca':'Nazca',
69:'Phlegra', 102:'Phlegra', 'phlegra':'Phlegra',
70:'Phaeacia', 'phaeacia':'Phaeacia',
77:'Ys', 'ys':'Ys',
82:'Lemuria', 'lemuria':'Lemuria' 
89:'Jomon', 'jomon':'Jomon',
95:'Midgard', 'midgard':'Midgard',
96:'Utgard', 'utgard':'Utgard'
97:'Bogarus', 'bogarus':'Bogarus',
98:'Patala', 'patala':'Patala',
99:'Gath', 'gath':'Gath',
100:'Ragha', 'ragha':'Ragha',
108:'Erytheia', 'erytheia':'Erytheia'
}

def save_data(f):
	global games
	with open(f, 'wb') as outfile:
		pickle.dump(games, outfile)
		
def load_data(f):
	global games
	if os.path.exists(f):
		with open(f, 'rb') as infile:
			games = pickle.load(infile)

@bot.command(brief="Safely shuts the bot down.", help="Safely shuts Pantokrator down.")
@commands.is_owner()
async def shutdown(ctx):
	save_data(DATAFILE)
	await ctx.send("All data saved, shutting down.")
	await bot.close()
	sys.exit()

@bot.command(brief="Lists active games.")
async def listgames(ctx):
	global games
	if len(games) >= 1:
		game_list = '\n'.join(games.keys())
	else:
		game_list = 'No games found; start one!'
	await ctx.send(game_list)

# @bot.command(brief="Sets currently-running game.", help="Sets currently-running game.")
# async def setgame(ctx, name=None):
	# global games
	# if name is not None:
		# game_name = "".join(c for c in name if c.isalnum() or c in KEEPCHARACTERS).rstrip()
		# if os.path.exists(os.path.join(SAVEDIR, game_name)):
			# games['current_game'] = game_name
			# if game_name not in games.keys():
				# games[games['current_game']] = {}
			# statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
			# if os.path.exists(statusdump):
				# game_info, nation_status = parsedatafile(statusdump)
				# current_turn = game_info['turn']
				# games[games['current_game']]['turn'] = current_turn
				# #games[games['current_game']]['next_autohost_time'] = None
			# else:
				# current_turn = '?'
			# await ctx.send("Now watching " + games['current_game'])
			# save_data(DATAFILE)
		# else:
			# await ctx.send("No game called " + game_name + " found")
	# else:
		# await ctx.send("No game specified; please specify a game next time")

# setting the named game as an active game; 'activate'?
# TODO: put stuff from setgame in here; might as well be setup for everything the bot does anyway; make sure all's added that we need
@commands.is_owner()
@bot.command(brief="Adds named game to the list of active games for update watching.", help="Adds the named game to the list of active games, if a valid game; Pantokrator will watch these games for updates.")
async def add(ctx, game_name):
	global games
	# first confirm game exists
	statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
	if os.path.exists(statusdump):
		if game_name not in games:
			game_info, nation_status = parsedatafile(statusdump)
			current_turn = game_info['turn']
			games[game_name]['turn'] = current_turn
			games[game_name]['next_reminder'] = 12
			games[game_name]['player_reminders'] = []
			games[game_name]['players'] = {}
			games[game_name]['next_autohost_time'] = None
			games[game_name]['paused'] = False
			await ctx.send(game_name + " is now listed as an active game, and available for use with commands.")
			save_data(DATAFILE)
		else:
			await ctx.send(game_name + " is already an active game.")
	else:
		await ctx.send("Can't find statusdump.txt for " + game_name + "; please make sure it's a valid game.")

@commands.is_owner()
@bot.command(brief="Removes named game from the list of active games.", help="Removes the named game from the list of active games. Pantokrator will stop watching games for updates.")
async def remove(ctx, game_name):
	global games
	if game_name in games:
		games.remove(game_name)
		save_data(DATAFILE)
	else:
		await ctx.send(game_name + " isn't an active game.")

@commands.is_owner()
@bot.command(brief="Pauses the autohost timer for the specified game.", help="Pauses the autohost timer for the specified game.")
async def pause(ctx, game_name=None):
	global games
	if game_name in games:
		shutil.copyfile(DOMCMD_PATH+'pause', os.path.join(SAVEDIR,game_name,'domcmd')
		await ctx.send(game_name + " is now paused.")
		games[game_name]['next_autohost_time'] = None
		games[game_name]['paused'] = True
		save_data(DATAFILE)
	else:
		await ctx.send(game_name + " isn't an active game.")

@commands.is_owner()
@bot.command(brief="Unpauses the autohost timer for the specified game.", help="Unpauses the autohost timer for the specified game.")
async def unpause(ctx, game_name=None):
	global games
	if game_name in games:
		shutil.copyfile(DOMCMD_PATH+'unpause', os.path.join(SAVEDIR,game_name,'domcmd')
		await ctx.send(game_name + " is now unpaused.")
		games[game_name]['paused'] = False
		save_data(DATAFILE)
	else:
		await ctx.send(game_name + " isn't an active game.")

@bot.command(brief="Starts watching an active game for updates.", help="Sets yourself as watching an active game; you will receive DMs from Pantokrator whenever it detects a new turn has been processed.")
async def watch(ctx, game_name=None):
	global games
	if game_name is not None:
		if game_name in games:
			if 'watchers' not in games[game_name]:
				games[game_name]['watchers'] = []
			user_id = ctx.author.id
			if user_id not in games[game_name]['watchers']:
				games[game_name]['watchers'].append(user_id)
				await ctx.send("You are now watching the game " + game_name + ", and will receive a DM whenever a new turn processes.")
				save_data(DATAFILE)
			else:
				await ctx.send("You are already watching this game, " + game_name + ".")
	else:
		await ctx.send("No game supplied; please state the name of the game you want to follow")

@bot.command(brief="Stops watching the current game for updates.", help="Removes yourself from the list of users watching the current game. Pantokrator will no longer DM you on new turns.")
async def unwatch(ctx, game_name=None):
	global games
	if game_name is not None:
		if game_name in games:
			if 'watchers' in games[game_name]:
				user_id = ctx.author.id
				if user_id in games[game_name]['watchers']:
					games[game_name]['watchers'].remove(user_id)
					await ctx.send("You have stopped watching the game " + game_name + ", and will not receive updates whenever a new turn processes.")
					save_data(DATAFILE)
				else:
					await ctx.send("You aren't watching the game " + game_name + ".")
			else:
				await ctx.send("You aren't watching the game " + game_name + ".")
		else:
			await ctx.send(game_name + " not found in active games list; please supply a valid game name.")
	else:
		await ctx.send("No game supplied; please state the name of the game you want to stop watching")
		
def get_nick_or_name(author):
	name = author.name
	if isinstance(author, discord.Member):
		if author.nick is not None:
			name = ctx.author.nick
	return name
	
def get_username_from_id(user_id):
	return bot.get_user(user_id).name
	
def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
		
# when comparing with the statusdump.txt content for checking if to remind someone, also use that
@bot.command(brief="Claim a nation for your own in the named game.", help="Claim a nation for yourself, in the named game. Note that this doesn't verify you entered a real nation, or something not already claimed.")
async def claim(ctx, game_name=None, nation=None):
	global games
	if game_name is not None:
		if game_name in games:
			if nation is not None:
				# converting string into an int, or lower-case string
				if represents_int(nation):
					nation = int(nation)
				else:
					nation = nation.lower()
				if nation in NATIONS_ALL_VALID_ALIASES:
					player = get_nick_or_name(ctx.author)
					user_id = ctx.author.id
					games[game_name]['players'][NATIONS_ALL_VALID_ALIASES[nation]] = user_id
					await ctx.send(player + " has claimed the nation " + NATIONS_ALL_VALID_ALIASES[nation] + " for the game " + game_name)
					save_data(DATAFILE)
				else:
					await ctx.send("Please supply a recognised nation; contact Feldherren to get new aliases added.")
			else:
				await ctx.send("Please supply a nation.")
		else:
			await ctx.send(game_name + " not found in games list; please supply a valid game name.")
	else:
		await ctx.send("Please supply a valid game name.")
	
@bot.command(brief="Unclaims your nation.", help="Unclaims the provided nation you've taken for yourself, in the stated game.")
async def unclaim(ctx, game_name, nation):
	global games
	if game_name is not None:
		if game_name in games:
			if nation is not None:
				# converting string into an int, or lower-case string
				if represents_int(nation):
					nation = int(nation)
				else:
					nation = nation.lower()
				if nation in NATIONS_ALL_VALID_ALIASES:
					player = get_nick_or_name(ctx.author)
					if nation in games[game_name]['players']:
						user_id = ctx.author.id
						if games[game_name]['players'][nation] == user_id:
							games[game_name]['players'].pop(NATIONS_ALL_VALID_ALIASES[nation])
							await ctx.send(get_username_from_id(user_id) + " has removed their claim on nation " + NATIONS_ALL_VALID_ALIASES[nation] + " in the game " + game_name)
							save_data(DATAFILE)
						else:
							await ctx.send("That nation is claimed, but you don't seem to own it.")
					else:
						await ctx.send("That nation has not been claimed.")
				else:
					await ctx.send("Please supply a recognised nation; contact Feldherren to get new aliases added.")
			else:
				await ctx.send("Please supply a nation.")
		else:
			await ctx.send(game_name + " not found in games list; please supply a valid game name.")
	else:
		await ctx.send("Please supply a valid game name.")
	
# WHOIS?
@bot.command(brief="Lists claimed nations and players in named game.", help="Lists players who have claimed a nation in the named game.")
async def who(ctx, game_name):
	global games
	output = []
	if game_name is not None:
		if game_name in games:
			if 'players' in games[game_name].keys():
				for nation in sorted(games[game_name]['players']):
					output.append(nation + ": " + get_username_from_id(games[game_name]['players'][nation]))
			if len(output) >= 1:
				whois = "\n".join(output)
				await ctx.send(whois)
			else:
				await ctx.send("No nations have been claimed in this game, yet; have someone use the claim command to start using this.")
		else:
			await ctx.send(game_name + " not found in games list; please supply a valid game name.")
	else:
		await ctx.send("Please supply a valid game name.")

@commands.is_owner()
@bot.command(brief="Sets autohost interval for the specified game.", help="Sets autohost interval used by bot to predict time until next autohost.")
async def autohost(ctx, game_name, hours):
	global games
	if game_name is not None:
		if game_name in games:
			if hours is not None:
				games[game_name]['autohost_interval'] = int(hours)
				await ctx.send("Autohost interval is now set to " + hours + " hours.")
				save_data(DATAFILE)
			else:
				await ctx.send("Please supply a valid autohost period in hours as an integer")
		else:
			await ctx.send(game_name + " not found in games list; please supply a valid game name.")
	else:
		await ctx.send("Please supply a valid game name.")
		
@bot.command(brief="Sets yourself as wanting (or not wanting) reminders for the specified game.", help="Sets yourself as wanting (or not wanting) reminders for the specified game, sent to you at 12, 6, 3 and 1 hours before turn autohosting if your turn has not been submitted. Requires having used ?claim to properly claim a nation. Use on or off as argument following command to set reminders on or off, or don't add the argument to toggle your current state.")
async def reminders(ctx, game_name=None, setting=None):
	global games
	user_id = ctx.author.id
	if game_name is not None:
		if game_name in games:
			if setting is not None:
				if setting == 'on':
					games[game_name][player_reminders].append(user_id)
					await ctx.send("Now receiving reminders for " + game_name)
				else setting == 'off':
					games[game_name][player_reminders].pop(games[game_name][player_reminders].index(user_id))
					await ctx.send("No longer receiving reminders for " + game_name)
			else:
				# assume they want to toggle it
				if user_id in games[game_name][player_reminders]:
					games[game_name][player_reminders].pop(games[game_name][player_reminders].index(user_id))
					await ctx.send("No longer receiving reminders for " + game_name)
				else:
					games[game_name][player_reminders].append(user_id)
					await ctx.send("Now receiving reminders for " + game_name)
		else:
			await ctx.send(game_name + " not found in games list; please supply a valid game name.")
	else:
		await ctx.send("Please supply a valid game name.")

p_gamename = re.compile("Status for '(.+)'", re.IGNORECASE)
p_gameinfo = re.compile('turn (-?\d+), era (\d), mods (\d+), turnlimit (\d+)')
p_nationstatus = re.compile("Nation\t(\d+)\t(\d+)\t(-?\d+)\t(\d+)\t(\d+)\t([\w_]+)\t([\w']+)\t(.+)$")

def parsedatafile(statusdump):
	game_info = {}
	nation_status = {}
	with open(statusdump) as f:
		lines = f.readlines()
		game_info['name'] = re.search(p_gamename, lines[0])[1]
		temp = re.search(p_gameinfo, lines[1])
		game_info['turn'], game_info['era'], game_info['mods'], game_info['turnlimit'] = int(temp[1]), temp[2], temp[3], temp[4]
		for i in range(2, len(lines)):
			n = re.search(p_nationstatus, lines[i])
			#print(n[7] + ", " + n[8])
			#n_status = 
			# has not taken turn: 1 0 0
			# mark as unfinished and exit: 1 0 1
			# turn submitted: 1 0 2
			# AI: no indicator?
			# defeated: -2 0 0
			nation_status[n[7]] = n
	return game_info, nation_status
	
# actual function for sending reminders
async def send_reminders(game_name, hour):
	global games
	statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
	game_info, nation_status = parsedatafile(statusdump)
	for user_id in games[game_name][player_reminders]:
		if user_id in games[game_name]['players'].values():
			for nation in games[game_name]['players']:
				if user_id == games[game_name]['players'][nation]:
					if nation_status[nation][5] == '0': # turn not taken
						# send the message
						user = bot.get_user(user_id)
						if user is not None:
							if user.dm_channel is None:
								await user.create_dm()
							dm = user.dm_channel
							await dm.send('This is your ' + hour + ' hour reminder for ' + game_name + ' as ' + nation + "; don't forget to get your turn in!")
						else:
							print("Error: User with ID " + str(id) + " not found")
		
# loop for checking each game and reminding registered players that a turn will be processed in 12, 6, 3 and 1 hours
@tasks.loop(seconds=60.0)
async def reminder_loop():
	global games
	for game_name in games:
		if games[game_name]['next_autohost_time'] is not None:
			if games[game_name]['next_reminder'] in REMINDER_HOURS and games[game_name]['next_autohost_time'] - datetime.now() > timedelta(hours=games[game_name]['next_reminder']):
				send_reminders(game_name, games[game_name]['next_reminder'])
				if len(REMINDER_HOURS) > REMINDER_HOURS.index(games[game_name]['next_reminder'])+1:
					games[game_name]['next_reminder'] = REMINDER_HOURS[REMINDER_HOURS.index(games[game_name]['next_reminder'])+1]
				else:
					games[game_name]['next_reminder'] = 0
			# if games[game_name]['next_reminder'] == 12 and games[game_name]['next_autohost_time'] - datetime.now() > timedelta(hours=12): 
				# # 12-hour reminder
				# send_reminders(game_name, games[game_name]['next_reminder'])
				# games[game_name]['next_reminder'] = 6
			# elif games[game_name]['next_reminder'] == 6 and games[game_name]['next_autohost_time'] - datetime.now() > timedelta(hours=6): 
				# # 6 hour reminder
				# send_reminders(game_name, games[game_name]['next_reminder'])
				# games[game_name]['next_reminder'] = 3
			# elif games[game_name]['next_reminder'] == 3 and games[game_name]['next_autohost_time'] - datetime.now() > timedelta(hours=3): 
				# # 3 hour reminder
				# send_reminders(game_name, games[game_name]['next_reminder'])
				# games[game_name]['next_reminder'] = 1
			# elif games[game_name]['next_reminder'] == 1 and games[game_name]['next_autohost_time'] - datetime.now() > timedelta(hours=1): 
				# # 1 hour reminder
				# send_reminders(game_name, games[game_name]['next_reminder'])
				# games[game_name]['next_reminder'] = 0

@tasks.loop(seconds=10.0)
async def check_active_games():
	global games
	for game_name in games:
		print("Checking " + game_name)
		statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
		if os.path.exists(statusdump):
			game_info, nation_data = parsedatafile(statusdump)
			if game_info['turn'] != games[game_name]['turn']:
				print("It is a new turn!")
				games[game_name]['next_autohost_time'] = datetime.now() + timedelta(hours=games[game_name]['autohost_interval'])
				for watcher in games[game_name]['watchers']:
					user = bot.get_user(watcher)
					if user is not None:
						if user.dm_channel is None:
							await user.create_dm()
						dm = user.dm_channel
						await dm.send(game_name + ' just generated a new turn!')
						games[game_name]['reminders'] = REMINDER_HOURS[0] # so it doesn't spam reminders
					else:
						print("Error: User with ID " + str(id) + " not found")
				games[game]['turn'] = game_info['turn']
				save_data(DATAFILE)

@check_active_games.before_loop
async def before_check_loop():
	global games
	print('starting up...')
	load_data(DATAFILE)
	await bot.wait_until_ready()
	reminder_loop.start()
				
@bot.command(brief="Outputs game status for provided", help="Outputs game status, including current turn, predicted autohost and nation status.")
async def status(ctx, name=None):
	global games
	game = None
	if name is not None:
		if os.path.exists(os.path.join(SAVEDIR, game_name)):
			game = game_name
		else:
			await ctx.send("No game called " + game_name + " found")
			return
	else:
		await ctx.send("Please supply a valid game name.")
		return
	# and now the actual command stuff
	if game is not None:
		# TODO: check if the file changed since last read
		# TODO: split updating status dump into its own thing entirely; globals?
		statusdump = os.path.join(SAVEDIR, game, "statusdump.txt")
		if os.path.exists(statusdump):
			game_info, nation_status = parsedatafile(statusdump)
			year = str(int(game_info['turn'])//12)
			season_string = seasons[int(game_info['turn'])%12]
			turn = 'Turn ' + str(game_info['turn']) + ' (Year ' + year + ', ' + season_string + ')'
			game_details = ['**'+game+'**', '*'+turn+'*']
			time_left = None
			if games[game]['next_autohost_time'] is not None:
				time_left = str(games[game]['next_autohost_time'] - datetime.now())
				next_autohost_str = "Next turn in approximately: " + time_left
			else:
				next_autohost_str = "Next turn in approximately: UNKNOWN"
			game_details.append(next_autohost_str)
			if games[game]['paused']:
				game_details.append("GAME PAUSED")
			# the below are 3, 4, 5 in result
			# has not taken turn: 1 0 0
			# mark as unfinished and exit: 1 0 1
			# turn submitted: 1 0 2
			# AI: no indicator?
			# defeated: -2 0 0
			for nation in sorted(nation_status):
				if game_info['turn'] == -1:
					if nation_status[nation][3] == '1':
						state = 'CLAIMED'
					else:
						state = 'FREE'
				else:
					state = 'WAITING'
					if nation_status[nation][3] == '-2':
						state = '~~defeated~~'
					elif nation_status[nation][5] == '1':
						state = 'UNFINISHED'
					elif nation_status[nation][5] == '2':
						state = 'turn submitted'
				game_details.append("__" + nation + "__" + ": " + state)
			output = '\n'.join(game_details)
			await ctx.send(output)
			
check_active_games.start()
bot.run(TOKEN, bot=True)
