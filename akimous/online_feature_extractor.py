import numpy as np

from .modeling.feature.feature_definition import FeatureDefinition
from .modeling.utility import p, to_key_value_columns


class OnlineFeatureExtractor(FeatureDefinition):
    def reset(self, initial_size=1):
        self.n_samples = 0
        self.X = np.zeros([initial_size, self.n_features], dtype=int)
        self.y = np.zeros(initial_size, dtype=int)
        self.sample = np.zeros(self.n_features, dtype=int)
        self.tokens = []

        self.index = []
        self.completions = []
        self.current_completion_start_index = 0
        self.last_token = None
        # self.stack_context_info = self.get_stack_context_info(None)

    def fill_preprocessor_context(self, line_content, line, doc):
        for f in FeatureDefinition.preprocessors:
            f(line_content=line_content, line=line, ch=0, doc=doc, context=self.context)

    def extract_online(self, completions, line_content, line, ch, doc, call_signatures):
        self.reset(len(completions))

        # context features
        completion = completions[0]
        # self.stack_context_info = self.get_stack_context_info(completion)
        completion_data_type = 'unknown'
        if completion.type == 'instance':
            definitions = completion.infer()
            if definitions:
                completion_data_type = definitions[0].name

        for f in FeatureDefinition.preprocessors:
            f(
                line_content=line_content[:ch],  # TODO: should slice at ch or not?
                line=line,
                ch=ch - 1,
                doc=doc,
                context=self.context)
        for i, f in enumerate(FeatureDefinition.context_features.values()):
            feature = f(
                line_content=line_content[:ch],
                line=line,
                ch=ch,
                doc=doc,
                call_signatures=call_signatures,
                completion_data_type=completion_data_type,
                context=self.context
                # stack_context_info=self.stack_context_info
            )
            self.sample[i + len(FeatureDefinition.completion_features)] = feature

        # completion features
        for completion in completions:
            for i, f in enumerate(FeatureDefinition.completion_features.values()):
                self.sample[i] = f(
                    completion=completion,
                    line_content=line_content[:ch],
                    line=line,
                    ch=ch,
                    doc=doc,
                    call_signatures=call_signatures,
                    completion_data_type=completion_data_type,
                    context=self.context
                    # stack_context_info=self.stack_context_info
                )
            self.X[self.n_samples] = self.sample
            self.n_samples += 1
            p('=' * 40 + f' {completion.name} ' + '=' * 40)
            p(to_key_value_columns(self.name_to_feature_index.keys(), self.sample))
        self.normalize_feature()
