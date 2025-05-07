import base64
import os
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageTk
import tkinter as tk
from PIL import ImageGrab
import pyautogui
import google.generativeai as genai
import asyncio
import threading
from functools import partial
import sys
import subprocess

class HandDrawingApp:
    def __init__(self):
        # Initialize Mediapipe Hand Model
        self.mp_hands = mp.solutions.hands
        # Changed to detect up to 2 hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # Changed to 2 hands
            min_detection_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Initialize drawing variables
        self.prev_x, self.prev_y = None, None
        self.is_processing = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Hand Drawing Application")
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.root, width=640, height=480, bg='white')
        self.canvas.pack(side=tk.LEFT)
        
        # Create numpy array for storing drawing
        self.drawing_array = np.zeros((480, 640, 3), dtype=np.uint8)
        self.drawing_array.fill(255)  # Fill with white background
        
        # Create label for webcam feed
        self.webcam_label = tk.Label(self.root)
        self.webcam_label.pack(side=tk.RIGHT)
        
        # Add status label
        self.status_label = tk.Label(self.root, text="Status: Waiting for hands to join", fg="blue")
        self.status_label.pack(side=tk.BOTTOM)
        
        # Add processing label
        self.processing_label = tk.Label(self.root, text="", fg="blue")
        self.processing_label.pack(side=tk.BOTTOM)
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open webcam")
        
        # Configure Google AI
        genai.configure(api_key='AIzaSyBVaiOIvtMG2TCXXy0OjsEKfn6GsD36TCc')
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Start the application
        self.update()
        self.root.mainloop()
    
    def detect_gesture(self, landmarks):
        """Detect gestures and return relevant landmarks"""
        index_tip = landmarks[8]  # Index finger tip
        thumb_tip = landmarks[4]  # Thumb tip
        middle_tip = landmarks[12]  # Middle finger tip
        return index_tip, thumb_tip, middle_tip
    
    def is_drawing(self, thumb_tip, middle_tip):
        """Check if thumb and middle finger are joined"""
        distance = ((thumb_tip.x - middle_tip.x) ** 2 + (thumb_tip.y - middle_tip.y) ** 2) ** 0.5
        return distance > 0.04
    
    def draw_with_index(self, index_tip):
        """Draw on both canvas and numpy array using the index finger"""
        x, y = int(index_tip.x * 640), int(index_tip.y * 480)
        if self.prev_x is not None and self.prev_y is not None:
            # Draw on tkinter canvas
            self.canvas.create_line(self.prev_x, self.prev_y, x, y, fill='black', width=3)
            # Draw on numpy array
            cv2.line(self.drawing_array, 
                    (int(self.prev_x), int(self.prev_y)), 
                    (x, y), 
                    (0, 0, 0), 3)
        self.prev_x, self.prev_y = x, y
    
    def reset_drawing(self):
        """Reset drawing when thumb and middle finger are joined"""
        self.prev_x, self.prev_y = None, None
    
    def is_fist(self, landmarks):
        """Detect if the hand is in a fist position"""
        if self.is_processing:
            return False
            
        fingertips_y = [landmarks[8].y, landmarks[12].y, landmarks[16].y, landmarks[20].y]
        pips_y = [landmarks[6].y, landmarks[10].y, landmarks[14].y, landmarks[18].y]
        fingers_bent = all(tip_y > pip_y for tip_y, pip_y in zip(fingertips_y, pips_y))
        thumb_bent = landmarks[4].x < landmarks[5].x if landmarks[5].x < 0.5 else landmarks[4].x > landmarks[5].x
        
        if fingers_bent and thumb_bent:
            self.status_label.config(text="Status: FIST DETECTED!", fg="green")
            print("Fist detected! Processing image...")
            self.process_image_with_ai()
        else:
            if not self.is_processing:
                self.status_label.config(text="Status: Not detecting fist", fg="red")
        
        return fingers_bent and thumb_bent
    
    def process_image_with_ai(self):
        """Process the drawing with Google's generative AI"""
        if self.is_processing:
            return
            
        try:
            self.is_processing = True
            self.processing_label.config(text="Processing... Please wait", fg="blue")
            print("Starting AI processing...")
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(self.drawing_array)
            
            # Start processing in a separate thread
            threading.Thread(
                target=self.send_to_gemini,
                args=(pil_image,),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Error in AI processing: {e}")
            self.is_processing = False
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            self.processing_label.config(text="")
    
    def send_to_gemini(self, image):
        """Send image to Gemini and process response"""
        try:
            response = self.model.generate_content([
                "Solve this math problem. Provide only the final numerical answer.",
                image
            ])
            
            print("AI Response:", response.text)
            self.root.after(0, self.process_complete, response.text)
            
        except Exception as e:
            print(f"Error with Gemini: {e}")
            self.root.after(0, self.process_complete, f"Error: {str(e)}")
    
    def process_complete(self, result):
        """Handle completion of AI processing"""
        self.is_processing = False
        self.status_label.config(text=f"Answer: {result}", fg="blue")
        self.processing_label.config(text="")
        # Clear both canvas and numpy array
        self.canvas.delete("all")
        self.drawing_array.fill(255)
        self.prev_x, self.prev_y = None, None
        print("Processing complete")

    def switch_to_game_control(self):
        """Safely close current script and start game control"""
        print("Switching to main mouse control...")
        
        # Release webcam
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        
        # Close all opencv windows
        cv2.destroyAllWindows()
        
        # Close tkinter window
        self.root.destroy()
        
        # Start the game control script
        subprocess.Popen([sys.executable, "main.py"])
        
        # Exit current script
        sys.exit()

    def are_hands_joined(self, multi_hand_landmarks):
        """
        Check if two hands are joined together
        Returns True if hands are close enough to be considered joined
        """
        if len(multi_hand_landmarks) != 2:
            return False
        
        # Get the center points of both hands
        def get_hand_center(landmarks):
            x_coords = [lm.x for lm in landmarks.landmark]
            y_coords = [lm.y for lm in landmarks.landmark]
            return (sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords))
        
        center1 = get_hand_center(multi_hand_landmarks[0])
        center2 = get_hand_center(multi_hand_landmarks[1])
        
        # Calculate distance between hand centers
        distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
        
        # If hands are close enough, consider them joined
        # Adjust threshold (0.15) as needed
        return distance < 0.15

    def update(self):
        """Update the application frame"""
        try:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks and not self.is_processing:
                    # Draw landmarks for all detected hands
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame, 
                            hand_landmarks, 
                            self.mp_hands.HAND_CONNECTIONS
                        )
                    
                    # Using your original gesture detection logic
                    index_tip, thumb_tip, middle_tip = self.detect_gesture(hand_landmarks.landmark)
                    
                    if self.is_fist(hand_landmarks.landmark):
                        pass  # Fist detection handled in is_fist method
                    elif self.is_drawing(thumb_tip, middle_tip):
                        self.draw_with_index(index_tip)
                    else:
                        self.reset_drawing()
                    
                    # # Check if hands are joined
                    # if self.are_hands_joined(results.multi_hand_landmarks):
                    #     self.status_label.config(
                    #         text="Hands joined! Switching to game control...", 
                    #         fg="green"
                    #     )
                    #     self.root.after(500, self.switch_to_game_control)  # Switch after 0.5 seconds
                    #     return
                    # elif len(results.multi_hand_landmarks) == 2:
                    #     self.status_label.config(
                    #         text="Two hands detected! Join them to switch.", 
                    #         fg="blue"
                    #     )
                    # else:
                    #     self.status_label.config(
                    #         text="Show both hands and join them to switch", 
                    #         fg="blue"
                    #     )
                
                img = Image.fromarray(rgb_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.webcam_label.imgtk = imgtk
                self.webcam_label.configure(image=imgtk)
            
            self.root.after(10, self.update)
            
        except Exception as e:
            print(f"Error in update loop: {e}")
            self.root.after(10, self.update)

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    app = HandDrawingApp()