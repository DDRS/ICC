import pgzrun
from random import shuffle, choice, randint
from itertools import product, repeat, chain
from threading import Thread
from time import sleep


COLORES = ['red', 'yellow', 'green', 'blue']
TODOS_COLORES = COLORES + ['black']
NUMEROS = list(range(10)) + list(range(1,10))
CARTAS_ESPECIALES = ['skip','reverse','+2']
TIPOS_CARTAS_COLOR = NUMEROS + CARTAS_ESPECIALES * 2
CARTA_NEGRA_TIPOS = ['wildcard', '+4']
TIPOS_CARTAS = NUMEROS + CARTAS_ESPECIALES + CARTA_NEGRA_TIPOS


class Carta:

    def __init__(self, color, tipo_carta):
        self._validacion(color, tipo_carta)
        self.color = color
        self.tipo_carta = tipo_carta
        self.temp_color = None
        self.sprite = Actor('{}_{}'.format(color, tipo_carta))

    def __repr__(self):
        return '<Carta object: {} {}>'.format(self.color, self.tipo_carta)

    def __str__(self):
        return '{}{}'.format(self.color_short, self.carta_tipo_short)

    def __format__(self, f):
        if f == 'full':
            return '{} {}'.format(self.color, self.tipo_carta)
        else:
            return str(self)

    def __eq__(self, otro):
        return self.color == otro.color and self.tipo_carta == otro.tipo_carta

    def _validacion(self, color, tipo_carta):

        if color not in TODOS_COLORES:
            raise ValueError('Invalid color')
        if color == 'black' and tipo_carta not in CARTA_NEGRA_TIPOS:
            raise ValueError('Invalid card type')
        if color != 'black' and tipo_carta not in TIPOS_CARTAS_COLOR:
            raise ValueError('Invalid card type')

    @property
    def color_short(self):
        return self.color[0].upper()

    @property
    def carta_tipo_short(self):
        if self.tipo_carta in ('skip', 'reverse', 'wildcard'):
            return self.tipo_carta[0].upper()
        else:
            return self.tipo_carta

    @property
    def _color(self):
        return self.temp_color if self.temp_color else self.color

    @property
    def temp_color(self):
        return self._temp_color

    @temp_color.setter
    def temp_color(self, color):
        if color is not None:
            if color not in COLORES:
                raise ValueError('Invalid Color')
        self._temp_color = color

    def playable(self, otro):
        return (
            self._color == otro.color or
            self.tipo_carta == otro.tipo_carta or
            otro.color == 'black'
        )

class Jugador:

    def __init__(self, cartas, jugador_id=None):
        if len(cartas) != 7:
            raise ValueError(
                'Invalid player: must be initalised with 7 Cards'
            )
        if not all(isinstance(carta, Carta) for carta in cartas):
            raise ValueError(
                'Invalid player: cards must all be Cards objects'
            )
        self.mano = cartas
        self.jugador_id = jugador_id

    def __repr__(self):
        if self.jugador_id is not None:
            return '<Player object: player {}>'.format(self.jugador_id)
        else:
            return '<Player object>'

    def __str__(self):
        if self.jugador_id is not None:
            return str(self.jugador_id)
        else:
            return repr(self)

    def para_jugar(self, carta_comun):

        return any(carta_comun.playable(carta) for carta in self.mano)


class OchoLocos:
    def __init__(self, jugadores, random=True):

        if not isinstance(jugadores, int):
            raise ValueError('Invalid game: players must be integer')
        if not 2 <= jugadores <= 15:
            raise ValueError('Invalid game: must be between 2 and 15 players')
        self.baraja = self._create_baraja(random=random)
        self.jugadores = [
            Jugador(self._deal_mano(), n) for n in range(jugadores)
        ]
        self._ciclo_juego = ReversibleCycle(self.jugadores)
        self._jugador_comun = next(self._ciclo_juego)
        self._ganador = None
        self._revisar_primera_carta()

    def __next__(self):

        self._jugador_comun = next(self._ciclo_juego)

    def _create_baraja(self, random):

        color_cards = product(COLORES, TIPOS_CARTAS_COLOR)
        black_cards = product(repeat('black', 4), BLACK_CARD_TYPES)
        all_cards = chain(color_cards, black_cards)
        baraja = [Carta(color, tipo_carta) for color, tipo_carta in all_cards]
        if random:
            shuffle(baraja)
            return baraja
        else:
            return list(reversed(baraja))

    def _deal_mano(self):

        return [self.baraja.pop() for i in range(7)]

    @property
    def carta_comun(self):
        return self.baraja[-1]

    @property
    def is_active(self):
        return all(len(jugador.mano) > 0 for jugador in self.jugadores)

    @property
    def jugador_comun(self):
        return self._jugador_comun

    @property
    def ganador(self):
        return self._ganador

    def play(self, jugador, carta=None, new_color=None):

        if not isinstance(jugador, int):
            raise ValueError('Invalid player: should be the index number')
        if not 0 <= jugador < len(self.jugadores):
            raise ValueError('Invalid player: index out of range')
        _jugador = self.jugadores[jugador]
        if self.jugador_comun != _jugador:
            raise ValueError('Invalid player: not their turn')
        if carta is None:
            self._pick_up(_jugador, 1)
            next(self)
            return
        _carta = _jugador.mano[carta]
        if not self.carta_comun.playable(_carta):
            raise ValueError(
                'Invalid card: {} not playable on {}'.format(
                    _carta, self.carta_comun
                )
            )
        if _carta.color == 'black':
            if new_color not in COLORES:
                raise ValueError(
                    'Invalid new_color: must be red, yellow, green or blue'
                )
        if not self.is_active:
            raise ValueError('Game is over')

        played_card = _player.hand.pop(carta)
        self.baraja.append(played_card)

        card_color = played_card.color
        tipo_carta = played_card.card_type
        if card_color == 'black':
            self.carta_comun.temp_color = new_color
            if tipo_carta == '+4':
                next(self)
                self._pick_up(self.current_player, 4)
        elif tipo_carta == 'reverse':
            self._ciclo_juego.reverse()
        elif tipo_carta == 'skip':
            next(self)
        elif tipo_carta == '+2':
            next(self)
            self._pick_up(self.jugador_comun, 2)

        if self.is_active:
            next(self)
        else:
            self._ganador = _jugador
            self._print_ganador()

    def _print_ganador(self):

        if self.ganador.jugador_id:
            ganador_nombre = self.ganador.jugador_id
        else:
            ganador_nombre = self.jugadores.index(self.ganador)
        print("Player {} wins!".format(ganador_nombre))

    def _pick_up(self, jugador, n):

        penalty_cartas = [self.baraja.pop(0) for i in range(n)]
        jugador.mano.extend(penalty_cartas)

    def _check_first_carta(self):
        if self.carta_comun.color == 'black':
            color = choice(COLORES)
            self.carta_comun.temp_color = color
            print("Selected random color for black card: {}".format(color))


class ReversibleCycle:

    def __init__(self, iterable):
        self._items = list(iterable)
        self._pos = None
        self._reverse = False

    def __next__(self):
        if self.pos is None:
            self.pos = -1 if self._reverse else 0
        else:
            self.pos = self.pos + self._delta
        return self._items[self.pos]

    @property
    def _delta(self):
        return -1 if self._reverse else 1

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, valor):
        self._pos = valor % len(self._items)

    def reverse(self):

        self._reverse = not self._reverse


class GameData:
    def __init__(self):
        self.carta_seleccionada = None
        self.color_seleccionado = None
        self.color_selection_required = False
        self.log = ''

    @property
    def carta_seleccionada(self):
        carta_seleccionada = self._carta_seleccionada
        self.carta_selecionada = None
        return carta_selecionada

    @carta_seleccionada.setter
    def carta_seleccionada(self, value):
        self._carta_seleccionada = value

    @property
    def color_seleccionado(self):
        color_seleccionado = self._color_seleccionado
        self.color_seleccionado = None
        return color_seleccionado

    @color_seleccionado.setter
    def color_seleccionado(self, value):
        self._color_seleccionado = value


game_data = GameData()


class AIOcho:
    def __init__(self, jugadores):
        self.juego = OchoLocos(jugadores)
        self.jugador = choice(self.juego.jugadores)
        self.jugador_index = self.juego.jugadores.index(self.jugador)
        print('The game begins. You are Player {}.'.format(self.jugador_index))

    def __next__(self):
        juego = self.juego
        jugador = juego.jugador_comun
        jugador_id = jugador.jugador_id
        carta_comun = juego.carta_comun
        if jugador == self.jugador:
            played = False
            while not played:
                carta_index = None
                while carta_index is None:
                    carta_index = juego_data.carta_seleccionada
                new_color = None
                if carta_index is not False:
                    carta = jugador.mano[carta_index]
                    if not juego.carta_comun.playable(carta):
                        juego_data.log = 'You cannot play that card'
                        continue
                    else:
                        juego_data.log = 'You played card {:full}'.format(carta)
                        if carta.color == 'black' and len(jugador.mano) > 1:
                            juego_data.color_selection_required = True
                            while new_color is None:
                                new_color = juego_data.color_seleccionado
                            juego_data.log = 'You selected {}'.format(new_color)
                else:
                    carta_index = None
                    juego_data.log = 'You picked up'
                juego.play(jugador_id, carta_index, new_color)
                played = True
        elif jugador.para_jugar(juego.carta_comun):
            for i, carta in enumerate(jugador.mano):
                if juego.carta_comun.playable(carta):
                    if carta.color == 'black':
                        new_color = choice(COLORES)
                    else:
                        new_color = None
                    juego_data.log = "Jugador {} jugó {:full}".format(jugador, carta)
                    juego.play(jugador=jugador_id, carta=i, new_color=new_color)
                    break
        else:
            juego_data.log = "Jugador {} escogió".format(jugador)
            juego.play(juego=juego_id, carta=None)


    def print_mano(self):
        print('Your hand: {}'.format(
            ' '.join(str(carta) for carta in self.jugador.mano)
        ))

cantidad_jugadores = 3

juego = AIOcho(cantidad_jugadores)

WIDTH = 1200
HEIGHT = 800

baraja_img = Actor('back')
color_imgs = {color: Actor(color) for color in COLORES}

def juego_loop():
    while juego.juego.is_active:
        sleep(1)
        next(juego)

juego_loop_thread = Thread(target=juego_loop)
juego_loop_thread.start()

def dibujar_baraja():
    baraja_img.pos = (130, 70)
    baraja_img.dibujar()
    carta_comun = juego.juego.carta_comun
    carta_comun.sprite.pos = (210, 70)
    carta_comun.sprite.dibujar()
    if juego_data.color_selection_required:
        for i, carta in enumerate(color_imgs.values()):
            carta.pos = (290+i*80, 70)
            carta.dibujar()
    elif carta_comun.color == 'black' and carta_comun.temp_color is not None:
        color_img = color_imgs[carta_comun.temp_color]
        color_img.pos = (290, 70)
        color_img.dibujar()

def draw_players_hands():
    for p, jugador in enumerate(juego.juego.players):
        color = 'red' if jugador == juego.juego.jugador_comun else 'black'
        text = 'P{} {}'.format(p, 'wins' if juego.juego.ganador == jugador else '')
        screen.draw.text(text, (0, 300+p*130), fontsize=100, color=color)
        for c, carta in enumerate(jugador.mano):
            if jugador == juego.jugador:
                sprite = carta.sprite
            else:
                sprite = Actor('back')
            sprite.pos = (130 + c*80, 330 + p*130)
            sprite.draw()

def show_log():
    screen.draw.text(juego_data.log, midbottom=(WIDTH/2, HEIGHT-50), color='black')

def update():
    screen.clear()
    screen.fill((255, 255, 255))
    draw_baraja()
    draw_jugadores_manos()
    show_log()

def on_mouse_down(pos):
    if juego.jugador == juego.juego.jugador_comun:
        for carta in juego.jugador.mano:
            if carta.sprite.collidepoint(pos):
                juego_data.carta_selecionada = juego.jugador.mano.index(carta)
                print('Selected card {} index {}'.format(carta, juego.jugador.mano.index(carta)))
        if baraja_img.collidepoint(pos):
            juego_data.carta_selecionada = False
            print('Selected pick up')
        for color, carta in color_imgs.items():
            if carta.collidepoint(pos):
                juego_data.color_seleccionado = color
                juego_data.color_selection_required = False
pgzrun.go()
