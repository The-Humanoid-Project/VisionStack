import os
import cv2
from ultralytics import YOLO
import google.generativeai as genai
from PIL import Image

class ImageProcessor:
    def __init__(self):
        self.captured_image_count = self._find_latest_image_index("inferencing/captured_images")
        self.book_count = self._find_latest_image_index("inferencing/Books")
        self.model = "Models/train_scratch_v2x.pt"
        self.ocr_api_key = "AIzaSyB35dxJDDEkLR_Cm58Xm0NYGxaBHoNYAK4"

    def _find_latest_image_index(self, directory):
        try:
            if not os.path.exists(directory):
                return 0
            image_files = [f for f in os.listdir(directory) if f.endswith('.jpg')]
            if not image_files:
                return 0
            latest_index = max([int(f.split('_')[-1].split('.')[0]) for f in image_files])
            return latest_index
        except Exception as e:
            print(f"Error finding latest image index: {e}")
            return 0

    def _jetson_capture_image(self):
        try:
            # Open the CSI camera
            cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM),format=NV12,width=1280,height=720,framerate=30/1 ! nvvidconv ! video/x-raw,format=BGRx ! appsink drop=1", cv2.CAP_GSTREAMER)
            cv2.namedWindow("Camera Feed")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Couldn't read frame from the camera")
                    break
                cv2.imshow("Camera Feed", frame)
                key = cv2.waitKey(1)
                if key == 13:
                    directory = "inferencing/captured_images"
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    self.captured_image_count += 1
                    save_path = os.path.join(directory, f"captured_image_{self.captured_image_count}.jpg")
                    cv2.imwrite(save_path, frame)
                    print("Image captured and saved successfully at:", save_path)
                    return save_path
                elif key == 27:
                    break
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
        finally:
            if cap:
                cap.release()
            cv2.destroyAllWindows()

    def capture_image(self, camera_index=0, target_resolution=(1920, 1080)):
        if camera_index == 1: # Assuming 1 represents Jetson Nano
            return self._jetson_capture_image()
        else:
            return self._pc_capture_image(camera_index, target_resolution)

    def _pc_capture_image(self, camera_index, target_resolution):
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                print("Error: Could not open camera.")
                return None
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2592)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1944)
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame.")
                    return None
                resized_frame = cv2.resize(frame, target_resolution)
                cv2.namedWindow("Press Enter to capture", cv2.WINDOW_AUTOSIZE)
                cv2.imshow("Press Enter to capture", resized_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 13:
                    directory = "inferencing/captured_images"
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    self.captured_image_count += 1
                    save_path = os.path.join(directory, f"captured_image_{self.captured_image_count}.jpg")
                    cv2.imwrite(save_path, resized_frame)
                    print("Image captured and saved successfully at:", save_path)
                    return save_path
                elif key == 27:
                    break
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def detect_and_crop_books(self, image_path):
        try:
            image = cv2.imread(image_path)
            yolomodel = YOLO(self.model)
            book_results = yolomodel.predict(source=image, classes=0, conf=0.5)
            for book_detection in book_results:
                data = book_detection.boxes.data.clone().detach()
                for book_subimage_parameters in data:
                    x1, y1, x2, y2, score, label = book_subimage_parameters
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    book_subimage = image[y1:y2, x1:x2]
                    self.book_count += 1
                    directory = "inferencing/Books"
                    bookcrops_save_path = f'{directory}/book_{self.book_count}.jpg'
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    cv2.imwrite(bookcrops_save_path, book_subimage)
                    print(f"Book Crop {self.book_count} saved successfully at:", bookcrops_save_path, f" Conf: {score} ", f" Label: {label}")
                    self._detect_and_crop_labels(bookcrops_save_path, self.book_count)
        except Exception as e:
            print(f"Error Saving Book Crops: {e}")
            return None
    
    def _detect_and_crop_labels(self, book_crop_path, book_count):
        try:
            book_image = cv2.imread(book_crop_path)
            model = YOLO(self.model)
            label_results = model.predict(source=book_image, classes=1, conf=0.6)
            for label_detection in label_results:
                data = label_detection.boxes.data.clone().detach()
                label_count = 1
                for label_subimage_parameters in data:
                    x1, y1, x2, y2, score, label = label_subimage_parameters
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    label_subimage = book_image[y1:y2, x1:x2]
                    directory = f'inferencing/labels/book_{book_count}'
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    labelcrops_save_path = f'{directory}/label_{label_count}.jpg'
                    cv2.imwrite(labelcrops_save_path, label_subimage)
                    print(f"Label Crop {label_count} saved successfully at:", labelcrops_save_path, f" Conf: {score} ", f" Label: {label}", f" for Book {book_count}")
                    label_count += 1
                    print(self._perform_ocr(labelcrops_save_path))
                print('\n')
        except Exception as e:
            print(f"Error Saving Label Crops: {e}")
            return None

    def _perform_ocr(self, img_path):
        GOOGLE_API_KEY = self.ocr_api_key
        genai.configure(api_key=GOOGLE_API_KEY)
        vmodel = genai.GenerativeModel('gemini-pro-vision')
        img = Image.open(img_path)
        ocr_base_prompt = "you are a optical character recognition tool, write what you see in this book label and return this as a single string with newline characters"
        try:
            response = vmodel.generate_content([ocr_base_prompt, img])
            return response.text
        except Exception as e:
            print(f"Error performing OCR: {e}")
            return "I don't really know how to answer your question. Sorry"

if __name__ == "__main__":
    image_processor = ImageProcessor()
    user_input = input("Enter 1 if Running on Jetson Nano | Enter 0 if Running on PC: ")
    try:
        captured_image_path = image_processor.capture_image(int(user_input))
    except Exception as e:
        print(f"Error Encountered: {e}")
        captured_image_path = None
    image_processor.detect_and_crop_books(captured_image_path)