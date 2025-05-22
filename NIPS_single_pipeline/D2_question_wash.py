import json
import re
import argparse
def clean_data(input_file, output_file):
    # Step 1: 读取 JSONL 文件为列表
    data_list = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data_list.append(json.loads(line.strip()))

    cleaned_data = []

    # 定义正则表达式
    quotation_pattern = re.compile(r'<\|quotation(\d+)_answer\|>(.*?)<\|end\|>', re.DOTALL)
    invalid_tag_pattern = re.compile(r'<[^<>|]+>|<\|[^<>|]+|<[^<>|]+\|>')
    question_pattern = re.compile(r'<\|Question\|>(.*?)<\|end\|>', re.DOTALL)

    for item in data_list:
        try:
        
            question_str = item.get('question', '')
            if not question_str:
                continue

        
            question_index = question_str.find('<|Question|>')
            if question_index == -1:
                continue
            question_str = question_str[question_index:]

        
            def remove_whitespace_around_tags(s):
                return re.sub(r'\s*<\|.*?\|>\s*', lambda m: m.group().strip(), s)
            question_str = remove_whitespace_around_tags(question_str)

        
            quotations = quotation_pattern.findall(question_str)
            if not quotations:
                continue

        
            quotation_numbers = [int(num) for num, _ in quotations]
            if quotation_numbers != list(range(1, len(quotation_numbers) + 1)):
                continue


            question_match = question_pattern.search(question_str)
            if not question_match:
                continue
            question_content = question_match.group(1).strip()

            
            new_item = {}
            new_item['Question'] = question_content
            for num, content in quotations:
                new_item[f'quotation{num}_answer'] = content.strip()

            
            for key, value in item.items():
                if key != 'question':
                    new_item[key] = value

    
            original_quotations = {key: value for key, value in item.items() if key.startswith('quotation') and not key.endswith('_answer')}
            original_answers = {key: value for key, value in new_item.items() if key.startswith('quotation') and key.endswith('_answer')}

            if len(original_quotations) != len(original_answers):
                continue

            def extract_numbers(keys):
                return sorted([int(re.match(r'quotation(\d+)(_answer)?', key).group(1)) for key in keys])

            original_quotation_numbers = extract_numbers(original_quotations.keys())
            original_answer_numbers = extract_numbers(original_answers.keys())

            if original_quotation_numbers != list(range(1, len(original_quotation_numbers) + 1)) or \
               original_answer_numbers != list(range(1, len(original_answer_numbers) + 1)):
                continue

            cleaned_data.append(new_item)

        except Exception as e:
            print(f"Error processing item: {item}, error: {e}")
            continue

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    # 添加参数定义
    parser.add_argument("--input_jsonl", type=str, help="")
    parser.add_argument("--output_jsonl", type=str, help="")

    # 解析命令行参数
    args = parser.parse_args()
    input_file = args.input_jsonl
    output_file = args.output_jsonl
    clean_data(input_file, output_file)