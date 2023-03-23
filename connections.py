import html5lib
from requests import get as get_request
from urllib.parse import quote as make_string_url_safe


BASE_URL = "http://www.cp.sk/{connection_type}/spojenie/vysledky/?f={station_from}&t={station_to}&direct=true"

TRAIN = "vlak"
BUS = "bus"
TRAINBUS = "vlakbus"
NODELAY = "No delay"


def save_html(content):
	'''used to save the retrieved connection html page to a file called \'transport.html\''''

	with open("transport.html", "wb") as file:
		file.write(content)


def read_saved_html():
	'''read_saved_html() -> bytes'''

	content = ""
	with open("transport.html", "rb") as file:
		content = file.read()
	return content


def grab_connection(station_from, station_to, connection_type=TRAINBUS):
	'''grab_connection(station_from, station_to [, connection_type='vlakbus']) -> bytes

	returns content of html page for the given connection from the cp website for further parsing
	args:
		station_from	(str)		name of the departure station*
		station_to  	(str)		name of the arrival station*
		connection_type (str-opt)	type of connection (bus, train, both; default = both)

		(*) names of stations should exactly match the ones on official website'''
	
	if station_from == station_to:
		raise StationsSame("departure station cannot be same as arrival station")
		
	connection_url = BASE_URL.format(
		connection_type=make_string_url_safe(connection_type),
		station_from=make_string_url_safe(station_from),
		station_to=make_string_url_safe(station_to)
	)

	content = b""
	with get_request(connection_url) as response:
		content = response.content
	
	return content


def parse_html_to_connections(html_content):
	'''parse_html_to_connections(html_content) -> [Connection, Connection, Connection]

	parse content of html page to list of connection objects'''

	tree = html5lib.parse(html_content)
	connection_list = []

	for element in tree.iter():
		e_class = element.get("class", "")
		
		if e_class != "connection-list":
			continue
		
		for child_element in element:
			child_id = child_element.get("id", "")
			
			if "connectionBox" in child_id:
				connection = Connection(
					child_element)
				connection_list.append(connection)
		
		break
	
	return connection_list



class Connection:
	
	def __init__(self, html_element):
		conn_head = html_element[0][0][1]
		self.data_share_url = html_element.get(
			"data-share-url")
		
		reset_date = conn_head[0]
		self.dep_time = reset_date.text
		self.dep_date = reset_date[0].text
		
		reset_total = conn_head[1]
		self.time_total = reset_total[0].text
		self.distance = reset_total[1].text
		
		conn_details = html_element[1][0][0]
		
		title_container = conn_details[0][0][0]
		title = title_container[1]
		self.title = title.attrib["title"]
		self.id = title[0].text
		specs = title_container[2]
		
		if specs.get("class") == "line-right-part reset":
			self.owner = specs[0][0].text
		else:
			self.owner = title_container[3][0][0].text
		
		delay_bubble = conn_details[1]
		
		if len(delay_bubble) != 0:
			self.delay = delay_bubble[0].text
		else:
			self.delay = delay_bubble.text
		
		self.delay = self.delay.strip()
		
		if self.delay.isspace():
			self.delay = None
		
		track = conn_details[2]
		_from = track[0]
		_to = track[1]
		self.depTime = _from[0].text
		self.arrTime = _to[0].text
		_from_st = _from[1]
		_to_st = _to[1]
		
		self.depSt = None
		self.depPlatform = None
		self.depReq = None
		self.arrSt = None
		self.arrPlatform = None
		self.arrReq = None
		
		for element in _from_st.iter():
			el_class = element.get("class")
			el_title = element.get("title")
			
			el_class = el_class.strip() if el_class else None
			
			if el_class == "name":
				self.depSt = element.text
			elif el_title == "nástupište":
				self.depPlatform = element.text
			elif el_title == "na znamenie":
				self.depReq = element.text
		
		for element in _to_st.iter():
			el_class = element.get("class")
			el_title = element.get("title")
			
			el_class = el_class.strip() if el_class else None
			
			if el_class == "name":
				self.arrSt = element.text
			elif el_title == "nástupište":
				self.arrPlatform = element.text
			elif el_title == "na znamenie":
				self.arrReq = element.text
	
	def __str__(self):
		return f'''{self.id}
{self.title}
{self.owner}
{self.dep_date} - {self.dep_time}
{self.time_total}
{self.distance}
{self.delay if self.delay else NODELAY}
{self.depTime} - {self.depSt}
{self.arrTime} - {self.arrSt}
'''
	
	@property
	def html(self):
		return f'''
<!DOCTYPE html>
<html>

<head>
<meta charset="utf-8" />
<style>
{
"""
body {
	font-size: 50px;
	color: black;
	background-color: white;
}
"""
}
</style>
</head>

<body>
<h3>
<a href="{self.data_share_url}">{self.id}</a>
</h3>
<p style="font-size:50px;">
{self.title} <br>
{self.owner} <br>
{self.dep_date} - {self.dep_time} <br>
{self.time_total} <br>
{self.distance} <br>
{self.delay if self.delay else NODELAY} <br>
{self.depTime} - {self.depSt} - {self.depPlatform} <br>
{self.arrTime} - {self.arrSt} - {self.arrPlatform} <br>
</p>
</body>

</html>
'''
			
	def print(self):
		print(self.id)
		print(self.title)
		print(self.owner)
		print(self.dep_date, '-', self.dep_time)
		print(f"Duration: {self.time_total}")
		print(f"Distance: {self.distance}")
		
		print(f"Delay: {self.delay if self.delay else NODELAY}")
		if self.depSt:
			print(
				f"{self.depTime} - {self.depSt}",
				end=""
			)
		else:
			print(f"{self.depTime}", end="")
		
		if self.depPlatform:
			print(f" - {self.depPlatform}", end="")
		if self.depReq:
			print(f" - {self.depReq}", end="")
		print()
		
		if self.arrSt:
			print(
				f"{self.arrTime} - {self.arrSt}",
				end=""
			)
		else:
			print(f"{self.arrTime}", end="")
		
		if self.depPlatform:
			print(f" - {self.arrPlatform}", end="")
		if self.depReq:
			print(f" - {self.arrReq}", end="")
		print()


class StationsSame (Exception):

	def __init__(self, *args, **kwargs):
		super().__init__(self, *args, **kwargs)


if __name__ == "__main__":
	pass