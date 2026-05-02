import json
from pathlib import Path
from collections import defaultdict

END_CHARS = " (){}[]+-!?/\\\\&%,.:-=<>\n"

class Localization:
    
    def __init__(self, language='Japanese'):
        self.language = language
        self.translations = defaultdict(defaultdict)

    def load(self, directory_path: Path):
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        for json_file in directory_path.glob('*.json'):
            with json_file.open('r', encoding='utf-8') as f:
                self.translations[json_file.stem] = json.load(f)

    def _find_next_word(self, text, start_index):
        if start_index >= len(text) - 1:
            return False, None, -1, -1

        word_start = text.find('$', start_index)
        if word_start != -1:
            indices = [text.find(c, word_start) for c in END_CHARS]
            indices = [i for i in indices if i != -1]

            if indices:
                num = min(indices)
                word = text[word_start + 1:num]
                word_end = num
            else:
                word = text[word_start + 1:]
                word_end = len(text)

            return True, word, word_start, word_end

        return False, None, -1, -1

    def _translate(self, text: str):
        if text.startswith('KEY_'):
            # TODO: GetBoundedKey?
            return text
        
        if self.language in self.translations:
            if text in self.translations[self.language]:
                return self.translations[self.language][text]
            
        return '[' + text + ']'

    def localize(self, text):
        if not text:
            return text

        if not self.language in self.translations:
            return text
        
        num = 0
        out = ''
        while True:
            ok, word, word_start, word_end = self._find_next_word(text, num)
            if not ok:
                break

            out += text[num:word_start - num]
            out += self._translate(word)
            num = word_end

        out += text[num:]
        return out
        

