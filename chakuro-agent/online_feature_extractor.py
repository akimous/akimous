import numpy as np
from modeling.feature_definition import FeatureDefinition

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
        
    def extract_online(self, completions, line_content, line, ch, doc, call_signatures):
        self.reset(len(completions))
        
        # context features
        completion = completions[0]
        # self.stack_context_info = self.get_stack_context_info(completion)
        completion_data_type = 'unknown'
        if completion.type == 'instance':
            definitions = completion.follow_definition()
            if definitions:
                completion_data_type = definitions[0].name

        for f in FeatureDefinition.preprocessors:
            f(line_content=line_content[:ch],
              line=line - 1, ch=ch - 1, doc=doc,
              call_signatures=call_signatures,
              completion_data_type=completion_data_type,
              context=self.context
              )
        for i, f in enumerate(FeatureDefinition.context_features.values()):
            feature = f(line_content=line_content[:ch],
                        line=line-1, ch=ch, doc=doc,
                        call_signatures=call_signatures,
                        completion_data_type=completion_data_type,
                        context=self.context
                        # stack_context_info=self.stack_context_info
                        )
            self.sample[i+len(FeatureDefinition.token_features)] = feature
            
        # completion features
        for completion in completions:
            for i, f in enumerate(FeatureDefinition.token_features.values()):
                self.sample[i] = f(completion=completion,
                                   line_content=line_content[:ch],
                                   line=line-1, ch=ch, doc=doc,
                                   call_signatures=call_signatures,
                                   completion_data_type=completion_data_type,
                                   context=self.context
                                   # stack_context_info=self.stack_context_info
                                   )
            self.X[self.n_samples] = self.sample
            self.n_samples += 1
            
        self.normalize_feature()