# SSH-ControlPanel

SSH Control Panel is a fully customizable framework for creating SSH based control panels to control your projects. It enables the creation of custom commands, custom database functions, and can easily be edited to add as many features as you require.

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
| `clear_terminal(self) -> None` | Clears the client's screen. |
