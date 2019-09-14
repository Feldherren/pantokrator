import discord
from discord.ext import tasks, commands
import os
import re
import asyncio
from datetime import datetime, timedelta
import sys
import pickle 

# TODO: double check nested dicts are created where necessary
# TODO: running and checking more than one game at once?
# Need to set what games are tracked/watched by the BOT; track/untrack? activate/deactivate?
# Need to make various commands require specifying name
# Keep command to scan for games, but listgames only lists tracked/active games?
# TODO: announce new turns for game(s) in specific channel(s); how to make this persistent? See if context can be pickled
# TODO: means of setting/resetting turn estimate, in case I extend it
# TODO: means of extending turn automatically? Going to want this limited to me, though
# TODO: means of limiting the use of certain commands to me only; better than hiding it. Store the ID like I do for watching games.
# TODO: means of marking someone as AI-controlled, since the bot can't read that

TOKEN = ''
SYMBOL = '?'
KEEPCHARACTERS = ['_', '-']

bot = commands.Bot(command_prefix=commands.when_mentioned_or(SYMBOL))

description = '''Pantokrator, a Dominions 5 bot for raspberry pi and python.'''

SAVEDIR = '/home/pi/.dominions5/savedgames'
DATAFILE = 'games'
global games
games = {'current_game':None}

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
NATIONS_ALL_VALID_ALIASES = {5:"Arcoscephale",'arco':'Arcoscephale', 'arcoscephale':'Arcoscephale', 6:"Ermor", 'ermor':'Ermor', 7:"Ulm", 'ulm':'Ulm', 8:'Marverni', 'marverni':'Marverni', 9:"Sauromatia", 'sauromatia':'Sauromatia', 'sauro':'Sauromatia', 10:"T'ien Ch'i", "t'ien ch'i":"T'ien Ch'i", "t'ien":"T'ien Ch'i", 'tien chi':"T'ien Ch'i", 'tien':"T'ien Ch'i", 11:'Machaka', 'machaka':'Machaka', 12:'Mictlan', 'mictlan':'Mictlan', 13:'Abysia', 'abysia':'Abysia', 14:'Caelum', 'caelum':'Caelum', "c'tis":"C'tis", 'ctis':"C'tis", 'pangaea':"Pangaea", 'agartha':"Agartha", "tir na n'og":"Tir na n'Og", 'tir na nog':"Tir na n'Og", 'tir':"Tir na n'Og", 'fomoria':"Fomoria", 'vanheim':"Vanheim", 'helheim':"Helheim", 'niefelheim':"Niefelheim", 'rus':"Rus", 'kailasa':"Kailasa", 'lanka':"Lanka", 'yomi':"Yomi", 'hinnom':"Hinnom", 'ur':"Ur", 'berytos':"Herytos", 'xibalba':"Xibalba", 'mekone':"Mekone", 'atlantis':"Atlantis", "r'lyeh":"R'lyeh", 'rlyeh':"R'lyeh", 'pelagia':"Pelagia", 'oceania':"Oceania", 'therodos':"Therodos"}

def save_data(f):
	global games
	with open(f, 'wb') as outfile:
		pickle.dump(games, outfile)
		
def load_data(f):
	global games
	if os.path.exists(f):
		with open(f, 'rb') as infile:
			games = pickle.load(infile)

@bot.command()
async def shutdown(ctx):
	save_data(DATAFILE)
	await ctx.send("All data saved, shutting down.")
	await bot.close()
	sys.exit()

@bot.command(brief="Lists detected games on Pi.")
async def listgames(ctx):
	games = [name for name in os.listdir(SAVEDIR) if os.path.isdir(os.path.join(SAVEDIR, name))]
	if len(games) >= 1:
		game_list = '\n'.join(games)
	else:
		game_list = 'No games found; start one!'
	await ctx.send(game_list)

@bot.command(brief="Sets currently-running game.", help="Sets currently-running game.")
async def setgame(ctx, name=None):
	global games
	if name is not None:
		game_name = "".join(c for c in name if c.isalnum() or c in KEEPCHARACTERS).rstrip()
		if os.path.exists(os.path.join(SAVEDIR, game_name)):
			games['current_game'] = game_name
			if game_name not in games.keys():
				games[games['current_game']] = {}
			statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
			if os.path.exists(statusdump):
				game_info, nation_status = parsedatafile(statusdump)
				current_turn = game_info['turn'] # always thought it was a new turn, because this was a string; do strings compare well?
				games[games['current_game']]['turn'] = current_turn
				#games[games['current_game']]['next_autohost_time'] = None
			else:
				current_turn = '?'
			await ctx.send("Now watching " + games['current_game'])
			save_data(DATAFILE)
		else:
			await ctx.send("No game called " + game_name + " found")
	else:
		await ctx.send("No game specified; please specify a game next time")

# TODO: allow setting watch on other games? Without setting them as current game first
@bot.command(brief="Starts watching current game for updates.", help="Sets yourself as watching the current game; you will receive DMs from Pantokrator whenever it detects a new turn has been processed.")
async def watch(ctx):
	global games
	if games['current_game'] in games:
		if 'watchers' not in games[games['current_game']]:
			games[games['current_game']]['watchers'] = []
		user_id = ctx.author.id
		if user_id not in games[games['current_game']]['watchers']:
			games[games['current_game']]['watchers'].append(user_id)
			await ctx.send("You are now watching the current game, " + games['current_game'] + ", and will receive a DM whenever a new turn processes.")
			save_data(DATAFILE)
		else:
			await ctx.send("You are already watching the current game, " + games['current_game'] + ".")
	else:
		await ctx.send("No game set; please set a game using ?setgame first")

@bot.command(brief="Stops watching the current game for updates.", help="Removes yourself from the list of users watching the current game. Pantokrator will no longer DM you on new turns.")
async def unwatch(ctx):
	global games
	if games['current_game'] in games:
		if 'watchers' in games[games['current_game']]:
			user_id = ctx.author.id
			if user_id in games[games['current_game']]['watchers']:
				games[games['current_game']]['watchers'].remove(user_id)
				await ctx.send("You have stopped watching the current game, " + games['current_game'] + ", and will not receive updates whenever a new turn processes.")
				save_data(DATAFILE)
			else:
				await ctx.send("You aren't watching the current game, " + games['current_game'] + ".")
		else:
			await ctx.send("You aren't watching the current game, " + games['current_game'] + ".")
	else:
		await ctx.send("No game set; please set a game using setgame first")
		
def get_nick_or_name(author):
	name = author.name
	if isinstance(author, discord.Member):
		if author.nick is not None:
			name = ctx.author.nick
	return name
		
# take basic discord name?
# TODO: maybe require verifying nation exists?
@bot.command(brief="Claim a nation for your own.", help="Claim a nation for yourself, in the current game. Note that this doesn't verify you entered a real nation, or something not already claimed.")
async def claim(ctx, nation):
	global games
	if games['current_game'] in games:
		if 'players' not in games[games['current_game']].keys():
			games[games['current_game']]['players'] = {}
		player = get_nick_or_name(ctx.author)
		games[games['current_game']]['players'][nation] = player
		await ctx.send(player + " has claimed the nation " + nation)
		save_data(DATAFILE)
	else:
		await ctx.send("No game set; please set a game using setgame first")
	
@bot.command(brief="Unclaims your nation.", help="Unclaims the provided nation you've taken for yourself, in the current game. Use this in the same context you used claim, as otherwise it may not recogise you.")
async def unclaim(ctx, nation):
	global games
	if games['current_game'] in games:
		if 'players' not in games[games['current_game']].keys():
			games[games['current_game']]['players'] = {}
		player = get_nick_or_name(ctx.author)
		if nation in games[games['current_game']]['players']:
			if games[games['current_game']]['players'][nation] == player:
				games[games['current_game']]['players'].pop(nation)
				await ctx.send(player + " has removed their claim on nation " + nation)
			else:
				await ctx.send("That nation is claimed, but you don't own it.")
		else:
			await ctx.send("That nation has not been claimed.")
		save_data(DATAFILE)
	else:
		await ctx.send("No game set; please set a game using setgame first")
	
# WHOIS?
@bot.command(brief="Lists claimed nations and players in current game.", help="Lists players who have claimed a nation in the current game.")
async def who(ctx):
	global games
	output = []
	if 'players' in games[games['current_game']].keys():
		for nation in sorted(games[games['current_game']]['players']):
			output.append(nation + ": " + games[games['current_game']]['players'][nation])
	if len(output) >= 1:
		whois = "\n".join(output)
		await ctx.send(whois)
	else:
		await ctx.send("No nations have been claimed in this game, yet; have someone use the claim command to start using this.")

# TODO: let people set it for arbitrary game, instead of just current
@bot.command(brief="Sets autohost interval for current game.", help="Sets autohost interval used by bot to predict time until next autohost.")
async def autohost(ctx, hours):
	global games
	if hours is not None:
		games[games['current_game']]['autohost_interval'] = int(hours)
		await ctx.send("Autohost interval is now set to " + hours + " hours.")
		save_data(DATAFILE)
	else:
		await ctx.send("Please supply a valid autohost period in hours as an integer")

p_gamename = re.compile("Status for '(.+)'", re.IGNORECASE)
p_gameinfo = re.compile('turn (-?\d+), era (\d), mods (\d+), turnlimit (\d+)')
p_nationstatus = re.compile("Nation\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+([\w_]+)\s+([\w']+)\s+(.+)$")

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
	
# @bot.command()
# async def test(ctx):
	# dm = None
	# id = ctx.author.id
	# print(id)
	# user = bot.get_user(id)
	# print(user)
	# if user.dm_channel is None:
		# await user.create_dm()
	# dm = user.dm_channel
	
	# await dm.send("Testing sending DMs via ID")
	
# @bot.command()
# async def watchers(ctx):
	# global watchers
	# if len(watchers) >= 1:
		# for watcher in watchers:
			# await ctx.send(watcher)
	# else:
		# await ctx.send("no watchers")

@tasks.loop(seconds=10.0)
async def check_current_game():
	print("Checking...")
	global games
	print(games['current_game'])
	if games['current_game'] is not None:
		# print("Checking " + current_game)
		statusdump = os.path.join(SAVEDIR, games['current_game'], "statusdump.txt")
		if os.path.exists(statusdump):
			game_info, nation_data = parsedatafile(statusdump)
			if game_info['turn'] != games[games['current_game']]['turn']:
				print("It is a new turn!")
				games[games['current_game']]['next_autohost_time'] = datetime.now() + timedelta(hours=games[games['current_game']]['autohost_interval'])
				for watcher in games[games['current_game']]['watchers']:
					print(watcher)
					user = bot.get_user(watcher)
					print(user) # this fails? when launched, anyway
					if user is not None:
						if user.dm_channel is None:
							await user.create_dm()
						dm = user.dm_channel
						await dm.send(games['current_game'] + ' just generated a new turn!')
					else:
						print("Error: User with ID " + str(id) + " not found")
				games[games['current_game']]['turn'] = game_info['turn']
				save_data(DATAFILE)

@check_current_game.before_loop
async def before_check_loop():
	global games
	print('starting up...')
	load_data(DATAFILE)
	await bot.wait_until_ready()
				
@bot.command(brief="Outputs game status", help="Outputs game status, including current turn, predicted autohost and nation status.")
async def status(ctx, name=None):
	global games
	game = None
	if name is not None:
		game_name = "".join(c for c in name if c.isalnum() or c in KEEPCHARACTERS).rstrip()
		if os.path.exists(os.path.join(SAVEDIR, game_name)):
			game = game_name
		else:
			await ctx.send("No game called " + game_name + " found")
			return
	else:
		if games['current_game'] is not None:
			game = games['current_game']
		else:
			await ctx.send("No game set; please set a game using !setgame first")
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
			if game == games['current_game']:
				time_left = None
				if 'next_autohost_time' in games[games['current_game']].keys():
					if games[games['current_game']]['next_autohost_time'] is not None:
						time_left = str(games[games['current_game']]['next_autohost_time'] - datetime.now())
						next_autohost_str = "Next turn in approximately: " + time_left
						game_details.append(next_autohost_str)
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
			
check_current_game.start()
bot.run(TOKEN, bot=True)
