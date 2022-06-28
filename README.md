# discord-blind-chess

Standalone script for bot (requires token) or in redbot cog to play blind chess over discord.

Base code was stolen (sorry can't remember find where from), but been modified to add all other functions other than move.

## Install 

Install cairo https://www.cairographics.org/download/ 
Install stockfish https://stockfishchess.org/ 
```
pip install -r requirements.txt
```
Edit path variables for your PC/server 
(Add token to bottom of file if using the standalone, 
token from https://discord.com/developers/applications)

## Commands

```
Commands:
  cheat       Show current board state
  end         End game # will print png of game, post gif and score graph
  eval        Show who is winning
  gif         Render game as gif
  help        Shows this message
  log         Print PGN of game
  material    Show taken pieces
  move        Make a move (standard notation) # back is also accepted if opponant not yet moved
  randopen    Set random opening
  score_graph Set stockfish think time
  set_depth   Set stockfish think time
  set_tt      Set stockfish think time
  start       Start a game with tagged player

Type -help command for more info on a command.
```
