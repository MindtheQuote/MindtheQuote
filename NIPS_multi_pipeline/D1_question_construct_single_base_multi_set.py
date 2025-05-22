import time
import openai
import json
import random
import requests
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
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
model = ''
temperature = 1

example_question_list = [
    "Based solely on the data provided in the quotations, arrange the revenue figures in ascending order.",
	"Using only the details contained in the quoted parts, order the reported revenue values from lowest to highest.",
	"Refer exclusively to the information in the quotations to sort the revenue figures from the smallest to the largest.",
	"With only the details given in the selected parts, rank the revenue amounts in increasing order.",
	"Using just the data from the the quoted parts, list the revenue figures in order from low to high."
]

eaxmple_instruction_list = [
    "Based solely on the data provided in the quotations",
	"Using only the details contained in the quoted parts",
	"Refer exclusively to the information in the quotations",
	"With only the details given in the selected parts",
	"Using just the data from the the quoted parts"
]

def generate_prompt(each_data):
    target_ability =  mission_type = each_data["attributes"]["target_ability"]
    mission_type = each_data["attributes"]["mission_type"]
    quotation_part = generate_quotation_string(each_data)
    example_question = random.choice(example_question_list)
    eaxmple_instruction = random.choice(eaxmple_instruction_list)
    return {
        "prompt": f'''You are an expert conversation architect tasked with creating a question-answer pair for testing the LLM's {target_ability} under the mission type of {mission_type} (Multi-Source Integration Basic Task). You are provided with multiple candidate quotation regions (each an exact, verbatim copy of a segment from a previously generated conversation). Your task is as follows:

1. Plan:
   - Analyze the provided candidate quotations and decide on several distinct subsets (Reference Sets) of these quotations. Each Reference Set must include multi of the candidate quotations (i.e. not all and not only one), and these sets could have some overlap.
   - Each Reference Set must, by itself, contain all the necessary information to answer a single question for the mission type {mission_type}. Importantly, the same question should yield different answers when answered solely based on each different Reference Set.
   - In your plan, clearly explain your rationale for choosing these quotations for each Reference Set and describe your approach to formulating a single question that forces the answer to be derived exclusively from the selected quotations.

2. Generate:
   - Generate one question that includes the instruction like "{eaxmple_instruction}."(For reference only.) The question must not include any specific details that could directly help locate the information within the conversation. The question should suit for each reference set, so it must be vague enough.
   - Then, for each Reference Set you have selected, generate an answer derived exclusively from the information contained in that set. The answers should differ based solely on which candidate quotations are used.
   - **Note:** The answer must not include any information from candidate quotations that were not selected in the corresponding Reference Set.

    For example, if the candidate quotations are:
    - quotation1: "Sure thing! The marketing department had a solid quarter. They generated a revenue of $50,000. It's important to note that this figure reflects their efforts in various campaigns and initiatives aimed at boosting brand visibility and customer engagement."
    - quotation2: "Absolutely. The IT department's expenses for the last quarter amounted to $30,000. This includes costs related to software upgrades, hardware maintenance, and cybersecurity measures to ensure our systems remain robust and secure."
    - quotation3: "Yes, the sales department performed quite well. They managed to bring in a revenue of $75,000 for the quarter. This is a significant achievement, reflecting strong sales strategies and effective market outreach."
    - quotation4: "Certainly. The HR department's expenses for the last quarter were $20,000. This covers areas like employee training programs, recruitment activities, and benefits administration, all crucial for maintaining a healthy work environment."

    You can choose:
    - Reference1: <|quotation1|><|quotation3|>
    - Reference2: <|quotation2|><|quotation3|>
    - Reference3: <|quotation3|><|quotation4|>
    - Reference4: <|quotation1|><|quotation2|><|quotation4|>
    - Reference5: <|quotation2|><|quotation3|><|quotation4|>
    ...
    Your generated question might be abstractly phrased (e.g., "{example_question}"), and the corresponding answers would be derived exclusively from the respective sets.

    The question must not include any specific details that could directly help locate the information within the conversation. The question should suit for each reference set, so it must be vague enough.
    Remember: Only one question should be generated, and it must explicitly instruct that the answer be based solely on the information in the selected reference quotations. The answers for each Reference Set must be entirely derived from the selected quotations in that set, and differences in the reference sets should lead to different answers.

Candidate Quotations:
{quotation_part}

3. Output Format:
   Your output must strictly follow the format below (do not introduce any extra labels):

<Planning>
[Your detailed plan: Describe which candidate quotations you choose for Reference Set X, and explain your rationale for each. Explain your approach to formulating a single question that instructs the respondent to rely solely on the information in the selected quotations. Ensure that each answer is logical.]</Planning>
<Question>
[Generate one question that includes instructions such as "{eaxmple_instruction}." The question must be abstract enough so that the answer cannot be derived without consulting the selected quotations.]</Question>
<Reference1>
<|quotationX|><|quotationY|>...[List the candidate quotation tags selected for Reference Set 1; do not alter their content.]
</Reference1>
<Answer1>
[Your generated answer derived solely from the content of Reference1. The answer should be a logical sentence or paragraph.]</Answer1>
<Reference2>
<|quotationA|><|quotationB|>...[List the candidate quotation tags selected for Reference2; do not alter their content.]</Reference2>
<Answer2>
[Your generated answer derived solely from the content of Reference2. The answer should be a logical sentence or paragraph.]</Answer2>
...More Reference sets and Answers...
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    # 添加参数定义
    parser.add_argument("--input_json", type=str, help="")
    parser.add_argument("--output_jsonl", type=str, help="")
    parser.add_argument("--model", type=str, help="")

    # 解析命令行参数
    args = parser.parse_args()
    input_file = args.input_json
    output_file = args.output_jsonl
    model = args.model

    responses = []
    batch_size = 1
    washed_data = read_json_to_list(input_file)
    for each_data in washed_data:
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