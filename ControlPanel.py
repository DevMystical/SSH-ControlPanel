import os, datetime, socket, sqlite3, threading, hashlib, paramiko, traceback, random, string, time, sys
from functools import wraps
from datetime import datetime

# Please be sure to carefully read through README.md, as it contains
# lots of important information on how to implement your project into
# this SSH Server framework.

# ----- START OF CONFIGURATION ----- #

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

# -----  END OF CONFIGURATION  ----- #

start_time = time.perf_counter()

class LogType:
	INFO	= "\033[0m", 		  "INFO"
	WARNING = "\033[1;38;5;220m", "WARNING"
	ERROR   = "\033[1;38;5;160m", "ERROR"

def log(message, user=None, ip=None, type=LogType.INFO):
	current_time = datetime.now().strftime("\033[0m(%I:%M:%S %p - %m/%d/%Y) ")
	if not user == None and not ip == None:
		print(current_time + f"[ {type[0] + type[1]}\033[0m - " + type[0] + user + "@" + ip + "\033[0m ] [" + type[0] + message + "\033[0m]")
	else:
		print(current_time + f"[ {type[0] + type[1]}\033[0m ] [" + type[0] + message + "\033[0m]")

os.system("cls" if os.name == "nt" else "clear")

if DEBUG_RAISE_ERRORS:
	log("!!! Working in development mode, raising errors when they come up !!!", type=LogType.WARNING)
	log("!!!        > Do not use this in a production environment. <       !!!", type=LogType.WARNING)

HOST_KEY = None
ENCODING = "UTF-8"
session_id = 0
connected_clients = []

if not os.name == "nt":
	for _ in range(5):
		os.system(f"lsof -t -i tcp:{SSH_PORT} | xargs kill")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", SSH_PORT))
s.listen(MAX_CONNECTIONS)

def create_password_hash(password):
	return hashlib.sha512(password.encode("utf-8")).hexdigest()

if not "database" in os.listdir():
	os.mkdir("database")
connection = sqlite3.connect(DATABASE_LOCATION, check_same_thread=False)
db_access_lock = threading.Lock()
cursor = None

format_time_no_brackets = lambda time_int: datetime.fromtimestamp(time_int).strftime("%I:%M:%S %p - %m/%d/%Y")
format_time = lambda time_int: " [" + format_time_no_brackets(time_int) + "] "
ctime = lambda: int(datetime.now().timestamp())

def log_to_file(text, path):
	with open(f"logs/{path}", "a+", encoding=ENCODING) as f:
		f.write(format_time(ctime()) + text + "\n")

def database_access():
	def outer(func):
		@wraps(func)
		def inner(*args, **kwargs):
			db_access_lock.acquire()
			global cursor
			cursor = connection.cursor()
			result = func(*args, **kwargs)
			connection.commit()
			db_access_lock.release()
			return result
		return inner
	return outer

needed_folders = list(set(needed_folders + ["logs", "keys"]))

@database_access()
def check_and_create_files():

	def table_exists(table_name, conn):
		return conn.cursor().execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()[0] == 1

	for folder in needed_folders:
		if not folder in os.listdir():
			os.mkdir(folder)

	for table, statement in database_schemas.items():
		if not table_exists(table, connection):
			log(f"Created table '{table}' in {DATABASE_LOCATION}")
			cursor.execute(statement)

			if table == "users":
				root_password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
				log("Generated new root credentials")
				log("A copy of the current root credentials can be found inside of logs/root_passwords.log")
				log_to_file(f"Updated root credentials: root:{root_password}", "root_passwords.log")
				cursor.execute("INSERT INTO users VALUES (?, ?)", ("root", create_password_hash(root_password)))

# These two functions are not used in any sample code but are explained in README.md and can be used to create nice looking tables
def get_display_table(headings: list, data: list) -> str:
	column_max_lens = [len(format_to_string(title)) for title in headings]
	for data_set in data:
		for index, column in enumerate(data_set):
			col_length = len(format_to_string(column))
			if col_length > column_max_lens[index]:
				column_max_lens[index] = col_length
	buffer = " \033[107;30m  " + "     ".join(title.ljust(column_max_lens[index]) for index, title in enumerate(headings)) + "  \033[0m"
	for data_set in data:
		buffer += "\n   " + "     ".join(format_to_string(value).ljust(column_max_lens[index]) for index, value in enumerate(data_set)) + "   "
	return "\033[0m" + buffer + "\033[0m"

def format_to_string(item) -> str:
	# Here you can definie custom rules for how table items are converted into strings
	if item == None:
		return "N/A"
	else:
		return str(item)

def format_seconds_to_time(time_int):
	m, s = divmod(time_int, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	return f"{d:d}d {h:d}h {m:d}m {s:d}s"

# ----- START OF CUSTOM FUNCTIONS AND VARIABLES ----- #





# -----  END OF CUSTOM FUNCTIONS AND VARIABLES  ----- #

class CommandReturnAction:
	BREAK = 0

class PermissionsLevel:
	NORMAL, ROOT = 0, 1

class SSHPanelDatabase:

	def __init__(self, user):
		self.user = user

	@database_access()
	def check_login_credentials(self, username, password):
		result = cursor.execute("SELECT password FROM users WHERE username=?", (username,)).fetchone()
		if not result or not result[0] == create_password_hash(password):
			return False
		return True

	@database_access()
	def regenerate_root_password(self):
		root_password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
		log("Generated new root credentials")
		log("A copy of the current root credentials can be found inside of logs/root_passwords.log")
		log_to_file(f"Updated root credentials: root:{root_password}", "root_passwords.log")
		cursor.execute("DELETE FROM users WHERE username=?", ("root",))
		cursor.execute("INSERT INTO users VALUES (?, ?)", ("root", create_password_hash(root_password)))

	@database_access()
	def set_user_password(self, username, password):
		cursor.execute("UPDATE users SET password=? WHERE username=?", (create_password_hash(password), username))

	@database_access()
	def add_new_user(self, username, password):
		cursor.execute("INSERT INTO users VALUES (?, ?)", (username, create_password_hash(password)))

	@database_access()
	def remove_user(self, username):
		cursor.execute("DELETE FROM users WHERE username=?", (username,))

	def log_login(self, username, ip, port):
		log_to_file(f"User logged in: '{username}' from {ip}:{port}", "logins.log")

	# Use this function for external calls that have not already locked all threads
	@database_access()
	def user_exists(self, username):
		return self.__user_exists(username)

	# Use this function strictly for internal database calls from functions that have the @database_access() decorator
	def __user_exists(self, username):
		return cursor.execute("SELECT count(*) FROM users WHERE username=?", (username,)).fetchone()[0] == 1

	# ----- START OF CUSTOM DATABASE FUNCTIONS ----- #





	# -----  END OF CUSTOM DATABASE FUNCTIONS  ----- #

class SSHServerEmulator(paramiko.ServerInterface):
	
	def __init__(self):
		self.username, self.password = None, None
		self.event = threading.Event()

	def check_channel_request(self, kind, _):
		if kind == "session":
			return paramiko.OPEN_SUCCEEDED
		return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

	def check_auth_password(self, username, password):
		self.username = username
		self.password = password
		return paramiko.AUTH_SUCCESSFUL

	def get_allowed_auths(self, username):
		return "password"

	def check_channel_shell_request(self, channel):
		self.event.set()
		return True

	def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
		return True

class SSHControlPanelClient(threading.Thread):

	def __init__(self, sock: socket.socket, address, session_id):
		threading.Thread.__init__(self, daemon=True)
		self.sock = sock
		self.address = address
		self.ip = f"{address[0]}:{address[1]}"
		self.database = None
		self.kill_socket_immediately = True
		self.session_id = session_id
		self.transport = None

	def run(self):
		try:
			self.process_ssh_client()
		except Exception as e:
			if not isinstance(e, ModuleNotFoundError):
				username = "Not Logged In" if not self.database else self.database.user
				log(f"Fatal error in Client Thread: {type(e).__name__}", username, self.ip)
				for line in traceback.format_exc().strip().split("\n"):
					log(line, username, self.ip, type=LogType.ERROR)
				log("Disconnecting client", username, self.ip, type=LogType.ERROR)
				self.send(FATAL_ERROR)
			if self.kill_socket_immediately:
				self.kill_connection()
			else:
				self.abort_connection()

	def process_ssh_client(self):
		self.transport = paramiko.Transport(self.sock)
		self.transport.add_server_key(HOST_KEY)
		self.transport.local_version = PUBLIC_SSH_BANNER
		self.server = SSHServerEmulator()
		try:
			self.transport.start_server(server=self.server)
		except paramiko.SSHException:
			log(f"Failed to negotiate SSH connection from {self.ip}")
			raise ModuleNotFoundError()
		self.chan = self.transport.accept(20)
		if self.chan is None:
			log(f"Error with SSH Connection from {self.ip}: No channel")
			raise ModuleNotFoundError()
		self.server.event.wait(10)
		if not self.server.event.is_set():
			log(f"Client at {self.ip} never requested a shell")
			raise ModuleNotFoundError()
		self.client_login_sequence()

	def client_login_sequence(self):
		username, password = self.server.username, self.server.password
		self.database = SSHPanelDatabase(username)
		login_success = self.database.check_login_credentials(username, password)

		if login_success == True:
			self.database.log_login(username, self.address[0], self.address[1])
			self.clear_terminal()
			self.kill_socket_immediately = False
			self.send(f" Welcome, {username}!")
			time.sleep(2)
			self.clear_terminal()
			log("User logged into their account successfully", username, self.ip)
			connected_clients.append([self.session_id, username, self.ip, self.sock])
			self.main_loop(username)
			connected_clients.remove([self.session_id, username, self.ip, self.sock])
			self.kill_socket_immediately = True
		else:
			self.send(LOGIN_FAILED)
			time.sleep(2)

		log("Connection was aborted properly", username, self.ip)
		self.clear_terminal()
		self.kill_connection()

	def main_loop(self, username):
		self.command_history = []
		permissions_level = PermissionsLevel.NORMAL if not username == "root" else PermissionsLevel.ROOT

		command_functions = {}

		def command(description, names, permissions_level=PermissionsLevel.NORMAL):
			def command_func_inner(func):
				for name in names:
					command_functions[name] = (func, description, permissions_level)
			return command_func_inner

		@command("Clear the terminal window", ["clear", "cls", "c"])
		def _clear():
			self.clear_terminal()

		@command("Add a new user to the system", ["adduser", "useradd", "newuser"], PermissionsLevel.ROOT)
		def _adduser():
			new_username = self.prompt("\r Username: ")
			new_password = self.prompt("\r Password: ")
			if self.database.user_exists(new_username):
				self.send(" That username is already in use.\r\n")
			else:
				self.database.add_new_user(new_username, new_password)
				self.send(" New user created successfully!\r\n")

		@command("Delete an existing user from the system", ["removeuser", "userremove", "remove", "deluser"], PermissionsLevel.ROOT)
		def _removeuser():
			target_username = self.prompt("\r Username: ")
			if self.database.user_exists(target_username):
				if target_username == "root":
					self.send(" You cannot delete the root user. To regenerate the password for root, use the command 'rootpassword'.\r\n")
				else:
					self.database.remove_user(target_username)
					self.send(" Removed user successfully!\r\n")
			else:
				self.send(" That user does not exist.\r\n")

		@command("Regenerate the password for the root account", ["rootpassword", "rootpass", "rootregen"], PermissionsLevel.ROOT)
		def _rootpassword():
			try:
				confirmation = self.yes_no_prompt(" Are you sure you want to do this? You will be logged out and have to retrieve the new password from logs/root_passwords.log (Y/N): ")
				if confirmation:
					self.database.regenerate_root_password()
					return CommandReturnAction.BREAK
			except:
				self.send(" Please give either 'y' or 'n' as a choice.\r\n")

		@command("Change the password of a user", ["updatepassword", "userpassword"], PermissionsLevel.ROOT)
		def _updatepassword():
			target_username = self.prompt("\r Username: ")
			new_password = self.prompt("\r Password: ")
			c_new_password = self.prompt("\r Confirm Password: ")
			if self.database.user_exists(target_username):
				if not new_password == c_new_password:
					self.send(" Passwords do not match, please try again.\r\n")
				else:
					if target_username == "root":
						self.send(" You cannot update the root password. Please regenerate it using 'rootpassword'.\r\n")
					else:
						self.database.set_user_password(target_username, new_password)
						self.send(" Password updated successfully.\r\n")
			else:
				self.send(" That user does not exist.\r\n")

		@command("Log out of your current session", ["logout", "exit", "disconnect", "dc"])
		def _logout():
			return CommandReturnAction.BREAK

		# ----- START OF CUSTOM COMMANDS ----- #





		# -----  END OF CUSTOM COMMANDS  ----- #

		while True:
			title = TERMINAL_TITLE_BAR.replace("$user", username).replace("$ip", self.ip).replace("$sid", str(self.session_id))
			self.send(f'\x1b]0;{title}\x07 [{username}@{self.ip}] > ')

			command_parts, self.command_history = self.get_input(self.command_history, [n for n in command_functions.keys()], return_updated_history=True)
			self.command_history.insert(0, command_parts)
			log(f"Command dispatched: {command_parts}", username, self.ip)
			log_to_file(f"Command dispatched by '{username}': {command_parts}", "commands.log")
			command_parts = command_parts.split(" ")
			command_item = command_parts[0].lower()

			done_executing = False
			action = None

			for name, data in command_functions.items():
				if done_executing:
					break
				if name == command_item:
					func, description, required_permissions_level = data
					if required_permissions_level == PermissionsLevel.ROOT and not permissions_level == PermissionsLevel.ROOT:
						self.send(COMMAND_PROHIBITED.replace("$command", name))
					else:
						try:
							action = func()
						except Exception as e:
							log(f"Non-fatal error in Client Thread: {type(e).__name__}", username, self.ip, type=LogType.WARNING)
							for line in traceback.format_exc().strip().split("\n"):
								log(line, username, self.ip, type=LogType.WARNING)
							self.send(COMMAND_FAILED)
					done_executing = True
			
			if action == CommandReturnAction.BREAK:
				break
			if not done_executing:
				self.send(COMMAND_UNKNOWN.replace("$command", command_item))

	def yes_no_prompt(self, prompt_text):
		self.send(prompt_text)
		resp = self.get_input(["y", "n"], ["y", "n"], empty_response_allowed=True).lower()
		if resp == "y" or resp == "yes":
			return True
		elif resp == "n" or resp == "no":
			return False
		else:
			raise Exception()

	def prompt(self, prompt_text, auto_complete_options=None):
		self.send(prompt_text)
		return self.get_input([], auto_complete_options if not auto_complete_options == None else [], empty_response_allowed=True)

	def get_input(self, scroll_history, auto_complete_options, return_updated_history=False, empty_response_allowed=False):
		username = "Nog Logged In" if not self.database else self.database.user
		try:
			char_pos, history_pos = 0, 0
			currently_viewing_autocomplete, currently_showing_autocomplete_preview, = False, False
			auto_complete_index, auto_complete_start_buf = 0, ""
			# Scroll history is the list of editable lines, and we always insert a new blank line at the front
			scroll_history.insert(0, "")
			while not scroll_history[history_pos].endswith("\r"):

				def check_and_clear_invalid_characters(showing_autocomplete_preview):
					if showing_autocomplete_preview:
						showing_autocomplete_preview = False
						self.chan.send("\x1b[0K")
					if buffer_len > 0:
						self.chan.send(f"\x1b[{buffer_len}D\x1b[0K")
					return showing_autocomplete_preview

				# \/\/\/ Start pre-character rendering portion \/\/\/
				buffer_len = len(scroll_history[history_pos])
				# If we are showing more than one letter of the first word of an input
				if buffer_len > 0 and len(scroll_history[history_pos].split(" ")) == 1:
					preview_autocomplete_options = self.get_matching_autocomplete_options(scroll_history[history_pos], auto_complete_options)
					# If there is a valid item to show, render it. Do not render if the user's input perfectly matches the first command
					if len(preview_autocomplete_options) > 0 and not preview_autocomplete_options[0] == scroll_history[history_pos]:
						currently_showing_autocomplete_preview = True
						option_to_display = preview_autocomplete_options[0][len(scroll_history[history_pos]):]
						self.chan.send(f"\x1b[0K\x1b[90m{option_to_display}\x1b[0m\x1b[{len(option_to_display)}D")
					# If there is a perfect match or the command no longer matches any option
					elif currently_showing_autocomplete_preview:
						currently_showing_autocomplete_preview = False
						self.chan.send("\x1b[0K")
				# If the user deletes everything, disable previewing
				elif currently_showing_autocomplete_preview:
					currently_showing_autocomplete_preview = False
				# Only clear the line of no previews are being shown
				if not currently_showing_autocomplete_preview:
					self.chan.send("\x1b[0K")
				# /\/\/\ End of the pre-character rendering portion /\/\/\

				# Recieve the current character from the buffer
				char = self.chan.recv(1024)
				if char in [b"\x03", b"\x1a"]:
					self.clear_terminal()
					raise ModuleNotFoundError("This is here to close the connection.")

				# Backspace
				elif char == b"\x7f":
					# Backspace turns off autocomplete
					currently_viewing_autocomplete = False
					# Take away a character from the current line and clear it in the terminal
					if char_pos > 0:
						scroll_history[history_pos] = scroll_history[history_pos][:-1]
						self.chan.send("\x1b[1D \x1b[1D")
						char_pos -= 1
					continue

				# Tab
				elif char == b"\t":
					# If we are not showing autocomplete
					if not currently_viewing_autocomplete:
						currently_viewing_autocomplete = True
						auto_complete_start_buf = scroll_history[history_pos]
						auto_complete_index = -1
					# Get a list of all of the options for matches of the currently selected buffer
					valid_auto_complete_options = self.get_matching_autocomplete_options(auto_complete_start_buf, auto_complete_options)
					# Move through the list of valid options infinitely (increment by 1 or reset to 0)
					auto_complete_index = auto_complete_index + 1 if not auto_complete_index + 1 == len(valid_auto_complete_options) else 0
					selected_word = valid_auto_complete_options[auto_complete_index][len(auto_complete_start_buf):]
					# The place that we need to delete characters to (If the user gives 'sev' and we want to autocomplete to 'seventeen',
					# we keep track of 'sev' in `auto_complete_start_buf` and then to move on to the next autocomplete suggestion, we delete
					# everything after 'sev'.)
					chars_to_remove = buffer_len - len(auto_complete_start_buf)
					if chars_to_remove > 0:
						self.chan.send(f"\x1b[{chars_to_remove}D\x1b[0K")
					self.chan.send(selected_word)
					# Edit the current line and set the character position to the end of the current autocomplete word
					scroll_history[history_pos] = auto_complete_start_buf + selected_word
					char_pos = len(scroll_history[history_pos])
					continue

				# Up Arrow
				elif char == b"\x1b[A":
					# If we can move to the next item in the history list
					if len(scroll_history) > history_pos + 1:   
						currently_showing_autocomplete_preview = check_and_clear_invalid_characters(currently_showing_autocomplete_preview)
						# Move forward in the history, set the character position, and send the history item
						history_pos += 1
						char_pos = len(scroll_history[history_pos])
						self.chan.send(scroll_history[history_pos])

				# Down Arrow
				elif (char == b"\x1b[B" or char == b"\x1b"):
					# If we are not at the very first item
					if not history_pos == 0:
						currently_showing_autocomplete_preview = check_and_clear_invalid_characters(currently_showing_autocomplete_preview)
						# Move backwards in the history. If escape is pressed when you are at a non-zero history
						# index, return to the very first item.
						history_pos -= history_pos if char == b"\x1b" else 1
						char_pos = len(scroll_history[history_pos])
						self.chan.send(scroll_history[history_pos])
					elif char == b"\x1b":
						currently_showing_autocomplete_preview = check_and_clear_invalid_characters(currently_showing_autocomplete_preview)
						# Since we are already at index 0, make the line blank
						scroll_history[0] = ""
						history_pos = 0
						char_pos = 0

				if b"\x1b" in char or char == b"\n":
					# All escape characters of any kind end autocomplete and are also not buffered
					currently_viewing_autocomplete = False
					continue

				currently_viewing_autocomplete = False
				# Clear autocomplete preview when the user presses enter
				if char == b"\r" and currently_showing_autocomplete_preview:
					self.chan.send("\x1b[0K")
				# Do not add the character if the user is pressing enter with a blank input
				if char == b"\r" and len(scroll_history[history_pos]) == 0:
					if not empty_response_allowed:
						continue

				self.chan.send(char)
				scroll_history[history_pos] += char.decode(ENCODING)
				# Add the length of the character
				char_pos += len(char)
				
			# Take away the '\r' and clean everything up
			scroll_history[history_pos] = scroll_history[history_pos][:-1]
			self.chan.send("\r\n")
			user_input = scroll_history[history_pos].strip("\r\n")
			return (user_input, scroll_history[1:]) if return_updated_history else user_input
		except:
			if DEBUG_RAISE_ERRORS:
				raise
			if not self.kill_socket_immediately:
				log("Recieved invalid data, removing the user from 'connected_clients' and aborting connection", username, self.ip, type=LogType.WARNING)
				self.abort_connection()
			else:
				log("Recieved invalid data, aborting connection", username, self.ip, type=LogType.WARNING)
				self.kill_connection()

	def send(self, message):
		username = "Not Logged In" if not self.database else self.database.user
		try:
			for index, line in enumerate(message.replace("\n", "\r\n").split("\n")):
				self.chan.send(line) if index == 0 else self.chan.send("\n" + line)
		except:
			if DEBUG_RAISE_ERRORS: 
				raise
			if not self.kill_socket_immediately:
				log("Failed to send data, removing the user from 'connected_clients' and aborting connection", username, self.ip, type=LogType.WARNING)
				self.abort_connection()
			else:
				log("Failed to send data, aborting connection", username, self.ip, type=LogType.WARNING)
				self.kill_connection()

	def clear_terminal(self):
		self.send("\033c\033[3J\033[0m")
	
	def get_matching_autocomplete_options(self, current_buffer, options):
		matches = []
		for option in options:
			if option.find(current_buffer) == 0:
				matches.append(option)
		return matches

	def abort_connection(self):
		connected_clients.remove([self.session_id, self.database.user, self.ip, self.sock])
		self.kill_connection()

	def kill_connection(self):
		try:
			self.transport.close()
			self.sock.close()
		except:
			pass
		sys.exit()

def main():
	check_and_create_files()

	log("Loading SSH Host Key")
	if not os.path.exists("keys/private.key"):
		log("No SSH Host Key file was found, regenerated file at keys/private.key", type=LogType.WARNING)
		open("keys/private.key", "a+").close()
	global HOST_KEY
	try:
		HOST_KEY = paramiko.RSAKey(filename="keys/private.key")
	except:
		log("Your SSH Host Key is invalid, please add a valid key to keys/private.key", type=LogType.ERROR)
		log("You can regenerate one (On MacOS and Linux) using: [ssh-keygen -t rsa -m PEM -f keys/private.key]")
		raise KeyboardInterrupt

	# ----- START OF CUSTOM INITIALIZATION CODE ----- #





	# -----  END OF CUSTOM INITIALIZATION CODE  ----- #

	log(f"Server initialization completed in {round(time.perf_counter() - start_time, 3)} seconds")
	log("Listening for connections from clients")
	while True:
		sock, addr = s.accept()
		global session_id
		db_access_lock.acquire()
		log(f"Accepted a connection from {addr[0]}:{addr[1]}, starting new server thread with Session ID {session_id}")
		session_id += 1
		local_session_id = session_id
		db_access_lock.release()
		try:
			SSHControlPanelClient(sock, addr, local_session_id - 1).start()
		except:
			if DEBUG_RAISE_ERRORS:
				raise

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("\033[F")
		log("Interrupt detected, shutting down program")
		connection.close()
		log("Closed SSH listener connection")
		log(f"Shutting down server after {format_seconds_to_time(round(time.perf_counter() - start_time))}")