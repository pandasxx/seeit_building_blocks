# coding=utf-8
import os
import openslide
import scipy.misc
import xml.dom.minidom

from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
from tslide.tslide import TSlide

from datetime import datetime

from gen_xml import Xml

from utils import *


def scan_files(directory, prefix=None, postfix=None):
    files_list = []
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))
    return files_list


# classes = {"#000000": "MC", "#aa0000": "HSIL", "#aa007f": "ASCH", "#aa00ff": "SC", "#ff0000": "RC",
#           "#005500": "LSIL", "#00557f": "ASCUS", "#0055ff": "SCC", "#aa5500": "GEC", "#aa557f": "ADC",
#           "#aa55ff": "EC", "#ff5500": "AGC1", "#ff557f": "AGC2", "#ff55ff": "AGC3", "#00aa00": "FUNGI",
#           "#00aa7f": "TRI", "#00aaff": "CC", "#55aa00": "ACTINO", "#55aa7f": "VIRUS"}
#classes = {"#aa0000": "HSIL", "#aa007f": "ASCH",
#          "#005500": "LSIL", "#00557f": "ASCUS", "#0055ff": "SCC", "#aa557f": "ADC",
#          "#aa55ff": "EC", "#ff5500": "AGC1", "#ff557f": "AGC2", "#ff55ff": "AGC3", "#00aa00": "FUNGI",
#          "#00aa7f": "TRI", "#00aaff": "CC", "#55aa00": "ACTINO", "#55aa7f": "VIRUS"}

classes = {"#aa0000": "HSIL", "#aa007f": "ASCH",
          "#005500": "LSIL", "#00557f": "ASCUS", "#0055ff": "SCC",
          "#aa55ff": "EC", "#ff5500": "AGC", "#00aa00": "FUNGI",
          "#00aa7f": "TRI", "#00aaff": "CC", "#55aa00": "ACTINO", "#55aa7f": "VIRUS"}

# get coordinates of labels in a xml
def get_labels(xml_file):
    """
        xml_file: single xml file for tif
        return: {i:(x_min, x_max, y_min, y_max, color)}
    """
    DOMTree = xml.dom.minidom.parse(xml_file)
    collection = DOMTree.documentElement
    annotations = collection.getElementsByTagName("Annotation")

    labels = {}
    i = 0
    for annotation in annotations:
        if annotation.getAttribute("Color") in classes:
            coordinates = annotation.getElementsByTagName("Coordinate")
            x_coords = []
            y_coords = []
            for coordinate in coordinates:
                x_coords.append(float(coordinate.getAttribute("X")))
                y_coords.append(float(coordinate.getAttribute("Y")))                    
            x_min = int(min(x_coords))
            x_max = int(max(x_coords))
            y_min = int(min(y_coords))
            y_max = int(max(y_coords))
            labels[i] = (x_min, x_max, y_min, y_max, classes[annotation.getAttribute("Color")])
            i += 1
    return labels

# get windows in tif that contain labels
def get_windows(labels, size_x, size_y, size):
    """
        labels: {i:(x_min, x_max, y_min, y_max, color)}
        size_x, size_y: dimensions of 0th layer of tif
        size: image size to crop
        return: {(x, y):[i,]}
    """
    points_xy = {}
    x, y = 0, 0
    while x + size <= size_x:
        while y + size <= size_y:
            for i, label in labels.items():
                if (x <= label[0] and label[1] <= x+size and y <= label[2] and label[3] <= y+size) or \
                   ((label[0] <= x and x+size <= label[1]) and (label[2] <= y and y+size <= label[3])) or \
                   ((label[0] <= x and x+size <= label[1]) and (y <= label[2] and label[3] <= y+size)) or \
                   ((x <= label[0] and label[1] <= x+size) and (label[2] <= y and y+size <= label[3])):
                    if (x, y) in points_xy:
                        points_xy[(x, y)].append(i)
                    else:
                        points_xy[(x, y)] = [i,]
            y += 200
        y = 0
        x += 200
    
    # remove duplicates
    points_xy_new = {}
    for key, value in points_xy.items():
        if value not in points_xy_new.values():
            points_xy_new[key] = value  
    # remove subsets
    points_xy_copy = {key:value for key,value in points_xy_new.items()}
    to_delete = []
    for key2, value2 in points_xy_copy.items():
        for key, value in points_xy_new.items():
            if key != key2 and set(value).issubset(set(value2)):
                to_delete.append(key)
    for key in to_delete:
        if key in points_xy_new:
            points_xy_new.pop(key)
    
    return points_xy_new

# get windows in tif that contain labels
def get_windows_new(labels, size_x, size_y, size, tiff_path):
    """
        labels: {i:(x_min, x_max, y_min, y_max, color)}
        size_x, size_y: dimensions of 0th layer of tif
        size: image size to crop
        return: {(x, y):[i,]}
    """
    graphs_xy = []

#       p0   p1   p2        # graph0_pointxy = p0.x         , p0.y
#       -------------       # graph1_pointxy = p1.x - 303   , p1.y
#       |           |       # graph2_pointxy = p2.x - 607   , p2.y
#       |           |       # graph3_pointxy = p3.x         , p3.y - 303
#    p3 |    p4   p5|       # graph4_pointxy = p4.x - 303   , p4.y - 303
#       |           |       # graph5_pointxy = p5.x - 607   , p5.y - 303
#       |           |       # graph6_pointxy = p6.x         , p6.y - 607
#       -------------       # graph7_pointxy = p7.x - 303   , p7.y - 607
#       p6   p7   p8        # graph8_pointxy = p8.x - 607   , p8.y - 607

# P0 = x_min, y_min
# p1 = (x_max - x_min)/2, ymin
# p2 = x_max, y_min
# p3 = x_min, (y_max - y_min)/2
# p4 = (x_max - x_min)/2, (y_max - y_min)/2
# p5 = x_max, (y_max - y_min)/2
# p6 = x_min, y_max
# p7 = (x_max - x_min)/2, y_max
# p8 = x_max, y_max

    big_count = 0
    small_count = 0

# 1 / 3 size of the small pic
    size_3 = int(size / 3) 
    size_2 = int(size / 2)
    size_1 = size

    for i, label in labels.items():

        x_min = label[0]
        x_max = label[1]
        y_min = label[2]
        y_max = label[3]

        label_max_size = max(x_max - x_min, y_max - y_min)
        label_size_x = x_max - x_min
        label_size_y = y_max - y_min


        p0 = (x_min,                            y_min)
        p1 = (int((x_max + x_min)/2),           y_min)
        p2 = (x_max,                            y_min)
        p3 = (x_min,                            int((y_max + y_min)/2))
        p4 = (int((x_max + x_min)/2),           int((y_max + y_min)/2))
        p5 = (x_max,                            int((y_max + y_min)/2))
        p6 = (x_min,                            y_max)
        p7 = (int((x_max + x_min)/2),           y_max)
        p8 = (x_max,                            y_max)

#        print(p0)
#        print(p1)
#        print(p2)
#        print(p3)
#        print(p4)
#        print(p5)
#        print(p6)
#        print(p7)
#        print(p8)

        # graph0 ~ 9

        # ok
        if ((label_size_x > size_3) and (label_size_y > size_3)):
            
            graphs_xy.append([x_min,                y_min])
            graphs_xy.append([p4[0] - size_2 + 1,   y_min])
            graphs_xy.append([x_max - size_1,       y_min])
            
            graphs_xy.append([x_min,                p4[1] - size_2])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - size_2])
            graphs_xy.append([x_max - size_1,       p4[1] - size_2])
            
            graphs_xy.append([x_min,                y_max - size_1])
            graphs_xy.append([p4[0] - size_2 + 1,   y_max - size_1])
            graphs_xy.append([x_max - size_1,       y_max - size_1])

        if ((label_size_x > size_3) and (label_size_y <= size_3)):
            graphs_xy.append([x_min,                p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int(size / 6)])
            graphs_xy.append([x_max - size_1,       p4[1] - int(size / 6)])

            graphs_xy.append([x_min,                p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int(size / 2)])
            graphs_xy.append([x_max - size_1,       p4[1] - int(size / 2)])
            
            graphs_xy.append([x_min,                p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - size_2 + 1,   p4[1] - int((size / 6) * 5)])
            graphs_xy.append([x_max - size_1,       p4[1] - int((size / 6) * 5)])
            
            big_count = big_count + 1

        if ((label_size_x <= size_3) and (label_size_y > size_3)):
            graphs_xy.append([p4[0] - int(size / 6),        y_min])
            graphs_xy.append([p4[0] - int(size / 2),        y_min])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  y_min])

            
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - size_2])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - size_2])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - size_2])
            
            graphs_xy.append([p4[0] - int(size / 6),        y_max - size_1])
            graphs_xy.append([p4[0] - int(size / 2),        y_max - size_1])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  y_max - size_1])
            
            big_count = big_count + 1

        if ((label_size_x <= size_3) and (label_size_y <= size_3)):
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int(size / 6)])
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int(size / 2)])
            graphs_xy.append([p4[0] - int(size / 6),        p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - int(size / 2),        p4[1] - int((size / 6) * 5)])
            graphs_xy.append([p4[0] - int((size / 6) * 5),  p4[1] - int((size / 6) * 5)])

            small_count = small_count + 1

#        print("### new generate windows ###")

#        print(graphs_xy)

#        print("### new generate windows ###")

    


    points_xy = {}
    x, y = 0, 0
    for xy in graphs_xy:
#        print(xy)
        x = xy[0]
        y = xy[1]

        for i, label in labels.items():
            if (x <= label[0] and label[1] <= x+size and y <= label[2] and label[3] <= y+size) or \
                ((label[0] <= x and x+size <= label[1]) and (label[2] <= y and y+size <= label[3])) or \
                ((label[0] <= x and x+size <= label[1]) and (y <= label[2] and label[3] <= y+size)) or \
                ((x <= label[0] and label[1] <= x+size) and (label[2] <= y and y+size <= label[3])):
                if (x, y) in points_xy:
                    points_xy[(x, y)].append(i)
                else:
                    points_xy[(x, y)] = [i,]

    print("################### tiff_path", tiff_path)
    print("################### big_count is ", big_count)
    print("################### small_count is ", small_count)

    print("################### graph num is ", len(graphs_xy))
    print("################### point num is ", len(points_xy))

#    print(x_min, " ", x_max, " ", y_min, " ", y_max)
#    print("###############################")
#    print(graphs_xy)
#    print("###############################")
#    for i in points_xy:
#        print(i)
    

    return points_xy



    
def cell_sampling(xml_file, tiff_path, save_path, size, scale):
    
#    print("#INFO# ", "start cp file")

    # copy remote file to local
#    local_xml_file = cp_originfile_from_remote(xml_file, path_temp)
#    xml_file = local_xml_file

#    print("#INFO# ", "end cp file")


    labels = get_labels(xml_file)

    # filename = os.path.splitext(xml_file)[0]
    # if (not os.path.isfile(filename+".tif")) and (not os.path.isfile(filename+".kfb")):
    #     print(filename + " doesn't exist")
    #     return

    print("PROCESSING %s ..." % tiff_path)

    try:
        try:
            slide = openslide.OpenSlide(tiff_path)
        except:
            slide = TSlide(tiff_path)
    except:
        print("ERROR #", "can not open pic ", tiff_path)
        exit()

    size_x, size_y = slide.dimensions
#    points_xy = get_windows(labels, size_x, size_y, size)
    # new gen method for cell base instead list all pic

    points_xy = get_windows_new(labels, size_x, size_y, size, tiff_path)
#    print("labels: ", labels)
#    print("points_xy: ", points_xy)
#    print("size_x: ", size_x, "   size_y:", size_y, "   size:", size)
    
    # generate jpg files
    # print(filename)
    points_num = len(points_xy)
    for i, (x, y) in enumerate(points_xy):
        if ((i % 100) == 0):
            print("# process # ", i, '/', points_num - 1, x, y, size, size)
        cell = slide.read_region((x, y), 0, (size, size)).convert("RGB")

        filename, _ = os.path.splitext(os.path.basename(tiff_path))
        image_file_name = save_path + "/" + filename + "_" + str(x) + "_" + str(y) + ".jpg"

# need scale pic from 1216 to 608
        
        cell = cell.resize((int(size * scale + 0.5), int(size * scale + 0.5)))
        cell.save(image_file_name)


        # print("#INFO# ", "get one region cost time is ", (end_get_region - start_get_region).microseconds)
        # print("#INFO# ", "save one region cost time is ", (end_save_region - end_get_region).microseconds)

    slide.close()

    # generate xml files
    new_xmls = Xml(os.path.basename(filename), save_path, points_xy, labels, size, scale)
    new_xmls.gen_xml()

    #end_one_big_pic = datetime.utcnow()

    print("INFO# ", "small pics num is ", i)

    # rm temp local file
#    rm_tempfile_from_local(local_xml_file, path_temp)

    print("INFO# ", "processed ", xml_file)

def cut_cells(xml_dict, tiff_dict, path_out, size, scale):
    if not os.path.exists(path_out):
        os.makedirs(path_out, exist_ok=True)


    executor = ProcessPoolExecutor(max_workers=cpu_count() - 4)
    # executor = ProcessPoolExecutor(1)
    tasks = []

    for key, xml_path in xml_dict.items():
        if key in tiff_dict:
            tiff_path = tiff_dict[key]
            tasks.append(executor.submit(cell_sampling, xml_path, tiff_path, path_out, size, scale))
        else:
            print("### ERROR ### %s IS NOT FOUND IN TIFF_DICT" % key)
        

    job_count = len(tasks)
    for future in as_completed(tasks):
        # result = future.result()  # get the returning result from calling fuction
        job_count -= 1
        print("One Job Done, last Job Count: %s" % (job_count))            



if __name__ == "__main__":
    # file_path = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/TRAIN_DATA_BIG/20181009"
    # save_path = "/home/super-speed-data/train-data-yolov3/20181009"

    pass

