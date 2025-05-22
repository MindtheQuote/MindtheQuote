import time
import openai
import json
import random
import re
import requests

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

def question_generate(data):
    Context = data["context"]
    Noun = data["options"][ data["answer"] ]
    Pronoun = data["pronoun"]
    if Context == "" or Noun == "" or Pronoun == "":
        return ""
    prompt = f'''You are a helpful assistant skilled in generating natural-sounding user queries. Given a context, a noun, and a pronoun that refers to that noun, generate a user question about the referent based on its role in the context. The question must follow these constraints:
1.	The question must mention the pronoun indirectly, using phrases like "the pronoun I selected", "this pronoun", "the pronoun I quoted".
2.	The question must not include any other pronouns or any direct hints about the referent.
3.	The question should focus on the referent’s actions, characteristics, or experiences in the given context.
4.	Provide a direct answer that clarifies what the pronoun refers to based on the context.

Input:
 - Context: {Context}
 - Noun: {Noun}
 - Pronoun: {Pronoun}

Expected Format and Output(Do not use other tags):
Query: A well-formed question referring to {Pronoun} in a inexplicit and constrained way (e.g., "What does the pronoun I selected/the pronoun I quoted/this pronoun do in this context?"), without any additional pronouns or direct hints.
Answer: First, explicitly state that the pronoun refers to {Noun}. Then, explain the role, actions, or characteristics of {Noun} in the given context.
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
    data["Question_and_Answer"] = Question_and_Answer
    save_incrementally(data, output_file)

print(f"Responses incrementally saved to {output_file}")
print(f"Saved {save_num} dicts")
print(f"Dropped {drop_num} dicts")
