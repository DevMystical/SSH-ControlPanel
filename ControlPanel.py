import os, datetime, socket, sqlite3, threading, hashlib, paramiko, traceback

# Please carefully go through README.md to ensure that each feature is
# properly and effecitvely used.

# TODO command line arguments/config file
DEBUG_RAISE_ERRORS  = False
DATABASE_LOCATION   = "database/Data.db"

SSH_PORT		    = 7000
MAXIMUM_CONNECTIONS = 50






database_schemas = {
	"users": "CREATE TABLE users (username VARCHAR(255), password VARCHAR(255))"
}
needed_folders = []

# END OF CONFIG

class LogType:
	INFO	= "\033[0m", 		  "INFO"
	WARNING = "\033[1;38;5;220m", "WARNING"
	ERROR   = "\033[1;38;5;160m", "ERROR"

def log(message, user=None, ip=None, type=LogType.INFO):
	current_time = datetime.now().strftime("\033[0m(%I:%M:%S %p - %m/%d/%Y) ")
	if user == None or ip == None:
		print(c_time + f"[ {type[0] + type[1]}\033[0m - " + type[0] + user + "@" + ip + "\033[0m ] [" + type[0] + message + "\033[0m]")
	else:
		print(c_time + f"[ {type[0] + type[1]}\033[0m ] [" + type[0] + message + "\033[0m]")

os.system("cls" if os.name == "nt" else "clear")

if DEBUG_RAISE_ERRORS:
	log("!!! Working in development mode, raising errors when they come up !!!", type=LogType.WARNING)
	log("!!!		> Do not use this in a production environment. <	   !!!", type=LogType.WARNING)

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
	if item == None:
		return "N/A"
	else:
		return str(item)

def format_seconds_to_time(time_int):
	m, s = divmod(time_int, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	return f"{d:d}d {h:d}h {m:d}m {s:d}s"

class CommandReturnAction:
	BREAK = 0

class CommandUsageError(Exception): pass

class SSHPanelDatabase:

	def __init__(self, user):
		self.user = user

	@database_access()
	def check_login_credentials(self, username, password):
		result = cursor.execute("SELECT password FROM users WHERE username=?", (username,)).fetchone()
		if not result or not result[0] == create_password_hash(password):
			return False
		return True

	# ----- START DATABASE FUNCTIONS ----- #



	# -----  END DATABASE FUNCTIONS  ----- #

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
				self.send("\r\n You have been disconnected due to a fatal error. We apologize for any inconvenience.\r\n")
			if self.kill_socket_immediately:
				self.kill_connection()
			else:
				self.abort_connection()

	def process_ssh_client(self):
		self.transport = paramiko.Transport(self.sock)
		self.transport.add_server_key(HOST_KEY)
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