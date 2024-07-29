from deep_translator import GoogleTranslator
import argparse

def translate_text(text, src='ja', dest='chinese (simplified)'):
    try:
        translator = GoogleTranslator(source=src, target=dest)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def process_file(input_path, output_path):
    # 读取文件
    with open(input_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # 翻译每行并重新格式化
    new_lines = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) == 4 and parts[1] == 'cut' and parts[2] == 'JA':
            chinese_text = translate_text(parts[3])
            new_line = f"{parts[0]}|{chinese_text}\n"
            new_lines.append(new_line)
    
    # 写入新内容到输出文件
    with open(output_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate Japanese text in .list files to Chinese and save to a new file.")
    parser.add_argument("input_path", type=str, help="The path to the input .list file.")
    parser.add_argument("output_path", type=str, help="The path where the output file will be saved.")

    args = parser.parse_args()
    process_file(args.input_path, args.output_path)
