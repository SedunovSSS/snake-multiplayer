import pygame
import socket
import pickle
import time
import sys
from tkinter import *

pygame.init()

name_of_lobby = None
name = None
s = None

BUFF_SIZE = 8192*8192
TIME_OUT = 5

# CONNECT FORM

def scan(host, port):
    global name_of_lobby, name, s

    try:
        s = socket.socket()
        s.settimeout(TIME_OUT)
        s.connect((host, port))
    except:
        error_label.config(text='Server not found')
        return
    
    temp_name_of_lobby = pickle.loads(s.recv(BUFF_SIZE))['snake_lobby']

    temp_name = name_entry.get()
    if temp_name == '':
        error_label.config(text='Username is empty')
        s.close()
        return
    
    s.send(temp_name.encode('utf8'))
    recv_name = s.recv(BUFF_SIZE).decode('utf8')

    if recv_name == 'success':
        name = temp_name
        name_of_lobby = temp_name_of_lobby
        root.destroy()
        return
    
    error_label.config(text='Username already exists')
    s.close()


def click():
    try:
        host, port = host_entry.get().split(':')
    except:
        error_label.config(text='Error server name')
        return
    port = int(port)
    scan(host, port)


root = Tk()

root.title('SNAKE | Connect Form')
root.iconbitmap('snake.ico')
root.resizable(False, False)

host_label = Label(text='HOST: ', font='Arial 16 bold')
host_label.grid(row=0, column=0)

host_entry = Entry(font='Arial 16 bold')
host_entry.grid(row=0, column=1, padx=5, pady=5)

name_label = Label(text='NAME: ', font='Arial 16 bold')
name_label.grid(row=1, column=0)

name_entry = Entry(font='Arial 16 bold')
name_entry.grid(row=1, column=1, padx=5, pady=5)

button = Button(text='CONNECT', font='Arial 16 bold', width=25, bg='black', fg='white', command=lambda: click())
button.grid(row=2, columnspan=2, padx=5, pady=5)

error_label = Label(text='', font='Arial 8 bold', fg='red')
error_label.grid(row=3, columnspan=2, padx=5, pady=5)

root.mainloop()

ping_start = time.time()

try:
    s.send(' '.encode('utf8'))
except:
    sys.exit()

# GAME

data = pickle.loads(s.recv(BUFF_SIZE))
ping_end = time.time()
ping = round((ping_end - ping_start) * 1000, 2)

WIDTH, HEIGHT = data['width'], data['height']
BLOCK_SIZE = data['block_size']
FPS = data['fps']

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.display.set_caption(f'Snake | LOBBY: {name_of_lobby}')
pygame.display.set_icon(pygame.image.load('snake.png'))

running = True

apple_cords = data['apples']
dx, dy = data['players_data'][name]['dx'], data['players_data'][name]['dy']
players_tab = data['players_tab']

game_over = data['players_data'][name]['game_over']
font = pygame.font.SysFont('Arial', 20, bold=True)
font1 = pygame.font.SysFont('Arial', 60, bold=True)

while running:
    for i in pygame.event.get():
        if i.type == pygame.QUIT:
            running = False

    screen.fill('black')

    keys = pygame.key.get_pressed()

    for i in data['players_data']:
        player = data['players_data'][i]
        if not player['game_over']:
            for x, y in player['snake']:
                pygame.draw.rect(screen, player['color'], (x, y, BLOCK_SIZE, BLOCK_SIZE), border_radius=5)

    [pygame.draw.rect(screen, (255, 0, 0), (*apple_cord, BLOCK_SIZE, BLOCK_SIZE), border_radius=10) for apple_cord in apple_cords]

    font_render_lobby = font.render(f'LOBBY: {name_of_lobby}', True, (255, 255, 255))
    screen.blit(font_render_lobby, (10, 10))

    font_render_ping = font.render(f'PING: {ping}', True, (0, 128, 255))
    screen.blit(font_render_ping, (10, 30))

    font_render_fps = font.render(f'FPS: {round(clock.get_fps(), 1)}', True, (255, 32, 0))
    screen.blit(font_render_fps, (10, 50))

    if keys[pygame.K_TAB]:
        font_render_online = font.render(f'ONLINE: {len(players_tab)}', True, (0, 255, 85))
        screen.blit(font_render_online, (10, 70))
        for j, pl_tab in enumerate(players_tab):
            player = data['players_data'][pl_tab[1]]
            if len(pl_tab[1]) > 10:
                player_name = pl_tab[1][:10] + '...'
            else:
                player_name = pl_tab[1]
            font_render = font.render(f'{player_name}: {pl_tab[0]}', True, player['color'])
            screen.blit(font_render, (10, 10+20*(j+4)))
    try:
        if not game_over:
            ping_start = time.time()
            if keys[pygame.K_w] and dy != 1:
                s.send(pickle.dumps({'keydown': 'w'}))
            elif keys[pygame.K_s] and dy != -1:
                s.send(pickle.dumps({'keydown': 's'}))
            elif keys[pygame.K_a] and dx != 1:
                s.send(pickle.dumps({'keydown': 'a'}))
            elif keys[pygame.K_d] and dx != -1:
                s.send(pickle.dumps({'keydown': 'd'}))
            else:
                s.send(pickle.dumps({'keydown': 'None'}))

        else:
            gm_render = font1.render('GAME OVER!', True, (255, 64, 0))
            a, b = font1.size('GAME OVER!')
            screen.blit(gm_render, ((WIDTH-a)/2, (HEIGHT-b)/2))
            ping_start = time.time()
            s.send(pickle.dumps({'keydown': 'None'}))
    
        data = pickle.loads(s.recv(BUFF_SIZE))
        ping_end = time.time()
        ping = round((ping_end - ping_start) * 1000, 2)
    except:
        sys.exit()

    apple_cords = data['apples']
    dx, dy = data['players_data'][name]['dx'], data['players_data'][name]['dy']
    players_tab = data['players_tab']
    game_over = data['players_data'][name]['game_over']

    pygame.display.flip()
    clock.tick(FPS)
