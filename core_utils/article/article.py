"""
Article implementation.
"""
import enum
import pathlib
import re
from datetime import datetime
from typing import Optional, Protocol, Sequence

from stanza.utils.conll import Document

from core_utils.constants import ASSETS_PATH


def date_from_meta(date_txt: str) -> datetime:
    """
    Convert text date to datetime object.

    Args:
        date_txt (str): Date in text format

    Returns:
        datetime.datetime: Datetime object
    """
    return datetime.strptime(date_txt, "%Y-%m-%d %H:%M:%S")


def get_article_id_from_filepath(path: pathlib.Path) -> int:
    """
    Extract the article id from its path.

    Args:
        path (pathlib.Path): Path to article

    Returns:
        int: Article id
    """
    return int(path.stem.split('_')[0])


def split_by_sentence(text: str) -> list[str]:
    """
    Splits the given text by sentence separators.

    Args:
        text (str): raw text to split

    Returns:
        list[str]: List of sentences
    """
    pattern = r"(?<!\w\.\w.)(?<![А-Я][а-я]\.)((?<=\.|\?|!)|(?<=\?\"|!\"))\s(?=[А-Я])"
    text = re.sub(r'[\n|\t]+', '. ', text)
    sentences = [sentence for sentence in re.split(pattern, text) if sentence.replace(' ', '')
                 and len(sentence) > 10]
    return sentences


# pylint: disable=too-few-public-methods
class SentenceProtocol(Protocol):
    """
    Protocol definition for sentences.

    Make dependency inversion from direct
    import from lab 6 implementation of ConlluSentence.
    """

    def get_cleaned_sentence(self) -> str:
        """
        Clean a sentence.

        All tokens should be normalized and joined with a space

        Returns:
            str: Clean sentence
        """

    def get_tokens(self) -> list:
        """
        Get tokens as ConlluToken instances.

        Returns:
            list: List of ConlluToken instances
        """

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Get a text in the CONLL-U format.

        Args:
            include_morphological_tags (bool): Include morphological tags or not

        Returns:
            str: A text in the CONLL-U format
        """


class ArtifactType(enum.Enum):
    """
    Types of artifacts that can be created by text processing pipelines.
    """
    CLEANED = 'cleaned'
    MORPHOLOGICAL_CONLLU = 'morphological_conllu'
    POS_CONLLU = 'pos_conllu'
    FULL_CONLLU = 'full_conllu'


class Article:
    """
    Article class implementation.
    """
    #: A date
    date: Optional[datetime]
    _conllu_sentences: Sequence[SentenceProtocol] | Document

    def __init__(self, url: Optional[str], article_id: int) -> None:
        """
        Initialize an instance of Article.

        Args:
            url (Optional[str]): Site url
            article_id (int): Article id
        """
        self.url = url
        self.article_id = article_id

        self.title = ''
        self.date = None
        self.author = []
        self.topics = []
        self.text = ''
        self.pos_frequencies = {}
        self._conllu_sentences = []

    def set_pos_info(self, pos_freq: dict) -> None:
        """
        Set POS frequencies attribute.

        Args:
            pos_freq (dict): POS frequencies
        """
        self.pos_frequencies = pos_freq

    def get_meta(self) -> dict:
        """
        Get all meta params.

        Returns:
            dict: Meta params
        """
        return {
            'id': self.article_id,
            'url': self.url,
            'title': self.title,
            'date': self._date_to_text() or None,
            'author': self.author,
            'topics': self.topics,
            'pos_frequencies': self.pos_frequencies
        }

    def get_raw_text(self) -> str:
        """
        Get raw text from the article.

        Returns:
            str: Raw text from the article
        """
        return self.text

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Get the text in the CONLL-U format.

        Args:
            include_morphological_tags (bool): Flag to include morphological information

        Returns:
            str: A text in the CONLL-U format
        """
        return '\n'.join([sentence.get_conllu_text(include_morphological_tags) for sentence in
                          self._conllu_sentences])

    def set_conllu_sentences(self, sentences: Sequence[SentenceProtocol]) -> None:
        """
        Set the conllu_sentences_attribute.

        Args:
            sentences (Sequence[SentenceProtocol]): CONLL-U sentences
        """
        self._conllu_sentences = sentences

    def get_conllu_sentences(self) -> Sequence[SentenceProtocol]:
        """
        Get the sentences from ConlluArticle.

        Returns:
            Sequence[SentenceProtocol]: Sentences from ConlluArticle
        """
        return self._conllu_sentences

    def get_cleaned_text(self) -> str:
        """
        Get cleaned text.

        Returns:
            str: Cleaned text.
        """
        if isinstance(self._conllu_sentences, Document):
            return str(self._conllu_sentences.text)
        return ' '.join([sentence.get_cleaned_sentence() for
                         sentence in self._conllu_sentences])

    def _date_to_text(self) -> str:
        """
        Convert datetime object to text.

        Returns:
            str: Datetime object
        """
        return self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else ''

    def get_raw_text_path(self) -> pathlib.Path:
        """
        Get path for requested raw article.

        Returns:
            pathlib.Path: Path to requested raw article
        """
        article_txt_name = f"{self.article_id}_raw.txt"
        return ASSETS_PATH / article_txt_name

    def get_meta_file_path(self) -> pathlib.Path:
        """
        Get path for requested article's meta info.

        Returns:
            pathlib.Path: Path to requested article's meta info
        """
        meta_file_name = f"{self.article_id}_meta.json"
        return ASSETS_PATH / meta_file_name

    def get_file_path(self, kind: ArtifactType) -> pathlib.Path:
        """
        Get a proper filepath for an Article instance.

        Args:
            kind (ArtifactType): A variant of a file

        Returns:
            pathlib.Path: Path to Article instance
        """
        conllu = kind in (ArtifactType.POS_CONLLU,
                          ArtifactType.MORPHOLOGICAL_CONLLU,
                          ArtifactType.FULL_CONLLU)

        extension = '.conllu' if conllu else '.txt'
        article_name = f"{self.article_id}_{kind.value}{extension}"

        return ASSETS_PATH / article_name

    def get_pos_freq(self) -> dict:
        """
        Get a pos_frequency parameter.

        Returns:
            dict: POS frequency
        """
        return self.pos_frequencies

    def get_pattern_path(self) -> pathlib.Path:
        """
        Get path for requested article's pattern info.

        Returns:
            pathlib.Path: Path to requested article's pattern info
        """
        pattern_file_name = f"{self.article_id}_pattern.json"
        return ASSETS_PATH / pattern_file_name
