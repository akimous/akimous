import numpy as np
import pandas as pd

from .feature import FeatureDefinition

INITIAL_SIZE = 1


class OfflineFeatureExtractor(FeatureDefinition):
    def __init__(self):
        super().__init__()
        self.n_samples = 0
        self.X = np.zeros([INITIAL_SIZE, self.n_features], dtype=int)
        self.y = np.zeros(INITIAL_SIZE, dtype=int)
        self.sample = np.zeros(self.n_features, dtype=int)
        self.tokens = []

        self.index = []
        self.completions = []
        self.current_completion_start_index = 0
        self.last_token = None

    def add(self,
            token,
            completion,
            line_content,
            line,
            ch,
            doc,
            call_signatures,
            positive=True):
        if len(self.y) == self.n_samples:
            new_size = self.n_samples * 2
            self.X.resize([new_size, self.n_features])
            self.y.resize(new_size)

        self.tokens.append(token)
        self.completions.append(completion.name)

        completion_data_type = 'unknown'
        try:
            definitions = completion.infer()
            if definitions:
                completion_data_type = definitions[0].name
        except:
            pass

        if id(self.last_token) != id(token):
            # self.stack_context_info = self.get_stack_context_info(completion)
            for f in FeatureDefinition.preprocessors:
                f(line_content=line_content[:ch],
                  line=line - 1,
                  ch=ch - 1,
                  doc=doc,
                  call_signatures=call_signatures,
                  completion_data_type=completion_data_type,
                  context=self.context)
            for i, f in enumerate(FeatureDefinition.context_features.values()):
                feature = f(line_content=line_content[:ch],
                            line=line - 1,
                            ch=ch - 1,
                            doc=doc,
                            call_signatures=call_signatures,
                            completion_data_type=completion_data_type,
                            context=self.context
                            # stack_context_info=self.stack_context_info
                            )
                self.sample[
                    i + len(FeatureDefinition.completion_features)] = feature

        self.last_token = token

        for i, f in enumerate(FeatureDefinition.completion_features.values()):
            self.sample[i] = f(completion=completion,
                               line_content=line_content[:ch],
                               line=line - 1,
                               ch=ch - 1,
                               doc=doc,
                               call_signatures=call_signatures,
                               completion_data_type=completion_data_type,
                               context=self.context
                               # stack_context_info=self.stack_context_info
                               )
        self.X[self.n_samples] = self.sample
        self.y[self.n_samples] = 1 if positive else 0
        self.n_samples += 1

    def end_current_completion(self, can_complete):
        if can_complete:
            self.index.append(self.n_samples)
            self.normalize_feature()
            self.current_completion_start_index = self.n_samples
        else:
            self.n_samples = self.current_completion_start_index
            if len(self.tokens) > self.n_samples:
                del self.tokens[self.n_samples:]
                del self.completions[self.n_samples:]

    def finalize(self):
        self.X.resize([self.n_samples, self.n_features])
        self.y.resize(self.n_samples)
        self.context = None
        self.preprocessors = None
        self.context_names_required_by_preprocessors = None

    def dataframe(self):
        feature_names = list(FeatureDefinition.completion_features) + list(
            FeatureDefinition.context_features)
        df = pd.DataFrame(self.X, columns=feature_names)
        token_names = pd.DataFrame(self.completions, columns=['c'])
        y = pd.DataFrame(self.y, columns=['y'])
        return pd.concat([token_names, y, df], axis=1)
