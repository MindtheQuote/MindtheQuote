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

conversation_rounds_list = [1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]   #
information_points_list = [2, 3, 4, 5, 6, 7, 8, 9, 10]
conversation_style_list = ["Formal", "Casual", "Persuasive", "Analytical", "Creative", "Narrative", "Enthusiastic"]
quotation_length_list = ["complete sentence", "complete paragraph"]
target_ability_list = ["Basic Quoting Ability (Single Quotation Region)"]
base_mission_type_list = [
    "Specified Passage Summarization: Summarize the single quoted passage into a concise statement. The user wants a brief overview or main idea derived exclusively from the quoted text",
    "Specified Segment Q&A: Answer a question based only on the single quoted text. The user's query should be resolved strictly using information found in that quoted segment",
    "Specified Segment Definition Extraction: Identify and restate the definition of a term or concept mentioned in the quoted text. The user is asking for a precise definition contained within that segment",
    "Keyword or Key-Phrase Extraction: Extract the most relevant keywords or key phrases from the single quoted segment. This task focuses on highlighting crucial points or topics directly mentioned",
    "Quoted Segment Rewriting: Rewrite the quoted segment while retaining its essential meaning. The user ask for a more readable or differently styled version of the same text",
    "Quoted Passage Simplification: Simplify the quoted passage while retaining its essential meaning. The user may ask for a more concise, more readable, or differently styled version of the same text",
    "Quoted Segment Sentiment Analysis: Analyze the emotions or attitudes expressed in the quoted segment. Identify and describe the feelings, such as happiness, sadness, anger, or neutrality, conveyed in the quoted region",
    "Quoted Segment Data Extraction: Extract requested data or details from the quoted segment. Focus on retrieving specific facts or figures mentioned in the text",
    "Quoted Segment True-or-False Verification: Present a factual statement about the single quoted text, and ask the model to determine whether it is True or False based strictly on that text. This can be verified by checking if the statement directly aligns or contradicts with the content in the quoted passage.",
    "Quoted Passage Step-by-Step Procedure Extraction: If the single quoted text describes a procedure or a set of ordered steps, request the model to list each step or stage in the correct sequence. The correctness can be checked by confirming each listed step appears (in the right order) within the quoted region.",
    "Specified Segment Contradiction Detection: Present a statement or claim and ask whether it contradicts the single quoted text, is supported by it, or is not mentioned at all. This is easy to verify: simply compare the statement to the quoted text to see if it's in direct conflict, alignment, or absent.",
    "Specified Information Existence Detection: Present a statement or claim and ask whether it appears in the quoted text. In this task, the statement refers to information that exists in the unquoted portion of the original context but not in the quoted segment. By comparing the statement to the quoted text, the model should determine if the statement is indeed absent there.",
    "Quoted Passage Named Entity Identification: Ask the model to extract and list all named entities (e.g., people, locations, organizations) exactly as they appear in the single quoted text. The correctness is judged by directly checking the text to see if any named entities are missed or incorrectly added.",
    "Quoted Segment Key Fact Listing: Instruct the model to list out the key factual points explicitly mentioned in the single quoted text (e.g., important dates, statistics, proper names, etc.). The user then checks if each item in the model's list appears verbatim (or unambiguously) in the passage, ensuring no extra or missing facts.",
]

def save_incrementally(data, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

client = Get()
temperature = 1

def generate_prompt():
    conversation_rounds = random.choice(conversation_rounds_list)
    if conversation_rounds == "1":
        information_points = random.choice(information_points_list)
    else:
        information_points = conversation_rounds
    conversation_rounds = str(conversation_rounds)
    mission_type = random.choice(base_mission_type_list)

    conversation_topic = random.choice(conversation_topic_list)
    conversation_style = random.choice(conversation_style_list)
    target_ability = random.choice(target_ability_list)
    quotation_length = random.choice(quotation_length_list)
    if ("Quoted Passage Simplification" in mission_type) or ("Specified Passage Summarization" in mission_type):
        quotation_length = random.choice(["complete paragraph", "long paragraph", "long paragraph"])

    return {
        "conversation_rounds": conversation_rounds,
        "information_points": information_points,
        "conversation_topic": conversation_topic,
        "target_ability": target_ability,
        "mission_type": mission_type,
        "quotation_length": quotation_length,
        "conversation_style": conversation_style,
        "prompt": f'''You are an expert conversation architect. Generate a multi-round conversation that will later be used to test specific Large Language Model abilities. Follow these instructions strictly:
Conversation Attributes:
   - This conversation is intended to assess the LLM's {target_ability} in real-world scenarios, focusing on the mission type of {mission_type}.
   - "Quotation" means highlighting a specific part from the conversation so that the model pays extra attention to it for future question-answering.
   - The conversation must contain multiple potential parts that could serve as candidate quotation regions. Each candidate region must be an **exact** verbatim copy of some part (a {quotation_length}) from the conversation text.
   - Critically, the conversation's content should be constructed such that relying on the **quoted** portion leads to one conclusive answer, while ignoring or missing the quoted portion would lead to an unanswerable question or a different conclusion due to distractor information elsewhere.
   - The conversation should be centered on a specific subtopic of {conversation_topic}.
   - The conversation should have at least {conversation_rounds} rounds.
   - The style of the conversation should be {conversation_style}.
   - The conversation must include at least {information_points} distinct information points (data, entities, theories, figures, etc.) across different turns, all at the **same information level**. Avoid global overviews, aggregated summaries, or comparisons. 
   - Each information point focuses on a different aspect or detail of the same topic. "Different" doesn't imply incorrect but rather multiple facets of a single subject.
   - Fictional content is allowed, as long as it remains logically consistent and coherent.

Conversation Requirements:
   - Generate a <subtopic> section specifying the exact subtopic within {conversation_topic}.
   - Then provide a <Planning> section where you outline (1) at least {information_points} distinct information points and (2) the logical flow for the conversation.
   - After <Planning>, produce a <Generation> section with the multi-round conversation. Each user turn begins with `<|user|>\n` and ends with `<|end|>\n`. Each assistant turn begins with `<|assistant|>\n` and ends with `<|end|>\n`.
   - Do **not** generate any question for the model to answer in this prompt. You are only creating the conversation itself.

**Key Addition**: Potential Quotation Parts
   - **After** the conversation, create several block begins with `<|quotationx|>\n` and ends with `<|end|>\n` containing **exactly one** {quotation_length} copied verbatim from the conversation. It must match character-for-character one part of the conversation text.
   - When quoting a {quotation_length} in a conversation, do not add any identifiers on either side of the quoted area, such as '**', '\'', etc.

Below is the conversation template (do not introduce any other labels beyond what is specified):
<subtopic>
[Describe the specific subtopic, e.g., "various local regulations on xx technology", "the number of practitioners in the xx field across different countries", "the connection between car size and consumer purchasing intention" etc.]
</subtopic>
<Planning>
Ensure that the characteristics of the conversation and reference parts are taken into account(information richness, information points, quotation length, etc.) when planning to meet the requirements for evaluating the above ability and mission type.
1. Define {information_points} distinct information points at the same information level, ensuring logical flow.
- Point 1: [One piece of information]
- Point 2: [Another piece of information]
...
2. Ensure the conversation meets the above attributes, enabling a scenario where quoting a certain {quotation_length} is critical.
</Planning>
<Generation>
<|user|>\n[User's initial query about one specific aspect of the subtopic]<|end|>\n<|assistant|>\n[Assistant's response]<|end|>\n
[Repeat for {conversation_rounds} rounds, include all information points in the conversation]
<|quotation1|>
[Copy here exactly one {quotation_length} from the conversation text, verbatim, as the quoted part]
<|end|>
<|quotation2|>
[Copy here exactly one {quotation_length} from the conversation text, verbatim, as the quoted part]
<|end|>
[Copy more if needed]
'''
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--output_file", type=str, help="")
    parser.add_argument("--model", type=str, default='', help="")
    parser.add_argument("--create_num", type=str, default='300', help="")
    # 解析命令行参数
    args = parser.parse_args()

    responses = []
    output_file = args.output_file
    model = args.model
    create_num = int(args.create_num)

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