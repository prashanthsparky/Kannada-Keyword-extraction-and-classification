import wx
import re
from indicnlp.tokenize import indic_tokenize
from collections import Counter
from stopwords_kannada.stopwords import stopword
from kannada_pos_package.kannada_pos import kannada_pos_dict
import docx
import PyPDF2
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # Ensures consistent results across runs

class KannadaKeywordExtractorClassifierApp(wx.Frame):
    def __init__(self, parent, title):
        super(KannadaKeywordExtractorClassifierApp, self).__init__(parent, title=title, size=(700, 500))

        # Initialize default output file paths
        self.output_file = None

        # Default number of keywords to extract
        self.num_keywords = "5"  # Default to extracting 5 keywords

        # Create and set up the GUI elements
        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)

        # File selection area for extraction
        extract_file_label = wx.StaticText(panel, label="Select Document for Extraction:")
        self.extract_file_entry = wx.TextCtrl(panel, style=wx.TE_READONLY)
        extract_browse_button = wx.Button(panel, label="Browse")
        extract_browse_button.Bind(wx.EVT_BUTTON, self.on_extract_browse)

        # File selection area for classification
        classify_file_label = wx.StaticText(panel, label="Select Document for Classification:")
        self.classify_file_entry = wx.TextCtrl(panel, style=wx.TE_READONLY)
        classify_browse_button = wx.Button(panel, label="Browse")
        classify_browse_button.Bind(wx.EVT_BUTTON, self.on_classify_browse)

        # Text input area
        text_label = wx.StaticText(panel, label="Or Enter Kannada Text:")
        self.text_input = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        # Number of keywords entry
        num_keywords_label = wx.StaticText(panel, label="Number of Keywords:")
        self.num_keywords_entry = wx.TextCtrl(panel, value=self.num_keywords)

        # Button to trigger keyword extraction
        extract_button = wx.Button(panel, label="Extract Keywords")
        extract_button.Bind(wx.EVT_BUTTON, self.extract_keywords)

        # Button to trigger keyword classification
        classify_button = wx.Button(panel, label="Classify Keywords")
        classify_button.Bind(wx.EVT_BUTTON, self.classify_keywords)

        # Display area for extracted keywords
        output_label = wx.StaticText(panel, label="Extracted Keywords:")
        self.keywords_display = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(200, 100))

        # Display area for classified nouns
        nouns_label = wx.StaticText(panel, label="ನಾಮಪದ:")
        self.noun_display = wx.ListBox(panel)

        # Display area for classified verbs
        verbs_label = wx.StaticText(panel, label="ಕ್ರಿಯಾಪದಗಳು:")
        self.verb_display = wx.ListBox(panel)

        # Button to save keywords
        save_button = wx.Button(panel, label="Save Keywords")
        save_button.Bind(wx.EVT_BUTTON, self.save_keywords)

        # Button to save nouns
        save_nouns_button = wx.Button(panel, label="Save ನಾಮಪದ")
        save_nouns_button.Bind(wx.EVT_BUTTON, self.save_nouns)

        # Button to save verbs
        save_verbs_button = wx.Button(panel, label="Save ಕ್ರಿಯಾಪದಗಳು")
        save_verbs_button.Bind(wx.EVT_BUTTON, self.save_verbs)

        # Button to clear all fields and lists
        clear_button = wx.Button(panel, label="Clear")
        clear_button.Bind(wx.EVT_BUTTON, self.clear_all)

        # Sizers for layout
        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(extract_file_label, (0, 0))
        sizer.Add(self.extract_file_entry, (0, 1), (1, 2), flag=wx.EXPAND)
        sizer.Add(extract_browse_button, (0, 3))
        sizer.Add(classify_file_label, (1, 0))
        sizer.Add(self.classify_file_entry, (1, 1), (1, 2), flag=wx.EXPAND)
        sizer.Add(classify_browse_button, (1, 3))
        sizer.Add(text_label, (2, 0))
        sizer.Add(self.text_input, (2, 1), (2, 3), flag=wx.EXPAND)
        sizer.Add(num_keywords_label, (4, 0))
        sizer.Add(self.num_keywords_entry, (4, 1))
        sizer.Add(extract_button, (4, 2))
        sizer.Add(classify_button, (4, 3))
        sizer.Add(output_label, (5, 0))
        sizer.Add(self.keywords_display, (6, 0), (2, 4), flag=wx.EXPAND)
        sizer.Add(nouns_label, (8, 0))
        sizer.Add(self.noun_display, (9, 0), (3, 2), flag=wx.EXPAND)
        sizer.Add(verbs_label, (8, 2))
        sizer.Add(self.verb_display, (9, 2), (3, 2), flag=wx.EXPAND)
        sizer.Add(save_button, (13, 0))
        sizer.Add(clear_button, (13, 1))
        sizer.Add(save_nouns_button, (13, 2))
        sizer.Add(save_verbs_button, (13, 3))

        panel.SetSizer(sizer)

        self.Centre()
        self.Show(True)

    def tag_kannada_words(self, words):
        tagged_words = []
        unknown_words = []  # List to store unknown words
        for word in words:
            if word.strip() in kannada_pos_dict:
                tagged_words.append((word.strip(), kannada_pos_dict[word.strip()]))
            else:
                # Apply additional rules based on morphology or context to classify the word
                if self.is_verb(word.strip()):
                    tagged_words.append((word.strip(), 'Verb'))
                elif self.is_noun(word.strip()):
                    tagged_words.append((word.strip(), 'Noun'))
                else:
                    unknown_words.append(word.strip())  # Add unknown word to list without newline characters
                    tagged_words.append((word.strip(), 'UNKNOWN'))

        # Display unknown words in the ListBox
        self.noun_display.SetItems(unknown_words)
        self.verb_display.SetItems([])  # Clear verb display

        return tagged_words

    def is_noun(self, word):
        # Implement a heuristic or rule to identify nouns based on morphology or context
        # For example, check if the word ends with specific suffixes common in Kannada nouns
        noun_suffixes = ['ಕಾರ', 'ಕೆ', 'ದ', 'ವರು', 'ವಳು', 'ಅದು', 'ವು', 'ನ', 'ನಿಂದ', 'ರು', 'ದು', 'ಕೆ', 'ಬೇಕು', 'ನಿಂದ', 'ಆಯಿ', 'ಉತ್ತಿತ್ತು',
                    'ಇದೆ', 'ಇಲ್ಲ', 'ಇರುತ್ತದೆ', 'ಒಂದು', 'ಒನ್ನು', 'ಗಳಿಗೆ', 'ಚೆನ್ನಾಗಿ', 'ತ್ತದೆ', 'ತ್ತಾನೆ', 'ದೆಯ', 'ದೇವರೆ','ಬೇಕು',
                    'ನಿಂದ', 'ಇಸುವುದು', 'ಇಕ್ಕುವುದು', 'ಇಕ್ಕೊಳ್ಳುವುದು', 'ಆಗುವುದು', 'ಕೊಳ್ಳುವುದು', 'ಮಾಡುವುದು', 'ಹೋಗುವುದು',
                    'ಬರುವುದು', 'ಹೇಳಿದು', 'ತಿಳಿಯುವುದು', 'ನೋಡುವುದು', 'ಕೇಳುವುದು', 'ಕೊಡುವುದು', 'ಬರುಸು', 'ಹೇಳಿಸೆ',
                    'ತಿಳಿದ್ದೆ', 'ನೋಡಿದ್ದೆ', 'ಕೇಳ್ದೆ', ' ಕೊಟ್ಟೆ', ' ಅಲ್ಲಿ', 'ಇಲ್ಲಿ', 'ಇದಿಗೆ, ಅವರು,ನಮ್ಮ',' ತನ್ನ', 'ಇವನು', 'ಅವಳು',
                    'ಅದು', 'ಇವರು', 'ಅಂತ', 'ಎಲ್ಲಾ', ' ಎಂತ', ' ಎಲ್ಲವೋ', 'ಎಂತದ್ದೇ', 'ಎಲ್ಲಾದು']
        return any(word.endswith(suffix) for suffix in noun_suffixes)

    def is_verb(self, word):
        # Implement a heuristic or rule to identify verbs based on morphology or context
        # For example, check if the word ends with specific suffixes common in Kannada verbs
        verb_suffixes = ['ಬರೆ', 'ಓದು', 'ನು', 'ನಿಂದ', 'ತೆ', 'ದು', 'ಕೆ', 'ಬೇಕು']
        return any(word.endswith(suffix) for suffix in verb_suffixes)

    def on_extract_browse(self, event):
        wildcard = "All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Choose a file for Extraction", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                               wildcard=wildcard)
        if dialog.ShowModal() == wx.ID_OK:
            self.extract_file_entry.SetValue(dialog.GetPath())
        dialog.Destroy()

    def on_classify_browse(self, event):
        wildcard = "All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Choose a file for Classification", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                               wildcard=wildcard)
        if dialog.ShowModal() == wx.ID_OK:
            self.classify_file_entry.SetValue(dialog.GetPath())
        dialog.Destroy()

    # Add a new method to clear all fields and lists
    def clear_all(self, event):
        # Clear text fields
        self.extract_file_entry.Clear()
        self.classify_file_entry.Clear()
        self.text_input.Clear()
        self.num_keywords_entry.SetValue(self.num_keywords)
        self.keywords_display.Clear()

        # Clear noun and verb lists
        self.noun_display.Clear()
        self.verb_display.Clear()

    def extract_keywords(self, event):
        # Get document file path or text input
        doc_file_path = self.extract_file_entry.GetValue()
        if doc_file_path:
            doc_text = self.extract_text_from_document(doc_file_path)
            self.text_input.SetValue(doc_text)  # Update text input area (optional)
        else:
            doc_text = self.text_input.GetValue()

        # Detect language
        try:
            detected_lang = detect(doc_text)
        except:
            wx.MessageBox("Unable to detect language. Please enter valid text.", "Error", wx.OK | wx.ICON_ERROR)
            return

        if detected_lang != 'kn':
            wx.MessageBox("Please use Kannada text.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Extract keywords
        num_keywords = int(self.num_keywords_entry.GetValue())
        keywords = self.extract_kannada_keywords(doc_text, num_keywords)

        # Display extracted keywords
        keywords_str = ', '.join(keywords)
        self.keywords_display.SetValue(keywords_str)

    # Helper function for keyword type classification (can be placed elsewhere)
    def classify_kannada_keyword(keyword):
        # Classifies a Kannada keyword into noun or verb based on suffixes.
        # Args:
        #     keyword (str): The Kannada keyword to classify.
        # Returns:
        #     str: The keyword type ("noun", "verb") or None if not classified.

        noun_suffixes = ["ವರು", "ವಳು", "ಅದು", "ವು", "ನ", "ನಿಂದ", "ರು", "ದು", "ಕೆ", "ಬೇಕು", "ಆಯಿ", "ಉತ್ತಿತ್ತು",
                         "ಇದೆ", "ಇಲ್ಲ", "ಇರುತ್ತದೆ", "ಒಂದು", "ಒನ್ನು", "ಗಳಿಗೆ", "ಚೆನ್ನಾಗಿ", "ತ್ತದೆ", "ತ್ತಾನೆ", "ದೆಯ",
                         "ದೇವರೆ",
                         "ನಿಂದ", "ಇಸುವುದು", "ಇಕ್ಕುವುದು", "ಇಕ್ಕೊಳ್ಳುವುದು", "ಆಗುವುದು", "ಕೊಳ್ಳುವುದು", "ಮಾಡುವುದು",
                         "ಹೋಗುವುದು",
                         "ಬರುವುದು", "ಹೇಳಿದು", "ತಿಳಿಯುವುದು", "ನೋಡುವುದು", "ಕೇಳುವುದು", "ಕೊಡುವುದು", "ಬರುಸು", "ಹೇಳಿಸೆ",
                         "ತಿಳಿದ್ದೆ", "ನೋಡಿದ್ದೆ", "ಕೇಳ್ದೆ", "ಕೊಟ್ಟೆ", "ಅಲ್ಲಿ", "ಇಲ್ಲಿ", "ಇದಿಗೆ", "ಅವರು", "ನಮ್ಮ", "ತನ್ನ",
                         "ಇವನು",
                         "ಅದು", "ಇವರು", "ಅಂತ", "ಎಲ್ಲಾ", "ಎಂತ", "ಎಲ್ಲವೋ", "ಎಂತದ್ದೇ", "ಎಲ್ಲಾದು"]

        verb_suffixes = ["ನು", "ನಿಂದ", "ಗಳು", "ತೆ", "ದು", "ಕೆ", "ಬೇಕು", "ವು", "ಲು", "ಡು", "ಲೆ", "ತು", "ಕ್ಕೆ", "ಗೆ",
                 "ಮಾಡು", "ಬಾರೆ", "ಬಾರ", "ಕೊಡು", "ಹೋಗು", "ಅಗಿ", "ಅನು", "ಅಲ್ಲಿ", "ತ್ತದೆ", "ತ್ತಾನೆ", "ಗೆಲ್ಲಲು", "ಮಾಡುವ",
                 "ಹೋಗುವ", "ಬರುವ", "ಹೇಳಿದ್ದೆ", "ನೋಡಿದ್ದೆ", "ಕೇಳ್ದೆ", "ಕೊಟ್ಟೆ", "ಇಲ್ಲಿ", "ಇದಿಗೆ", "ತನ್ನ", "ಅಂತ",
                 "ಎಲ್ಲಾ", "ಎಂತ", "ಅಲ್ಲಿ", "ಇಲ್ಲವೋ", "ಎಂತದ್ದೆ", "ಎಲ್ಲಾದು"]

        if any(keyword.endswith(suffix) for suffix in noun_suffixes):
            return "noun"
        elif any(keyword.endswith(suffix) for suffix in verb_suffixes):
            return "verb"
        else:
            return None

    def classify_keywords(self, event):
        # Get document file path
        doc_file_path = self.classify_file_entry.GetValue()

        # Check if the text is entered manually
        if not doc_file_path:
            doc_text = self.text_input.GetValue()
        else:
            # Extract text from document
            doc_text = self.extract_text_from_document(doc_file_path)

            # Display extracted text in the text input area
            self.text_input.SetValue(doc_text)

        # Detect language
        try:
            detected_lang = detect(doc_text)
        except:
            wx.MessageBox("Unable to detect language. Please enter valid text.", "Error", wx.OK | wx.ICON_ERROR)
            return

        if detected_lang != 'kn':
            wx.MessageBox("Please use Kannada text.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Tokenize text into words
        tokens = indic_tokenize.trivial_tokenize(doc_text, lang='kn')

        # Tag Kannada words
        tagged_tokens = self.tag_kannada_words(tokens)

        # Classify keywords into nouns and verbs
        nouns = []
        verbs = []
        for word, pos_tag in tagged_tokens:
            if pos_tag == 'Noun':
                nouns.append(word)
            elif pos_tag == 'Verb':
                verbs.append(word)

        # Display classified keywords
        self.noun_display.Set(nouns)
        self.verb_display.Set(verbs)

    def extract_text_from_document(self, file_path):
        if file_path.endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        elif file_path.endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.txt'):
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError("Unsupported file format")

    def extract_text_from_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text

    def extract_text_from_docx(self, file_path):
        text = ''
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text
        except Exception as e:
            print("Error:", str(e))
        return text

    def extract_text_from_pdf(self, file_path):
        text = ''
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfFileReader(file)
                for page_num in range(reader.numPages):
                    page = reader.getPage(page_num)
                    text += page.extractText()
        except Exception as e:
            print("Error:", str(e))
        return text



    def extract_kannada_keywords(self, text, num_keywords):
        tokens = indic_tokenize.trivial_tokenize(text, lang='kn')

        def remove_numbers(word):
            """Removes numbers from a word using regular expressions."""
            return re.sub(r"\d+", "", word)

        stopwords = stopword()  # Assuming stopword() returns a list of stopwords
        filtered_tokens = [remove_numbers(token) for token in tokens if token not in stopwords]
        filtered_tokens = [token for token in filtered_tokens if token]  # Remove empty strings

        word_frequencies = Counter(filtered_tokens)
        keywords = [word for word, _ in word_frequencies.most_common(num_keywords)]
        return keywords

    def save_keywords(self, event):
        # Get input text
        text = self.text_input.GetValue()

        # Extract keywords
        num_keywords = int(self.num_keywords_entry.GetValue())
        keywords = self.extract_kannada_keywords(text, num_keywords)

        # Prompt user to select a file to save
        wildcard = "Text files (*.txt)|*.txt"
        dialog = wx.FileDialog(self, "Save Keywords", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            output_file_path = dialog.GetPath()
            self.save_list_to_file(keywords, output_file_path)
        dialog.Destroy()

    def save_nouns(self, event):
        nouns = self.noun_display.GetItems()
        self.save_list_to_file(nouns, r"C:\Users\X1\Desktop\kannada files\nouns_list.txt")

    def save_verbs(self, event):
        verbs = self.verb_display.GetItems()
        self.save_list_to_file(verbs, r"C:\Users\X1\Desktop\kannada files\verbs_list.txt")

    def save_list_to_file(self, keywords, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            for keyword in keywords:
                file.write(f"{keyword}\n")


if __name__ == '__main__':
    app = wx.App()
    KannadaKeywordExtractorClassifierApp(None, title='Kannada Keyword Extraction and Classifier')
    app.MainLoop()
