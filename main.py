'''10.01.2022 - 23.03.2023'''

from connections import *
from stations import STATIONS


def main():
	response_content = grab_connection(
		STATIONS["BA hl.st."],
		STATIONS["Miloslavov"],
		TRAIN
	)
	
	connections = parse_html_to_connections(response_content)
	
	if not connections:
		print("No connections found.")
		return 
	
	for conn in connections:
		conn.print()
		print()


if __name__ == "__main__":
	main()
