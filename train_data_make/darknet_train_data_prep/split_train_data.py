import random

def split_train_data(origin_file = 'train_proc.txt', train_target_file = 'train_ready.txt', valid_target_file = 'valid_ready.txt'):

	ratio = 0.05

	file_object = open(origin_file)

	try:
		file_context = file_object.read()
	finally:
		file_object.close()

	file_context = file_context.split("\n")

	random.shuffle(file_context)
	random.shuffle(file_context)
	random.shuffle(file_context)

	total_num = len(file_context)
	valid_num = int(total_num * ratio)
	train_num = total_num - valid_num


	train_file_object = open(train_target_file,'w')
	for i, single_line in enumerate(file_context[valid_num:]):
		if ((i % 10000) == 0):
			print(i)
		if ("" == single_line):
			print("train file ### line ", i + 1, " is dummy ###")
		if ("" != single_line):
			train_file_object.write(single_line + '\n')
	train_file_object.close()

	valid_file_object = open(valid_target_file,'w')
	for i, single_line in enumerate(file_context[:valid_num]):
		if ((i % 10000) == 0):
			print(i)
		if ("" == single_line):
			print("valid file ### line ", i + 1, " is dummy ###")
		if ("" != single_line):
			valid_file_object.write(single_line + '\n')
	valid_file_object.close()

if __name__ == "__main__":
	

	split_train_data(origin_file =  '/home/nvme/train-data-yolov3/20181029/train.txt', 
					 train_target_file = '/home/nvme/train-data-yolov3/20181029/train_ready.txt', 
					 valid_target_file = '/home/nvme/train-data-yolov3/20181029/valid_ready.txt')
