import time
import openai
import json
import random
import re
import requests
import argparse
from filelock import FileLock

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line: 
                try:
                    json_obj = json.loads(line)
                    data.append(json_obj)
                except json.JSONDecodeError as e:
                    pass
    
    return data

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

client = Get()
model = ''
temperature = 1

def only_conversation_check(prompt, answer):
    response_conversation = client.calc(
        query=[{"role": "user", "content": prompt}],
        temp=temperature,
        n=1,
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

def only_quotation_check(prompt, answer):
    response_conversation = client.calc(
        query=[{"role": "user", "content": prompt}],
        temp=temperature,
        n=1,
        model=model
    )
    response_conversation = response_conversation[0]
    generate_answer = extract_answer(response_conversation)
    if generate_answer == answer:
        return True
    else:
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str)
    parser.add_argument("--output_jsonl", type=str)

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_jsonl

    responses = []

    data_list = read_jsonl(input_file)

    eaxmple_instruction_list = [
        "Ignoring the quotations",
        "Do not use the quotations",
        "Ignoring the selected parts",
        "Ignoring the selected regions",
        "Neglecting the selected parts",
        "Neglecting the selected regions",
        "Do not use the informations in the selected parts",
        "Do not use the informations in the selected regions",
        "Do not use the information in the selected regions",
        "Do not use the information in the selected parts",
        "Do not use the information in the quoted parts",
        "Do not use the information in the quoted regions",
        "Neglecting the information in the quotations",
    ]

    save_num = 0 
    drop_num = 0 
    for data in data_list:
        options, answer = generate_options_and_answer(data)
        quotation = data["conversation"]

        find_all_Ignore_text = True
        for index, each_part in enumerate(data["Ignore_text"], start=1):
            if each_part not in quotation:
                find_all_Ignore_text = False
                print("find_all_Ignore_text == False")
                break
            quotation = quotation.replace(each_part, "") 
        if find_all_Ignore_text == False:
            continue

        question = data["Question"]
        for eaxmple_instruction in eaxmple_instruction_list:
            question = question.replace(eaxmple_instruction, "")

        only_conversation_check_prompt = data["conversation"] + "<|user|>\nBased entirely on the conversation above, answer the following question:\n" + question + "\n" + options + "D. If multiple or no options are correct, choose D." + "\nPlease analye the question first, then provide the answer in the format strictly: 'The answer is X.' For example: The answer is A.<|end|>\n<|assistant|>\n"
        only_quotation_check_prompt = quotation + "<|user|>\nBased entirely on the conversation above, answer the following question:\n" + question + "\n" + options + "D. If multiple or no options are correct, choose D." + "\nPlease analye the question first, then provide the answer in the format strictly: 'The answer is X.' For example: The answer is A.<|end|>\n<|assistant|>\n"

        conversation_check_flag = only_conversation_check(only_conversation_check_prompt, answer)
        if conversation_check_flag == False:
            drop_num += 1
            print("drop one")
            continue

        quotation_check_flag = only_quotation_check(only_quotation_check_prompt, answer)
        if quotation_check_flag:
            save_incrementally(data, output_file) # Incrementally save dict
            save_num += 1
            print("save one")
        else:
            drop_num += 1
            print("drop one")

    print(f"Responses incrementally saved to {output_file}")
    print(f"Saved {save_num} dicts")
    print(f"Dropped {drop_num} dicts")
