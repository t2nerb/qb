import numpy as np
import pickle
from unidecode import unidecode
from qanta.extractors.abstract import FeatureExtractor
from qanta.util.qdb import QuestionDatabase
from qanta.util.constants import SENTENCE_STATS
from qanta.util.io import safe_open


class Labeler(FeatureExtractor):
    def __init__(self, question_db: QuestionDatabase):
        super(Labeler, self).__init__()
        self.name = 'label'
        self.counts = {}
        all_questions = question_db.questions_with_pages()
        with open(SENTENCE_STATS, 'rb') as f:
            self.mean, self.std = pickle.load(f)

        # Get the counts
        for ii in all_questions:
            self.counts[ii] = sum(1 for x in all_questions[ii] if x.fold == "train")
        # Standardize the scores
        count_mean = np.mean(list(self.counts.values()))
        count_var = np.var(list(self.counts.values()))
        for ii in all_questions:
            self.counts[ii] = float(self.counts[ii] - count_mean) / count_var

    def score_guesses(self, guesses, text):
        n_words = len(text.split())
        normalized_count = (n_words - self.mean) / self.std
        for guess in guesses:
            formatted_guess = guess.replace(":", "").replace("|", "")

            if formatted_guess == self._correct:
                feature = "1 '%s |guess %s sent:%0.1f count:%f words_seen:%i norm_words_seen:%f" % \
                    (self._id, unidecode(formatted_guess).replace(" ", "_"),
                     self._sent, self.counts.get(formatted_guess, -2), n_words, normalized_count)
                yield feature, guess
            else:
                feature = "-1 %i '%s |guess %s sent:%0.1f count:%f words_seen:%i norm_words_seen:%f" % \
                    (self._num_guesses, self._id,
                     unidecode(formatted_guess).replace(" ", "_"),
                     self._sent, self.counts.get(formatted_guess, -2), n_words, normalized_count)
                yield feature, guess


def compute_question_stats(question_db: QuestionDatabase):
    question_lengths = [len(q.flatten_text().split())
                        for q in question_db.guess_questions()
                        if q.fold == 'train' or q.fold == 'dev']

    mean = np.mean(question_lengths)
    std = np.std(question_lengths)

    stats = (mean, std)

    with safe_open(SENTENCE_STATS, 'wb') as f:
        pickle.dump(stats, f)
