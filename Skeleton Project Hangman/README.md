#Full Stack Nanodegree Project 4 Refresh

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
  
 
##Game Description:
Hangman is a word-guessing game. Each game begins with a secret word 'target'.
The player tries to guess it by suggesting letters within a certain number of guesses 'attempts'.
'Guesses' are sent to the 'make_move' endpoint which will reply with 'Hit' or 'Miss' replies and a revealed word.
If the target word contains the guessed letter, the letters in the target will be revealed.
While the other letters in the target word will be screened with a '*'.
If all letters in the target word are revealed within allowed attempts, the user wins the game. If the maximum attempts are reached, the user loses the game.

Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
     
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, target, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Target is the answer word, which cannot be null. Attempts is the max allowed guess chances. Also adds a task to a task queue to update the average moves remaining for active games.
     
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: POST
    - Parameters: urlsafe_game_key
    - Returns: Messages confirming deletion of the game.
    - Description: Cancel an incompleted game.

- **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

- **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms with the user's current games.
    - Description: Returns all of an individual User's active games
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created and the user's performance will be updated. Each move will be recorded for history.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered). Will raise a NotFoundException if the User does not exist.

- **get_high_scores**
    - Path: 'scores/high'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all winning Scores ascending ordered by the attempts used (descending high scores). 

- **get_user_rankings**
    - Path: 'ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForms. 
    - Description: Return user rankings according to user's performance in descending order, and second order of count of winning games.

- **get_game_history**
    - Path: 'game/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: MoveHistoryForm. 
    - Description: Return all moves history of a game.
    
 - **get_average_attempts_remaining**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name, (optional) email address, winning games, lost games and performance.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty. Append a revealed word field for the feedback to user to each guess.
    Append a moves field to record each guess and feedback for game history.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name, revealed_word, moves).

 - **GameForms**
    - Multiple ScoreForm container.

 - **NewGameForm**
    - Used to create a new game (user_name, target, attempts)

 - **MakeMoveForm**
    - Inbound make move form (guess).

 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).

 - **ScoreForms**
    - Multiple ScoreForm container.

 - **UserForm**
    - Representation of a user's performance (user_name, performance).

 - **UserForms**
    - Multiple UserForm container.

- **MoveHistoryForm**
    - MoveHistoryForm for outbound a completed game's moves history.

 - **StringMessage**
    - General purpose String container.
