# SSH-ControlPanel

SSH Control Panel is a fully customizable framework for creating SSH based control panels to control your projects. It enables the creation of custom commands, custom database functions, and can easily be edited to add as many features as you require. If you have a question, please read this entire file before creating an issue. Thank you, and enjoy!

Contents:
1. Configuration Options
2. Default Commands
3. Included Classes
4. Available Functions
5. Custom Code

## Configuration Options

Configuration options can be found at the start of the program and have the following values by default:

```py
DEBUG_RAISE_ERRORS = False
DATABASE_LOCATION  = "database/Data.db"

SSH_PORT           = 13333
MAX_CONNECTIONS    = 50
PUBLIC_SSH_BANNER  = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1"

TERMINAL_TITLE_BAR = "Project Name >> [$user] - Connected from [$ip] - Session ID [$sid]"
WELCOME_MESSAGE    = " Welcome, $user"
LOGIN_FAILED       = " Incorrect login credentials, please connect again.\r\n"
COMMAND_UNKNOWN    = "\r Command '$command' not found.\r\n"
COMMAND_PROHIBITED = "\r You do not have permission to execute '$command'. This is reserved for the root user. If you believe this is an error, please contact the system administrator.\r\n"
COMMAND_FAILED     = "\r There was an error executing your command. Please try again later or contact the system administrator.\r\n"
FATAL_ERROR        = "\r\n You have been disconnected due to a fatal error. We apologize for any inconvenience.\r\n"

database_schemas   = {
	"users": "CREATE TABLE users (username VARCHAR(255), password VARCHAR(255))"
}
needed_folders     = []
```

| Value | Description |
| --- | --- |
| `DEBUG_RAISE_ERRORS` | Set to `True` if you would like to be shown full stack traces of errors that would normally be excepted and result in a client disconnect. Not to be used in production environments. |
| `DATABASE_LOCATION` | The path where the database should be created. If you change the folder name, then it must also be changed later in the program (around line 100) when the `needed_folders` variable is updated. Should be `folder_name/database_name.db`. |
| `SSH_PORT` | The port that users must connect to in order to access the server. |
| `MAXIMUM_CONNECTIONS` | The number of simultaneous connections that should be listened for at one time. |
| `PUBLIC_SSH_BANNER` | Banner to be displayed publicly. Should typically be left alone. |
| `TERMINAL_TITLE_BAR` | The text that will appear in the top bar of the terminal of users. Supports placeholders for `$user`, `$ip`, and `$sid` (Session ID) |
| `WELCOME_MESSAGE` | Message that will be displayed to the user for two seconds before continuing to the command line interface. |
| `LOGIN_FAILED` | Message for if the user does not give the correct credentials. |
| `COMMAND_UNKNOWN` | Message for when the user gives a command that is not valid. |
| `COMMAND_PROHIBITED` | Message for when the user does not have permission to use a command. |
| `COMMAND_FAILED` | Message for if a command causes a non-fatal error. |
| `FATAL_ERROR` | Apology message to be shown to a user who induced a fatal error in their client thread. Hopefully the user never has to see this. |
| `database_schemas` | Dictionary of database table creation statements that your project requires. Tables will not be created again if they already exist so no Do not touch the `users` table without adding necessary parameters to the part of the program where the default root credentials are created and added to the table. |
| `needed_folders` | List of folders for assets and resources that your program requires. The list is empty by default but should include strings which are valid folder names. Additional code is required to create sub-folders or default files, and this code should go inside of the `check_and_create_files()` function. |

## Default Commands

The following commands come with the server by default and it is recommended that they remain unchanged unless you are editing the messages or prompts.

| Command | Aliases | Description | Permissions Level |
| --- | --- | --- | --- |
| `clear` | `cls`, `c` | Clears the client's terminal window. | All users (`PermissionsLevel.NORMAL`) |
| `adduser` | `useradd`, `newuser` | Brings up prompts to add a new normal user. Does not permit the creation of accounts with duplicate usernames. | Root only (`PermissionsLevel.ROOT`) |
| `removeuser` | `userremove`, `remove`, `deluser` | Brings up prompts to delete a user given a username. | Root only (`PermissionsLevel.ROOT`) |
| `rootpassword` | `rootpass`, `rootregen` | Regenerates the root login credentials. Asks the user to confirm that they want to do this. The root password is changed, logged, and the user is forced to log back in with the new credentials. | Root only (`PermissionsLevel.ROOT`) |
| `updatepassword` | `userpassword` | Brings up prompts to change the password of an existing normal account. | Root only (`PermissionsLevel.ROOT`) |
| `logout` | `exit`, `disconnect`, `dc` | Ends the client's current session and logs them out. | All users (`PermissionsLevel.NORMAL`) |

## Included Classes

These classes are included as enums which represent various constants.

| Class Name | Description | Values |
| --- | --- | --- |
| `LogType` | Contains three different levels for logging, each of which is a tuple containing an ANSI color and a string with the level name. | `INFO`, `WARNING`, `ERROR` |
| `CommandReturnAction` | Specifies what should be done after a command is done executing. Except for very specific cases, only one value is required which instructs the server to disconnect the client who executed the command. | `BREAK` |
| `PermissionsLevel` | Constant to describe what type of user a client is. By default, permissions is only based on if the account's username is `root` but can be modified for more complex user hierarchies. | `NORMAL`, `ROOT` |

## Available Functions

The following functions are available at any place in the code. Note that their definitions may need to be re-arranged depending on what code you run when the server starts.

| Function/Syntax/Defaults | Description |
| --- | --- |
| `log(message: str, user: str = None, ip: str = None, type: LogType = LogType.INFO) -> None` | The all purpose logging function for this program. `message` is simply the message that you would like sent to the console. `user` and `ip` both default to `None` and allow you to display information about the client in question. If you do not provide both, then the log will only show the log level and the message. Finally, `type` is either `LogType.INFO`, `LogType.WARNING`, or `LogType.ERROR` which each make the message a different color and indicate varying levels of severity. If you are just giving information, there is no need to provide the `type` argument. |
| `create_password_hash(password: str) -> str` | Hashing function used throughout the program which is used to create the passwords used throughout. Creates hashes using SHA-512 and accepts the string `password` which will be hashed. |
| `log_to_file(text: str, path: str) -> None` | Enables easy file-based logging. `text` is simply the message that you wanted logged. It should not contain additional line breaks or any timestamps, as those will be automatically added before it is logged. `path` should simply be a file name in the form of `*.log`, and will automatically go into the `logs/` directory. |
| `get_display_table(headings: list, data: list) -> str` | Creates clean tables as a string that can be send directly to the client for display. `headings` should be the column titles of the table in a list of strings. `data` must be a list of lists or tuples, each containing a row of data. If there is only one row, a double list is still required (`[[datapoint1, datapoint2, ...]]`) as the `data` argument. |
| `format_to_string(item: Any) -> str` | Used by `get_display_table` to format each item of a table. By default, this function uses `str()` on everything except `NoneType`, which is converted to `"N/A"`. Here, you can define custom rules for how tables convert items to `str` to your liking by adding your own code. |
| `format_seconds_to_time(time_int: int) -> str` | Function that takes in an integer for `time_int` as a number of seconds and outputs a formatted time duration as a string in the form of `*d *h *m *s`. |

These database functions are available at any point inside of `SSHControlPanelClient > main_loop()` and are accessed using each client's database object, found using `self.database`. The following are the defaults that are included and necessary for functionality. To add your own, see the section titled **Custom Code**. Please be very careful of the `database_access()` decorator when adding your own functions. Additionally, be sure to check required permissions for commands that use protected database functions.

| Function/Syntax/Defaults | Description |
| --- | --- |
| `check_login_credentials(self, username: str, password: str) -> bool` | Returns `True` if the username and password combination matches and is found inside of the `users` table of the database. |
| `regenerate_root_password(self) -> None` | Creates a new root password and updates the root account's login credentials. The new password will be added to `logs/root_passwords.log`. |
| `set_user_password(self, username: str, password: str) -> None` | Changes the password for an existing user, which is the `username` argument. `password` should be the new plaintext password with no hashing. |
| `add_new_user(self, username: str, password: str) -> None` | Adds a new user account with the given `username` and `password` with no hashing. |
| `remove_user(self, username: str) -> None` | Removes the user with a username matching `username`. |
| `log_login(self, username: str, ip: str, port: int | str) -> None` | By default, this function only logs the login to a file. However, if you want a login history table for your database then you can implement that here. |
| `user_exists(self, username: str) -> bool` | Returns `True` if the username is the name of a registered user. |
| `__user_exists(self, username: str) -> bool` | Has the exact same functionality as the previous function, but does not lock any threads and should be used strictly by other database functions. |

These functions are available within the client class and provide simple functionality that can be used within `SSHControlPanelClient > main_loop()`. Please note that `get_input(...)` is a complex function which requires very specific arguments that is encapsulated by the following functions. Its raw use is highly discouraged. The same goes for `abort_connection(...)` and `kill_connection(...)`, which are handled automatically by the command framework.

| Function/Syntax/Defaults | Description |
| --- | --- |
| `yes_no_prompt(self, prompt_text: str) -> bool / Exception()` | Function to display a yes/no choice to the client. `prompt_text` is not padded and thus must contain necessary newline characters and carriage returns. If the user gave a valid choice, it will return either `True` or `False`. Must be placed inside of a `try/except` block to handle invalid inputs. |
| `prompt(self, prompt_text: str, auto_complete_options: list = None) -> str` | Function to get a string input from the client. `prompt_text` is not padded and thus must contain necessary newline characters and carriage returns. `auto_complete_options` is an optional `list` of strings that contains a list of possibilities that can be auto-completed. |
| `send(self, message: str) -> None` | Sends the string `message` to the client. For messages that are multiple lines, they will be split apart into multiple buffers and sent to the client in the correct format without exceeding outgoing socket limits. |
| `clear_terminal(self) -> None` | Clears the client's screen. |

## Custom Code

There are four different locations in the program where code can be conveniently added to meet your needs.

### Custom Functions and Variables

Here you can define functions or variables that are required for your project to operate. Avoid making direct calls that access databases or files/folders, because at this point they have not been created yet. Wait until the section labeled "Custom Initialization Code" to call functions which you define in this space.

### Custom Database Functions

In this section you can define any functions relating to your database as well as file management and logging. Any class methods placed here which access your database must use the following style:

```py
@database_access()
def function(*args, **kwargs):
    # FUNCTION BODY
```

When this decorator is used, the database can be accessed in a unique way. Typically, when using the `sqlite3` library, you have to create a new cursor, execute a statement with the cursor, commit any changes made, and then close the cursor object. The `database_access` decorator simplifies this process. When a function is surrounded with it, a global cursor object will be updated. All threads will be locked preventing database conflicts (this shouldn't happen anyways but it can be helpful for file editing and various other applications). Once the function is done executing, any changes will be committed and execution of the client's thread can continue. An example of its use can be found in other simple database functions:

```py
@database_access()
def remove_user(self, username):
    cursor.execute("DELETE FROM users WHERE username=?", (username,))
```

For methods meant to make life easier within the database class, for example, a function that is called to perform a statement that must be repeated frequently in many different functions, a protected function should be created and does not need the `database_access` decorator. However, you may still use the same shortcuts as other database functions, like so:

```py
def __user_exists(self, username):
    return cursor.execute("SELECT count(*) FROM users WHERE username=?", (username,)).fetchone()[0] == 1
```

### Custom Commands

One of the most robust and useful tools that this framework offers are flexible custom commands. Custom commands must go in the designated section, denoted by comments, in order to work properly. The function name for the command can be whatever you would like, although it is best practice to make it the first name of the command with an underscore before it. Commands can be defined in the following way:

```py
@command("Description of the command", ["main_name", "alias1", "alias2", *])
def _mycommand():
    # FUNCTION BODY
```

By default, a command defined in this way will be accesible by all users. To prevent this and restrict access to only the root user, define the command like this:

```py
@command("Description of the command", ["main_name", "alias1", "alias2", *], PermissionsLevel.ROOT)
```

Be sure to always double check and make sure that dangerous commands or administrative commands are restricted to the root user. Additionally, the function name has no influence on the final command, so make sure that there is at least one string in the list of aliases. Although there is currently only one command result that cannot be handled within the command's function (`CommandReturnAction.BREAK`), there is a possibility that you could require additional actions in the future. However, most things will work within the function, aside from calls like `break`. If this functionality is necessary, return an action at the end of the function like so:

```py
return CommandReturnAction.BREAK
```

Commands do not currently support directly taking in arguments from the command line, so prompts must be used to input data.

### Custom Initialization Code

This block of code will be called immediately following the creation of all of the requisite folders and files and the loading of the SSH Host Key. Here, any functions that you defined in your **Custom Functions and Variables** section should be called to get your code and data ready for users to access it.

### Other Code Locations

Obviously, these four locations are not the only places where you may insert your own code to make the framework fit your needs. However, if you wish to deviate from these areas then it is recommended that you fully read through the program and understand its flow so you can properly place code. As a rule of thumb, when working with the client thread, you should wait until after the user is authenticated to run code that does work for a specific.
