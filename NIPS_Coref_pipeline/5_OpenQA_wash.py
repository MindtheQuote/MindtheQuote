import json

def process_jsonl(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            try:
                data = json.loads(line.strip())
                
                qa_string = data.get("Question_and_Answer", "")
                
                if not (qa_string.startswith("Query:") and "\nAnswer:" in qa_string):
                    continue
                
                query_start = len("Query:")
                answer_start = qa_string.find("\nAnswer:") + len("\nAnswer:")
                
                query = qa_string[query_start:qa_string.find("\nAnswer:")].strip()
                answer = qa_string[answer_start:].strip()
                
                data["OpenQA_Query"] = query
                data["OpenQA_Answer"] = answer
                
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            except Exception as e:
                pass

input_file = "" 
output_file = "" 
process_jsonl(input_file, output_file)