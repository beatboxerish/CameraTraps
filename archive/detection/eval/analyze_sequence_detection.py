import cPickle as  pickle
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np
import json

#export PYTHONPATH=$PYTHONPATH:tfmodels/research
from object_detection.utils import metrics, np_box_ops
from object_detection.utils import per_image_evaluation

det_folder = '/data/experiments/object_detection/inception_resnet_v2_atrous/exported_124762/predictions/'
db_file = '/data/iwildcam/CaltechCameraTrapsFullAnnotations.json'
def get_im_to_seq_map(db_file):
    with open(db_file,'r') as f:
        data = json.load(f)
    im_to_seq = {}
    for im in data['images']:
        im_to_seq[im['id']] = im['seq_id']
    return im_to_seq

def compute_precision_recall_with_sequences(detection_file, db_file):
    
    print('Loading detection file...')
    
    with open(detection_file) as f:
        detection_results = pickle.load(f)

    im_to_seq = get_im_to_seq_map(db_file)
    seqs = {}
    for im in detection_results['images']:
        if im in im_to_seq:
            if im_to_seq[im] not in seqs:
                seqs[im_to_seq[im]] = []
            seqs[im_to_seq[im]].append(im)
    #print(len(detection_results['images']))
    #print(len(seqs))
    #print(len(seqs[0]),len(seqs[ 

    
    print('Clustering detections by image...')
    #print(detection_results.keys())
    # group the detections by image id:
    per_image_detections = {detection_results['images'][idx] :{'bboxes': detection_results['detections'][idx], 'scores': detection_results['detection_scores'][idx], 'labels':detection_results['detection_labels'][idx]} for idx in range(len(detection_results['images']))}

    # group the ground truth annotations by image id:
    per_image_gts ={detection_results['images'][idx] : {'bboxes':detection_results['gts'][idx],'labels':detection_results['gt_labels'][idx]} for idx in range(len(detection_results['images']))}

    per_image_eval = per_image_evaluation.PerImageEvaluation(
        num_groundtruth_classes=1,
        matching_iou_threshold=0.5,
        nms_iou_threshold=1.0,
        nms_max_output_boxes=10000
    )
    
    print('Running per-image analysis...')

    detection_labels = []
    detection_scores = []
    num_total_gts = 0
    count = 0
    for seq in seqs:
        seq_detection_labels = []
        seq_detection_scores = []
        seq_num_gts  = []
        max_seq_scores = []
        #print(seq)
        for image_id in seqs[seq]:
                    
        #for image_id, dets in per_image_detections.iteritems():
            dets = per_image_detections[image_id]
            num_detections = len(dets['bboxes'])

            # [ymin, xmin, ymax, xmax] in absolute image coordinates.
            detected_boxes = np.zeros([num_detections, 4], dtype=np.float32)
            # detection scores for the boxes
            detected_scores = np.zeros([num_detections], dtype=np.float32)
            # 0-indexed detection classes for the boxes
            detected_class_labels = np.zeros([num_detections], dtype=np.int32)
            detected_masks = None

            for i in range(num_detections):
                x1, y1, x2, y2 = dets['bboxes'][i]
                detected_boxes[i] = np.array([y1, x1, y2, x2])
                detected_scores[i] = dets['scores'][i]
                detected_class_labels[i] = dets['labels'][i] - 1

            max_seq_scores.append(np.max(detected_scores))
            box_id = np.argmax(detected_scores)
            
            gts = per_image_gts[image_id]
            num_gts = len(gts['bboxes'])
            seq_num_gts.append(num_gts)
            #print(num_gts)
            if num_gts > 0:

                # [ymin, xmin, ymax, xmax] in absolute image coordinates
                groundtruth_boxes = np.zeros([num_gts, 4], dtype=np.float32)
                # 0-indexed groundtruth classes for the boxes
                groundtruth_class_labels = np.zeros(num_gts, dtype=np.int32)
                groundtruth_masks = None
                groundtruth_is_difficult_list = np.zeros(num_gts, dtype=bool)
                groundtruth_is_group_of_list = np.zeros(num_gts, dtype=bool)

             
                for i in range(num_gts):
                    x1, y1, x2, y2 = gts['bboxes'][i]
                    groundtruth_boxes[i] = np.array([y1, x1, y2, x2])
                    groundtruth_class_labels[i] = gts['labels'][i] - 1

                ious = np_box_ops.iou(detected_boxes,groundtruth_boxes)
                if np.max(ious[box_id, :]) < 0.5:
                    max_seq_scores[-1] = 0
                #if sum(detected_class_labels)>0:
                    #print('detected animal box')

                #print(groundtruth_boxes, groundtruth_class_labels,detected_scores[0],detected_boxes[0], detected_class_labels[0])

                scores, tp_fp_labels, is_class_correctly_detected_in_image = (
                per_image_eval.compute_object_detection_metrics(
                    detected_boxes=detected_boxes,
                    detected_scores=detected_scores,
                    detected_class_labels=detected_class_labels,
                    groundtruth_boxes=groundtruth_boxes,
                    groundtruth_class_labels=groundtruth_class_labels,
                    groundtruth_is_difficult_list=groundtruth_is_difficult_list,
                    groundtruth_is_group_of_list=groundtruth_is_group_of_list,
                    detected_masks=detected_masks,
                    groundtruth_masks=groundtruth_masks
                    )
                )
                #print(scores, tp_fp_labels)
                seq_detection_labels.append(tp_fp_labels[0])
                seq_detection_scores.append(scores[0])
                #num_total_gts += num_gts
            
                count +=1
                if count % 1000 == 0:
                    print(str(count) + ' images complete') 

                #if (tp_fp_labels[0].shape[0] != num_detections):
                #    print('Incorrect label length')
                #if scores[0].shape[0] != num_detections:
                #    print('Incorrect score length')
                #if tp_fp_labels[0].sum() > num_gts:
                #    print('Too many correct detections')

            else:
                seq_detection_labels.append(np.zeros(num_detections, dtype=np.int32))
                seq_detection_scores.append(detected_scores)
                max_seq_scores[-1] = 0

        best_score = np.max(max_seq_scores)
        if best_score > 0:
            #print('valid box')
            best_im = np.argmax(max_seq_scores)
            #print(best_im, best_score)
            for i in range(len(seqs[seq])):
                
                temp_labels = np.zeros(len(seq_detection_labels[i]),  dtype=np.int32)
                temp_scores = np.zeros(len(seq_detection_scores[i]), dtype=np.float32)
                for j in range(min(seq_num_gts[i], len(temp_labels))):
                    temp_labels[j] = True #TODO: this currently only works for oneclass?
                    temp_scores[j] = best_score
                seq_detection_labels[i] = temp_labels
                seq_detection_scores[i] = temp_scores

        num_total_gts+=sum(seq_num_gts)
        
        for i in range(len(seqs[seq])): 
            detection_labels.append(seq_detection_labels[i])
            detection_scores.append(seq_detection_scores[i])


    scores = np.concatenate(detection_scores)
    labels = np.concatenate(detection_labels).astype(np.bool)

    precision, recall = metrics.compute_precision_recall(
        scores, labels, num_total_gts
    )

    average_precision = metrics.compute_average_precision(precision, recall)
    
    
    return precision, recall, average_precision

if __name__ == '__main__':

    inter_prec, inter_recall, inter_ap = compute_precision_recall_with_sequences(det_folder + 'cis_test.p',db_file)
    loc_prec, loc_recall, loc_ap = compute_precision_recall_with_sequences(det_folder + 'trans_test.p', db_file)
    print('Cis mAP: ', inter_ap,', Trans mAP: ', loc_ap)
    recall_thresh = 0.9
    recall_idx = np.argmin([np.abs(x-recall_thresh) for x in inter_recall])
    print('Cis prec. at ',inter_recall[recall_idx],' recall: ', inter_prec[recall_idx])
    recall_idx = np.argmin([np.abs(x-recall_thresh) for x in loc_recall])
    print('Trans prec. at ',loc_recall[recall_idx],' recall: ', loc_prec[recall_idx])


    plt.figure("Precision Recall Curve - Sequences")
    plt.plot(inter_recall, inter_prec, 'C0-', label='cis-locations')
    plt.plot(loc_recall, loc_prec, 'C1-', label='trans-locations')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel("Precision")
    plt.xlabel("Recall")
    plt.legend()
    plt.title("%0.2f mAP Cis vs %0.2f mAP Trans" % (inter_ap, loc_ap))
    plt.savefig(det_folder + 'seq_PR_cis_v_trans.jpg')

    np.savez(det_folder + 'seq_cis_v_trans_prec_recall_data.npz', cis_prec=inter_prec, cis_recall=inter_recall, cis_ap=inter_ap, trans_prec=loc_prec, trans_recall=loc_recall, trans_ap=loc_ap)
