from wtforms.validators import ValidationError


class DuplicateBreachTypeException(ValidationError):
    """
    Custom Exception Class if there is already a record present for the breach type in score table
    """
    def __init__(self, breach_type, breach_category):
        self.message = "Record for Breach Type: '{0}' and Breach Category: '{1}' already exists, please change the existing record.".format(breach_type, breach_category)
        super().__init__(self.message)


class DuplicateBreachSubTypeException(ValidationError):
    """
    Custom Exception Class if there is already a record present for the breach type group and subtype group in breach_subtype_group_score table
    """
    def __init__(self, breach_type_group, breach_subtype):
        self.message = "Record for Breach Type Group: '{0}' and Breach Type SubGroup: '{1}' already exists, please change the existing record.".format(breach_type_group, breach_subtype)
        super().__init__(self.message)


class DuplicateBreachTypeGroupFrequencyException(ValidationError):
    """
    Custom Exception Class if there is already a record present for the breach type group and frequency in breach_subtype_group_score table
    """
    def __init__(self, breach_type_group, frequency):
        self.message = "Record for Breach Type Group: '{0}' and Frequency: '{1}' already exists, please change the existing record.".format(breach_type_group, frequency)
        super().__init__(self.message)


class DuplicateBreachTypeGroupQuestionException(ValidationError):
    """
    Custom Exception Class if there is already a record present for the breach type group, breach subtype and frequency in breach_subtype_group_score table
    """
    def __init__(self, breach_type_group, breach_subtype, question):
        self.message = "Record for Breach Type Group: '{0}', Breach SubType: '{1}' and Question: '{2}' already exists, please change the existing record.".format(breach_type_group, breach_subtype, question)
        super().__init__(self.message)


class DuplicateTotalBreachScoreException(ValidationError):
    """
    Custom Exception Class if there is already a record present for the score in recommended actions table
    """
    def __init__(self, total_breach_score):
        self.message = "Record for Breach Score: '{0}' already exists, please change the existing record.".format(total_breach_score)
        super().__init__(self.message)


class EmptyBreachTypesException(ValidationError):
    """
    Custom Exception Class if no Breach Types have been selected
    """
    def __init__(self):
        self.message = "Please select at least one Breach Type."
        super().__init__(self.message)


class MultipleQuestionForOneLevelException(ValidationError):
    """
    Custom Exception Class if no Breach Types have been selected
    """
    def __init__(self):
        self.message = "For a single breach type group, there cannot be different questions at one level."
        super().__init__(self.message)


class WrongFrequencyCountException(ValidationError):
    """
    Custom Exception Class if frequency count < 1
    """
    def __init__(self):
        self.message = "Frequency count has to be greater than 1."
        super().__init__(self.message)


class InvalidLevelException(ValidationError):
    """
    Custom Exception Class if level entered is invalid
    """
    def __init__(self):
        self.message = "Level has to be >= 1."
        super().__init__(self.message)


class InvalidArgumentsForBreachSubtypeScore(ValidationError):
    """
    Custom Exception Input arguments are incorrect
    """
    def __init__(self):
        self.message = "Cannot provide values for both frequency_count and question"
        super().__init__(self.message)



class EmptyBreachSubTypeException(ValidationError):
    """
    Custom Exception Class if the Breach Type SubGroup field is empty
    """
    def __init__(self):
        self.message = "Breach Type SubGroup cannot be empty."
        super().__init__(self.message)


class NullQuestionOrLevelException(ValidationError):
    """
    Custom Exception Class if the Breach Type SubGroup field is empty
    """
    def __init__(self):
        self.message = "Question and Level both will have to be defined if Frequency Count is not defined."
        super().__init__(self.message)
