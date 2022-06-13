import cv2
import mediapipe as mp


class HandTracking(object):
    def __init__(self, static_image_mode=False, max_num_hands=2, model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initializes the MediaPipe drawing_utils solution and the Hands class from the hands solution based on the input
        or default parameters:
        :param static_image_mode: If set to false, it detects a hand based on the first set of input images and then
            localizes the hand landmarks. Once max_num_hands has been reached, stops invoking another detection until a
            loss of a current detection. If set to true, hand detection runs on every input image.
        :param max_num_hands: Maximum number of hands to detect on screen.
        :param model_complexity: Complexity of the hand landmark model: 0 or 1.
        :param min_detection_confidence: Minimum confidence value from the hand detection model for the detection to be
            considered successful.
        :param min_tracking_confidence: Minimum confidence value from the landmark-tracking model for the hand landmarks
            to be considered tracked successfully, or otherwise hand detection will be invoked automatically on the next
            input image.
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode, max_num_hands, model_complexity, min_detection_confidence, min_tracking_confidence)
        self.mp_draw = mp.solutions.drawing_utils

    def detect_hands(self, img):
        """
        Processes an image and returns hand landmarks and handedness of each detected hand.
        :param img: Image to be processed.
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        return results

    def draw_hands(self, img):
        """
        Draws hand landmarks and their connections upon an image. Returns the image.
        :param img: Image to be processed.
        """
        results = self.detect_hands(img)
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, handLms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_lm_positions(self, img, hand_number=0):
        """
        Creates and returns a list of each of the landmarks' position. Returns a list for the hand specified in the
        parameters.
        :param img: Image to be processed.
        :param hand_number: Specified hand to focus on.
        """
        landmark_lst = []
        results = self.detect_hands(img)
        if results.multi_hand_landmarks:
            for id, lm in enumerate(results.multi_hand_landmarks[hand_number].landmark):
                height, width, channel = img.shape
                lm_x, lm_y = int(lm.x * width), int(lm.y * height)
                landmark_lst.append([id, lm_x, lm_y])
        return landmark_lst
