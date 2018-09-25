"""Grade when the signal is given"""

import time
import threading
import subprocess
import visutil
import numpy as np
import traceback
import pdb
import sys
import cv2
import argparse
import glob
import os

import detect_cants_and_knots


USE_CPU_ONLY = False
if USE_CPU_ONLY is True:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

LIVE = True
DEBUG = True
USEMOTION = False
size = 300
DPI = 20.0
max_Spec1_standard_knot_diam_inch = 8
max_Spec2_standard_knot_diam_inch = 1
max_Spec2_premium_knot_diam_inch = 0.25
max_premium_knot_area_px = (max_Spec2_premium_knot_diam_inch*DPI)**2
cant_min_face_filter_size = 100  # Filter to use on cant face objects at
section_length_inches = 24

spec1_saw_kerf = 0.124
spec2_saw_kerf = 0.124
spec1_saw_space = 1.70
spec2_saw_space = 1.25
spec1_bf_per_inch = 1/12
spec2_bf_per_inch = 0.75/12
spec1_stand_price_per_1kBF = 400
spec2_stand_price_per_1kBF = 600
spec2_prem_price_per_1kBF = 1000


def find_value(num_boards,
               length_of_boards,
               bf_per_inch,
               price_per_1kBF):
    price_per_bf = price_per_1kBF/1000
    per_board_value = length_of_boards*bf_per_inch*price_per_bf
    return num_boards*per_board_value


def determine_how_many_boards(saw_kerf, board_size, cant_face_size):
    """Find the number of boards that can fit in the cant."""
    board_count = 0
    while (((board_count*board_size) + ((board_count-1)*saw_kerf))
           < cant_face_size):
        board_count += 1
    board_count -= 1
    if board_count < 0:
        return 0
    else:
        return board_count


def find_longest_good_section(sections):
    """For a list of boolean values, find the longest run of 'True's.
    length"""
    largest = 0
    for start_index in range(len(sections)):
        for end_index in range(len(sections)):
            if end_index < start_index:
                continue
            if all(sections[start_index:end_index+1]):
                if len(sections[start_index:end_index+1]) > largest:
                    largest = len(sections[start_index:end_index+1])
    return largest


def define_good_sections(cants, knots, max_knot_size, piece_length):
    sections = [False for x in range(10)]
    for sec_idx, sub_section in enumerate(sections):
        start = farthest_left_px(cants)
        section_start_px = sec_idx*(section_length_inches*DPI)+start
        section_end_px = (sec_idx+1)*(section_length_inches*DPI)-1+start
        # Filter IN this section if it doesn't extend past the piece length
        if section_end_px-start <= piece_length:
            sections[sec_idx] = True
        # Filter OUT this section if it contains detected knot objects
        for knot in knots:
            if (
                abs(knot.ymax-knot.ymin) > max_knot_size*DPI or
                abs(knot.xmax-knot.xmin) > max_knot_size*DPI
               ):
                if (
                    (section_start_px < knot.xmin and
                     knot.xmin < section_end_px)
                    or
                    (section_start_px < knot.xmax and
                     knot.xmax < section_end_px)
                   ):
                    sections[sec_idx] = False
    return sections


def find_piece_length(cants):
    if len(cants) > 0:
        start = farthest_left_px(cants)
        end = farthest_right_px(cants)
        length = end-start
    else:
        length = 196*DPI  # 16'4' length
    return length


def farthest_left_px(boxes):
    if len(boxes) > 0:
        farthest_left = boxes[0].xmin
        for box in boxes:
            if box.xmin < farthest_left:
                farthest_left = box.xmin
            if box.xmax < farthest_left:
                farthest_left = box.xmax

        return farthest_left
    else:
        return 0


def farthest_right_px(boxes):
    if len(boxes) > 0:
        farthest_right = boxes[0].xmin
        for box in boxes:
            if box.xmin > farthest_right:
                farthest_right = box.xmin
            if box.xmax > farthest_right:
                farthest_right = box.xmax

        return farthest_right
    else:
        return 200


def draw_piece_good_length(cants, im, sections, y_pos):
    if len(cants) > 0:
        start = (cants[0].xmin
                 if cants[0].xmin < cants[0].xmax
                 else cants[0].xmax)
        end = (cants[-1].xmax
               if cants[-1].xmax > cants[0].xmin
               else cants[-1].xmin)
        cv2.line(im,
                 (start, y_pos),
                 (end, y_pos),
                 (0, 0, 255),
                 3)
        for sec_idx, section_clear in enumerate(sections):
            if section_clear is True:
                section_start_px = int(sec_idx*(
                    section_length_inches*DPI))+start
                section_end_px = int((sec_idx+1)*(
                    section_length_inches*DPI)-1)+start
                if section_end_px > end:
                    section_end_px = end
                cv2.line(im,
                         (section_start_px, y_pos),
                         (section_end_px, y_pos),
                         (0, 255, 0),
                         3)
        for i in range(start, im.shape[1]-1, int(DPI*section_length_inches)):
            cv2.line(im,
                     (i, 0),
                     (i, im.shape[0]-1),
                     (255, 0, 255),
                     1)


def grade_now(topimg, botimg, start_time):
    print("Now Grading...")
    drawn_topimg = topimg.copy()
    drawn_botimg = botimg.copy()
    width = topimg.shape[1]
    height = topimg.shape[0]
    # height = topimg.shape[0]

    # Scan the top image
    total_top_knots = []
    total_top_cants = []
    y = find_cant(topimg, start_left=True)
    # for x in range(width-int(size/2), int(size/2), -200):
    for x in range(int(size/2), width-int(size/2), 200):
        # Crop the image to the current ROI
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        crop = drawn_topimg[y1:y2, x1:x2]
        cants, knots = finder.get_cant_and_knots(crop)
        # Filter the cants based on cant_min_face_filter_size
        cants = [cant for cant in cants if
                 abs(cant.ymax-cant.ymin) > cant_min_face_filter_size]
        cants = cants[:1]  # Only keep the first cant per crop

        # Draw in blue the upper and lower limits of the current crop
        cv2.line(crop,
                 (0, 1),
                 (300, 1),
                 (255, 0, 0),
                 2)
        cv2.line(crop,
                 (0, 299),
                 (300, 299),
                 (255, 0, 0),
                 2)
        # Recenter the scan window for next scan based on
        # the cant's y coord
        if len(cants) > 0:
            the_cant = cants[0]
            if the_cant.ymin != the_cant.ymax:
                y = ((the_cant.ymin+the_cant.ymax)/2)+y1
                # Keep inside bounds
                if y > height-size/2:
                    y = (height-(size/2))-1
                if y < size/2:
                    y = 1 + size/2
        for knot in knots:
            knot.ymin += y1
            knot.ymax += y1
            knot.xmin += x1
            knot.xmax += x1
        for cant in cants:
            cant.ymin += y1
            cant.ymax += y1
            cant.xmin += x1
            cant.xmax += x1
        total_top_knots += knots
        total_top_cants += cants  # This only adds 1 cant, if there are any

    # Scan the bottom image
    y = find_cant(botimg)
    total_bot_knots = []
    total_bot_cants = []
    for x in range(int(size/2), width-int(size/2), 200):
        # Crop the image to the current ROI
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        crop = drawn_botimg[y1:y2, x1:x2]
        cants, knots = finder.get_cant_and_knots(crop)
        # Filter the cants based on cant_min_face_filter_size
        cants = [cant for cant in cants if
                 abs(cant.ymax-cant.ymin) > cant_min_face_filter_size]
        cants = cants[:1]  # Only keep the first cant per crop

        # Draw in blue the upper and lower limits of the current crop
        cv2.line(crop,
                 (0, 1),
                 (300, 1),
                 (255, 0, 0),
                 2)
        cv2.line(crop,
                 (0, 299),
                 (300, 299),
                 (255, 0, 0),
                 2)
        # Recenter the scan window for next scan based on
        # the cant's y coord
        if len(cants) > 0:
            the_cant = cants[0]
            if the_cant.ymin != the_cant.ymax:
                y = ((the_cant.ymin+the_cant.ymax)/2)+y1
                # Keep inside bounds
                if y > height-size/2:
                    y = (height-(size/2))-1
                if y < size/2:
                    y = 1 + size/2
        # Translate the view coordinates to gobal coordinates
        for knot in knots:
            knot.ymin += y1
            knot.ymax += y1
            knot.xmin += x1
            knot.xmax += x1
        for cant in cants:
            cant.ymin += y1
            cant.ymax += y1
            cant.xmin += x1
            cant.xmax += x1
        total_bot_knots += knots
        total_bot_cants += cants  # This only adds 1 cant, if there are any
    total_bot_knots = [knot for knot in total_bot_knots if knot.area < 10000]
    total_top_knots = [knot for knot in total_top_knots if knot.area < 10000]

    all_cants = total_bot_cants+total_top_cants
    all_knots = total_bot_knots+total_top_knots
    piece_length = find_piece_length(all_cants)

    spec1_stand_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec1_standard_knot_diam_inch,
        piece_length)
    spec2_stand_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec2_standard_knot_diam_inch,
        piece_length)
    spec2_prem_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec2_premium_knot_diam_inch,
        piece_length)

    spec1_stand_length = find_longest_good_section(
        spec1_stand_sections_clear)*section_length_inches
    spec2_stand_length = find_longest_good_section(
        spec2_stand_sections_clear)*section_length_inches
    spec2_prem_length = find_longest_good_section(
        spec2_prem_sections_clear)*section_length_inches

    if len(all_cants) > 0:
        smallest_cant_face = abs(all_cants[0].ymax-all_cants[0].ymin)
        for cant in all_cants:
            if abs(cant.ymax-cant.ymin) < smallest_cant_face:
                smallest_cant_face = abs(cant.ymax-cant.ymin)

    spec1_num_boards = determine_how_many_boards(spec1_saw_kerf,
                                                 spec1_saw_space,
                                                 smallest_cant_face)
    spec2_num_boards = determine_how_many_boards(spec2_saw_kerf,
                                                 spec2_saw_space,
                                                 smallest_cant_face)
    spec1_s_value = find_value(spec1_num_boards,
                               spec1_stand_length,
                               spec1_bf_per_inch,
                               spec1_stand_price_per_1kBF)
    spec2_s_value = find_value(spec2_num_boards,
                               spec2_stand_length,
                               spec2_bf_per_inch,
                               spec2_stand_price_per_1kBF)
    spec2_p_value = find_value(spec2_num_boards,
                               spec2_prem_length,
                               spec2_bf_per_inch,
                               spec2_prem_price_per_1kBF)

    print('Done Grading. Time taken ='+str(time.time() - start_time))

    if spec1_s_value > spec2_s_value and spec1_s_value > spec2_p_value:
        print("Activating Spec1 output.")
        subprocess.call("IO_Adapter/Output/Send_Bad")
    else:
        print("Activating Spec2 output.")
        subprocess.call("IO_Adapter/Output/Send_Good")

    print('Spec1 Standard length:{}'.format(spec1_stand_length))
    print('Spec2 Premium length:{}'.format(spec2_prem_length))
    print('Spec2 Premium length:{}'.format(spec2_prem_length))
    print('Spec1 Standard value:{}'.format(spec1_s_value))
    print('Spec2 Premium value:{}'.format(spec2_s_value))
    print('Spec2 Premium value:{}'.format(spec2_p_value))

    grade_string = None
    draw_piece_good_length(all_cants,
                           drawn_topimg,
                           spec2_prem_sections_clear,
                           drawn_topimg.shape[0]-1)
    draw_piece_good_length(all_cants,
                           drawn_botimg,
                           spec2_prem_sections_clear,
                           drawn_botimg.shape[0]-1)
    draw_piece_good_length(all_cants,
                           drawn_topimg,
                           spec2_stand_sections_clear,
                           drawn_topimg.shape[0]-11)
    draw_piece_good_length(all_cants,
                           drawn_botimg,
                           spec2_stand_sections_clear,
                           drawn_botimg.shape[0]-11)
    draw_piece_good_length(all_cants,
                           drawn_topimg,
                           spec1_stand_sections_clear,
                           drawn_topimg.shape[0]-21)
    draw_piece_good_length(all_cants,
                           drawn_botimg,
                           spec1_stand_sections_clear,
                           drawn_botimg.shape[0]-21)

    # Draw the cant and knots
    for cant in total_top_cants:
        cant.draw(drawn_topimg)
    for knot in total_top_knots:
        knot.draw(drawn_topimg, color=(0, 0, 255))
    for cant in total_bot_cants:
        cant.draw(drawn_botimg)
    for knot in total_bot_knots:
        knot.draw(drawn_botimg, color=(0, 0, 255))

    # Save to disk
    fold = "{}{}/{}/".format(
        output_root,
        grade_string,
        time.time())
    visutil.write_image_set([topimg, botimg], fold+'raw/')
    visutil.write_image_set([drawn_topimg, drawn_botimg], fold)
    print("Saving scan to {}.".format(fold))


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG:
    sys.excepthook = info


def find_cant(img, start_left=True):
    height = img.shape[0]
    i = size/2
    cants_y_coord_and_height = []
    if start_left is True:
        start = int(size/2)
        end = height-int(size/2)
        step = 10
    else:
        start = height-int(size/2)
        end = int(size/2)
        step = -10

    for j in range(start, end, step):
        # Crop the image to the current ROI
        y1 = int(j-(size/2))
        y2 = int(j+(size/2))
        x1 = int(i-(size/2))
        x2 = int(i+(size/2))
        crop = img[y1:y2, x1:x2]
        cants, _ = finder.get_cant_and_knots(crop)
        if len(cants) > 0:
            cants_y_coord_and_height.append((j,
                                            abs(cants[0].ymin-cants[0].ymax)))

    # Pick the y coord that has the highest height
    if len(cants_y_coord_and_height) > 0:
        biggest = cants_y_coord_and_height[0]
        for indx, coord_and_height in enumerate(cants_y_coord_and_height):
            if coord_and_height[1] > biggest[1]:
                biggest = coord_and_height
    else:  # If no cants were found, we use a default y of size/2
        return size/2+1
    return biggest[0]


def online_grading():
    v = ["rtsp://root:millelec01@10.0.1.10:554/axis-media/media.amp",
         "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/101/",
         "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/201/",
         "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/301/",
         "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/401/"]

    cams = []
    first = True
    for cam_num, vstream in enumerate(v):
        if first:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     queueSize=6,
                                     fake=True,
                                     rectify=True)
            first = False
        else:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     rectify=True,
                                     undistort=True,
                                     fake=True,
                                     queueSize=19)
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=True)
        t.start()
        if USEMOTION is True:
            t2 = threading.Thread(target=visutil.motion_detect,
                                  args=(new_cam,),
                                  daemon=True)
            t2.start()
        cams.append(new_cam)

    print("Waiting 5 seconds while cameras connect.")
    time.sleep(5)

    imgs = [cam.img for cam in cams]

    while True:
        input_reader = subprocess.Popen("IO_Adapter/Input/INPUT",
                                        stdout=subprocess.PIPE)
        for input_word in iter(input_reader.stdout.readline, ''):
            for cam in cams:
                if cam.ret is False:
                    raise ValueError("{} offline, exiting main thread.".
                                     format(cam.path))
            if visutil.input_means_GRADENOW(input_word):
                break
        start_t = time.time()
        # Get images
        imgs = [cam.img for cam in cams]
        bot_img = np.concatenate(tuple(imgs[1:5]), axis=1)
        top_img = np.fliplr(imgs[0]).copy()

        input_reader.terminate()
        grade_now(top_img, bot_img, start_t)


def simulated_grading():
    scan_folders = glob.glob(input_root+'*/raw/')
    for scan_folder in scan_folders:
        if os.path.isfile(scan_folder[:-4]+'0.png.checked'):
            continue
        if os.path.isfile(scan_folder[:-4]+'1.png.checked'):
            continue
        top_img = cv2.imread(scan_folder+'0.png')
        bot_img = cv2.imread(scan_folder+'1.png')
        grade_now(top_img, bot_img, time.time())
    print('All done simulating. Exiting')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input_folder',
                    required=False,
                    help='Folder containing scans')
    ap.add_argument('-o', '--output_folder',
                    required=False,
                    help='Folder to store training image')
    args = vars(ap.parse_args())

    input_root = args['input_folder']
    output_root = args['output_folder']
    if input_root is None:
        if output_root is None:
            output_root = '/data/All_training_data/Scans/'
            print('Using default output scan folder {}'.format(output_root))
        finder = detect_cants_and_knots.knot_finder()
        online_grading()
    else:
        if output_root is None:
            print('No output filder specified, exiting')
            exit()
        else:
            finder = detect_cants_and_knots.knot_finder()
            simulated_grading()
