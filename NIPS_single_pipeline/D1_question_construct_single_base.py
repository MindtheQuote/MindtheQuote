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

from topic import conversation_topic_list

def save_incrementally(data, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

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
temperature = 1

def generate_prompt(each_data):
    target_ability =  mission_type = each_data["attributes"]["target_ability"]
    mission_type = each_data["attributes"]["mission_type"]
    quotation_part = generate_quotation_string(each_data)
    return {
        "prompt": f'''You are an expert question architect. Below are multiple candidate quotation passages from a conversation. **Each** quotation is a verbatim excerpt from that conversation. In this stage, you will generate a question and several answers for testing an LLM's {target_ability}, specifically the {mission_type}. Follow these instructions strictly:

Generation Requirements:
1. Propose **one** question that can be answered by relying solely on **one** chosen quotation region at a time.
2. For each quotation, produce a separate answer, using only the content within that specific quotation.
3. You must explicitly **forbid referencing** any other quotation region when answering for a particular quotation.
4. The question must be designed such that each quotation alone could plausibly answer it and yield a different answer each other.
5. The final output should follow the structure:
<Planning>
A concise plan of how you will create a question that can be answered from each quotation independently, plus how those answers may differ or be incomplete when referencing a single quotation.
<Generation>
<|Question|>\n[Your single question]<|end|>
<|quotation1_answer|>\n[Answer based strictly on quotation1]<|end|>
<|quotation2_answer|>\n[Answer based strictly on quotation2]<|end|>
...and so on for all provided quotations...

Here are the candidate quotations (do not merge or alter them; treat each as an isolated snippet when answering):
{quotation_part}
...

**Important**:
- Rely on exactly one quotation at a time to produce each corresponding answer.
- **Do not** incorporate knowledge from the other quotations in that specific answer.
- **Do not** import external or world knowledge. 
- Keep each answer strictly grounded in the text of the quoted region itself, even if that information is incomplete or ambiguous.

Below is the conversation template (do not introduce any other labels beyond what is specified):
<Planning>\n[Outline your approach to forming a single question and distinct answers for each quotation]<|end|>
<Generation>
<|Question|>\n[One question that can be answered differently (or partially) by each individual quotation snippet]<|end|>
<|quotation1_answer|>\n[Answer derived ONLY from quotation1]<|end|>
<|quotation2_answer|>\n[Answer derived ONLY from quotation2]<|end|>
<|quotation3_answer|>\n[Answer derived ONLY from quotation3]<|end|>
[… repeat for however many quotations exist …]
'''
}


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description="")

    # 添加参数定义
    parser.add_argument("--input_json", type=str, help="")
    parser.add_argument("--output_jsonl", type=str, help="")
    parser.add_argument("--model", type=str, default='', help="")
    
    # 解析命令行参数
    args = parser.parse_args()
    input_file = args.input_json
    output_file = args.output_jsonl
    model = args.model

    responses = []
    batch_size = 1
    washed_data = read_json_to_list(input_file)
    num = 0
    for each_data in washed_data:
        print(num)
        num+=1
        batch_responses = []
        for i in range(batch_size):
            prompt_data = generate_prompt(each_data)
            response, _ = client.calc(
                query=prompt_data["prompt"],
                temp=temperature,
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
    #  Please begin by analyzing the question, then provide the answer in the format: 'The answer is [option].'