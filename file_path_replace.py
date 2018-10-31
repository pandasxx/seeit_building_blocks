#-*- coding:utf-8 -*-
from sys import argv



def do_replace_string(traintxt_file_path, proc_traintxt_file_path, replaced_string, replace_string):
	file_object = open(traintxt_file_path)

	print(traintxt_file_path)

	try:
		file_context = file_object.read()
	finally:
		file_object.close()

	file_contexts = file_context.split("\n")

	print(len(file_contexts))

	proc_file_object = open(proc_traintxt_file_path,'w')
	for i, single_line in enumerate(file_contexts):
		if ((i % 10000) == 0):
			print(i)
		if ("" == single_line):
			print("### line ", i + 1, " is dummy ###")
		if ("" != single_line):
			
			proc_single_line = single_line.replace(replaced_string, replace_string)

			proc_file_object.write(proc_single_line + '\n')
	proc_file_object.close()

if __name__ == "__main__":

	if (len(argv) == 5):
		do_replace_string(argv[1], argv[2], argv[3], argv[4])
	else:
		print("you should type in three args")
		print("#1 path of files_path.txt")
		print("#2 path of processed files_path.txt")
		print("#3 the string should be replaced")
		print("#4 the string you want to replace ")