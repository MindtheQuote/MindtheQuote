import time
import openai
import json
import random
import re
import requests
import argparse
from filelock import FileLock

def clean_and_extract(input_string):
    def remove_spaces_around_tags(s):
        return re.sub(r'\s*<([^>]+)>\s*', r'<\1>', s)

    input_string = remove_spaces_around_tags(input_string)

    match = re.search(r'<correct_answer>.*</wrong_answer>', input_string, re.DOTALL)

    cleaned_string = match.group(0)

    correct_answer_match = re.search(r'<correct_answer>(.*?)</correct_answer>', cleaned_string, re.DOTALL)

    correct_answer = correct_answer_match.group(1).strip()

    wrong_answer_match = re.search(r'<wrong_answer>(.*?)</wrong_answer>', cleaned_string, re.DOTALL)
    wrong_answer = wrong_answer_match.group(1).strip()

    return correct_answer, wrong_answer

def save_incrementally(dict_data, jsonl_file_path):
    with open(jsonl_file_path, 'a', encoding='utf-8') as file:
        json.dump(dict_data, file, ensure_ascii=False)
        file.write('\n')

def generate_nobg_paragraph(data):
    quotation = "Quotations:\n"
    i = 1
    for item in data['Reference']:
        if item not in data:
            return ""
        quotation += data[item] + "\n\n"
    return quotation

client = Get()
model = ''
temperature = 1

def distractor_generate(prompt):
    response_conversation, _ = client.calc(
        query=prompt,
        temp=temperature,
        model=model
    )
    response_conversation = response_conversation[0]
    return response_conversation

eaxmple_instruction_list = [
    "With only the details given in the chosen quotations plus the background, please answer",
	"Please base your response solely on the information found in the selected quotations and the background",
	"Using only the details provided in the chosen quotations plus the unquoted context",
	"Rely exclusively on the chosen quotations and the remaining background to give your answer",
	"Please derive your answer strictly from the content of the selected quotations and the remaining background from the conversation",
    "Craft your answer purely using the facts in the chosen quotation regions alongside the background context",
]

# 主函数
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_json", type=str, default='', help="")
    parser.add_argument("--output_jsonl", type=str, default='', help="")
    parser.add_argument("--model", type=str, default='')

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
        no_bg_paragraph = generate_nobg_paragraph(data)
        if no_bg_paragraph == "":
            continue
        nobg_check_prompt = no_bg_paragraph + "\n" + "Question:\n" + data["Question"] + "\nPlease generate the answer based only on the quotation region. Answer:"
        for eaxmple_instruction in eaxmple_instruction_list:
            nobg_check_prompt = nobg_check_prompt.replace(eaxmple_instruction, "")
        correct_answer = distractor_generate(nobg_check_prompt)
        if correct_answer == "":
            continue
        data["distractor1"] = data["distractor1"][0]
        data["distractor2"] = correct_answer
        save_incrementally(data, output_file)

    print(f"Responses incrementally saved to {output_file}")
    print(f"Saved {save_num} dicts")
    print(f"Dropped {drop_num} dicts")
