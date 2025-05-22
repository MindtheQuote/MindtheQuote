import time
import openai
import json
import random
import requests
import re
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filelock import FileLock

def save_incrementally(data, file_path):
    lock_path = file_path + ".lock"
    lock = FileLock(lock_path)
    try:
        with lock:
            with open(file_path, "a", encoding="utf-8") as f:
                for entry in data:
                    json.dump(entry, f, ensure_ascii=False)
                    f.write("\n")
    except Exception as e:
        print(f"Error saving data: {e}")

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

def read_json_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    if isinstance(data, list):
        return data
    else:
        raise ValueError("")

def generate_quotation_string(quotation_dict):
    items = []
    for key, value in quotation_dict.items():
        if key.startswith("quotation"):
            try:
                num = int(key[len("quotation"):])
                items.append((num, key, value))
            except ValueError:
                continue

    items.sort(key=lambda x: x[0])

    result = []
    for _, key, value in items:
        result.append(f"<|{key}|>\n{value}<|end|>\n")

    return "".join(result)

client = Get()
model = ''
temperature = 1

example_instruction_list = [
    "Ignoring the selected parts",
    "Ignoring the selected regions",
    "Neglecting the selected parts",
    "Neglecting the selected regions",
    "Do not use the information in the selected parts",
    "Do not use the information in the selected regions"
]

def generate_prompt(text):
    example_instruction = random.choice(example_instruction_list)
    return {
        "prompt": f'''You will be provided with a question that references "selected parts" of a text or dataset, such as:
"With only the details given in the selected parts, xxx."

Your task is to modify the question so that it instead instructs the model to ignore the selected parts while retaining the rest of the question's structure and meaning as much as possible. For example, the revised question should read:
"{example_instruction}, xxx."

Ensure that the modification maintains clarity and logical coherence, and minimizes changes to the original phrasing beyond changing "With only the details given in the selected parts" to "{example_instruction}".
You should only output the changed question.
Question:
{text}
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, help="")
    parser.add_argument("--output_jsonl", type=str, help="")

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_jsonl

    responses = []
    batch_size = 1
    washed_data = read_jsonl(input_file)
    num=0
    for each_data in washed_data:
        print(num)
        num+=1
        batch_responses = []
        for i in range(batch_size):
            prompt_data = generate_prompt(each_data['Question'])
            response = client.calc(
                query=[{"role": "user", "content": prompt_data["prompt"]}],
                temp=temperature,
                n=1,
                model=model
            )

            for resp in response:
                conversation_data = each_data
                conversation_data['Question'] = resp
                batch_responses.append(conversation_data)

        # Incrementally save batch
        save_incrementally(batch_responses, output_file)

    print(f"Responses incrementally saved to {output_file}")