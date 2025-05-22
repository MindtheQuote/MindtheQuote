import json
import re

def remove_after_last_answer_tag(input_string):
    pattern = r'</Answer\d+>'
    
    matches = list(re.finditer(pattern, input_string))
    
    if matches:
        last_match = matches[-1]
        end_position = last_match.end()
        
        result = input_string[:end_position]
        return result
    else:
        return input_string

def clean_data(input_file, output_file):
    # Step 1: Read the JSONL file into a list of dictionaries
    with open(input_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    cleaned_data_list = []

    # Regular expressions for parsing
    question_pattern = re.compile(r'<Question>(.*?)</Question>', re.DOTALL)
    ignore_pattern = re.compile(r'<Ignore(\d+)>(.*?)</Ignore\1>', re.DOTALL)
    answer_pattern = re.compile(r'<Answer(\d+)>(.*?)</Answer\1>', re.DOTALL)
    quotation_pattern = re.compile(r'<\|quotation(\d+)\|>')

    for item in data:
        cleaned_data = {}

        # Step 2: Extract the 'question' key's string
        if 'question' not in item:
            continue
        question_str = item['question']

        # Step 3: Check and remove everything before <Question>
        if '<Question>' not in question_str:
            continue
        question_str = question_str[question_str.find('<Question>'):]
        
        # Step 4: Remove spaces and newlines around "<xxx>" tags
        def remove_spaces_around_tags(s):
            return re.sub(r'\s*<(/?\w+)>\s*', r'<\1>', s)
        question_str = remove_spaces_around_tags(question_str)

        question_str = remove_after_last_answer_tag(question_str)

        # Step 5: Validate the format of the string
        if not re.match(r'^<Question>.*?</Question>(<Ignore\d+>.*?</Ignore\d+><Answer\d+>.*?</Answer\d+>)+$', question_str, re.DOTALL):
            continue

        # Step 6: Extract <Question> content
        question_match = question_pattern.search(question_str)
        if not question_match:
            continue
        cleaned_data['Question'] = question_match.group(1).strip()

        # Step 7: Process <IgnoreN> and <AnswerN>
        ignore_matches = ignore_pattern.findall(question_str)
        answer_matches = answer_pattern.findall(question_str)

        ignore_data = {}
        answer_data = {}

        for idx, (ignore_num, ignore_content) in enumerate(ignore_matches, start=1):
            # Step 7.1: Validate <IgnoreN> content format
            quotations = quotation_pattern.findall(ignore_content)
            if not quotations or len(set(quotations)) != len(quotations):
                break

            # Step 7.2: Save quotations as "quotationX" format
            ignore_data[f'Ignore{ignore_num}'] = [f'quotation{q}' for q in quotations]

        for idx, (answer_num, answer_content) in enumerate(answer_matches, start=1):
            answer_data[f'Answer{answer_num}'] = answer_content.strip()

        # Step 9: Check if the number of IgnoreN and AnswerN matches
        if len(ignore_data) != len(answer_data):
            continue

        # Add IgnoreN and AnswerN to cleaned_data
        cleaned_data.update(ignore_data)
        cleaned_data.update(answer_data)

        # Step 10: Copy other keys from the original dictionary
        for key, value in item.items():
            if key != 'question':
                cleaned_data[key] = value

        # Append cleaned data to the list
        cleaned_data_list.append(cleaned_data)

    # Step 11: Save cleaned data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data_list, f, ensure_ascii=False, indent=4)

input_file = ""
output_file = 
# Example usage
clean_data(input_file, output_file)