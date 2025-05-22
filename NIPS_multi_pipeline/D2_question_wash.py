import json
import re
import argparse
def clean_data(input_file, output_file):
    # Step 1: Read the JSONL file into a list of dictionaries
    with open(input_file, 'r', encoding='utf-8') as f:
        data_list = [json.loads(line) for line in f]

    cleaned_data_list = []

    for data in data_list:
        cleaned_data = {}

        # Step 2: Extract the 'question' key's string
        question_str = data.get('question', '')
        if not question_str:
            continue  # Skip this data if 'question' is missing

        # Step 3: Check and remove everything before '<Question>'
        question_start = question_str.find('<Question>')
        if question_start == -1:
            continue  # Discard this data if '<Question>' is missing
        question_str = question_str[question_start:]

        # Step 4: Remove spaces and newlines around "<xxx>" patterns
        question_str = re.sub(r'\s*<[^>]+>\s*', lambda m: m.group().strip(), question_str)

        # Step 5: Validate the overall format
        pattern = r'<Question>(.*?)</Question>(<Reference\d+>.*?</Reference\d+><Answer\d+>.*?</Answer\d+>)+'
        match = re.fullmatch(pattern, question_str, re.DOTALL)
        if not match:
            continue  # Discard this data if the format is invalid

        # Step 6: Extract <Question> content
        question_content = re.search(r'<Question>(.*?)</Question>', question_str, re.DOTALL)
        cleaned_data['Question'] = question_content.group(1).strip()

        # Step 7: Extract and process <ReferenceN> and <AnswerN>
        references = {}
        answers = {}
        reference_pattern = r'<Reference(\d+)>(.*?)</Reference\1>'
        answer_pattern = r'<Answer(\d+)>(.*?)</Answer\1>'

        reference_matches = re.findall(reference_pattern, question_str, re.DOTALL)
        answer_matches = re.findall(answer_pattern, question_str, re.DOTALL)

        # Step 7.1: Validate Reference format
        for ref_num, ref_content in reference_matches:
            quotation_pattern = r'<\|quotation(\d+)\|>'
            quotations = re.findall(quotation_pattern, ref_content)
            if not quotations or len(quotations) != len(set(quotations)):
                break  # Discard this data if Reference format is invalid
            
            # Convert to [quotation1, quotation2, ...]
            quotations_with_prefix = [f"quotation{q}" for q in quotations]
            references[f'Reference{ref_num}'] = quotations_with_prefix

        else:  # Only proceed if no break occurred (all References are valid)
            # Step 7.2: Extract Answers
            for ans_num, ans_content in answer_matches:
                answers[f'Answer{ans_num}'] = ans_content.strip()

            # Step 8: Remove ReferenceN and AnswerN pairs where ReferenceN has only one element
            filtered_references = {}
            filtered_answers = {}
            new_index = 1  # New index for renumbering

            for ref_num, ref_value in sorted(references.items()):
                ans_key = f'Answer{ref_num.split("Reference")[1]}'
                if len(ref_value) > 1:  # Keep only References with more than one element
                    filtered_references[f'Reference{new_index}'] = ref_value
                    filtered_answers[f'Answer{new_index}'] = answers[ans_key]
                    new_index += 1

            # Step 9: Check if the number of References and Answers is at least 3
            if len(filtered_references) < 3:
                continue  # Discard this data if there are fewer than 3 References/Answers

            # Step 10: Add filtered References and Answers to cleaned_data
            cleaned_data.update(filtered_references)
            cleaned_data.update(filtered_answers)

            # Step 11: Copy all other key-value pairs from the original data
            for key, value in data.items():
                if key != 'question':
                    cleaned_data[key] = value

            # Append the cleaned data to the list
            cleaned_data_list.append(cleaned_data)

    # Save the cleaned data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data_list, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, help="")
    parser.add_argument("--output_json", type=str, help="")

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_json

    clean_data(input_file, output_file)