import cv2
import mediapipe as mp
import pyautogui
import subprocess
import sys

# Initialize webcam
cap = cv2.VideoCapture(0)

# Initialize MediaPipe Hands with detection for 2 hands
hand_detector = mp.solutions.hands.Hands(max_num_hands=2)  # Changed to detect 2 hands
drawing_utils = mp.solutions.drawing_utils
screen_width, screen_height = pyautogui.size()
index_y = 0
index_x = 0
thumb_x = 0
thumb_y = 0
fist_detected = False

def are_hands_joined(hands):
    """Check if two hands are joined together by comparing wrist distances"""
    if len(hands) != 2:
        return False
    
    # Get wrist positions for both hands
    wrist1 = hands[0].landmark[0]
    wrist2 = hands[1].landmark[0]
    
    # Calculate Euclidean distance between wrists
    distance = ((wrist1.x - wrist2.x) ** 2 + (wrist1.y - wrist2.y) ** 2) ** 0.5
    print(f"Distance between wrists: {distance}")  # Debugging
    
    # Return True if wrists are close enough
    return distance < 0.15  # Adjust this threshold based on testing


while True:
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = hand_detector.process(rgb_frame)
    hands = output.multi_hand_landmarks

    if hands:
        # # First check if hands are joined
        # if are_hands_joined(hands):
        #     print("Hands joined! Switching to Math Solver...")
        #     subprocess.Popen([sys.executable, "mathSolver.py"])
        #     cap.release()
        #     cv2.destroyAllWindows()
        #     sys.exit()

        # Process single hand gestures
        for hand in hands:
            drawing_utils.draw_landmarks(frame, hand)
            landmarks = hand.landmark
            
            for id, landmark in enumerate(landmarks):
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)

                # if id == 0:
                #     wrist_x = screen_width/frame_width * x
                #     wrist_y = screen_height/frame_height * y
                #     if((wrist_x - thumb_x) < 200 and (wrist_y - index_y) < 200):
                #         print("Fist detected!")
                #         subprocess.Popen([sys.executable, "gameControl.py"])
                #         cap.release()
                #         cv2.destroyAllWindows()
                #         sys.exit()

                if id == 8:
                    cv2.circle(frame, (x,y), 15, (0,255,255))
                    index_x = screen_width/frame_width * x
                    index_y = screen_height/frame_height * y
                    pyautogui.moveTo(index_x, index_y)

                if id == 4:
                    cv2.circle(frame, (x,y), 15, (0,255,255))
                    thumb_x = screen_width/frame_width * x
                    thumb_y = screen_height/frame_height * y
                    if abs(index_y - thumb_y) < 100:
                        pyautogui.mouseDown()
                    if abs(index_y - thumb_y) > 100:
                        pyautogui.mouseUp()

                if id == 12:
                    cv2.circle(frame, (x,y), 15, (0,255,255))
                    middle_x = screen_width/frame_width * x
                    middle_y = screen_height/frame_height * y
                    if abs(index_x - middle_x) < 100:
                        pyautogui.click()
                        pyautogui.sleep(1)
                
                if id == 16:
                    cv2.circle(frame, (x,y), 15, (0,255,255))
                    ring_x = screen_width/frame_width * x
                    ring_y = screen_height/frame_height * y
                    if abs(thumb_x - ring_x) < 30:
                        pyautogui.click(clicks=2)
                        pyautogui.sleep(1)

                if id == 20:
                    cv2.circle(frame, (x,y), 15, (0,255,255))
                    pinky_x = screen_width/frame_width * x
                    pinky_y = screen_height/frame_height * y
                    if abs(thumb_x - pinky_x) < 50:
                        pyautogui.click(button='right')
                        pyautogui.sleep(1)
    
    cv2.imshow('Personal Mouse', frame)
    cv2.waitKey(1)