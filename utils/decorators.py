from functools import wraps
from rest_framework import status
from rest_framework.response import Response


def required_params(method='GET', params=None):
    """
    This decorator is used for parameters check in viewsets
    """
    if params is None:
        params = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            """
            @wraps is used for restoring view_func's properties
            instance is 'self' in viewset fucntion parameters
            """
            # request_attr might be 'query_params' for GET or 'data' for POST
            if method.lower() == 'get':
                data = request.query_params
            else:
                data = request.data
            missing_params = [
                param
                for param in params
                if param not in data
            ]
            if missing_params:
                params_str = ','.join(missing_params)
                return Response({
                    'message': u'missing {} in request'.format(params_str),
                    'success': False,
                }, status=status.HTTP_400_BAD_REQUEST)

            return view_func(instance, request, *args, **kwargs)

        return _wrapped_view

    return decorator
