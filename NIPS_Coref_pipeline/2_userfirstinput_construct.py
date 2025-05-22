import time
import openai
import json
import random
import re
import requests

from filelock import FileLock

def save_incrementally(dict_data, jsonl_file_path):
    lock_path = f"{jsonl_file_path}.lock"
    lock = FileLock(lock_path)

    with lock:
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
model = ''
temperature = 1

def question_generate(text):
    prompt = f'''I will provide you with a piece of text. Your task is to generate the original user query that would have led to this response. Output only the query, and nothing else.
Text:
{text}
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

with open(input_file, 'r', encoding='utf-8') as file:
    data_list = json.load(file)

save_num = 0  
drop_num = 0  

for data in data_list:
    context = data["context"]
    user_input = question_generate(context)
    if user_input=="":
        continue
    data["user_input"] = user_input
    save_incrementally(data, output_file)

print(f"Responses incrementally saved to {output_file}")
print(f"Saved {save_num} dicts")
print(f"Dropped {drop_num} dicts")
