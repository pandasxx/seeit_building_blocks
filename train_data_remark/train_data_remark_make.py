import os
import xml.dom.minidom
import xml.etree.ElementTree as ET
import shutil
from utils import *


def save_file(src_file_path, dst_file_path, cell_class):
	
	final_dst_file_path = dst_file_path + "/" + cell_class
	
	if not os.path.exists(final_dst_file_path):
		os.makedirs(final_dst_file_path)

	shutil.copy(src_file_path, final_dst_file_path)


def dispatch_files_according_cellclass(xml_file_dict, jpg_file_dict, remark_data_dir, cell_classes):

	err = 0
	count = 0

	cell_class = ""
	
	for file_name, xml_file_path in xml_file_dict.items():

		DOMTree = xml.dom.minidom.parse(xml_file_path)
		collection = DOMTree.documentElement
		objects = collection.getElementsByTagName("object")

		for object_list in objects:
			cell_class = object_list.getElementsByTagName('name')[0].childNodes[0].nodeValue.strip()

			if (cell_class in cell_classes):
				save_file(jpg_file_dict[file_name], remark_data_dir, cell_class)
				save_file(xml_file_dict[file_name], remark_data_dir, cell_class)
				# only match once
				break

		count = count + 1
		if ((count % 10000) == 0):
			print(count, "/", len(xml_file_dict), " files processed......")

	return err

def check_files(xml_file_dict, jpg_file_dict):

	err = 0

	for file_name, xml_file_path in xml_file_dict.items():

		if file_name not in jpg_file_dict:
			print("file_name not found in jpg file dict")	
			err = -1

	return err

if __name__ == "__main__":

	cell_classes = ["HSIL", "ASCH", "LSIL",  "ASCUS",  "SCC", "EC",  "AGC",  "FUNGI", "TRI", "CC", "ACTINO", "VIRUS"]

	raw_data_dir = "/home/super-speed-data/train-data-yolov3/remark-20181018/raw-data"
	remark_data_dir = "/home/super-speed-data/train-data-yolov3/remark-20181018/remark-data"

	# gen file name(without .*) and path dict
	xml_file_dict = generate_name_path_dict(raw_data_dir, ['.xml'])
	jpg_file_dict = generate_name_path_dict(raw_data_dir, ['.jpg'])

	# check if all xml and jpg are matched
	err = check_files(xml_file_dict, jpg_file_dict)

	if (err == 0):
		dispatch_files_according_cellclass(xml_file_dict, jpg_file_dict, remark_data_dir, cell_classes)
	else:
		print("files not match")