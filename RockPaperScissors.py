import cv2
import time
from handtracking import HandTracking
from math import sqrt


def get_length(x1, y1, x2, y2):
    """
    Receives the coordinates of two points, calculates and returns the length between them.
    """
    return int(sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def identify_r_p_s(landmark_lst):
    """
    Checks the state of the ring, index and middle finger. Returns rock if all are closed, papper if all are open, and
    scissors if only the middle and index finger are open.
    :param landmark_lst: A list of hand landmarks.
    """
    distance = get_length(landmark_lst[9][1], landmark_lst[9][2], landmark_lst[13][1], landmark_lst[13][2])
    index_length = get_length(landmark_lst[5][1], landmark_lst[5][2], landmark_lst[8][1], landmark_lst[8][2])
    middle_length = get_length(landmark_lst[12][1], landmark_lst[12][2], landmark_lst[9][1], landmark_lst[9][2])
    ring_length = get_length(landmark_lst[16][1], landmark_lst[16][2], landmark_lst[13][1], landmark_lst[13][2])
    open_index, open_middle, open_ring = False, False, False

    if distance * 3 <= index_length:
        open_index = True
    if distance * 3 <= middle_length:
        open_middle = True
    if distance * 3 <= ring_length:
        open_ring = True

    if open_middle and open_ring and open_index:
        return "Paper"
    if open_middle and open_index:
        return "Scissors"
    else:
        return "Rock"


def show_fps(img, cur_time, prev_time):
    """
    Calculates the current frames per second and prints them on the given image.
    :param img: Image to write the FPS on.
    :param cur_time: Current time.
    :param prev_time: Previous time.
    """
    fps = 1 / (cur_time - prev_time)
    cv2.putText(img, "FPS: " + str(int(fps)), (10, 40), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)


def take_and_identify_snapshot():
    """
    Take a snap shot and identify a hand gesture in the image. Returns image with hand gesture written upon it and the
    identified hand gesture. If no gesture was made, the gesture is saved as "No gesture was made!".
    """
    cap = cv2.VideoCapture(0)
    success, img = cap.read()
    tracker = HandTracking()
    landmark_lst = tracker.find_lm_positions(img)
    if landmark_lst:
        gesture = identify_r_p_s(landmark_lst)
        cv2.putText(img, gesture, (100, 400), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)
    else:
        gesture = "No gesture was made!"
        cv2.putText(img, gesture, (100, 400), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)
    return img, gesture


def blur_hand(img, landmark_lst):
    pnt = (landmark_lst[9][1], landmark_lst[9][2])
    rad = get_length(landmark_lst[9][1], landmark_lst[9][2], landmark_lst[0][1], landmark_lst[0][2]) + 15
    cv2.circle(img, pnt, rad, (0, 0, 0), thickness=-1)
    cv2.putText(img, "?", pnt, cv2.FONT_ITALIC, 1, (255, 255, 255), 2)


def put_username(username, img):
    cv2.putText(img, f"Playing against: {username}", (10, 40), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)


def put_pos(num, img):
    if num == 5:
        return
    if num == 4:
        pos = "Rock"
    elif num == 3:
        pos = "Paper"
    elif num == 2:
        pos = "Scissors"
    else:
        pos = "Shoot!"
    cv2.putText(img, pos, (img.shape[1]//2, img.shape[0]//2), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)
