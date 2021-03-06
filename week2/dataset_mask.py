import os
import cv2
import numpy as np
import detectron2
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.structures import BoxMode
from PIL import Image
import mots_utils

DATASET_PATH = 'C:/Users/servi/Desktop/Computer Vision Master/M5. Visual Recognition/Project/week2/KITTI-MOTS'
#DATASET_PATH = '/home/group07/M5-T7-Project/KITTI-MOTS'
gt_path = 'C:/Users/servi/Desktop/Computer Vision Master/M5. Visual Recognition/Project/week2/KITTI-MOTS/instances'
#gt_path = '/home/group07/M5-T7-Project/KITTI-MOTS/instances'

TRAINING_SEQ = ["0011","0017","0009","0020","0019","0005","0000","0015","0001", "0004" , "0003" , "0012"]
TESTING_SEQ = ["0002","0006" ,"0007" ,"0008" ,"0010" ,"0013" ,"0014" ,"0016" ,"0018"]
CLASSES = ['Cars', 'Pedestrian']
#CLASSES_MAP = {1:2,2:0}
CLASSES_MAP = {1:0,2:1}

def get_dataset_files(dataset_path, type_seq):
    sequence_map = {
        "train": TRAINING_SEQ,
        "test": TESTING_SEQ
    }
    sequence = sequence_map[type_seq]
    
    image_paths = []
    instances_txt_path = []
    instances_path = []

    for seq in sequence:
        image_paths.append(os.path.join(dataset_path, "training/image_02", seq))
        #instances_txt_path.append(os.path.join(dataset_path, 'instances_txt', seq + '.txt'))
        instances_path.append(os.path.join(dataset_path, 'instances', seq))

    image_folders = sorted(image_paths)
    instances = sorted(instances_path)
    return [(folder,img) for folder,img in zip(image_folders, instances)]

def get_dataset_dicts(dataset_path, type_seq):
    dataset_dicts = []
    for train_folder, train_img in get_dataset_files(dataset_path, type_seq):
        # get data folder and its corresponding txt file
        # load the annotations for the folder
        annotations = mots_utils.load_images_for_folder(train_img)
        image_paths = sorted(os.listdir(train_folder))
        for indx, (image_path, (file_id, objects)) in enumerate(zip(image_paths, list(annotations.items()))):
            #check the file is png or jpg
            if image_path.split('.')[1] in ['png','jpg']:
                record = {}

                filename = os.path.join(train_folder, image_path)
                height,width = cv2.imread(filename).shape[:2]
                
                #print("filename path:", filename)
                gt_filename = os.path.join(gt_path, train_img, image_path.split('.')[0]+'.png')
                #print("gt path:", gt_filename)

                gt = np.asarray(Image.open(gt_filename))
                #print("image:", gt)
                
                record["file_name"] = filename
                record["image_id"] = filename
                record["height"] = height
                record["width"] = width

                patterns = list(np.unique(gt))[1:-1]
                #print("Patterns:", patterns)
                #print("GT:", gt)
                objs = []
                for pattern in patterns:
                    coords = np.argwhere(gt==pattern)
                    #print("Coord:", coords)    
                    x0, y0 = coords.min(axis=0)
                    x1, y1 = coords.max(axis=0)

                    bbox = [y0, x0, y1, x1]

                    copy = gt.copy()
                    copy[gt==pattern] = 255
                    copy[gt!=pattern] = 0
                    copy = np.asarray(copy,np.uint8)

                    contours, _ = cv2.findContours(copy, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

                    contour = [np.reshape(contour,(contour.shape[0],2)) for contour in contours]
                    contour = np.asarray([item for tree in contour for item in tree])
                    px = contour[:,0]
                    py = contour[:,1]
                    poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
                    poly = [p for x in poly for p in x]

                    if len(poly) < 6:
                        continue


                    obj_dic = {
                        "bbox": bbox,
                        "bbox_mode":BoxMode.XYXY_ABS,
                        "segmentation": [poly],
                        "category_id": CLASSES_MAP[int(np.floor(gt[coords[0][0]][coords[0][1]]/1e3))],
                        "iscrowd": 0
                    }

                    objs.append(obj_dic)

                record["annotations"] = objs
                dataset_dicts.append(record)
    return dataset_dicts


if __name__ == '__main__':
    
    for d in ['train', 'test']:
        DatasetCatalog.register("kitti_" + d, lambda d= d: get_dataset_dicts(DATASET_PATH, d))
        MetadataCatalog.get("kitti_" + d).set(thing_classes=CLASSES)


    kitti_metadata = MetadataCatalog.get("kitti_train")
    dataset_dicts = get_dataset_dicts(DATASET_PATH, "train")

