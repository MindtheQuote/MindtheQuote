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
temperature = 1

eaxmple_instruction_list = [
    "Please answer using only the details given in the chosen quotations and the related background.",
    "Please base your response solely on the information found in the selected quotations and the relevant background",
    "Please use only the details provided in the chosen quotations and the relevant unquoted context to craft your response",
    "Rely exclusively on the chosen quotations and the relevant background to give your answer",
    "Please derive your answer strictly from the content of the selected quotations and the related background",
    "Craft your answer using only the facts in the chosen quotations and the relevant background context",
]

def generate_prompt(each_data):
    mission_type = each_data["attributes"]["selected_mission_type_list"][0]
    quotation_part = generate_quotation_string(each_data)
    eaxmple_instruction = random.choice(eaxmple_instruction_list)
    return {
        "prompt": f'''You are an expert conversation architect tasked with creating a question-answer pair for testing the LLM's ability on the question of **{mission_type}**. You are provided with multiple candidate quotation regions (each an exact, verbatim copy of a segment from a previous conversation). Your task is as follows:

1. Plan:
   - Analyze the provided candidate quotations. Partition them for each Reference Set and Background Set (You should create several pairs of Reference Sets and Background Sets.):
     - A subset marked as the "quoted region(s)" (at least one quotation, possibly more).
     - Select all quotations from the remaining candidate quotation that can serve as background information for the quoted region(s) and use them as the background.
     - Ensure that the Reference Set and Background Set include all information necessary to answer the question, while other candidate quotations must not contain any information related to the content in the Reference Set.
   - You need to devide several Reference Set and Background Set, each chosen Reference Set plus their Background Set together must contain all the information relevant and needed to answer a single question. Critically, neither the chosen quotation(s) alone nor the background alone should suffice to answer that question accurately.
   - Formulate ONE question that focus on the information in the Reference Set, and correctly answering the question will require referencing the selected background information.
   - The single question must yield different answers depending on which Reference Set (quotation(s) and their associated backgrounds) is used.
   - In your plan, clearly explain your rationale for:
     - How you decided which quotation(s) to designate as 'Reference Set' and which as 'Background Set' in each Reference Set and Background Set.
     - How you constructed the problem that meets the above requirements.

2. Generate:
   - Generate exactly ONE question that includes an instruction like: "{eaxmple_instruction}"
   - Then, for each Reference Set and Background Set you have chosen:
     1) Show which quotation(s) are in the <ReferenceX> block.
     2) Show which quotation(s) are in the <BackgroundX>.
     3) Produce an <AnswerX> that can clearly answer the generated question:
        • Must include the information from <ReferenceX> + <BackgroundX>.
        • The answer should primarily focus on the information in the <Reference> section, using only the content from <Background> as supplementary information.
        • For different Reference Sets and Background Sets, the Answer must be as distinct as possible. The answer should first briefly identify the content of the referenced area in the current Reference Set, then provide the response.

Question example:
Example1:
    quotation1: user: I am very tired from work today.
    quotation2: assistant: Then you should rest early.
    Reference: quotation2
    Background: quotation1
    Question: What is the reason for the statement in the quotation part?
    Answer: You referenced the statement where the assistant suggested that the user take a break. This is connected to the Background where the user says, "I am very tired from work today." So the reason for this statement is the user's tiredness from work.

Example2:
    quotation1: Item A: 10 dollar.
    quotation2: Item B: 8 dollar.
    quotation3: Item C: 5 dollar.
    quotation4: Item A is made in Country X.
    quotation5: Item A is made in Country Y.
    quotation6: Item A is made in Country Z.
    Reference: quotation2
    Background: quotation1, quotation3(contain all information relevant with the quotation part)
    Question: Which item is more expensive than the one I have chosen?
    Answer: You quoted Item B, which is 8 dollar, so Item A is more expensive than the item you have chosen.

Do not introduce quotation tags(e.g., quote 1, <|quotation1|>, quotation 1) in the Answer; use the content of the quotation directly. The quotation tags are for generating the Reference Sets and Background Sets.

3. Output Format:
   Your output must strictly follow the format below (do not introduce any extra labels or deviate from the tags). You should list the chosen quotation tags verbatim inside <ReferenceX>, then list the quotation tags relevent with them inside <BackgroundX>
<Planning>
[Your detailed plan.]</Planning>
<Question>
[Generate one question here, including instructions like "{eaxmple_instruction}". The question should be ambiguous enough that the answer cannot be derived without knowing which paragraphs are treated as quotations.]</Question>
<Reference1>
<|quotationX|></Reference1>[List only the candidate quotation tags selected for Reference Set 1;]
<Background1>
<|quotationM|><|quotationN|><|quotationK|></Background1>[List only the candidate quotation tags selected for Background Set 1; do not include their content.]
<Answer1>
[Your answer primarily focus on the information in the <Reference1>, using the content from <Background1> as supplementary information. When answering the Question, the Answer must explicitly utilize information from both the <Reference1> and the <Background1>.]</Answer1>
<Reference2>
<|quotationA|><|quotationB|></Reference2>
<Background1>
<|quotationI|><|quotationJ|></Background1>
<Answer2>
[Your answer primarily focus on the information in the <Reference2>, using the content from <Background2> as supplementary information. When answering the Question, the Answer must explicitly utilize information from both the <Reference2> and the <Background2>.]</Answer2>
...and so on for any sets...

Candidate Quotations:
{quotation_part}
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_json", type=str, default='', help="")
    parser.add_argument("--output_jsonl", type=str, default='', help="")
    parser.add_argument("--model", type=str, default='', help="")

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