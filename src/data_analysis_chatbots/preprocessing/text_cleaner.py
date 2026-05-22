"""Text cleaning and preprocessing utilities for NLP tasks."""

import re
import string
from typing import List, Optional, Set, Union
import pandas as pd
from loguru import logger


class TextCleaner:
    """Clean and preprocess text data."""

    def __init__(
        self,
        lowercase: bool = True,
        remove_urls: bool = True,
        remove_mentions: bool = True,
        remove_hashtags: bool = False,
        remove_numbers: bool = False,
        remove_punctuation: bool = True,
        remove_extra_whitespace: bool = True
    ):
        """
        Initialize the TextCleaner.

        Args:
            lowercase: Convert text to lowercase
            remove_urls: Remove URLs
            remove_mentions: Remove @ mentions
            remove_hashtags: Remove # hashtags
            remove_numbers: Remove numbers
            remove_punctuation: Remove punctuation
            remove_extra_whitespace: Remove extra whitespace
        """
        self.lowercase = lowercase
        self.remove_urls = remove_urls
        self.remove_mentions = remove_mentions
        self.remove_hashtags = remove_hashtags
        self.remove_numbers = remove_numbers
        self.remove_punctuation = remove_punctuation
        self.remove_extra_whitespace = remove_extra_whitespace

        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(r'http\S+|www\S+|https\S+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.number_pattern = re.compile(r'\d+')

    def clean_text(self, text: str) -> str:
        """
        Clean a single text string.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""

        cleaned = text

        # Remove URLs
        if self.remove_urls:
            cleaned = self.url_pattern.sub('', cleaned)

        # Remove mentions
        if self.remove_mentions:
            cleaned = self.mention_pattern.sub('', cleaned)

        # Remove hashtags
        if self.remove_hashtags:
            cleaned = self.hashtag_pattern.sub('', cleaned)

        # Remove numbers
        if self.remove_numbers:
            cleaned = self.number_pattern.sub('', cleaned)

        # Remove punctuation
        if self.remove_punctuation:
            cleaned = cleaned.translate(str.maketrans('', '', string.punctuation))

        # Convert to lowercase
        if self.lowercase:
            cleaned = cleaned.lower()

        # Remove extra whitespace
        if self.remove_extra_whitespace:
            cleaned = ' '.join(cleaned.split())

        return cleaned.strip()

    def clean_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str,
        output_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Clean text in a DataFrame column.

        Args:
            df: Input DataFrame
            text_column: Name of the column containing text
            output_column: Name for the output column. If None, overwrites input column.

        Returns:
            DataFrame with cleaned text

        Raises:
            ValueError: If df is None or not a pandas DataFrame, or if text_column not found
        """
        if df is None:
            raise ValueError("DataFrame cannot be None")

        if not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")

        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")

        logger.info(f"Cleaning text in column: {text_column}")

        # Create output column
        if output_column is None:
            output_column = text_column

        # Clean each text
        df[output_column] = df[text_column].apply(self.clean_text)

        logger.success(f"Successfully cleaned {len(df)} texts")

        return df

    # Alias kept for the simpler name pattern; some callers use
    # `clean_dataframe_column` because that's what the test suite
    # standardised on. Behaviour is identical.
    def clean_dataframe_column(
        self,
        df: pd.DataFrame,
        text_column: str,
        output_column: Optional[str] = None,
    ) -> pd.DataFrame:
        return self.clean_dataframe(df, text_column, output_column)

    def get_word_count(self, text: str) -> int:
        """Get the number of words in text."""
        return len(text.split())

    def get_char_count(self, text: str) -> int:
        """Get the number of characters in text."""
        return len(text)

    def remove_stopwords(self, text: str, stopwords: Union[List[str], Set[str]]) -> str:
        """
        Remove stopwords from text.

        Args:
            text: Input text
            stopwords: List or set of stopwords to remove

        Returns:
            Text with stopwords removed
        """
        # Convert to set for O(1) lookup if not already a set
        stopwords_set = stopwords if isinstance(stopwords, set) else set(stopwords)
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in stopwords_set]
        return ' '.join(filtered_words)

    def __repr__(self):
        return (
            f"TextCleaner(lowercase={self.lowercase}, "
            f"remove_urls={self.remove_urls}, "
            f"remove_mentions={self.remove_mentions}, "
            f"remove_hashtags={self.remove_hashtags}, "
            f"remove_numbers={self.remove_numbers}, "
            f"remove_punctuation={self.remove_punctuation})"
        )


class NLTKTextCleaner(TextCleaner):
    """Text cleaner using NLTK for advanced preprocessing."""

    def __init__(self, *args, use_lemmatization: bool = True, language: str = 'english', **kwargs):
        """
        Initialize NLTK-based text cleaner.

        Args:
            use_lemmatization: Use lemmatization instead of stemming
            language: Language for stopwords and lemmatization
            *args, **kwargs: Arguments passed to TextCleaner
        """
        super().__init__(*args, **kwargs)
        self.use_lemmatization = use_lemmatization
        self.language = language

        # Import NLTK components
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer, PorterStemmer

            # Download required NLTK data
            for resource in ['stopwords', 'wordnet', 'punkt']:
                try:
                    nltk.data.find(f'corpora/{resource}' if resource != 'punkt' else f'tokenizers/{resource}')
                except LookupError:
                    nltk.download(resource, quiet=True)

            self.stopwords = set(stopwords.words(language))
            self.lemmatizer = WordNetLemmatizer() if use_lemmatization else None
            self.stemmer = PorterStemmer() if not use_lemmatization else None

        except ImportError:
            logger.warning("NLTK not installed. Install with: pip install nltk")
            self.stopwords = set()
            self.lemmatizer = None
            self.stemmer = None

    def clean_text(self, text: str) -> str:
        """
        Clean text using NLTK tools.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # First apply basic cleaning
        cleaned = super().clean_text(text)

        if not cleaned:
            return ""

        # Remove stopwords
        if self.stopwords:
            cleaned = self.remove_stopwords(cleaned, self.stopwords)

        # Apply lemmatization or stemming
        if self.lemmatizer:
            words = cleaned.split()
            words = [self.lemmatizer.lemmatize(word) for word in words]
            cleaned = ' '.join(words)
        elif self.stemmer:
            words = cleaned.split()
            words = [self.stemmer.stem(word) for word in words]
            cleaned = ' '.join(words)

        return cleaned
