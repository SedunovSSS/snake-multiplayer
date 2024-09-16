import socket
from threading import Thread
from random import randrange
import json
import pickle
import time
import pygame
import os
import sys

if sys.platform == 'win32':
    os.system('cls')
else:
    os.system('clear')

s = socket.socket() 

server_data = json.load(open('server_config.json'))

host = server_data['HOST']
port = server_data["PORT"]

WIDTH, HEIGHT = server_data["WIDTH"], server_data["HEIGHT"]
BLOCK_SIZE = server_data["BLOCK_SIZE"]
FPS = server_data["MAX_FPS"]
BUFF_SIZE = 8192*8192
APPLE_COUNT = server_data["APPLE_COUNT"]
TIME_OUT_LOGIN = server_data["TIME_OUT_LOGIN"]
TIME_OUT = server_data["TIME_OUT"]

s.bind((host, port))
s.listen(0)

name_of_lobby = input('NAME OF LOBBY: ')

if host == '0.0.0.0':
    print(f'SERVER STARTING ON 127.0.0.1:{port}')
else:
    print(f'SERVER STARTING ON {host}:{port}')

clients = []
usernames = []

apple_cords = []

while len(apple_cords) < APPLE_COUNT:
    cords = [randrange(BLOCK_SIZE*5, WIDTH-BLOCK_SIZE, BLOCK_SIZE), randrange(BLOCK_SIZE*5, HEIGHT-BLOCK_SIZE, BLOCK_SIZE)]
    if cords not in apple_cords:
        apple_cords.append(cords)

game_data = {
    'width': WIDTH,
    'height': HEIGHT,
    'fps': FPS,
    'block_size': BLOCK_SIZE,
    'apples': apple_cords,
    'players_data': dict(),
    'players_tab': []
}


def start_new_client(conn, addr):
    global game_data
    print(f'NEW CONNECTION FROM {addr}')
    try:
        conn.settimeout(TIME_OUT_LOGIN)
        conn.send(pickle.dumps({'snake_lobby': name_of_lobby}))
        name = conn.recv(BUFF_SIZE).decode('utf8')

        while name in usernames:
            conn.send('exists'.encode('utf8'))
            name = conn.recv(BUFF_SIZE).decode('utf8')

        conn.send('success'.encode('utf8'))

        usernames.append(name)
        conn.recv(BUFF_SIZE)
    except:
        print(f'CONNECTION FROM {addr} CLOSE')
        return
    
    conn.settimeout(TIME_OUT)
    player_x, player_y = randrange(BLOCK_SIZE*5, WIDTH-BLOCK_SIZE, BLOCK_SIZE), randrange(BLOCK_SIZE*5, HEIGHT-BLOCK_SIZE, BLOCK_SIZE)
    while [player_x, player_y] in game_data['apples']:
        player_x, player_y = randrange(BLOCK_SIZE*5, WIDTH-BLOCK_SIZE, BLOCK_SIZE), randrange(BLOCK_SIZE*5, HEIGHT-BLOCK_SIZE, BLOCK_SIZE)

    snake = [[player_x, player_y]]
    length = 1

    game_over = False

    player_color = (randrange(32, 256), randrange(32, 256), randrange(32, 256))
    
    dx, dy = 0, 0

    game_data['players_tab'].append([length, name])
    game_data['players_tab'] = list(sorted(game_data['players_tab'], reverse=True))

    game_data['players_data'][name] = dict()
    game_data['players_data'][name]['name'] = name
    game_data['players_data'][name]['snake'] = snake
    game_data['players_data'][name]['length'] = length
    game_data['players_data'][name]['color'] = player_color
    game_data['players_data'][name]['game_over'] = game_over
    game_data['players_data'][name]['last_game_over_time'] = None
    game_data['players_data'][name]['dx'] = dx
    game_data['players_data'][name]['dy'] = dy

    conn.send(pickle.dumps(game_data))

    while True:
        try:
            snake = game_data['players_data'][name]['snake']
            length = game_data['players_data'][name]['length']
            game_over = game_data['players_data'][name]['game_over']
            dx = game_data['players_data'][name]['dx']
            dy = game_data['players_data'][name]['dy']

            data = pickle.loads(conn.recv(BUFF_SIZE))

            if data['keydown'] == 'w':
                dx = 0
                dy = -1
            if data['keydown'] == 's':
                dx = 0
                dy = 1
            if data['keydown'] == 'a':
                dx = -1
                dy = 0
            if data['keydown'] == 'd':
                dx = 1
                dy = 0

            player_x, player_y = snake[-1]

            if not game_over:
                player_x += dx * BLOCK_SIZE
                player_y += dy * BLOCK_SIZE
            else:
                if time.time() - game_data['players_data'][name]['last_game_over_time'] >= 5:
                    game_over = False

            if player_x < 0:
                player_x = WIDTH - BLOCK_SIZE
            if player_x > WIDTH - BLOCK_SIZE:
                player_x = 0
            if player_y < 0:
                player_y = HEIGHT - BLOCK_SIZE
            if player_y > HEIGHT - BLOCK_SIZE:
                player_y = 0

            snake.append([player_x, player_y])
            snake = snake[-length:]

            for i in game_data['players_data']:
                if i != name:
                    player1 = game_data['players_data'][i]
                    if not player1['game_over'] or not game_over:
                        if snake.count(player1['snake'][-1]) > 0:
                            r1 = pygame.Rect(player1['snake'][-1][0]-1, player1['snake'][-1][1]-1, BLOCK_SIZE+1, BLOCK_SIZE)
                            r2 = pygame.Rect(player_x-1, player_y-1, BLOCK_SIZE+1, BLOCK_SIZE+1)
                            if r1.colliderect(r2):
                                if len(player1['snake']) > len(snake):
                                    game_over = True
                                    game_data['players_data'][name]['last_game_over_time'] = time.time()
                                    player_x, player_y = randrange(0, WIDTH-BLOCK_SIZE, BLOCK_SIZE), randrange(0, HEIGHT-BLOCK_SIZE, BLOCK_SIZE)
                                    dx, dy = 0, 0
                                    game_data['apples'] += snake
                                    snake = [[player_x, player_y]]
                                    length = 1
                            else:
                                index_to_strip = snake.index(player1['snake'][-1])
                                game_data['apples'] += snake[:-(len(snake)-index_to_strip)]
                                snake = snake[-(len(snake)-index_to_strip):]
                                length = len(snake)

            for apple_cord in game_data['apples']:    
                if apple_cord in snake:
                    length += 1
                    game_data['apples'].remove(apple_cord)
                    while len(apple_cords) < APPLE_COUNT:
                        cords = [randrange(BLOCK_SIZE*5, WIDTH-BLOCK_SIZE, BLOCK_SIZE), randrange(BLOCK_SIZE*5, HEIGHT-BLOCK_SIZE, BLOCK_SIZE)]
                        if cords not in apple_cords:
                            apple_cords.append(cords)

            if snake.count([player_x, player_y]) > 1:
                index_to_strip = snake.index([player_x, player_y])
                game_data['apples'] += snake[:-(len(snake)-index_to_strip)]
                snake = snake[-(len(snake)-index_to_strip):]
                length = len(snake)

            for i, el in enumerate(game_data['players_tab']):
                if el[1] == name:
                    game_data['players_tab'][i][0] = length

            game_data['players_tab'] = list(sorted(game_data['players_tab'], reverse=True))

            game_data['players_data'][name]['snake'] = snake
            game_data['players_data'][name]['length'] = length
            game_data['players_data'][name]['game_over'] = game_over
            game_data['players_data'][name]['dx'] = dx
            game_data['players_data'][name]['dy'] = dy
            conn.send(pickle.dumps(game_data))

        except:
            break
    
    del(game_data['players_data'][name])
    for i, el in enumerate(game_data['players_tab']):
        if el[1] == name:
            game_data['players_tab'].pop(i)
    clients.remove(conn)
    usernames.remove(name)
    conn.close()
    print(f'CONNECTION FROM {addr} CLOSE')


while True:
    conn, addr = s.accept()
    clients.append(conn)
    Thread(target=lambda: start_new_client(conn, addr)).start()

s.close()
