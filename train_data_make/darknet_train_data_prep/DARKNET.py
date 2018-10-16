import os
from cell_slicing_tif import cut_cells
from rotate import do_rotate
from flip import do_flip
from select_separate import split_test_from_train, split_valid_from_train
from generate_txt import gen_txt
from datetime import datetime
from multiprocessing import cpu_count
#from split_train_data import *
import time
from utils import *


def process(xml_dict, tiff_dict, path_out):
    """prepare training data for darknet
    :params path_in: the directory storing kfb/tif, the tree view of path_in should be:
                     path_in:
                        sub_dir1:
                            xxxx.kfb
    :params path_out: resulting training data should include three folders: train/valid/test, and three corresponding txts
    """

    start_ = datetime.utcnow()  
      
    # cut from kfb/tif to 608 sized jpgs/xmls
    print("#INFO# " ,"start cut cell")
    cut_cells(xml_dict, tiff_dict, path_out, size=608)
    print("#INFO# " ,"end cut cell")

    cells_end_ = datetime.utcnow()

    # do augmentation: rotate
    #do_rotate(path_train)

    # do augmentation: flip
    do_flip(path_out)

    enhance_end_ = datetime.utcnow()

    # select from train folder to valid/test folder
    #split_test_from_train(path_train, factor=0.1)
    #split_valid_from_train(path_train, factor=0.1)

    # generate txt files
    gen_txt(path_out)

    txt_end_ = datetime.utcnow()

    print("all cost time: ", (txt_end_ - start_).seconds)
    print("cell cut cost time: ", (cells_end_ - start_).seconds)
    print("enhance cost time: ", (enhance_end_ - cells_end_).seconds)
    print("txt gen cost time: ", (txt_end_ - enhance_end_).seconds)


if __name__ == "__main__":
    # path_in = "/home/data_samba/DATA/checked_cells/manual_labelled_checked/label_kfb_tif/label_data"
    # path_out = "/home/data_samba/TRAIN_DATA/4yolov3/20180929"

    xml_files_path = '/home/cnn/Development/code/seeit_building_blocks/data/xml'
    tiff_files_path = '/home/cnn/Development/code/seeit_building_blocks/data/tiff'

    xml_dict = generate_name_path_dict(xml_files_path)
    tiff_dict = generate_name_path_dict(tiff_files_path)

    path_out = "/home/cnn/Development/data/tmp"

    process(xml_dict, tiff_dict, path_out)

    # split_train_data(origin_file = path_out + '/' + 'train.txt', 
    #                  train_target_file = path_out + '/' + 'train_ready.txt', 
    #                  valid_target_file = path_out + '/' + 'valid_ready.txt')