import discord
from discord.ext import tasks, commands
import os
import re
import asyncio

TOKEN = ''
SYMBOL = '?'
KEEPCHARACTERS = ['_', '-']

client = discord.Client()
bot = commands.Bot(command_prefix=SYMBOL)

description = '''Pantokrator, a Dominions 5 bot for raspberry pi and python.'''

SAVEDIR = '/home/pi/.dominions5/savedgames'
global current_game
current_game = None
global current_turn
current_turn = None

#watching for updates is only for the current game, currently
global watchers

seasons = {0: 'early spring', 1: 'spring', 2:'late spring', 3:'early summer', 4:'summer', 5:'late summer', 6:'early fall', 7:'fall', 8:'late fall', 9:'early winter', 10:'winter', 11:'late winter'}
eras = {'early':0, 'middle':1, 'mid':1, 'late':2}
# nation lists and dicts for each era
nations_early_ids = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,36,37,38,39,40]
nations_early = {'arcoscephale':5, 'ermor':6, 'ulm':7, 'marverni':8, 'sauromatia':9, "t'ien chi'":10, "t'ien":10, 'tien chi':10, 'tien':10, 'machaka':11, 'mictlan':12, 'abysia':13, 'caelum':14, "c'tis":15, 'ctis':15, 'pangaea':16, 'agartha':17, "tir na n'og":18, 'tir na nog':18, 'tir':18, 'fomoria':19, 'vanheim':20, 'helheim':21, 'niefelheim':22, 'rus':24, 'kailasa':25, 'lanka':26, 'yomi':27, 'hinnom':28, 'ur':29, 'berytos':30, 'xibalba':31, 'mekone':32, 'atlantis':36, "r'lyeh":37, 'rlyeh':37, 'pelagia':38, 'oceania':39, 'therodos':40}
nations_mid_ids = [43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,73,74,75,76,77]
nations_mid = {'arcoscephale':43, 'ermor':44, 'sceleria':45, 'pythium':46, 'man':47, 'eriu':48, 'ulm':49, 'marignon':50, 'mictlan':51, "t'ien chi'":52, "t'ien":52, 'tien chi':52, 'tien':52, 'machaka':53, 'agartha':54, 'abysia':55, 'caelum':56, "c'tis":57, 'ctis':57, 'pangaea':58, 'asphodel': 59, 'vanheim':60, 'jotunheim':61, 'vanarus':62, 'bandar log':63, 'bandar':63, 'shinuyama':64, 'ashdod':65, 'uruk':66, 'nazca':67, 'xibalba':68, 'phlegra':69, 'phaeacia':70, 'atlantis':73, "r'lyeh":74, 'rlyeh':74, 'pelagia':75, 'oceania':76, 'ys':77}
nations_late_ids = [80,81,82,83,84,85,86,87,89,90,91,92,93,94,95,96,97,98,99,100,101,102,106,107,108]
nations_late = {'arcoscephale':80, 'pythium':81, 'lemuria':82, 'man':83, 'ulm':84, 'marignon':85, 'mictlan':86, "t'ien chi'":87, "t'ien":87, 'tien chi':87, 'tien':87, 'jomon':89, 'agartha':90, 'abysia':91, 'caelum':92, "c'tis":93, 'ctis':93, 'pangaea':94, 'midgard':95, 'utgard':96, 'bogarus':97, 'patala':98, 'gath':99, 'ragha':100, 'xibalba':101, 'phlegra':102, 'atlantis':106, "r'lyeh":107, 'rlyeh':107, 'erytheia':108}

@bot.command()
async def listgames(ctx):
	games = [name for name in os.listdir(SAVEDIR) if os.path.isdir(os.path.join(SAVEDIR, name))]
	if len(games) >= 1:
		game_list = '\n'.join(games)
	else:
		game_list = 'No games found; start one!'
	await ctx.send(game_list)
	
@bot.command()
async def setgame(ctx, name=None):
	global current_game
	global watchers
	global current_turn
	if name is not None:
		game_name = "".join(c for c in name if c.isalnum() or c in KEEPCHARACTERS).rstrip()
		if os.path.exists(os.path.join(SAVEDIR, game_name)):
			current_game = game_name
			statusdump = os.path.join(SAVEDIR, game_name, "statusdump.txt")
			if os.path.exists(statusdump):
				game_info, nation_status = parsedatafile(statusdump)
				current_turn = game_info['turn']
			else:
				current_turn = '?'
			watchers = []
			await ctx.send("Now watching " + game_name + " and all watchers have been removed.")
		else:
			await ctx.send("No game called " + game_name + " found")
	else:
		await ctx.send("No game specified; please specify a game next time")

@bot.command()
async def watch(ctx):
	global watchers
	global current_game
	if current_game is not None:
		if ctx.author not in watchers:
			watchers.append(ctx.author)
			await ctx.send("You are now watching the current game, " + current_game + ", and will receive a DM whenever a new turn processes.")
		else:
			await ctx.send("You are already watching the current game, " + current_game + ".")
	else:
		await ctx.send("No game set; please set a game using !setgame first")

p_gamename = re.compile("Status for '(.+)'", re.IGNORECASE)
p_gameinfo = re.compile('turn (\d+), era (\d), mods (\d+), turnlimit (\d+)')
p_nationstatus = re.compile("Nation\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+([\w_]+)\s+([\w']+)\s+(.+)$")

def parsedatafile(datafile):
	game_info = {}
	nation_status = {}
	with open(datafile) as f:
		lines = f.readlines()
		game_info['name'] = re.search(p_gamename, lines[0])[1]
		temp = re.search(p_gameinfo, lines[1])
		game_info['turn'], game_info['era'], game_info['mods'], game_info['turnlimit'] = temp[1], temp[2], temp[3], temp[4]
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
	# if ctx.author.dm_channel is None:
		# await ctx.author.create_dm()
	# dm = ctx.author.dm_channel
	
	# await dm.send("Testing sending DMs")
	
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
	global current_game
	global current_turn
	global watchers
	if current_game is not None:
		# print("Checking " + current_game)
		statusdump = os.path.join(SAVEDIR, current_game, "statusdump.txt")
		if os.path.exists(statusdump):
			# print("Reading statusdump.txt")
			game_info, nation_data = parsedatafile(statusdump)
			# print("statusdump.txt turn: " + game_info['turn'])
			# print("current turn: " + current_turn)
			# if game_info['turn'] == current_turn:
				# print("the turns match")
			if game_info['turn'] != current_turn:
				print("It is a new turn!")
				for watcher in watchers:
					print("Messaging " + watcher)
					if watcher.dm_channel is None:
						await watcher.create_dm()
					dm = watcher.dm_channel
					await dm.send(current_game + ' just generated a new turn!')
				current_turn = game_info['turn']
				
@bot.command()
async def status(ctx, arg=None):
	global current_game
	game = None
	if arg is not None:
		game_name = "".join(c for c in arg if c.isalnum() or c in KEEPCHARACTERS).rstrip()
		if os.path.exists(os.path.join(SAVEDIR, game_name)):
			game = game_name
		else:
			await ctx.send("No game called " + game_name + " found")
			return
	else:
		if current_game is not None:
			game = current_game
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
			turn = 'Turn ' + game_info['turn'] + ' (Year ' + year + ', ' + season_string + ')'
			game_details = ['**'+game+'**', '*'+turn+'*']
			# the below are 3, 4, 5 in result
			# has not taken turn: 1 0 0
			# mark as unfinished and exit: 1 0 1
			# turn submitted: 1 0 2
			# AI: no indicator?
			# defeated: -2 0 0
			for nation in sorted(nation_status):
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
