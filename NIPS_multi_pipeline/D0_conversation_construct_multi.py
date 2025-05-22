import time
import openai
import json
import random
import requests
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic import conversation_topic_list


def save_incrementally(data, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

client = Get()
temperature = 1

conversation_rounds_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
information_points_list = [3, 4, 5, 6]
conversation_style_list = ["Formal", "Casual", "Persuasive", "Analytical", "Creative", "Narrative", "Enthusiastic"]
quotation_length_list = ["sentence", "sentence", "paragraph", "paragraph", "paragraph"]
target_ability_list = ["Multiple-Source Integration Ability (Multiple Quotation Regions)"]
base_mission_type_list = [
    "Multi-Source Information Comparison: Compare or contrast two or more separate quoted passages (e.g., comparing their data, opinions, or attributes). The user's question focuses on differences or similarities across these quoted segments",
    "Multi-Source Consolidated Summarization: Provide a unified summary that covers all key points from two or more quoted passages. The user wants an integrated overview of multiple fragments",
    "Temporal (Time-Order) Reasoning: Determine or explain the chronological order of events or facts mentioned across multiple quoted segments. The user's question involves identifying which event or statement occurred first or last",
    "Contrasting Viewpoints Analysis: Identify differing viewpoints or stances across multiple quoted regions. The user wants to see how authors or speakers in those passages disagree or differ in perspective",
    "Merged Key Point Listing: Extract the core points from each quoted passage and then compile them into a single combined list. The user wants a concise set of bullet points that captures all cited texts",
    "Numerical/Data Comparison Across Sources: Identify and compare numerical values or data points mentioned in two or more quoted passages. The user's question focuses on determining the highest, lowest, or most significant value among these sources.",
    "Numerical/Data Sorting: Extract numerical values or data points from two or more quoted passages and arrange them in a specified order (e.g., from high to low or low to high). The user's question focuses on presenting the data in a sorted list.",
    "Multi-Source Condition Fulfillment: The user poses a set of conditions (e.g., "Condition A is stated in quotation 1, Condition B is in quotation 2"). Ask the model to determine if those conditions are satisfied or met collectively, based strictly on the referenced segments.",
    "Multi-Passage/Sequence Reconstruction: If multiple quoted segments each describe different parts or phases of a single process or timeline, the user asks to arrange these parts in a coherent sequence or flow. Correctness can be verified by checking if each step appears in the right chronological or logical order as indicated by the individual passages.",
]
def generate_prompt():
    conversation_rounds = random.choice(conversation_rounds_list)
    
    if conversation_rounds==1 or conversation_rounds==2:
        information_points = random.choice(information_points_list)
    else:
        information_points = conversation_rounds
    conversation_rounds = str(conversation_rounds)
    conversation_topic = random.choice(conversation_topic_list)
    conversation_style = random.choice(conversation_style_list)
    target_ability = random.choice(target_ability_list)
    quotation_length = random.choice(quotation_length_list)
    mission_type = random.choice(base_mission_type_list)
    if ("Multi-Source Consolidated Summarization" in mission_type) or ("Merged Key Point Listing" in mission_type):
        quotation_length = random.choice(["full response", "long paragraph", "long paragraph"])
    return {
        "conversation_rounds": conversation_rounds,
        "information_points": information_points,
        "conversation_topic": conversation_topic,
        "target_ability": target_ability,
        "mission_type": mission_type,
        "quotation_length": quotation_length,
        "conversation_style": conversation_style,
        "prompt": f'''You are an expert conversation architect. Generate a multi-round conversation that will later be used to test the LLM's {target_ability} in real-world scenarios, focusing on the mission type of {mission_type}. In this task, the conversation must include multiple candidate quotation regions that will be used later to integrate key information for answering questions.
Instructions:
1. The conversation must be centered on a specific subtopic of {conversation_topic} and include at least {conversation_rounds} rounds. The conversation style should be {conversation_style}.
2. The conversation must introduce at least one distinct information point (e.g., specific data, figures, dates, or viewpoints regarding a single subject). All information points should be presented at the same level without differentiating between "key" and "distractor" details. (Every information point is equally important; later, the selection of which points to use for question generation will be determined. For example, only discuss the temperature in different cities on the same day throughout the entire conversation, or only discuss different views on one theory throughout the entire conversation.)
3. The conversation must be constructed so that if, later on, only the selected candidate quotation regions are used, a question on the mission type {mission_type} can be answered conclusively using only that information.
For example:
   - If the conversation includes the prices of three cars (Car A at 10k, Car B at 8k, and Car C at 5k) and candidate quotations are later selected only for Car B and Car C, then a question such as "Which car is the most expensive among the selected quotations?" would yield Car B. (The answer must be derived solely from the information in the quotations.)
   - If the conversation discusses several scientists (e.g., Newton, Hawking, Galileo, Nobel) across different turns and only the segments about Newton and Nobel are selected as quotations, then the answer to "Which scientists are discussed in the selected quotation regions?" should include only Newton and Nobel.
4. After the conversation, output **all** candidate quotation regions. Each candidate must be exactly an {quotation_length} copied verbatim from the assistant's response. These segments should come from different parts of the conversation and represent distinct information points.
5. Fictional content is allowed, as long as it remains logically consistent and coherent.

Conversation Requirements:
   - Generate a `<subtopic>` section that describes the specific subtopic.
   - Then create a `<Planning>` section where you list at least {information_points} distinct information points. List each information point without categorizing them as "key" or "distractor"; simply include the details that will later be available for quotation selection.
   - Next, generate a `<Generation>` section containing the full multi-round conversation. Use the following format:
       - Each user turn begins with `<|user|>\n` and ends with `<|end|>\n`.
       - Each assistant turn begins with `<|assistant|>\n` and ends with `<|end|>\n`.
   - **Do not generate any question** for the LLM to answer in this prompt; you are only creating the conversation text.
   - Do not include any comparisons, versus statements, global overviews, or summaries in the conversation.

Key Addition - Candidate Quotation Regions:
   - After the conversation, output multiple candidate quotation blocks. Each block must follow this format:
       `<|quotationX|>\n[Exact copy of one {quotation_length} from the assistant's response]\n<|end|>\n`
     (Where X is a sequential number.)
   - These candidate quotations must be exact, verbatim copies of segments chosen from different parts of the conversation.
   - When quoting a {quotation_length} in a conversation, do not add any identifiers on either side of the quoted area, such as '**', '\'', etc.

Below is the conversation template (do not introduce any additional labels):
<subtopic>
[Describe the specific subtopic, e.g., "Comparing the prices of different car models in various regions", "Chronology of events in the evolution of renewable energy technology."]</subtopic>
<Planning>
Outline {information_points} distinct information points.
For example:
- Information Point 1: [A specific data point, such as "Car A costs 10k"]
- Information Point 2: [A specific data point, such as "Car B costs 8k"]
- Information Point 3: [A specific data point, such as "Car C costs 5k"]
...
Explain the logical flow of the conversation and how these distinct information points can later be used to derive a conclusive answer for the mission type {mission_type}.
Ensure that the conversation is constructed so that if a future question is generated based solely on the selected candidate quotations, the answer (for mission type {mission_type}) can be derived unambiguously. The additional details in the full conversation will serve as context, but the definitive answer must come solely from the selected quotations.
</Planning>
<Generation>
<|user|>
[User's initial query about an aspect of the subtopic]<|end|>
<|assistant|>
[Assistant's response that incorporates the above information points in a natural conversation.]<|end|>
...Repeat for {conversation_rounds} rounds...
<|quotation1|>
[Exact copy of one {quotation_length} from the assistant's response]<|end|>
<|quotation2|>
[Exact copy of another {quotation_length} from the assistant's response]<|end|>
[Include all candidate quotations]
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    # 添加参数定义
    parser.add_argument("--output_jsonl", type=str, help="")
    parser.add_argument("--model", type=str, default='', help="")
    parser.add_argument("--create_num", type=str, default='300', help="")

    # 解析命令行参数
    args = parser.parse_args()
    output_file = args.output_jsonl
    model = args.model
    create_num = int(args.create_num)

    responses = []
    batch_size = 1
    for _ in range(int(create_num/batch_size)):
        batch_responses = []
        print(_)
        for i in range(batch_size):
            print(i)
            prompt_data = generate_prompt()
            response, _ = client.calc(
                query=prompt_data["prompt"],
                temp=temperature,
                model=model
            )

            for resp in response:
                conversation_data = {
                    "conversation": resp,
                    "attributes": {
                        "conversation_rounds": prompt_data["conversation_rounds"],
                        "information_points": prompt_data["information_points"],
                        "conversation_topic": prompt_data["conversation_topic"],
                        "target_ability": prompt_data["target_ability"],
                        "mission_type": prompt_data["mission_type"],
                        "quotation_length": prompt_data["quotation_length"],
                        "conversation_style": prompt_data["conversation_style"],
                        "model": model
                    }
                }
                batch_responses.append(conversation_data)

        # Incrementally save batch
        save_incrementally(batch_responses, output_file)

    print(f"Responses incrementally saved to {output_file}")
    #  Please begin by analyzing the question, then provide the answer in the format: 'The answer is [option].'