def train_text_test_fix(train_file = 'train_proc.txt', valid_file = 'train_ready.txt', test_file = 'valid_ready.txt'):



	file_object = open(train_file)

	try:
		file_context = file_object.read()
	finally:
		file_object.close()

	file_context = file_context.split("\n")

	print("len of the file_context is ", len(file_context))

	for i, single_line in enumerate(file_context):
#		if (0 == (i % 1000)):
#			print(i)
		if ("" == single_line):
			print("train file ### line ", i + 1, " is dummy ###")


	file_object = open(valid_file)

	try:
		file_context = file_object.read()
	finally:
		file_object.close()

	file_context = file_context.split("\n")

	print("len of the file_context is ", len(file_context))

	for i, single_line in enumerate(file_context):
#		if (0 == (i % 1000)):
#			print(i)
		if ("" == single_line):
			print("valid file ### line ", i + 1, " is dummy ###")

	file_object = open(test_file)

	try:
		file_context = file_object.read()
	finally:
		file_object.close()

	file_context = file_context.split("\n")

	print("len of the file_context is ", len(file_context))

	for i, single_line in enumerate(file_context):
#		if (0 == (i % 1000)):
#			print(i)
		if ("" == single_line):
			print("origi file ### line ", i + 1, " is dummy ###")



if __name__ == "__main__":
	
	train_text_test_fix(train_file = '/home/super-speed-data/train-data-yolov3/20181009/train_ready.txt', 
					 valid_file = '/home/super-speed-data/train-data-yolov3/20181009/valid_ready.txt', 
					 test_file = '/home/super-speed-data/train-data-yolov3/20181009/train_proc.txt')
