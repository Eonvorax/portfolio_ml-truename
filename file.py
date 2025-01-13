#!/usr/bin/env python3
"""
This the file module, containing the File class
"""
from os.path import splitext, join, dirname, normpath
from langdetect import detect
import fitz
from clean_filename import secure_filename
import fr_core_news_sm
import en_core_web_sm
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

file_formats = {
    "image_formats": ("png", "jpeg", "jpg", "webp"),
    "text_formats": ("pdf")
}


class File:
    """
    This is the File class, representing the file to manipulate and all the
    necessary information to rename it properly.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize a File instance from a file path
        """
        self._original_path: str = normpath(file_path)

        # Splitting the file path :
        filename, file_extension = splitext(file_path)
        self._original_name: str = filename

        # Exluding the "." character from the file extension
        self._file_type: str = file_extension[1:]
        # NOTE Need to be careful with more exotic file extensions like .tar.gz or .JPG
        # Case-sensitive issues of bad splitting could happen

        self._text_content: str = ""
        self._file_data: dict = {}
        self._new_name: str = ""
        self._new_path: str = ""
        self._language: str = ""

    @property
    def original_path(self) -> str:
        return self._original_path

    @original_path.setter
    def original_path(self, value: str) -> None:
        self._original_path = normpath(value)

    @property
    def original_name(self) -> str:
        return self._original_name

    @original_name.setter
    def original_name(self, value: str) -> None:
        self._original_name = value

    @property
    def file_type(self) -> str:
        return self._file_type

    @file_type.setter
    def file_type(self, value: str) -> None:
        self._file_type = value

    @property
    def text_content(self) -> str:
        return self._text_content

    @text_content.setter
    def text_content(self, value: str) -> None:
        self._text_content = value

    @property
    def file_data(self) -> dict:
        return self._file_data

    @file_data.setter
    def file_data(self, value: dict) -> None:
        self._file_data = value

    @property
    def new_name(self) -> str:
        return self._new_name

    @new_name.setter
    def new_name(self, value: str) -> None:
        # Making sure the filename string won't cause issues
        self._new_name = secure_filename(value)

    @property
    def new_path(self) -> str:
        return self._new_path

    @new_path.setter
    def new_path(self, value: str) -> None:
        self._new_path = value

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        self._language = value

    def extract_content(self) -> None:
        """
        Extracts text content from the file at "original_path"
        """

        text = ""
        # TODO this seems pointlessly complicated, try using self.original_path ?
        doc = fitz.open(f"{self.original_name}.{self.file_type}")  # open a document
        for page in doc:  # iterate over the document's pages
            text += page.get_text()
            # NOTE Might need to cap this loop for large documents
        self.text_content = text

    def extract_data(self) -> None:
        """
        TODO
        """
        pass

    def generate_word_count(self, processed_text):
        """
        Builds a word count dictionary from the given list of entities (tuples)
        """
        # Extract entities using boolean word.is_stop to remove irrelevant words
        # NOTE also could exclude URLs
        entities = [(word.text, word.pos_) for word in processed_text if not word.is_stop]

        # TODO improve the entity selection here
        filtered_entities_list = []
        for entity in entities:
            if (entity[1] == 'PROPN' or entity[0].isupper()) and len(entity[0]) > 2:
                filtered_entities_list.append(entity)

        print(f"Filtered entities count: {len(filtered_entities_list)}")

        # Use a dictionary to count occurrences of each word
        merged_words = {}
        for entity in filtered_entities_list:
            word : str = entity[0]
            lowercase_word = word.casefold()
            # Trying to match word with existing key, ignoring case
            if word in merged_words:
                merged_words[word] += 1
            elif lowercase_word in merged_words:
                merged_words[lowercase_word] += 1
            elif lowercase_word.capitalize() in merged_words:
                merged_words[lowercase_word.capitalize()] += 1
            elif lowercase_word.upper() in merged_words:
                merged_words[lowercase_word.upper()] += 1
            else:
                # No match, add the word to the dictionary
                merged_words[word] = 1

        return merged_words

    def generate_name(self) -> None:
        """
        Generate a new name for the file based on the text content and language.

        This method uses spaCy models to process the text content and extract entities.
        It then selects specific entities based on their type or capitalization.
        The selected entities are merged and counted to create a new filename.
        The new filename is stored in the `new_name` attribute of the object.

        NOTE: This method assumes that the `language` and `text_content` attributes are already set.
        """
        models = {
            "fr": fr_core_news_sm,
            "en": en_core_web_sm
        }

        try:
            if self.language not in models:
                raise KeyError
            nlp_model = models[self.language].load()

        except Exception as err:
            print(f"Error: {err}")

        print(f"Text content length: {len(self.text_content)}")
        # NOTE Taking care of files too long for the model, still needs better solution
        if len(self.text_content) > nlp_model.max_length:
            self.text_content = self.text_content[:nlp_model.max_length - 1]
        processed_text = nlp_model(self.text_content)

        merged_words = self.generate_word_count(processed_text)
        print(f"Merged words count: {len(merged_words)}")

        # NOTE Could sort dictionary by value ? Or use a different DS ?
        filename = ""
        switch_underscore = False
        while len(filename) < 70 and len(merged_words) > 0:
            max_word = max(merged_words, key=merged_words.get)
            if len(max_word) < 30:
                if switch_underscore:
                    filename += '_'
                switch_underscore = True
                filename += max_word
            del merged_words[max_word]

        self.new_name = f"{filename}.{self.file_type}"

    def identify_language(self) -> None:
        """
        Identifies the language the text content from the File is in.
        """
        # NOTE Might need to reduce text sample to increase detection speed
        # Could reduce accuracy, so not done for now
        try:
            self.language = detect(self.text_content)
        except Exception as err:
            print(f"Error: {err}")

    def build_new_path(self):
        """
        From the new filename and the original path, build the new path.
        """
        # Extract directory from the original path
        directory = dirname(self.original_path)

        # Join directory and new filename to create the new path, and normalize it
        self.new_path = normpath(join(directory, self.new_name))

    def process_file(self, file_number: int):
        """
        Processes a file using its corresponding File object.
        """
        print(f"\nWorking on file n°{file_number}")
        print(f"File path : {self.original_path}")

        if self.file_type in file_formats["text_formats"]:
            self.extract_content()
            if self.text_content == "":
                # No content was extracted, either met an issue or the file
                # may be empty
                # NOTE could extend this to handling files too short to have
                # any value for name generation, e.g. len(content) < 100 or so
                return

            self.identify_language()
            print(f"Detected language: {self.language}")
            self.generate_name()

        elif self.file_type in file_formats["image_formats"]:
            # TODO implement a dedicated function
            with open(self.original_path, 'rb') as file:
                print("Processing image...")
                raw_image = Image.open(file).convert('RGB')
            inputs = processor(raw_image, return_tensors="pt")

            print("Generating output...")
            hyper_params = {"max_new_tokens": 50,
                            "do_sample": True,
                            "temperature": 1.0}
            out = model.generate(**inputs, **hyper_params)
            name: str = processor.decode(out[0], skip_special_tokens=True)
            self.new_name = f"{name.replace(' ', '_')}.{self.file_type}"

        else:
            # File format not in file_formats, skipping it.
            return

        print(f"Generated new name: [{self.new_name}]")
        self.build_new_path()
        print(f"Built new path: {self.new_path}")
