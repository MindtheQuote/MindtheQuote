import json
import random
import argparse
def generate_multiple_choice_questions(input_file, output_file):
    
    with open(input_file, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)

    
    filtered_data = [item for item in cleaned_data if 'quotation3' in item]

    for idx, item in enumerate(filtered_data):
        item['id'] = idx

    all_new_dicts = []

    for item in filtered_data:
        quotation_keys = [key for key in item.keys() if key.startswith('quotation') and not key.endswith('_answer')]
        answer_keys = [key for key in item.keys() if key.startswith('quotation') and key.endswith('_answer')]

        if len(quotation_keys) < 3 or len(answer_keys) < 3:
            continue

        for i, (quotation_key, answer_key) in enumerate(zip(quotation_keys, answer_keys)):
            new_dict = {}

            new_dict['quotation'] = item[quotation_key]  
            new_dict['gt_label'] = item[answer_key]      

            remaining_answers = [item[key] for key in answer_keys if key != answer_key]
            distractors = random.sample(remaining_answers, 2)
            new_dict['distractor1'] = distractors[0]
            new_dict['distractor2'] = distractors[1]

            new_dict['conversation'] = item.get('conversation', '')
            new_dict['Question'] = item.get('Question', '')
            new_dict['id'] = item['id']
            new_dict['attributes'] = item.get('attributes', {})

            ordered_dict = {
                'conversation': new_dict['conversation'],
                'Question': new_dict['Question'],
                'quotation': new_dict['quotation'],
                'gt_label': new_dict['gt_label'],
                'distractor1': new_dict['distractor1'],
                'distractor2': new_dict['distractor2'],
                'id': new_dict['id'],
                'attributes': new_dict['attributes']
            }

            all_new_dicts.append(ordered_dict)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_new_dicts, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, help="")
    parser.add_argument("--output_json", type=str, help="")

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_json

    generate_multiple_choice_questions(input_file, output_file)