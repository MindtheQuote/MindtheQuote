import time
import openai
import json
import random
import re
import requests

from filelock import FileLock

def read_jsonl_to_list(file_path):
    data_list = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data_list.append(json_obj)
    return data_list

def generate_options_and_answer(data):
    gt_label = data.get("gt_label", "")
    distractor1 = data.get("distractor1", "")
    distractor2 = data.get("distractor2", "")

    options = [gt_label, distractor1, distractor2]
    random.shuffle(options)
    option_labels = ["A", "B", "C"]
    formatted_options = "\n".join([f"{label}. {option}" for label, option in zip(option_labels, options)])

    correct_index = options.index(gt_label)
    answer = option_labels[correct_index]

    return formatted_options, answer

def save_incrementally(dict_data, jsonl_file_path):
    with open(jsonl_file_path, 'a', encoding='utf-8') as file:
        json.dump(dict_data, file, ensure_ascii=False)
        file.write('\n')

def extract_answer(input_string):
    input_string = input_string.lower()
    pattern = r"the\s*(answer|correct\s*option)\s*(is|are)\s*\(?\s*([a-zA-Z, ]+)\s*\)?"
    matches = re.findall(pattern, input_string)
    if not matches:
        return "X"
    options_set = set()
    for match in matches:
        options = match[2].strip()
        options_split = [opt.strip().upper() for opt in options.replace('and', ',').split(',')]
        for opt in options_split:
            if opt in options_set:
                continue
            options_set.add(opt)
    if len(options_set) > 1:
        return "X"
    return options_set.pop()

def generate_bg_and_quotation_paragraph(data): 
    quotation_keys = [key for key in data.keys() if key.startswith("quotation") and key[9:].isdigit()]
    reference_keys = data.get('Reference', [])

    Background_list = [key for key in quotation_keys if key not in reference_keys]

    quotation = "**Quotations**:\n"
    for each_quotation_tag in data['Reference']:
        quotation = quotation + data[each_quotation_tag] + "\n\n"

    background_conversation = "**Backgrounds**:\n"
    quotation += background_conversation
    for each_background_tag in Background_list:
        quotation = quotation + data[each_background_tag] + "\n\n"

    return quotation
    
def generate_quotation_paragraph(data): 
    quotation = "**Quotations**:"
    for each_quotation_tag in data['Reference']:
        quotation = quotation + data[each_quotation_tag] + "\n\n"
    return quotation

def generate_conversation_paragraph(data):
    conversation = data['conversation']
    return conversation

client = Get()
model = ''
temperature = 1

def conversation_check(prompt, answer):
    response_conversation, _ = client.calc(
        query=prompt,
        temp=temperature,
        model=model
    )
    response_conversation = response_conversation[0]
    generate_answer = extract_answer(response_conversation)
    if generate_answer == 'X':
        print("X")
    if generate_answer != answer:
        return True
    else:
        return False

def quotation_check(prompt, answer):
    response_conversation, _ = client.calc(
        query=prompt,
        temp=temperature,
        model=model
    )
    response_conversation = response_conversation[0]
    generate_answer = extract_answer(response_conversation)
    if generate_answer == 'X':
        print("X")
    if generate_answer != answer: 
        return True
    else:
        return False

def bg_and_quotation_check(prompt, answer):
    response_conversation, _ = client.calc(
        query=prompt,
        temp=temperature,
        model=model
    )
    response_conversation = response_conversation[0]
    generate_answer = extract_answer(response_conversation)
    if generate_answer == answer:
        return True
    else:
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, default='', help="")
    parser.add_argument("--output_jsonl", type=str, default='', help="")

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_jsonl

    responses = []

    data_list = read_jsonl_to_list(input_file)
    print(input_file)

    save_num = 0  
    drop_num = 0  
    for data in data_list:
        try:
            options, answer = generate_options_and_answer(data)

            bg_and_quotation_paragraph = generate_bg_and_quotation_paragraph(data)
            quotation_paragraph = generate_quotation_paragraph(data)
            conversation_paragraph = generate_conversation_paragraph(data)

            bg_and_quotation_check_prompt = bg_and_quotation_paragraph + "Which option of the following question best addresses the issue raised in the Quotation section: \n" + data["Question"] + "\nOptions:\n" + options + "\nD. If two or more of the options A, B and C are correct, or all of them are wrong, then choose D." + "\nThe correct answer should primarily focus on the quotation part, while drawing from the extensive background information available, and clearly use the one or more pieces of information that are most relevant to effectively address the question. Please output the analysis of each option first, then choose the correct option in the following format: 'The answer is X.'(Do not include other marker)"
            quotation_check_prompt = quotation_paragraph + " Answer the following Single-Choice questions based solely on the Quotation paragraphs above:\n" + data["Question"] + "\nOptions:\n" + options + "\nD. If two or more of the options A, B and C are correct, or all of them are wrong, then choose D." + "\nThe correct answer must not include the information not from the quotation parts. Please output the analysis of each option first, then choose the correct option in the following format: 'The answer is X.'(Do not include other marker)"
            conversation_check_prompt = conversation_paragraph + "<|user|>\nAnswer the following Single-Choice questions based solely on the preceding conversation:\n" + data["Question"] + "\nOptions:\n" + options + "\nD. If two or more of the options A, B and C are correct, or all of them are wrong, then choose D." + "\nPlease focus only on whether each option contains sufficient information, and do not pay attention to how each option is written. Please output the analysis of each option first, then choose the correct option in the following format: 'The answer is X.'(Do not include other marker)<|end|>\n<|assistant|>\n"

            quotation_check_flag = quotation_check(quotation_check_prompt, answer) 
            if quotation_check_flag == False:
                drop_num += 1
                print("drop one quotation_check")
                continue

            conversation_check_flag = conversation_check(conversation_check_prompt, answer)
            if conversation_check_flag == False:
                drop_num += 1
                print("drop one conversation_check")
                continue

            bg_and_quotation_flag = bg_and_quotation_check(bg_and_quotation_check_prompt, answer)
            if bg_and_quotation_flag:
                save_incrementally(data, output_file) # Incrementally save dict
                save_num += 1
                print("save one")
            else:
                drop_num += 1
                print("drop one bg_and_quotation")
        except Exception as e:
            print(f"Error: {e}")
            drop_num += 1
            print("drop one due to unexpected error")
            continue

    print(f"Responses incrementally saved to {output_file}")
    print(f"Saved {save_num} dicts")
    print(f"Dropped {drop_num} dicts")