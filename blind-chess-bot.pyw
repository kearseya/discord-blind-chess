import chess
import random
import json
import numpy as np
import chess.engine
from stockfish import Stockfish
import chess.pgn
## rednering cheat board
import chess.svg
from cairosvg import svg2png
import os
import shutil
import imageio
import discord
from discord.ext import commands
import time
from collections import Counter
import matplotlib.pyplot as plt
import datetime
import itertools
import re

bot = commands.Bot(command_prefix="-")
chess_params = {}

chess_params["isBoard"] = False
chess_params["game"] = []
chess_params["scores"] = []
chess_params["best_moves"] = []
chess_params["norm"] = []
chess_params["cheat_moves"] = []
chess_params["think_time"] = 0.1

chess_params["ongoing_depth"] = 18
chess_params["cheat_counter"] = 0
chess_params["cheat_move_num"] = 0
chess_params["pgn_game"] = ""

##########################################
# variables to change for your PC/server #
#        also add token to bottom!       #
##########################################
## windows
chess_params["engine_path"] = r"C:\Users\Alex\Downloaded Apps\stockfish_14.1_win_x64_avx2\stockfish_14.1_win_x64_avx2.exe"
chess_params["cheat_board_path"] = r"C:\Users\Alex\Downloaded Apps\discord-bots\board_renders\cheat.png"
chess_params["score_graph_path"] = r"C:\Users\Alex\Downloaded Apps\discord-bots\board_renders\score.png"
chess_params["gif_render_path"] = r"C:\Users\Alex\Downloaded Apps\discord-bots\board_renders\gif"
## linux
#engine_path = "stockfish"
#chess_params["cheat_board_path"] = r"/home/alex/Applications_Downloaded/discord-bots/chess-renders/cheat.png"
#chess_params["score_graph_path"] = r"/home/alex/Applications_Downloaded/discord-bots/chess-renders/score.png"
#chess_params["gif_render_path"] = r"/home/alex/Applications_Downloaded/discord-bots/chess-renders/gif"

def simple_pgn():
	result = ""
	n = 1
	for i in range(len(chess_params["game"])):
		if i % 2:
			result += " " + chess_params["game"][i] + "\n"
			continue
		else:
			result += str(n) + ". " + chess_params["game"][i]

		n += 1
	return result

def get_current_score_bestmove():
	global chess_params
	pv_list = []
	print(board)
	prev_board = board.copy()
	prev_board.pop()
	engine = chess.engine.SimpleEngine.popen_uci(chess_params["engine_path"])
	## hopefully can be removed, maybe some useful functions though
	sf = Stockfish(chess_params["engine_path"], depth=int(chess_params["ongoing_depth"]))
	sf.set_fen_position(prev_board.fen())
	if chess_params["ongoing_depth"] != None:
		info = engine.analyse(board, chess.engine.Limit(depth=int(chess_params["ongoing_depth"])))
		## removing stockfish dependancy looks something like
		# best_move = engine.play(prev_board, chess.engine.Limit(depth=int(ongoing_depth)))
		best_move = chess.Move.from_uci(sf.get_best_move())
		## kept as list to add variation arrows (look into ponders)
		pv_list.append(best_move)
		## norm for best move count/percentage function (not implimented yet)
		## would require book move db for book move counter to not skew percentage
		## also scores, requires looking into value swing for mistake/blunder counter
		chess_params["norm"].append(prev_board.san_and_push(best_move))
		prev_board.pop()
		## pv not all legal moves, not best moves either
		# for i in info["pv"]:
		# 	if i in prev_board.legal_moves:
		# 		pv_list.append(prev_board.san_and_push(i))
		# 		prev_board.pop()
	else:
		info = engine.analyse(board, chess.engine.Limit(time=0.1))
	try:
		score_value = float(info["score"].relative.cp/100)
		pov = info["score"].turn
		## if point of view is from black, flip to white
		if pov == False:
			score_value = score_value/-1
	except:
		score_value = 0
	print(pv_list)
	return score_value, pv_list

def alter_string_board(board):
		black = "□"
		white = "■"
		strboard = str(board)
		listboard = list(strboard)
		## font is different for linux install of discord and text looks ok, if windows use false
		change_pieces = False
		piece_map = {"k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙",
					"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟︎"}
		piece_set = set(piece_map.keys())

		w_pos = [0,4,8,12, 18,22,26,30, 32,36,40,44, 50,54,58,62, 64,68,72,76, 82,86,90,94, 96,100,104,108, 114,118,122,126]
		for pos, i in enumerate(strboard):
			if i == ".":
				if pos in w_pos:
					listboard[pos] = white
				else:
					listboard[pos] = black
			if change_pieces == True:
				if i in piece_set:
					listboard[pos] = piece_map[i]
		strboard = "".join(listboard)
		## add numbers down side
		num = 8
		idx = [(i*16)+(i+0) for i in range(0,8)]
		for i in idx:
			listboard.insert(i, f"{num}\t")
			num = num-1
		strboard = "".join(listboard)
		## add letters at bottom
		strboard = strboard+"\n\n \ta b c d e f g h"
		return strboard

def gen_score_graph():
	x_vals = [i/2 for i in range(len(chess_params["scores"]))]
	ticks_array = [i for i in range(int(len(chess_params["scores"])/2)+1)]

	x = np.array(x_vals)
	y = np.array(chess_params["scores"])
	my_cmap = plt.get_cmap("RdYlGn")
	rescale = lambda y: (y - np.min(y)) / (np.max(y) - np.min(y))

	plt.bar(x, y, color=my_cmap(rescale(y)), width=0.5, align="edge")
	plt.xticks(ticks_array)
	for x, y, s in zip(x_vals, chess_params["scores"], chess_params["game"]):
		if (y < 0):
			y -= 1.5
		plt.text(x, y+0.5, s)
	plt.ylabel("score")
	plt.margins(0.1)
	plt.savefig(chess_params["score_graph_path"])
	plt.clf()

@bot.command(brief='Start a game with tagged player', description="Takes: member, side (default, author = white), vairation (960 for random). Tag the bot to play against stockfish (use set_tt to change difficulty).")
async def start(ctx, user: discord.Member = None, side: str = "white", variation: str = None):
	global board
	global chess_params

	chess_params["botIsPlayer"] = False

	bot_id = await bot.application_info()
	if not user:
		await ctx.channel.send("Tag a user to play.")
		return

	elif user.id == bot_id.id:
		chess_params["botIsPlayer"] = True

	if "w" in side.lower():
		chess_params["white_id"] = ctx.author.id
		chess_params["black_id"] = user.id
		chess_params["white_name"] = str(ctx.message.author.mention)
		chess_params["black_name"] = str(user.mention)
	elif "b" in side.lower():
		chess_params["black_id"] = ctx.author.id
		chess_params["white_id"] = user.id
		chess_params["white_name"] = str(user.mention.name)
		chess_params["black_name"] = str(ctx.message.author.mention.name)
	else:
		await ctx.channel.send("Sorry didn't understand the sides")
		return

	chess_params["isBoard"] = True

	if not variation:
		board = chess.Board()
	elif variation == "960" or variation == "chess960":
		r = random.randint(0, 959)
		board = chess.Board().from_chess960_pos(r)
		await ctx.channel.send("```" + str(board) + "```")
	else:
		await ctx.channel.send("Unknown chess variant.")
		return

	await ctx.channel.send("Board was created.")
	if "w" in side.lower():
		await ctx.channel.send(f"White: {ctx.message.author.mention}\nBlack: {user.mention}")
	else:
		await ctx.channel.send(f"White: {user.mention}\nBlack: {ctx.message.author.mention}")

	if chess_params["botIsPlayer"] == True:
		if "b" in side.lower():
			engine = chess.engine.SimpleEngine.popen_uci(chess_params["engine_path"])
			# 0.1 because maybe the player will have a tiny chance, if stockfish doesn't do the *perfect* moves
			limit = chess.engine.Limit(time=chess_params["think_time"])
			move = engine.play(board, limit)
			if move.move is None:
				if move.resigned:
					await ctx.channel.send("Engine resigned; Congratulations!")
					await end(ctx)
					return

				elif move.draw_offered:
					await ctx.channel.send("Engine offered you a draw, do you accept? (This isn't implemented yet :/)")
					await end(ctx)
					return

			move_normal_notation = board.san(move.move)
			await ctx.channel.send(move_normal_notation)
			board.push(move.move)
			chess_params["game"].append(move_normal_notation)

			if chess_params["ongoing_depth"] != None:
				score_value, pv_list = get_current_score_bestmove()
				chess_params["scores"].append(score_value)
				chess_params["best_moves"].append(pv_list)

@start.error
async def start_error(ctx, error):
	if isinstance(error, commands.BadArgument):
		await ctx.channel.send("User not found.")


@bot.command(brief='Make a move (standard notation)', description="fyi 0-0 kingside castle, 0-0-0 queenside")
async def move(ctx, arg):
	global game
	global scores
	if chess_params["isBoard"]:
		try:
			author_id = ctx.author.id

			if board.turn and author_id == chess_params["white_id"]:  # board.turn returns True if
				# white to move and false otherwise
				pass
			elif not board.turn and author_id == black_id:
				pass
			else:
				if arg == "back":
					chess_params["game"] = chess_params["game"][:-1]
					chess_params["scores"] = chess_params["scores"][:-1]
					board.pop()
					await ctx.channel.send("You took that move back.")
					return
				await ctx.channel.send("You can't move for other player.")
				return

			board.push_san(arg)

		except ValueError:
			await ctx.channel.send("Invalid move.")
			return

		if board.outcome(claim_draw=True) != None:
			s = str(board.outcome(claim_draw=True).termination)
			s = s.split(".")

			await ctx.channel.send(s[-1].replace("_", " "))
			await end(ctx)

		elif board.is_check():
			await ctx.channel.send("Check.")
		else:
			await ctx.message.add_reaction("✅")

		chess_params["game"].append(arg)
		if chess_params["ongoing_depth"] != None:
			score_value, pv_list = get_current_score_bestmove()
			chess_params["scores"].append(score_value)
			chess_params["best_moves"].append(pv_list)

		#print(chess_params["game"])

		if chess_params["botIsPlayer"]:

			engine = chess.engine.SimpleEngine.popen_uci(chess_params["engine_path"])
			# 0.1 because maybe the player will have a tiny chance, if stockfish doesn't do the *perfect* moves
			limit = chess.engine.Limit(time=chess_params["think_time"])
			move = engine.play(board, limit)
			if move.move is None:
				if move.resigned:
					await ctx.channel.send("Engine resigned; Congratulations!")
					await end(ctx)
					return

				elif move.draw_offered:
					await ctx.channel.send("Engine offered you a draw, do you accept? (This isn't implemented yet :/)")
					await end(ctx)
					return

			move_normal_notation = board.san(move.move)
			await ctx.channel.send(move_normal_notation)
			board.push(move.move)
			chess_params["game"].append(move_normal_notation)

			if board.is_game_over():
				await ctx.channel.send(board.outcome(claim_draw=True))
				await end(ctx)
			elif board.is_check():
				await ctx.channel.send("Check.")

			if chess_params["ongoing_depth"] != None:
				score_value, pv_list = get_current_score_bestmove()
				chess_params["scores"].append(score_value)
				chess_params["best_moves"].append(pv_list)

	else:
		await ctx.channel.send("Board wasn't created. Use -start to create.")


@bot.command(brief='Print PGN of game')
async def log(ctx):
	if len(game) == 0:
		await ctx.channel.send("No piece was moved yet.")
		return
	result = simple_pgn()
	await ctx.channel.send("```" + str(result) + "```")


@bot.command(brief='End game')
async def end(ctx, sc="a"):
	global board
	global chess_params

	strboard = alter_string_board(board)
	await ctx.channel.send("```" + strboard + "```")

	if len(chess_params["game"]) == 0:
		await ctx.channel.send("No piece was moved yet.")
		return

	if ctx.author.id == chess_params["white_id"]:
		result = "0-1"
	else:
		result = "1-0"
	if sc == "draw":
		result = "1/2-1/2"

	pgn_string =f"[Event \"blind match\"]\n[Site: \"discord bot\"]\n[Date \"{datetime.datetime.today().replace(microsecond=0)}\"]\n[White \"{chess_params['white_name']}\"]\n[Black \"{chess_params['black_name']}\"]\n[Result \"{result}\"]\n"

	n = 1
	for i in range(len(chess_params["game"])):
		if i % 2:
			pgn_string += f" {chess_params['game'][i]} "
			continue
		else:
			pgn_string += f"{n}. {chess_params['game'][i]}"
		n += 1

	chess_params["pgn_game"] = pgn_string

	await ctx.channel.send("```" + pgn_string + "```")

	await gif(ctx)

	if sc != "nograph":
		gen_score_graph()
		await ctx.channel.send(file=discord.File(chess_params["score_graph_path"]))

	board.reset()
	chess_params["isBoard"] = False
	chess_params["botIsPlayer"] = False
	chess_params["game"] = []
	chess_params["scores"] = []
	chess_params["best_moves"] = []
	chess_params["norm"] = []
	chess_params["cheat_moves"] = []
	chess_params["think_time"] = 0.1

	chess_params["ongoing_depth"] = 18
	chess_params["cheat_counter"] = 0
	chess_params["cheat_move_num"] = 0
	chess_params["pgn_game"] = ""

	await ctx.channel.send(f"```Cheat moves: {chess_params['cheat_moves']}```")
	await ctx.channel.send("Game ended. Board is reset.")




@bot.command(brief='Show current board state', description="Add anything after cheat so only person who asked recieves board (can be configured to use ascii or send png of board)")
async def cheat(ctx, one_sided=None):
	global board
	global chess_params

	text_board = False
	if text_board == True:
		strboard = alter_string_board(board)
		#print(strboard)
		if one_sided == None:
			await ctx.channel.send("```" + strboard + "```")
		else:
			await ctx.author.send("```" + strboard + "```")

	send_png = True
	if send_png == True:
		boardsvg = chess.svg.board(board=board)
		svg2png(bytestring=boardsvg, write_to=chess_params["cheat_board_path"])
		time.sleep(1)
		if one_sided == None:
			await ctx.channel.send(file=discord.File(chess_params["cheat_board_path"]))
		else:
			await ctx.author.send(file=discord.File(chess_params["cheat_board_path"]))

	if len(chess_params["game"])//2 > 0:
		chess_params["cheat_counter"] += 1
		cheat_length = len(chess_params["game"])//2 - chess_params["cheat_move_num"]
		chess_params["cheat_move_num"] = len(chess_params["game"])//2
		chess_params["cheat_moves"].append(len(chess_params["game"])//2)

		await ctx.channel.send(f"```Cheat number: {chess_params['cheat_counter']}\nStreak:       {cheat_length}\nCheat moves:  {chess_params['cheat_moves']}```")



@bot.command(brief='Show taken pieces')
async def material(ctx):
	on_board = Counter(str(board).split())
	piece_type = {chess.PAWN: "P", chess.ROOK: "R", chess.KNIGHT: "N", chess.BISHOP: "B", chess.KING: "K", chess.QUEEN: "Q"}

	#start_material = {chess.PAWN: 8, chess.ROOK: 2, chess.KNIGHT: 2, chess.BISHOP: 2, chess.KING: 1, chess.QUEEN: 1}
	white_material = {chess.PAWN: 8, chess.ROOK: 2, chess.KNIGHT: 2, chess.BISHOP: 2, chess.KING: 1, chess.QUEEN: 1}
	black_material = {chess.PAWN: 8, chess.ROOK: 2, chess.KNIGHT: 2, chess.BISHOP: 2, chess.KING: 1, chess.QUEEN: 1}
	for p in list(piece_type.keys()):
		white_material[p] = white_material[p] - len(board.pieces(p, chess.WHITE))
		black_material[p] = black_material[p] - len(board.pieces(p, chess.BLACK))

	white_string = ""
	black_string = ""
	for p in list(piece_type.keys()):
		if white_material[p] != 0:
			white_string = white_string + f" {white_material[p]}{piece_type[p]}"
		if black_material[p] != 0:
			black_string = black_string + f" {black_material[p]}{piece_type[p].lower()}"

	await ctx.channel.send("```" +
	"white:	" + white_string + "\n" +
	"black:	" + black_string + "```")


@bot.command(brief='Show who is winning', description="Takes depth, adding \"score\" will show you the score value")
async def eval(ctx, depth="20", hidden="yup"):
	global board

	## allow skipping of adding depth value to get score at default 20
	if depth.isdigit() == False:
		hidden = depth
		depth = "20"

	engine = chess.engine.SimpleEngine.popen_uci(chess_params["engine_path"])
	await ctx.channel.send(f"`Analysing at depth {depth}`")
	info = engine.analyse(board, chess.engine.Limit(depth=int(depth)))
	try:
		score_value = float(info["score"].relative.cp/100)
		pov = info["score"].turn
		## if point of view is from black, flip to white
		if pov == False:
			score_value = score_value/-1
		if "yup" in hidden.lower():
			if score_value > 0:
				await ctx.channel.send("```Looks like white is ahead```")
			elif score_value < 0:
				await ctx.channel.send("```Looks like black is ahead```")
			elif score_value == float(0):
				await ctx.channel.send("```Looks like a dead draw```")
		
		if "g" in hidden.lower():
			if -1 <= score_value <= 1:
				await ctx.channel.send("```Looks like it's pretty equal```")
			if 1 <= score_value <= 3:
				await ctx.channel.send("```Looks like white is slightly ahead```")
			if score_value > 3:
				await ctx.channel.send("```Looks like white is pretty ahead```")
			if -3 <= score_value <= -1:
				await ctx.channel.send("```Looks like black is slightly ahead```")
			if score_value < -3:
				await ctx.channel.send("```Looks like black is pretty ahead```")

		if "s" in hidden.lower():
			await ctx.channel.send(f"```Score: {score_value}```")
	except:
		await ctx.channel.send("```Looks like there is a mate here```")


@bot.command(brief="Render game as gif", description="Render game as gif with annoations")
async def gif(ctx, annotate="jkashdf"):
	move_images = []
	previous_game = board.copy()
	gif_board = chess.Board()
	boardsvg = chess.svg.board(board=gif_board)
	svg2png(bytestring=boardsvg, write_to=str(os.path.join(chess_params["gif_render_path"], "position_000.png")))

	def arrows_generate(pv_list):
		arrow_array = []
		if len(pv_list) > 3:
			pv_list = pv_list[:3]
		for i, m in enumerate(pv_list):
			if i == 0:
				arrow_array.append(chess.svg.Arrow(m.from_square, m.to_square, color="green"))
			if i > 0:
				arrow_array.append(chess.svg.Arrow(m.from_square, m.to_square, color="blue"))
		return arrow_array


	for i, move in enumerate(previous_game.move_stack):
		gif_board.push(move)
		if annotate == None:
			boardsvg = chess.svg.board(gif_board, lastmove=move
				#fill={move.from_square: "yellow", move.to_square: "yellow"},
				#arrows=[chess.svg.Arrow(move.from_square, move.from_square, color="#0000cccc")]
				)
			svg2png(bytestring=boardsvg, write_to=str(os.path.join(chess_params["gif_render_path"], f"position_{str(i+1).zfill(3)}.png")))
		else:
			if i <= len(previous_game.move_stack)-1:
				boardsvg = chess.svg.board(gif_board, lastmove=move,
					#fill={move.from_square: "yellow", move.to_square: "yellow"},
					arrows=arrows_generate(chess_params["best_moves"][i])
					)
			## am aware not needed but
			else: #if i == len(previous_game.move_stack)-1:
				boardsvg = chess.svg.board(gif_board, lastmove=move
				#fill={move.from_square: "yellow", move.to_square: "yellow"},
				#arrows=[chess.svg.Arrow(move.from_square, move.from_square, color="#0000cccc")]
				)
			svg2png(bytestring=boardsvg, write_to=str(os.path.join(chess_params["gif_render_path"], f"position_{str(i+1).zfill(3)}.png")))
	gif_path = os.path.join(chess_params["gif_render_path"], "game.gif")
	print(gif_path)
	
	for filename in [f for f in os.listdir(chess_params["gif_render_path"]) if re.search(r"position\_\d\d\d\.png", f)]:
		move_images.append(imageio.imread(str(os.path.join(chess_params["gif_render_path"], filename))))
	imageio.mimsave(gif_path, move_images, duration=len(move_images)/4)
	#with imageio.get_writer(gif_path, mode='I') as writer:
	#	for filename in os.listdir(chess_params["gif_render_path"]):
	#		image = imageio.imread(str(os.path.join(chess_params["gif_render_path"], filename)))
	#		writer.append_data(image)
	await ctx.channel.send(file=discord.File(gif_path))
	
	# delete files 
	for filename in [f for f in os.listdir(chess_params["gif_render_path"]) if re.search(r"position\_\d\d\d\.png", f)]:
		file_path = os.path.join(chess_params["gif_render_path"], filename)
		try:
			if os.path.isfile(file_path) or os.path.islink(file_path):
				os.unlink(file_path)
			#elif os.path.isdir(file_path):
			#	shutil.rmtree(file_path)
		except Exception as e:
			print('Failed to delete %s. Reason: %s' % (file_path, e))

		



@bot.command(brief='Set stockfish think time', desciption="Increasing will make game harder")
async def score_graph(ctx):
	gen_score_graph()
	await ctx.channel.send(file=discord.File(chess_params["score_graph_path"]))

@bot.command(brief='Set stockfish think time', desciption="Increasing will make game harder")
async def set_tt(ctx, tt=0.1):
	global chess_params
	try:
		chess_params["think_time"] = float(tt)
		await ctx.channel.send(f"`Think time set to {tt}`")
	except:
		await ctx.channel.send(f"`{tt} not a valid think time value`")


@bot.command(brief='Set stockfish think time', desciption="Increasing will make game harder")
async def set_depth(ctx, od=18):
	global chess_params
	try:
		chess_params["ongoing_depth"] = int(od)
		await ctx.channel.send(f"`Ongoing depth {ongoing_depth}`")
	except:
		chess_params["ongoing_depth"] = None
		await ctx.channel.send(f"`Depth remove, using 1 second`")

@bot.command(brief='Set random opening', description='Set random opening')
async def randopen(ctx, setboard="no", openlen=">=3"):
	con = "="
	try:
		openlen = int(setboard)
	except:
		for i in ["<=", "<", ">=", ">"]:
			if str(setboard).startswith(i):
				con = i
				openlen = int(setboard[len(i):])
				break

	for i in ["<=", "<", ">=", ">"]:
		if str(openlen).startswith(i):
			con = i
			openlen = int(openlen[len(i):])
			break

	with open(r"books\eco.json") as f:
		t = json.load(f)
	
	index_lengths = {}
	for x, i in enumerate(t):
		l = len(i["moves"].split()) // 3
		if l not in set(index_lengths.keys()):
			index_lengths[l] = [x]
		else:
			index_lengths[l].append(x)
	
	max_length = max(set(index_lengths.keys()))
	valid_lengths = set(index_lengths.keys())
	indexes = []
	if openlen > max_length:
		openlen = max_length
		ctx.channel.send(f"Max opening is {max_length}")
	if openlen not in valid_lengths: # no 15, 16, 17 openings
		openlen = 14
	
	if con == "=":
		randop = t[index_lengths[openlen][random.randint(0, len(index_lengths[openlen])-1)]]
	elif con == "<":	
		for i in range(0, openlen):
			if i in valid_lengths:
				indexes.append(index_lengths[i])
	elif con == "<=":
		for i in range(0, openlen+1):
			if i in valid_lengths:
				indexes.append(index_lengths[i])
	elif con == ">":
		for i in range(openlen+1, max_length+1):
			if i in valid_lengths:
				indexes.append(index_lengths[i])
	elif con == ">=":
		for i in range(openlen, max_length+1):
			if i in valid_lengths:
				indexes.append(index_lengths[i])
	else:
		indexes = [random.randint(0, len(t)-1)]

	if len(indexes) > 0:
		indexes = list(itertools.chain.from_iterable(indexes))
		randop = t[indexes[random.randint(0, len(indexes)-1)]]
	
	randopmoves = randop["moves"].split()

	await ctx.channel.send(f'```{randop["name"]}:\n{randop["moves"]}```')

	if "s" in str(setboard).lower():
		global board
		global chess_params
		for move in [i for num, i in enumerate(randopmoves) if num % 3 != 0]:
			chess_params["game"].append(move)
			board.push_san(move)

bot.run("YOUR TOKEN HERE")