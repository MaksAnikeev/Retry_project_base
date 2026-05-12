from src.exceptions import NotAllowedParameterException

def check_safe_filters(safe_filters):
    if not safe_filters:
        raise NotAllowedParameterException
