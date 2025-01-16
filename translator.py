import openai
# from openai.error import AuthenticationError, RateLimitError, APIError
import yaml
import os
from tqdm import tqdm
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(
    filename='translator.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize OpenAI client

# Load configuration
def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# Verify API key
def verify_api_key():
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Test API key"}],
        )
        print("Klucz API działa poprawnie.")
    except openai.OpenAIError as e:
        raise ValueError(f"Błąd OpenAI API: {e}")
    except Exception as e:
        raise ValueError(f"Nieoczekiwany błąd: {e}")

# Split Markdown file
def split_markdown(file_path, max_words=250):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Plik {file_path} nie został znaleziony.")

    if not content.strip():
        raise ValueError("Plik wejściowy jest pusty.")

    paragraphs = content.split("\n\n")
    fragments = []
    current_fragment = []
    current_word_count = 0

    for paragraph in paragraphs:
        word_count = len(paragraph.split())
        if current_word_count + word_count <= max_words:
            current_fragment.append(paragraph)
            current_word_count += word_count
        else:
            fragments.append("\n\n".join(current_fragment))
            current_fragment = [paragraph]
            current_word_count = word_count

    if current_fragment:
        fragments.append("\n\n".join(current_fragment))

    return fragments

# Load glossary files from a folder
def load_glossary(folder_path):
    glossary_content = ""
    try:
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and file_name.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    glossary_content += f.read() + "\n"
    except FileNotFoundError:
        raise FileNotFoundError(f"Folder {folder_path} does not exist.")
    except Exception as e:
        raise ValueError(f"Error reading glossary files: {e}")

    return glossary_content.strip()

# Translate a fragment
def translate_fragment(fragment, instructions, glossary):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional translator."},
                {"role": "system", "content": f"Use the following glossary for reference:\n{glossary}"},
                {"role": "user", "content": f"{instructions}\n\n{fragment}"}
            ]
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        print(f"Translation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Append to output file
def append_to_file(output_path, translated_text):
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(translated_text + "\n\n")

# Main translation function
def translate_markdown_file(source_path, output_path, instructions, max_words, glossary):
    fragments = split_markdown(source_path, max_words)

    if os.path.exists(output_path):
        print(f"Removing existing output file: {output_path}")
        os.remove(output_path)

    for i, fragment in enumerate(tqdm(fragments, desc="Translating fragments"), start=1):
        translated = translate_fragment(fragment, instructions, glossary)
        if translated:
            append_to_file(output_path, translated)
        else:
            print(f"Fragment {i} skipped due to an error.")

    print("Translation completed!")

# Main function
def main():
    config = load_config("config.yaml")
    verify_api_key()

    try:
        glossary = load_glossary(config["glossary_folder"])
        translate_markdown_file(
            source_path=config["source_file"],
            output_path=config["output_file"],
            instructions=config["instructions"],
            max_words=config["max_words"],
            glossary=glossary
        )
    except Exception as e:
        logging.error(f"Critical error: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
