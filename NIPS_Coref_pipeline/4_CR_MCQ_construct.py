import time
import openai
import json
import random
import re
import requests
from filelock import FileLock

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

def format_multiple_choice(options):
    required_keys = {'A', 'B', 'C', 'D'}
    if set(options.keys()) != required_keys:
        raise ValueError("")
    
    formatted_options = "\n".join(f"{key}. {options[key]}" for key in sorted(options))
    return formatted_options

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

def save_incrementally(dict_data, jsonl_file_path):
    with open(jsonl_file_path, 'a', encoding='utf-8') as file:
        json.dump(dict_data, file, ensure_ascii=False)
        file.write('\n')
    
def generate_nobg_paragraph(data):
    quotation = ""
    i = 1
    for item in data['Reference']:
        quotation += f"quotation {i}:\n" + data[item]
        i+=1
    return quotation

client = Get()
model = 'g'
temperature = 1

def question_generate(data):
    Context = data["context_with_select"]
    Question = data["question"]
    Options = data["options"]
    Options = format_multiple_choice(Options)
    Question = Question + "\n" + Options
    if Context == "" or Question == "":
        return ""
    prompt = f'''You are a highly capable assistant. You have been provided with the following input:
1.	A context containing a pronoun that is marked using <emphasize> tags.
2.	A single-choice question asking which option’s noun this pronoun refers to.

Your task is:
1.	Identify the correct noun that the pronoun refers to.
2.	Provide a detailed explanation focusing on why that noun is the correct referent, without mentioning or referencing the <emphasize> tags in your answer.
3.	End your response with a single line in the exact format:
The answer is X.
where X is the chosen option (for example, A, B, C, or D).

Please note:
 - Do not mention or display the <emphasize> tags in any way.
 - Your explanation should clearly demonstrate how you determined the pronoun’s referent but should not use any extraneous symbols or special characters.
 - Only output the explanation and answer fluently, do not output any other irrelevant information..

Input:
 - Context with marked pronoun: {Context}
 - Multiple-choice Question: {Question}
'''
    response_conversation = client.calc(
        query=[{"role": "user", "content": prompt}],
        temp=temperature,
        n=1,
        model=model
    )
    response_conversation = response_conversation[0]
    return response_conversation


responses = []
input_file = ""
output_file = ""

data_list = read_jsonl(input_file)

save_num = 0
drop_num = 0

for data in data_list:
    Question_and_Answer = question_generate(data)
    if Question_and_Answer=="":
        continue
    label = extract_answer(Question_and_Answer)
    if label == data["answer"]:
        data["choice_gt_label"] = Question_and_Answer
        save_incrementally(data, output_file)
        print("save one")
    else:
        print("drop one")

print(f"Responses incrementally saved to {output_file}")
print(f"Saved {save_num} dicts")
print(f"Dropped {drop_num} dicts")
