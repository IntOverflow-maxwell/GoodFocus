import json
import os
import re
import secrets
import threading
import tkinter as tk
import fitz  # PyMuPDF
import atexit
from tqdm import tqdm
from neuro import Neuro
import datetime
import time

USE_TRIVIAL = True
log_file_path = "./extract_log.txt"


def extract_quiz_bowl_content_from_directory(directory_path):
    quiz_data = []
    print("Loading...")

    # Iterate through each file in the directory
    for filename in tqdm(os.listdir(directory_path)):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory_path, filename)
            # Open the PDF file
            document = fitz.open(pdf_path)

            # Iterate through each page in the PDF
            for page_num in range(document.page_count):
                page = document[page_num]
                text = page.get_text("text")

                # Regex to find questions and answers
                qa_pattern = re.compile(r'(\d+\..+?)(?=\n\d+\.|\nANSWER:)', re.DOTALL)
                answer_pattern = re.compile(r'ANSWER:\s(.+?)(?=\n\d+\.|\n<|$)', re.DOTALL)

                # Find all questions
                questions = qa_pattern.findall(text)
                # Find all answers
                answers = answer_pattern.findall(text)

                # Make sure the number of questions matches the number of answers
                if len(questions) != len(answers):
                    print(f"Warning: Mismatch in questions and answers in file {filename}, page {page_num}")
                    continue

                for question, answer in zip(questions, answers):
                    # Clean up the extracted text
                    question = question.strip().replace("\n", " ")
                    answers_list = [ans.strip() for ans in re.split(r'\[or|\;', answer.strip())]

                    # Skip empty questions
                    if not question or not answers_list:
                        continue

                    # Skip multi-part questions
                    if re.search(r'\[\d+.*\]', question):
                        continue

                    # Create a dictionary for each quiz entry
                    quiz_entry = {
                        "question": question,
                        "answers": answers_list
                    }
                    quiz_data.append(quiz_entry)

    # Output the combined data as JSON
    with open("combined_quiz_bowl_data.json", "w") as json_file:
        json.dump(quiz_data, json_file, indent=4)

    print(f"Extraction completed. Data saved to combined_quiz_bowl_data.json with {len(quiz_data)} questions.")
    return quiz_data


import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

print("Please select the serial port for your TGAM USB device:")

for port in ports:
    print(f"Device: {port.device}")
    print(f"  Name: {port.name}")
    print(f"  Description: {port.description}")
    print(f"  HWID: {port.hwid}")
    print(f"  VID: {port.vid}")
    print(f"  PID: {port.pid}")
    print(f"  Serial number: {port.serial_number}")
    print(f"  Location: {port.location}")
    print(f"  Manufacturer: {port.manufacturer}")
    print(f"  Product: {port.product}")
    print(f"  Interface: {port.interface}")

neuro_port = input("Enter your selection here:")

neuropy = Neuro.NeuroPy(neuro_port, "57600")
gamma = 0.8
alpha = 0.05
attention_average = 50
attention_threshold = 65
inattention_threshold_1 = 35
inattention_threshold_2 = 35
model_run = -1
current_gpt = 'Y'


def attention_callback(attention_value):
    global attention_average, alpha
    attention_average = alpha * attention_value + (1 - alpha) * attention_average
    return None


neuropy.setCallBack("attention", attention_callback)
neuropy.start()


def attention_popup(adjust_model):
    reminder_window = tk.Toplevel()
    reminder_window.title("Reminder")
    reminder_window.geometry("300x100")
    reminder_window.wm_attributes("-topmost", 1)

    label = tk.Label(reminder_window, text="Stay focused!")
    label.pack(pady=10)

    button_frame = tk.Frame(reminder_window)
    button_frame.pack(pady=5)

    yes_button = tk.Button(button_frame, text="Good Reminder", command=lambda: adjust_model(reminder_window, True))
    yes_button.pack(side="left", padx=10)

    no_button = tk.Button(button_frame, text="Not Useful", command=lambda: adjust_model(reminder_window, False))
    no_button.pack(side="right", padx=10)

    reminder_window.focus_force()
    log_message("Reminder window triggered.")


last_time = 0


def trivial_model(attention_value, gpt_response):
    global attention_threshold, model_run, inattention_threshold_1, inattention_threshold_2, gamma, attention_average, last_time
    last_time += 1

    def adjust_model(window, feedback):
        window.destroy()
        global attention_threshold, inattention_threshold_1, inattention_threshold_2
        thresh_low_table_1 = {
            (False, True, False): -4,
            (False, True, True): 2,
        }
        thresh_low_table_2 = {
            (False, False, False): -2,
            (False, False, True): 2,
        }
        thresh_high_table = {
            (True, False, False): 4,
            (True, False, True): -2,
        }
        attentiveness = False
        if attention_value > attention_threshold:
            attentiveness = True
        relatedness = False
        if gpt_response == 'Y':
            relatedness = True
        key = (attentiveness, relatedness, feedback)
        factor = gamma ** model_run
        if key in thresh_low_table_1:
            inattention_threshold_1 += thresh_low_table_1[key] * factor
        if key in thresh_low_table_2:
            inattention_threshold_2 += thresh_low_table_2[key] * factor
        if key in thresh_high_table:
            attention_threshold += thresh_high_table[key] * factor

    if last_time >= 4:
        if (gpt_response != 'Y' and attention_average > attention_threshold) or \
                (gpt_response == 'Y' and attention_average < inattention_threshold_1) or \
                (gpt_response != 'Y' and attention_average < inattention_threshold_2):
            model_run += 1
            last_time = 0
            attention_popup(adjust_model)


from openai import OpenAI
from PIL import ImageGrab
# from PIL import Image
import io
import pytesseract
import time

with open('./openaikey') as f: openai_key = f.read()


# Automatically closes the file. No need for explicit close.

# OCR to extract text from the image using pytesseract
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Point pytesseract to exe not in PATH.

client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_key
)


# Take a screenshot
def take_screenshot():
    screenshot = ImageGrab.grab()
    buffer = io.BytesIO()
    screenshot.save(buffer, format='PNG')
    buffer.seek(0)
    return screenshot


# Ask ChatGPT about the text
def ask_chatgpt(question):
    answer = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
        model="gpt-3.5-turbo",
    ).choices[0].message.content
    return answer


quiz_running = False
current_question = ""


def gpt_thread():
    global current_question, quiz_running, current_gpt
    while quiz_running:
        time.sleep(20)
        screenshot = take_screenshot()
        extracted_text = extract_text_from_image(screenshot)

        import re
        _RE_COMBINE_WHITESPACE = re.compile(r"\s+")
        extracted_text = _RE_COMBINE_WHITESPACE.sub(" ", extracted_text).strip()
        context = _RE_COMBINE_WHITESPACE.sub(" ", current_question).strip()

        question = (f"Here is a quiz bowl question.\n{context}\nDo the contents of the following screen grab of my "
                    f"screen partially contain research on Wikipedia towards solving any part of this quiz bowl "
                    f"question, or the question itself?"
                    f"Respond with Yes or No. The following is the result of OCR on the screen grab, "
                    f"so it may be messy:\n{extracted_text}")
        response = ask_chatgpt(question)
        response = " " + response + " "
        current_gpt = 'N'
        pattern = r'\s+(yes|YES|Yes|yEs|YeS|YEs|yeS|YeS)\s+'
        if re.search(pattern, response):
            current_gpt = 'Y'
        log_message(f"asking GPT... Q: {question} A: {current_gpt}")
        print(".", end="", flush=True)


def log_message(message):
    global log_file_path
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} - {message}\n")


root = tk.Tk()


def model_thread():
    global quiz_running, current_gpt, attention_average, root
    trivial_model(attention_average, current_gpt)
    print("-", end="", flush=True)
    log_message(f"Attention: {attention_average} GPT: {current_gpt}")
    if quiz_running:
        root.after(5000, model_thread)


def take_quiz(quiz_data):
    global quiz_running, current_question

    def select_data(data, number):
        tot_list = []
        for index in range(number):
            choice = secrets.randbelow(len(data))
            datum = data[choice]
            data.pop(choice)
            tot_list.append(datum)
        return tot_list

    # Select 10 random questions
    selected_questions = select_data(quiz_data, 10)
    score = 0
    quiz_running = True
    time.sleep(0.3)
    # model_thread_instance = threading.Thread(target=model_thread)
    gpt_thread_instance = threading.Thread(target=gpt_thread)
    # window_thread_instance = threading.Thread(target=window_thread)

    # model_thread_instance.start()
    gpt_thread_instance.start()
    # window_thread_instance.start()

    for i, quiz_entry in enumerate(selected_questions):
        quiz_running = True
        print(f"Question {i + 1}: {quiz_entry['question']}")
        current_question = quiz_entry['question']
        input("Your answer: ").strip().lower()
        # correct_answers = [ans.lower() for ans in quiz_entry['answers']]

        print(f"Correct answers: {', '.join(quiz_entry['answers'])}")
        is_correct = input("Did you get it right? (yes/no): ").strip().lower()

        if is_correct == 'yes':
            score += 1

    def kill_threads():
        global quiz_running
        quiz_running = False
        print("Killing threads...")
        # model_thread_instance.join()
        gpt_thread_instance.join()
        root.destroy()

    atexit.register(kill_threads)

    print("Waiting for quiz to end...")
    quiz_running = False

    print(f"Your final score: {score}/10")

    kill_threads()


def main():
    global quiz_running
    # directory_path = input("Enter the path to the directory containing the quiz bowl PDFs: ").strip()
    # attention_popup(max)
    log_message("Starting up!!!!\n\n")
    quiz_data = extract_quiz_bowl_content_from_directory("./PACE_data")
    root.withdraw()
    quiz_running = True
    quiz_thread = threading.Thread(target=take_quiz, kwargs={"quiz_data": quiz_data})
    quiz_thread.start()
    model_thread()
    # attention_popup()
    root.mainloop()
    quiz_thread.join()


if __name__ == "__main__":
    main()
