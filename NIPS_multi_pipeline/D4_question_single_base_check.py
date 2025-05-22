import time
import openai
import json
import random
import re
import requests

import argparse
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
model = 
temperature = 1

def only_conversation_check(prompt, answer):
    response_conversation, _ = client.calc(
        query=prompt,
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
    response_conversation, _ = client.calc(
        query=prompt,
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

    parser.add_argument("--input_json", type=str, help="")
    parser.add_argument("--output_jsonl", type=str, help="")
    parser.add_argument("--model", type=str, help="")

    args = parser.parse_args()
    input_file = args.input_json
    output_file = args.output_jsonl
    model = args.model

    responses = []

    with open(input_file, 'r', encoding='utf-8') as file:
        data_list = json.load(file)

    save_num = 0
    drop_num = 0
    for data in data_list:
        options, answer = generate_options_and_answer(data)
        quotation = ""
        for index, each_part in enumerate(data["Reference_text"], start=1):
            quotation += f"paragraph{index}" + each_part + "\n"

        only_conversation_check_prompt = data["conversation"] + "<|user|>\nBased entirely on the conversation above, answer the following question:\n" + data["Question"] + "\nOptions:\n" + options + "\nD. If two or more of the options A, B and C are correct, or all of them are wrong, then choose D." + "\nPlease begin by analyzing the question, then provide the answer in the format: 'The answer is X.'(Do not include other marker)<|end|>\n<|assistant|>\n"
        only_quotation_check_prompt = quotation + "\nBased entirely on these paragraphs, answer the following question:\n" + data["Question"] + "\nOptions:\n" + options + "\nD. If two or more of the options A, B and C are correct, or all of them are wrong, then choose D." + "\nPlease begin by analyzing the question, then provide the answer in the format: 'The answer is X.'(Do not include other marker)"

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
