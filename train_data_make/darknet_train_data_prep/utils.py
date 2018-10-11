import shutil
import os


def cp_originfile_from_remote(xml_file, dst_dir):
	
#	print(xml_file)
#	print(dst_dir)
#	print(dst_dir + "/" + xml_file.split('/')[-1])
	shutil.copy(xml_file, dst_dir + "/" + xml_file.split('/')[-1])

	filename = os.path.splitext(xml_file)[0]
	if (os.path.isfile(filename + ".tif")):
		filename = filename + ".tif"
	if (os.path.isfile(filename + ".kfb")):
		filename = filename + ".kfb"

#	print(filename)
#	print(dst_dir)
#	print(dst_dir + "/" + filename.split('/')[-1])
	shutil.copy(filename, dst_dir + "/" + filename.split('/')[-1])

	return (dst_dir + "/" + xml_file.split('/')[-1])


def rm_tempfile_from_local(local_xml_file, path_temp):

	filename = os.path.splitext(local_xml_file)[0]
	local_pic_file = ''
	if (os.path.isfile(filename + ".tif")):
		local_pic_file = filename + ".tif"	
	if (os.path.isfile(filename + ".kfb")):
		local_pic_file = filename + ".kfb"

	try:
		os.remove(local_pic_file)
	except:
		print("#WARNING# ", "fail to rm ", local_pic_file)
	
	try:
		os.remove(local_xml_file)
	except:
		print("#WARNING# ", "fail to rm ", local_xml_file)