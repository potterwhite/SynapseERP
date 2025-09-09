from django.utils import translation
from django.urls import translate_url
from django.http import HttpResponseRedirect

# The key used by Django to store the language setting in the session.
LANGUAGE_SESSION_KEY = "_language"
DEFAULT_LANGUAGE = "zh-hans"


class ForceDefaultLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We check if the language key is already in the session dictionary.
        if LANGUAGE_SESSION_KEY not in request.session:
            # If the key is not present, this is the user's first visit.
            # We activate the default language and set it in the session.
            translation.activate(DEFAULT_LANGUAGE)
            request.session[LANGUAGE_SESSION_KEY] = DEFAULT_LANGUAGE
            
            # Also, we redirect to the same URL but with the language prefix.
            # This ensures the URL bar reflects the correct language.
            redirect_url = translate_url(request.path, DEFAULT_LANGUAGE)
            
            # Add query string if it exists
            if request.GET:
                redirect_url += '?' + request.GET.urlencode()

            return HttpResponseRedirect(redirect_url)

        response = self.get_response(request)
        return response
