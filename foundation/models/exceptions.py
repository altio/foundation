class AssociativeAttributeError(AttributeError):
    def __init__(self, class_name, attr_name):
        message = (
            'This {class_name} does not have a {attr_name} attached.  This '
            'most likely happened because a {class_name} instance method was '
            'called outside of a view context.'
        ).format(class_name=class_name, attr_name=attr_name)
        super(AssociativeAttributeError, message)
