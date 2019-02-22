from pycocotools.coco import COCO
import json
import numpy as np
import argparse

parser = argparse.ArgumentParser('Tools for getting dataset statistics. It is written for datasets generated with ' + \
                                 'the make_classification_dataset.py script.')
parser.add_argument("camera_trap_json", type=str, help='Path to json file of the camera trap dataset from LILA.')
parser.add_argument('train_json', type=str, help='Path to train.json generated by the make_classification_dataset.py script')
parser.add_argument('test_json', type=str, help='Path to test.json generated by the make_classification_dataset.py script')
args = parser.parse_args()

CT_JSON = args.camera_trap_json
TRAIN_JSON = args.train_json
TEST_JSON = args.test_json

coco = COCO(CT_JSON)

def print_locations(json_file):
    #json_file = TEST_JSON
    with open(json_file, 'rt') as fi:
        js = json.load(fi)
    print('Locations used: ')
    print(sorted(list(set([coco.loadImgs(['/'.join(im['file_name'].split('/')[1:])[:-4]])[0]['location'] for im in js['images']]))))
    #js_keys = ['/'.join(im['file_name'].split('/')[1:])[:-4] for im in js['images']]
    #for tk in js_keys:
    #    assert np.isclose(1, np.sum(detections[tk]['detection_scores'] > 0.5))
    class_to_name = {c['id']:c['name'] for c in js['categories']}
    labels = np.array([a['category_id'] for a in js['annotations']])
    print('Classes with one or more images: ')
    print('In total ', len(set(labels)))
    print('{:5} {:<15} {:>11}'.format('ID','Name','Image count'))
    for cls in set([a['category_id'] for a in js['annotations']]):
        print('{:5} {:<15} {:>11}'.format(cls, class_to_name[cls], np.sum(labels==cls)))

print('Statistics of the training split: ')
print_locations(TRAIN_JSON)
print('\n\nStatistics of the testing split: ')
print_locations(TEST_JSON)

