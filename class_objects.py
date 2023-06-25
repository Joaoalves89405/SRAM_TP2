import itertools

class Stream(object):
	"""docstring for Stream"""
	""" This represents the metadata of a stream"""
	newtag = itertools.count(start=1, step=1 )
	def __init__(self, name, fps, max_delay, type_of_data, tag = next(newtag)):
		super(Stream, self).__init__()
		self.tag = tag
		self.name = name
		self.fps = fps
		self.max_delay = max_delay
		self.type_of_data = type_of_data
		
class Node(object):
	"""docstring for Node"""
	def __init__(self, tag, type, ip, state = False):
		super(Node, self).__init__()
		self.tag = tag
		self.type = type
		self.ip = ip
		self.neighbours_list = []
		self.state = state

	def add_neighbour(self, neighbour):
		self.neighbours_list.append(neighbour)
		
	def get_neighbours_list(self):
		return self.neighbours_list

	def activate(self):
		self.state = True
	def deactivate(self):
		self.state = False
	def is_active(self):
		return self.state

class Request(object):
	"""docstring for Request"""
	def __init__(self, request_id, stream_id, state, element, ttl = 0):
		super(Request, self).__init__()
		self.request_id = request_id
		self.stream_id = stream_id
		self.state = state
		self.element = element
		self.ttl = ttl

	def change_state(self, new_state):
		match new_state:
			case 'R':
				#new state is: Received
				self.state = "Received"
				return 0
			case 'S':
				#new state is: Sent
				self.state = "Sent"
				return 0
			case 'A':
				#new state is: Answered
				self.state = "Answered"
				return 0
			case 'C':
				#new state is: Confirmed
				self.state = "Confirmed"
				return 0
			case 'AR':
				#new state is: Active Retransmission
				self.state = "Active Retransmission"
				return 0
			case 'D':
				#new state is: Deleted
				self.state = "Deleted"
				return 0