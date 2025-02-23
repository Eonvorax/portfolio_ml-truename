#!/usr/bin/env python3
"""
This the file module, containing the File class and the models used to process
text and image files.
"""
from os.path import splitext, join, dirname, normpath, basename
import fitz
from clean_filename import secure_filename
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


def clean_caption(caption):
    """
    Remove common starting filler phrases or words from a BLIP-generated caption.

    Args:
        caption (str): the caption to clean up
    
    Returns:
        str: the cleaned caption
    """
    # "If it's stupid but it works, it ain't stupid."
    for phrase in ["this is", "there is", "there are", "it is", "an image of"]:
        if caption.lower().startswith(phrase):
            # Remove it from the start of the caption only, and strip extra whitespace
            caption = caption[len(phrase):].strip()
    return caption


flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")

flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large", device_map="auto")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large", device_map="auto")


file_formats = {
    "image_formats": ("png", "jpeg", "jpg", "webp"),
    "text_formats": ("pdf")
}

class File:
    """
    This is the File class, representing the file to manipulate and all the
    necessary information to rename it properly.

    Attributes:
        original_path (str): the path to the file to manipulate
        original_name (str): the name of the file without its extension
        file_type (str): the extension of the file
        text_content (str): the text content of the file if it's a text file
        image_content (PIL.Image): the raw image content of the file if it's an image
        new_name (str): the new name of the file
        new_path (str): the new path of the file after renaming
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize a File instance from a file path.
        Args:
            file_path (str): the path to the file to manipulate
        """
        # Normalize the file path
        self._original_path: str = normpath(file_path)

        # Extract the full filename with extension
        full_filename = basename(self._original_path)

        # Splitting the file path into name and extension
        filename, file_extension = splitext(full_filename)
        
        # Storing the extracted values
        self._original_name: str = filename
        
        # Exluding the "." character from the file extension
        self._file_type: str = file_extension[1:]
        # NOTE Need to be careful with more exotic file extensions like .tar.gz or .JPG
        # Case-sensitive issues or bad splitting could happen

        self._text_content: str = ""
        self._image_content = None
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
    def image_content(self):
        return self._image_content
    
    @image_content.setter
    def image_content(self, value):
        self._image_content = value

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


    def extract_text_content(self) -> None:
        """
        Extracts text content from the file at "original_path" and stores it
        in the "text_content" attribute.
        If an error occurs when opening the file, text_content is set to an empty string.
        """
        text = ""
        try:
            with fitz.open(self.original_path) as doc:
                pages_text_list = []
                for page in doc:
                    pages_text_list.append(page.get_text("text"))
                text = "".join(pages_text_list)

        except Exception as e:
            print(f"Error: {e} when opening file at path [{self.original_path}]")
            text = ""

        self.text_content = text

    def extract_image_content(self) -> None:
        """
        Extracts and returns raw image content from the file at "original_path".
        If an error occurs when opening the image, image_content is set to None.
        """
        try:
            with open(self.original_path, 'rb') as file:
                self.image_content = Image.open(file).convert('RGB')
        except Exception as e:
            self.image_content = None
            print(f"Error : {e} when opening image at path [{self.original_path}]")

    def generate_text_name(self) -> None:
        """
        Generate a new name for the file based on the text content.

        This method uses the preset instruct model to process the text content
        and generate a new name for the file. The new filename is stored in the
        `new_name` attribute of the object. Assumes the `text_content` attribute
        contains the full text content of the file.
        """
        prompt = """Instruction: Generate a short descriptive filename for this text file.
        Content:\n 
        """

        print(f"Text content length: {len(self.text_content)}")
        input_text = prompt + self.text_content

        print("Processing text...")
        inputs = flan_tokenizer([input_text], return_tensors='pt', truncation=True)

        ## Uncomment to see the tokens of the input
        # print("Input tokens:", inputs.tokens())

        # Move inputs to the same device as flan_model
        inputs = inputs.to(flan_model.device)
        
        print("Generating output...")
        output_ids = flan_model.generate(
            inputs['input_ids'],
            min_length=10,
            max_length=25,
            do_sample=False,  # Deterministic output for reliability
            repetition_penalty=1.5,  # Penalize repetitive tokens
            no_repeat_ngram_size=3  # Avoid repeated phrases
        )

        # Decode the output
        decoded_output = flan_tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Set the generated filename
        self.new_name = f"{decoded_output}.{self.file_type}"

    def generate_image_name(self) -> None:
        """
        Generate a new name for the file based on the image content.

        This method uses the BLIP-large image captioning model to process the image
        and generate a new name for the file.
        The new filename is stored in the `new_name` attribute of the object.
        This method assumes that the `original_path` attribute points to an
        image file.
        """
        inputs = blip_processor(self.image_content, return_tensors="pt")

        # Move inputs to the same device as blip_model
        inputs = inputs.to(blip_model.device)

        print("Generating output...")
        hyper_params = {
            "do_sample": False,          # No sampling for deterministic results
            "num_beams": 8,              # Beam search to improve reliability
            "repetition_penalty": 1.3,   # Higher repetition penalty
            "no_repeat_ngram_size": 3,   # Avoid repeating the 3 same words
            "min_length": 10,
            "max_length": 25
            }
        out = blip_model.generate(**inputs, **hyper_params)
        name: str = clean_caption(blip_processor.decode(out[0], skip_special_tokens=True))
        self.new_name = f"{name.replace(' ', '_')}.{self.file_type}"


    def build_new_path(self) -> None:
        """
        From the new filename and the original path, build the new path and
        store it in the `new_path` attribute.
        """
        # Extract directory from the original path
        directory = dirname(self.original_path)

        # Join directory and new filename to create the new path, and normalize it
        self.new_path = normpath(join(directory, self.new_name))

    def process_file(self, file_number: int) -> None:
        """
        Processes a file using its corresponding File object.
        If an error occurs during the process, the file is skipped.

        Args:
            file_number (int): the number of the file in the list of files to process
                (purely for display and logging purposes)
        """
        print(f"\nWorking on file n°{file_number}")
        print(f"File path : {self.original_path}")

        # Check if the file type is supported (case-insensitive)
        if self.file_type.lower() in file_formats["text_formats"]:
            if self.text_content == "":
                # No content was extracted, either met an issue or the file
                # may be empty
                # NOTE could extend this to handling files too short to have
                # any value for name generation, e.g. len(content) < 100 or so
                return

            if self.generate_text_name() == "":
                # No name was generated, skipping this file
                return

        elif self.file_type.lower() in file_formats["image_formats"]:
            if self.image_content is None:
                # No content was extracted, met an issue when opening the image
                return
            
            if self.generate_image_name() == "":
                # No name was generated, skipping this file
                return

        else:
            # File format not in file_formats, skipping it.
            return

        print(f"Generated new name: [{self.new_name}]")
        self.build_new_path()
        print(f"Built new path: {self.new_path}")
