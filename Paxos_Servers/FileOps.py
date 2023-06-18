import dill


def write_to_file(data):
	try :
		with open("log","wb+") as file:
			dill.dump(data,file)

	except Exception as e:
		print("error in writing to log file",e)


def read_from_file():
	server_info = None
	try:
		with open("log","rb") as file:
			server_info = dill.load(file)

	except Exception as e:
		print("error in reading from log file ", e)
		return server_info

	return server_info


# Dummy operation to write incoming data to a file
def write_to_file_dummy(data):
	try:
		f = open("test.txt", "a")
		f.write(str(data))
		print("Write Successful")
	except Exception as e:
		print("Error in writing dummy data to file: {0}".format(e))
