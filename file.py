#!/usr/bin/env python3
"""
This the file module, containing the File class
"""
from os.path import splitext, join, dirname, normpath
import fitz
from clean_filename import secure_filename
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

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

    def generate_name(self) -> None:
        """
        Generate a new name for the file based on the text content.

        This method uses the FLAN-T5 instruct model to process the text content
        and generate a new name for the file.
        The new filename is stored in the `new_name` attribute of the object.

        NOTE: This method assumes that the `text_content` attribute is already set.
        """
        prompt = """Instruction: Generate a short descriptive filename for this text file.
        Content:\n 
        """

        print(f"Text content length: {len(self.text_content)}")
        input_text = prompt + self.text_content

        inputs = flan_tokenizer([input_text], return_tensors='pt', truncation=True)
        print("Input tokens:", inputs.tokens())

        # NOTE Not handling moving to GPU for now
        # inputs = inputs.to(device)  # Move inputs to the same device as the model
        output_ids = flan_model.generate(
            inputs['input_ids'],
            min_length=10,
            max_length=25,
            do_sample=False
        )
        decoded_output = flan_tokenizer.decode(output_ids[0], skip_special_tokens=True)

        self.new_name = f"{decoded_output}.{self.file_type}"

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

            self.generate_name()

        elif self.file_type in file_formats["image_formats"]:
            # TODO implement a dedicated function
            with open(self.original_path, 'rb') as file:
                print("Processing image...")
                raw_image = Image.open(file).convert('RGB')
            inputs = blip_processor(raw_image, return_tensors="pt")

            print("Generating output...")
            hyper_params = {"max_new_tokens": 50,
                            "do_sample": True,
                            "temperature": 1.0}
            out = blip_model.generate(**inputs, **hyper_params)
            name: str = blip_processor.decode(out[0], skip_special_tokens=True)
            self.new_name = f"{name.replace(' ', '_')}.{self.file_type}"

        else:
            # File format not in file_formats, skipping it.
            return

        print(f"Generated new name: [{self.new_name}]")
        self.build_new_path()
        print(f"Built new path: {self.new_path}")
