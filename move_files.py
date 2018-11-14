import os
import shutil

src_path = "/home/nvme/train-data-xception-pre/20181029/train"
dst_path = "/home/nvme/train-data-xception-pre/20181103/abnormal"
target_file_type = "jpg"

files = os.listdir(src_path)

for file in files:
	file_type = file.split(".")[-1]
	if (target_file_type == file_type):
		src_file_path = os.path.join(src_path, file)
		shutil.copy(src_file_path, dst_path)
