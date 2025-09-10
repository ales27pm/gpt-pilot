from django.http import HttpResponse


def index(request):
    """
    Return a simple HTTP response with the greeting "Hello, Django!".
    
    Parameters:
        request (django.http.HttpRequest): Incoming HTTP request (unused).
    
    Returns:
        django.http.HttpResponse: Response containing the plain-text greeting.
    """
    return HttpResponse("Hello, Django!")
