import json
import re
import argparse
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def clean_data(data_list):
    cleaned_data_list = []

    for data in data_list:
        try:
            question_str = data.get('question', '')
            if not question_str:
                continue

            match_question_start = re.search(r'<Question>', question_str)
            if not match_question_start:
                continue
            question_str = question_str[match_question_start.start():]

            question_str = re.sub(r'\s*<([^>]+)>\s*', r'<\1>', question_str)

            pattern = re.compile(
                r'^<Question>(.*?)</Question>'
                r'(<Reference\d+><\|quotation\d+\|>(<\|quotation\d+\|>)*</Reference\d+>)'
                r'(<Background\d+><\|quotation\d+\|>(<\|quotation\d+\|>)*</Background\d+>)'
                r'(<Answer\d+>.*?</Answer\d+>)+$',
                re.DOTALL
            )
            if not pattern.match(question_str):
                continue

            cleaned_data = {}
            match_question_content = re.search(r'<Question>(.*?)</Question>', question_str)
            cleaned_data['Question'] = match_question_content.group(1).strip()

            references = {}
            reference_matches = re.finditer(r'<Reference(\d+)>(.*?)</Reference\1>', question_str)
            for match in reference_matches:
                ref_num = match.group(1)
                ref_content = match.group(2).strip()
                quotation_pattern = re.compile(r'^<\|quotation\d+\|>(<\|quotation\d+\|>)*$')
                if not quotation_pattern.match(ref_content):
                    raise ValueError("Invalid Reference format")
                quotations = re.findall(r'<\|quotation(\d+)\|>', ref_content)
                if len(set(quotations)) != len(quotations):
                    raise ValueError("Duplicate quotation numbers in Reference")
                references[f'Reference{ref_num}'] = [f'quotation{q}' for q in quotations]
            cleaned_data.update(references)

            backgrounds = {}
            background_matches = re.finditer(r'<Background(\d+)>(.*?)</Background\1>', question_str)
            for match in background_matches:
                bg_num = match.group(1)
                bg_content = match.group(2).strip()
                if not quotation_pattern.match(bg_content):
                    raise ValueError("Invalid Background format")
                quotations = re.findall(r'<\|quotation(\d+)\|>', bg_content)
                if len(set(quotations)) != len(quotations):
                    raise ValueError("Duplicate quotation numbers in Background")
                backgrounds[f'Background{bg_num}'] = [f'quotation{q}' for q in quotations]
            cleaned_data.update(backgrounds)

            answers = {}
            answer_matches = re.finditer(r'<Answer(\d+)>(.*?)</Answer\1>', question_str)
            for match in answer_matches:
                ans_num = match.group(1)
                ans_content = match.group(2).strip()
                answers[f'Answer{ans_num}'] = ans_content
            cleaned_data.update(answers)

            num_references = len(references)
            num_backgrounds = len(backgrounds)
            num_answers = len(answers)
            if not (num_references == num_backgrounds == num_answers):
                raise ValueError("Inconsistent number of References, Backgrounds, and Answers")

            cleaned_data.update({k: v for k, v in data.items() if k != 'question'})

            cleaned_data_list.append(cleaned_data)

        except Exception as e:
            continue

    return cleaned_data_list

def save_to_json(data_list, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input_jsonl", type=str, default='', help="")
    parser.add_argument("--output_json", type=str, default='', help="")

    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_json

    data_list = read_jsonl(input_file)

    cleaned_data_list = clean_data(data_list)

    save_to_json(cleaned_data_list, output_file)
