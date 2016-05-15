# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, UserForm, UserForms, MoveHistoryForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
HIGH_SCORE_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.target, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Target word cannot be null.')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancel an incompleted game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if not game.game_over:
                game.key.delete()
                return StringMessage(message='Game {} cancelled!'.format(
                    game.key.urlsafe()))
            else:
                return StringMessage(
                    message='Game is over, cannot be cancelled!'.format(
                        game.key.urlsafe()))
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key).filter(
            Game.game_over == False)
        return GameForms(items=[game.to_form('') for game in games])

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        if request.guess == game.target:
            move_history = 'You got the whole word! You win!'
            game.moves.append(move_history)
            game.end_game(True)
            return game.to_form('You win!')

        if len(request.guess) != 1 or not request.guess.isalpha():
            raise endpoints.BadRequestException(
                'Guess one letter or the whole word each round!')

        msg = ''
        for i in range(len(game.target)):
            if game.target[i].lower() == request.guess.lower():
                game.revealed_word = game.revealed_word[:i] + \
                    game.target[i] + game.revealed_word[i+1:]
                msg = 'Hit!'
            else:
                msg = 'Miss!'
                game.attempts_remaining -= 1

        move_history = "Guess: '%s', Result: '%s'" % (
            request.guess, game.revealed_word)

        if game.revealed_word == game.target:
            move_history += ', You win!'
            game.moves.append(move_history)
            game.end_game(True)
            return game.to_form('You win!')

        if game.attempts_remaining < 1:
            move_history += ', Game over!'
            game.moves.append(move_history)
            game.end_game(False)
            return game.to_form('Game over!')
        else:
            game.moves.append(move_history)
            game.put()
            return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=HIGH_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='scores/high',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns highest scores in winning game ascending order of guesses
            used."""
        scores = Score.query(Score.won == True).order(Score.guesses).fetch(
            request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserForms,
                      path='ranking',
                      http_method='GET',
                      name='get_user_rankings')
    def get_user_rankings(self, request):
        """Return user rankings according to user's performance in descending
            order."""
        users = User.query().order(-User.performance).order(User.wins)
        return UserForms(
            items=[user.to_form() for user in users])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=MoveHistoryForm,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return all moves history of a game."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return MoveHistoryForm(moves=game.moves)
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(
          message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum(
              [game.attempts_remaining for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(
              MEMCACHE_MOVES_REMAINING,
              'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
