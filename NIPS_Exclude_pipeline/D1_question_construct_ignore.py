import time
import openai
import json
import random
import requests
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic import conversation_topic_list

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

eaxmple_instruction_list = [
    "Ignoring the selected parts",
    "Ignoring the selected regions",
    "Neglecting the selected parts",
    "Neglecting the selected regions",
    "Do not use the informations in the selected parts",
    "Do not use the informations in the selected regions"
]

def generate_prompt(each_data):
    target_ability =  mission_type = each_data["attributes"]["target_ability"]
    mission_type = each_data["attributes"]["mission_type"]
    quotation_part = generate_quotation_string(each_data)
    eaxmple_instruction = random.choice(eaxmple_instruction_list)
    return {
        "prompt": f'''You are an expert conversation architect tasked with creating a question-answer pair to test the LLM's {target_ability} under the mission type of {mission_type} (Negative/Ignore Quoting Basic Task). You are provided with multiple candidate quotation regions (each an exact, verbatim copy of a segment from a previously generated conversation). Your task is as follows:

1. Plan:
   - Analyze the provided candidate quotations and select **one or more** quotation regions to be **ignored** while answering the question. Decide which quotation part(s) should be ignored and which should remain.
   - The remaining, non-ignored quotation regions must contain **all necessary information** to answer the question correctly, without reference to the ignored regions.
   - Ensure that the question is constructed in a way that using the ignored part(s) would lead to a different answer. Additionally, each answer must be based solely on the information from all non-ignored part(s) relevant to that answer.
   - In your plan, explain which quotations are ignored and which are retained, and provide a rationale for these selections. Describe your approach to formulating a single question that forces the answer to be derived exclusively from **all non-ignored quotations**.

2.Generate:
   - Generate a **single question** that requires using only the non-ignored quotation regions to answer. The question must be abstract enough so that the answer cannot be derived without consulting the selected quotations. The question should contain an instruction like: "{eaxmple_instruction}"
   - Then, for each **ignored set** you have selected, generate an **answer derived exclusively** from the non-ignored regions. The answer must related to the information from all unquoted parts.
   - **Note**: The answer must not reference any information from the ignored quotation regions. Ensure the answers differ based on which quotations are ignored.

For example, if the candidate quotations are:
   - Quotation 1: "The marketing department had a revenue of $50,000 last quarter, reflecting various campaigns aimed at boosting brand visibility."
   - Quotation 2: "The IT department's expenses for the last quarter amounted to $30,000, covering software upgrades and hardware maintenance."
   - Quotation 3: "The sales department's revenue for the last quarter was $75,000, largely due to successful outreach and sales strategies."
   - Quotation 4: "HR's expenses last quarter totaled $20,000, mostly for employee training programs and recruitment activities."

You could choose:
   - Ignore Set 1: Ignore <|quotation2|> and <|quotation4|>  
     - **Question: "{eaxmple_instruction}, what was the total revenue for the marketing and sales departments last quarter?"
     - **Answer1: "The marketing department generated $50,000 and the sales department earned $75,000, totaling $125,000."

   - Ignore Set 2: Ignore <|quotation1|> and <|quotation3|>  
     - **Question: "{eaxmple_instruction}, what were the primary expenses of the IT and HR departments last quarter?"
     - Answer2: "The IT department's expenses were $30,000, and HR’s expenses totaled $20,000."

   - Similarily, Ignore Set 3 could be only <|quotation1|>; Ignore Set 4 could be <|quotation1|><|quotation2|><|quotation4|>;...

### Candidate Quotations:
{quotation_part}

3. Output Format:
   Your output must strictly follow the format below (do not introduce any extra labels):

<Planning>
[Your detailed plan: Describe which candidate quotations you choose to ignore, and explain your rationale for selecting these quotations. Discuss how you will formulate a single question that instructs the respondent to rely solely on the information in the selected quotations. Ensure that each answer is logical.]</Planning>
<Question>
[Generate a question that explicitly instructs the model to answer using only the non-ignored quotations. The question must be abstract enough so that the answer cannot be derived without consulting the selected quotations.]</Question>
<Ignore1>
<|quotationX|><|quotationY|>...[List the candidate quotation tags selected to be ignored. Do not alter their content.]</Ignore1>
<Answer1>
[Your generated answer derived solely from the content of the non-ignored quotations based on Ignore1. The answer should be a logical sentence or paragraph based only on the remaining information.]</Answer1>
<Ignore2>
<|quotationA|><|quotationB|>...[List the candidate quotation tags selected to be ignored.]</Ignore2>
<Answer2>
[Your generated answer derived solely from the content of the non-ignored quotations based on Ignore2. The answer should be a logical sentence or paragraph based only on the remaining information.]</Answer2>
...More Ignore sets and Answers...
'''
}

responses = []
input_file = ""
output_file = ""
batch_size = 1
washed_data = read_json_to_list(input_file)
for each_data in washed_data:
    batch_responses = []
    for i in range(batch_size):
        prompt_data = generate_prompt(each_data)
        response = client.calc(
            query=[{"role": "user", "content": prompt_data["prompt"]}],
            temp=temperature,
            n=1,
            model=model
        )

        for resp in response:
            conversation_data = {
                "conversation": each_data["conversation"],
                "question": resp
            }
            pattern = re.compile(r"^quotation\d+$")
            conversation_data["attributes"] = each_data["attributes"]
            for key, value in each_data.items():
                if pattern.match(key):
                    conversation_data[key] = value

            batch_responses.append(conversation_data)

    # Incrementally save batch
    save_incrementally(batch_responses, output_file)

print(f"Responses incrementally saved to {output_file}")