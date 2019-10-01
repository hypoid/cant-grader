"""Grade when the signal is given"""
import os
import traceback
import pdb
import sys
import time
import threading
import subprocess
import visutil
import numpy as np
import cv2
import argparse
import glob
import shutil
import paho.mqtt.client as paho

import detect_cants_and_knots

DEBUG = True
USE_MQTT = True


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG:
    sys.excepthook = info


USE_CPU_ONLY = False
if USE_CPU_ONLY is True:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""


SAVE_SCANS = True
LIVE = True
USEMOTION = False
size = 300
DPI = 20.0
min_spec2_length_inch = 96

max_Spec1_standard_knot_diam_inch = 8
max_Spec2_standard_knot_diam_inch = 1.3
max_Spec2_premium_knot_diam_inch = 0.5

spec1_s_ignore_knot_size_inch = 2
spec2_s_ignore_knot_size_inch = 0
spec2_p_ignore_knot_size_inch = 0

spec1_s_max_knots = 6
spec2_s_max_knots = 1
spec2_p_max_knots = 1

cant_min_face_filter_size = 100  # Filter to use on cant face objects
section_length_inches = 24

spec1_saw_kerf = 0.124
spec2_saw_kerf = 0.124

spec1_saw_space = 1.70
spec2_saw_space = 1.25

spec1_bf_per_inch = 1/12
spec2_bf_per_inch = 0.75/12

downgrade_price_per_1kBF = 299
spec1_stand_price_per_1kBF = 299
spec2_stand_price_per_1kBF = 300
spec2_prem_price_per_1kBF = 300


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
    length
    """
    largest = 0
    # Starting at the beginning index 0, count start_index up until
    # the last index in 'sections'
    for start_index in range(len(sections)):
        # Starting at the beginning index 0, count end_index up until
        # last index in 'sections'
        for end_index in range(len(sections)):
            # If the end_index is less than the start index, skip to
            # the next end_index
            if end_index < start_index:
                continue
            # Check the sub list starting at start_index and ending at
            # end_index to see if it is all True.
            if all(sections[start_index:end_index+1]):
                # Check to see if the current all True sublist is larger
                # than the largest so far. If it is, record it as the
                # largest.
                if len(sections[start_index:end_index+1]) > largest:
                    largest = len(sections[start_index:end_index+1])
    return largest


def define_good_sections(cants,
                         knots,
                         max_knot_size,
                         piece_length,
                         knot_ignore_size,
                         max_knots):
    sections = [False for x in range(10)]
    for sec_idx, sub_section in enumerate(sections):
        start = farthest_left_px(cants)
        section_start_px = sec_idx*(section_length_inches*DPI)+start
        section_end_px = (sec_idx+1)*(section_length_inches*DPI)-1+start
        # Filter IN this section if it doesn't extend past the piece length
        if section_end_px-start <= piece_length:
            sections[sec_idx] = True
        # Filter OUT this section if it contains detected knot large or
        # too many knots that are above the knot_ignore size
        knot_count = 0
        for knot in knots:
            if (
                (section_start_px < knot.xmin and
                 knot.xmin < section_end_px)
                or
                (section_start_px < knot.xmax and
                 knot.xmax < section_end_px)
               ):
                current_knot_x_size = abs(knot.xmax-knot.xmin)/DPI
                current_knot_y_size = abs(knot.ymax-knot.ymin)/DPI
                if (
                    current_knot_x_size > knot_ignore_size or
                    current_knot_y_size > knot_ignore_size
                   ):
                    knot_count += 1
                if (
                    current_knot_x_size > max_knot_size or
                    current_knot_y_size > max_knot_size
                   ):
                    sections[sec_idx] = False
        if knot_count > max_knots:
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


def clip_knots_to_cant_face(cants, knots):
    n_knots = []
    for cant in cants:
        for knot in knots:
            if knot.xmin > cant.xmin and knot.xmax < cant.xmax:
                if cant.ymin > (knot.ymin+knot.ymax)/2:
                    continue
                if cant.ymax < (knot.ymin+knot.ymax)/2:
                    continue
                n_knot = detect_cants_and_knots.Box(knot.ymin,
                                                    knot.xmin,
                                                    knot.ymax,
                                                    knot.xmax,
                                                    knot.score)
                n_knots.append(n_knot)
    return n_knots


def draw_piece_good_length(cants, im, sections, y_pos):
    if len(cants) > 0:
        start = farthest_left_px(cants)
        end = farthest_right_px(cants)
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
                     3)


def filter_cants_and_knots(cants, knots):
    # Filter the cants based on cant_min_face_filter_size
    cants = [cant for cant in cants if
             abs(cant.ymax-cant.ymin) > cant_min_face_filter_size and
             cant.score > .75]
    n_cants = cants[:1].copy()  # Only keep the first cant

    knots = clip_knots_to_cant_face(cants, knots)
    n_knots = [knot for knot in knots if
               knot.score > .5 and
               abs(knot.ymax-knot.ymin)/abs(knot.xmax-knot.xmin) > 0.05]
    return n_cants, n_knots


def grade_now(topimg, botimg,
              start_time,
              display=None,
              folder_name=None,
              mqtt_client=None):
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
    strides = width // size
    stride_width = int((width - size)/strides)
    x_values = list(
        range(int(size/2), width-int(size/2), stride_width))
    x_values += [width-int(size/2)]
    for x in x_values:
        # Crop the image to the current ROI
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        crop = drawn_topimg[y1:y2, x1:x2]
        cants, knots = finder.get_cant_and_knots(crop)
        cants, knots = filter_cants_and_knots(cants, knots)

        # Draw in blue the upper and lower limits of the current crop
        cv2.line(crop,
                 (0, 1),
                 (300, 1),
                 (255, 0, 0),
                 3)
        cv2.line(crop,
                 (0, 299),
                 (300, 299),
                 (255, 0, 0),
                 3)
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
        total_top_knots += knots
        total_top_cants += cants  # This only adds 1 cant, if there are any

    # Scan the bottom image
    y = find_cant(botimg)
    total_bot_knots = []
    total_bot_cants = []
    strides = width // size
    stride_width = int((width - size)/strides)
    x_values = list(
        range(int(size/2), width-int(size/2), stride_width))
    x_values += [width-int(size/2)]
    for x in x_values:
        # Crop the image to the current ROI
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        crop = drawn_botimg[y1:y2, x1:x2]
        cants, knots = finder.get_cant_and_knots(crop)
        cants, knots = filter_cants_and_knots(cants, knots)

        # Draw in blue the upper and lower limits of the current crop
        cv2.line(crop,
                 (0, 1),
                 (300, 1),
                 (255, 0, 0),
                 3)
        cv2.line(crop,
                 (0, 299),
                 (300, 299),
                 (255, 0, 0),
                 3)
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

    if len(total_top_cants) > 0:
        filtered_total_top_cants = [total_top_cants[0]]
        for index, cant in enumerate(total_top_cants):
            if index is not 0:
                if cant.xmin - filtered_total_top_cants[-1].xmax < 300:
                    filtered_total_top_cants.append(cant)
    else:
        filtered_total_top_cants = []
    if len(total_bot_cants) > 0:
        filtered_total_bot_cants = [total_bot_cants[0]]
        for index, cant in enumerate(total_bot_cants):
            if index is not 0:
                if cant.xmin - filtered_total_bot_cants[-1].xmax < 300:
                    filtered_total_bot_cants.append(cant)
    else:
        filtered_total_bot_cants = []

    all_cants = filtered_total_bot_cants + filtered_total_top_cants
    all_knots = total_bot_knots+total_top_knots
    piece_length = find_piece_length(all_cants)

    spec1_stand_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec1_standard_knot_diam_inch,
        piece_length,
        spec1_s_ignore_knot_size_inch,
        spec1_s_max_knots)
    spec2_stand_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec2_standard_knot_diam_inch,
        piece_length,
        spec2_s_ignore_knot_size_inch,
        spec2_s_max_knots)
    spec2_prem_sections_clear = define_good_sections(
        all_cants,
        all_knots,
        max_Spec2_premium_knot_diam_inch,
        piece_length,
        spec2_p_ignore_knot_size_inch,
        spec2_p_max_knots)

    spec1_stand_length = find_longest_good_section(
        spec1_stand_sections_clear)*section_length_inches
    spec2_stand_length = find_longest_good_section(
        spec2_stand_sections_clear)*section_length_inches
    spec2_prem_length = find_longest_good_section(
        spec2_prem_sections_clear)*section_length_inches
    spec1_down_length = ((piece_length/DPI) //
                         section_length_inches)*section_length_inches

    if len(all_cants) > 0:
        smallest_cant_face = abs(all_cants[0].ymax-all_cants[0].ymin)
        for cant in all_cants:
            if abs(cant.ymax-cant.ymin) < smallest_cant_face:
                smallest_cant_face = abs(cant.ymax-cant.ymin)
    else:
        smallest_cant_face = DPI*3

    spec1_num_boards = determine_how_many_boards(spec1_saw_kerf,
                                                 spec1_saw_space,
                                                 smallest_cant_face/DPI)
    spec2_num_boards = determine_how_many_boards(spec2_saw_kerf,
                                                 spec2_saw_space,
                                                 smallest_cant_face/DPI)
    downgrade_value = find_value(spec1_num_boards,
                                 spec1_down_length,
                                 spec1_bf_per_inch,
                                 downgrade_price_per_1kBF)
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

    # if (
    #     (
    #      (spec1_s_value > spec2_s_value and spec1_s_value > spec2_p_value)
    #      or
    #      (downgrade_value > spec2_s_value and downgrade_value > spec2_p_value)
    #     )
    #     and len(total_top_knots) > 0 and len(total_bot_knots) > 0
    #    ):

    # Here we make the final decision:
    if (
        (
         (spec1_s_value > spec2_s_value and spec1_s_value > spec2_p_value)
         or
         (downgrade_value > spec2_s_value and downgrade_value > spec2_p_value)
         or
         (len(all_cants) < 10) # Grade Spec1 if we don't have a complete scan
        )
       ):
        print("Activating Spec1 output.")
        subprocess.call("IO_Adapter/Output/Send_Bad")
        grade_string = 'Spec1'
    else:
        print("Activating Spec2 output.")
        subprocess.call("IO_Adapter/Output/Send_Good")
        grade_string = 'Spec2'

    print('Spec1 Downgrade length:{}'.format(spec1_stand_length))
    print('Spec1 Standard length:{}'.format(spec1_stand_length))
    print('Spec2 Standard length:{}'.format(spec2_stand_length))
    print('Spec2 Premium length:{}'.format(spec2_prem_length))
    print('Spec1 Downgrade value:{}'.format(downgrade_value))
    print('Spec1 Standard value:{}'.format(spec1_s_value))
    print('Spec2 Standard value:{}'.format(spec2_s_value))
    print('Spec2 Premium value:{}'.format(spec2_p_value))

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

    for cant in total_top_cants:
        cant.draw(drawn_topimg, draw_probability=False)
    for knot in total_top_knots:
        knot.draw(drawn_topimg, color=(0, 0, 255), draw_probability=False)
    for cant in total_bot_cants:
        cant.draw(drawn_botimg, draw_probability=False)
    for knot in total_bot_knots:
        knot.draw(drawn_botimg, color=(0, 0, 255), draw_probability=False)
    if mqtt_client is not None:
        try:
            piece_length_feet = spec1_down_length/12
            top_knot_count = len(total_top_knots)
            bot_knot_count = len(total_bot_knots)
            top_knots_per_foot = top_knot_count / piece_length_feet
            bot_knots_per_foot = bot_knot_count / piece_length_feet
            total_knots_per_foot = top_knots_per_foot + bot_knots_per_foot
            knots_per_foot_top_percentage = top_knots_per_foot / total_knots_per_foot
            ret = mqtt_client.publish("cant_grader_latest_piece_length_inches", str(spec1_down_length))
            ret = mqtt_client.publish("cant_grader_latest_piece_bottom_knots", bot_knot_count)
            ret = mqtt_client.publish("cant_grader_latest_piece_top_knots", top_knot_count)
            ret = mqtt_client.publish("cant_grader_latest_piece_bottom_knots_per_foot",
                                      bot_knots_per_foot)
            ret = mqtt_client.publish("cant_grader_latest_piece_top_knots_per_foot",
                                      top_knots_per_foot)
            ret = mqtt_client.publish("cant_grader_latest_piece_total_knots_per_foot",
                                      total_knots_per_foot)
            ret = mqtt_client.publish("cant_grader_latest_piece_knot_per_foot_top_percentage",
                                      knots_per_foot_top_percentage)
            total_knot_diams = 0.0
            for knot in all_knots:
                current_knot_x_size = abs(knot.xmax-knot.xmin)/DPI
                current_knot_y_size = abs(knot.ymax-knot.ymin)/DPI
                if current_knot_y_size > current_knot_x_size:
                    total_knot_diams += current_knot_y_size
                else:
                    total_knot_diams += current_knot_x_size
            average_knot_diam = total_knot_diams / len(all_knots)
            ret = mqtt_client.publish("cant_grader_latest_piece_average_knot_diameter_inches",
                                      average_knot_diam)
        except:
            print("Error sending MQTT data")

    if SAVE_SCANS is True:
        if not os.path.exists(output_root):
            os.mkdir(output_root)
        old_scans = os.listdir(output_root)
        scan_count = len(old_scans)
        if scan_count > 200:
            oldest = old_scans[0]
            for scan in old_scans:
                scan_num = int(scan[:2]
                               + scan[3:5]
                               + scan[6:8]
                               + scan[9:11]
                               + scan[12:14])
                oldest_num = int(oldest[:2]
                                 + oldest[3:5]
                                 + oldest[6:8]
                                 + oldest[9:11]
                                 + oldest[12:14])
                if scan_num < oldest_num:
                    oldest = scan
            shutil.rmtree(output_root+oldest)
            print("Deleting old scan {} to make room".format(oldest))

        # Save to disk
        if folder_name is None:
            fold = "{}{}{}/".format(output_root,
                                    time.strftime("%m-%d %H:%M:%S "),
                                    grade_string)
        else:
            fold = "{}{}/".format(output_root, folder_name)
        display_img = visutil.write_scan(drawn_topimg,
                                         drawn_botimg,
                                         topimg,
                                         botimg,
                                         fold,
                                         grade_string)
        print("Saving scan to {}.".format(fold))

        # Display the last scan in another thread
        if display is not None:
            display.update_display(display_img)


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
    if USE_MQTT:
        broker = "192.168.16.240"
        port = 1883
        mqttclient = paho.Client('ID-cant-grader')
        mqttclient.connect(broker, port)
        mqttclient.loop_start()
    v = ["rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/101/",
         "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/201/",
         "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/301/",
         "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/401/",
         "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/501/",
         "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/601/"]

    HMI_display = visutil.display()
    t = threading.Thread(target=visutil.refresh_display,
                         args=(HMI_display,),
                         daemon=True)
    t.start()

    cams = []
    for cam_num, vstream in enumerate(v):
        if cam_num < 4:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     rectify=True,
                                     undistort=True,
                                     fake=False,
                                     queueSize=10,
                                     jit=True)
        elif cam_num:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     rectify=True,
                                     undistort=True,
                                     fake=False,
                                     queueSize=1,
                                     jit=True)
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=True)
        t.start()
        cams.append(new_cam)

    print("Waiting 5 seconds while cameras connect.")
    time.sleep(5)

    # imgs = [cam.img for cam in cams]
    imgs = []
    for cam in cams:
        new_img = cv2.undistort(cam.img,
                                cam.wide_camera_cal[0],
                                cam.wide_camera_cal[1],
                                cam.wide_camera_cal[2],
                                cam.wide_camera_cal[3])
        new_img = cv2.warpPerspective(new_img,
                                      cam.M,
                                      (cam.cp[2][0],
                                       cam.cp[2][1]))
        imgs.append(new_img)
    pad_height = imgs[0].shape[0]
    pad_1_width = 57
    pad_1 = np.zeros((pad_height, pad_1_width, 3), dtype=np.uint8)
    pad_2_width = 57
    pad_2 = np.zeros((pad_height, pad_2_width, 3), dtype=np.uint8)
    pad_3_width = 56
    pad_3 = np.zeros((pad_height, pad_3_width, 3), dtype=np.uint8)

    while True:
        input_reader = subprocess.Popen("IO_Adapter/Input/INPUT",
                                        stdout=subprocess.PIPE)
        print("Waiting for signal to grade.")
        wait_start = time.time()
        for input_word in iter(input_reader.stdout.readline, ''):
            for cam in cams:
                if cam.ret is False:
                    raise ValueError("{} offline, exiting main thread.".
                                     format(cam.path))
            if visutil.input_means_GRADENOW(input_word):
                break
        print('Waited {} seconds'.format(time.time()-wait_start))
        start_t = time.time()
        # Get images
        # imgs = [cam.img for cam in cams]
        imgs = []
        for cam in cams:
            new_img = cv2.undistort(cam.img,
                                    cam.wide_camera_cal[0],
                                    cam.wide_camera_cal[1],
                                    cam.wide_camera_cal[2],
                                    cam.wide_camera_cal[3])
            new_img = cv2.warpPerspective(new_img,
                                          cam.M,
                                          (cam.cp[2][0],
                                           cam.cp[2][1]))
            imgs.append(new_img)


        # bot_img = np.concatenate(tuple(imgs[1:5]), axis=1)
        bot_img = np.concatenate((imgs[0], pad_1,
                                  imgs[1], pad_2,
                                  imgs[2], pad_3,
                                  imgs[3]),
                                 axis=1)

        top_img = np.concatenate((np.flip(imgs[4], axis=1),
                                  np.flip(imgs[5], axis=1)),
                                 axis=1)

        input_reader.terminate()
        if USE_MQTT:
            grade_now(top_img, bot_img, start_t, display=HMI_display, mqtt_client=mqttclient)
        else:
            grade_now(top_img, bot_img, start_t, display=HMI_display, mqtt_client=None)


def simulated_grading():
    scan_folders = glob.glob(input_root+'*/raw/')
    for scan_folder in scan_folders:
        if os.path.isfile(scan_folder[:-4]+'0.tif.checked'):
            continue
        raw_img = cv2.imread(scan_folder+'0.tif')
        top_img = raw_img[0:int(raw_img.shape[0]/2),
                          0:raw_img.shape[1]]
        bot_img = raw_img[int(raw_img.shape[0]/2):raw_img.shape[0],
                          0:raw_img.shape[1]]
        e = scan_folder.rfind('/raw/')
        scan_folder_without_raw = scan_folder[:e]
        e = scan_folder_without_raw.rfind('/') + 1
        new_name = scan_folder_without_raw[e:]
        grade_now(top_img, bot_img, time.time(), folder_name=new_name)
    print('All done simulating. Exiting')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input_folder',
                    required=False,
                    help='Folder containing scans')
    ap.add_argument('-o', '--output_folder',
                    required=False,
                    help='Folder to store training image')
    ap.add_argument('-m', '--model_path',
                    required=False,
                    help='Folder to store training image')
    args = vars(ap.parse_args())

    input_root = args['input_folder']
    output_root = args['output_folder']
    model_path = args['model_path']
    if output_root is not None:
        if output_root[-1] != '/':
            output_root += '/'
    if input_root is None:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        if output_root is None:
            # output_root = '/data/All_training_data/Scans/'
            output_root = '/mnt/ramdisk/Scans/'
            print('Using default output scan folder {}'.format(output_root))
        finder = detect_cants_and_knots.knot_finder(None)
        online_grading()
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = "1"
        if model_path is None:
            model_path = ('Training_Job/'
                          'fine_tuned_model/'
                          'frozen_inference_graph.pb')
        if output_root is None:
            print('No output folder specified, exiting')
            exit()
        else:
            print('Using {} for simulated grading'.format(model_path))
            time.sleep(5)
            finder = detect_cants_and_knots.knot_finder(model_path)
            simulated_grading()
