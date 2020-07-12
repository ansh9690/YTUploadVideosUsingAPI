from django.shortcuts import redirect, render
from django.views.generic.base import View
from django.http import HttpResponseBadRequest, HttpResponse
from django.conf import settings
from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel

import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django import forms
from django.contrib import messages


class YouTubeForm(forms.Form):
    video = forms.FileField()


def home(request):
    if request.method == 'POST' and request.FILES['video']:
        form = YouTubeForm(request.POST, request.FILES)
        if form.is_valid():
            if request.FILES['video'].size >= 2621440:
                fname = request.FILES['video'].file.name
                messages.success(request, "Equal to or over 2.5 megabytes, saving to disk and uploading")
                storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
                credentials = storage.get()
                client = build('youtube', 'v3', credentials=credentials)
                body = {
                    'snippet': {
                        'title': 'Upload Youtube Video',
                        'description': 'Video Description',
                        'tags': 'django,howto,video,api',
                        'categoryId': '27'
                    },
                    'status': {
                        'privacyStatus': 'unlisted'
                    }
                }
                with tempfile.NamedTemporaryFile('wb', suffix='yt-django') as tmpfile:
                    with open(fname, 'rb') as fileobj:
                        tmpfile.write(fileobj.read())
                        insert_request = client.videos().insert(
                            part=','.join(body.keys()),
                            body=body,
                            media_body=MediaFileUpload(tmpfile.name, chunksize=-1, resumable=True)
                        )
                        insert_request.execute()
            else:
                messages.success(request, "Under 2.5 megabytes, uploading from memory")
                storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
                credentials = storage.get()
                client = build('youtube', 'v3', credentials=credentials)

                body = {
                    'snippet': {
                        'title': 'Upload Youtube Video',
                        'description': 'Video Description',
                        'tags': 'django,howto,video,api',
                        'categoryId': '27'
                    },
                    'status': {
                        'privacyStatus': 'unlisted'
                    }
                }

                with tempfile.NamedTemporaryFile('wb', suffix='yt-django') as tmpfile:
                    tmpfile.write(request.FILES['video'].read())
                    insert_request = client.videos().insert(
                        part=','.join(body.keys()),
                        body=body,
                        media_body=MediaFileUpload(tmpfile.name, chunksize=-1, resumable=True)
                    )
                    insert_request.execute()

                return HttpResponse('It worked!')
    else:
        form = YouTubeForm()
    return render(request, 'upload/home.html', {'form': form})


flow = OAuth2WebServerFlow(
    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
    scope='https://www.googleapis.com/auth/youtube',
    redirect_uri='http://127.0.0.1:8000/oauth2callback/')


class AuthorizeView(View):

    def get(self, request, *args, **kwargs):
        storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
        credential = storage.get()
        if credential is None or credential.invalid == True:
            flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
            authorize_url = flow.step1_get_authorize_url()
            return redirect(authorize_url)
        return redirect('/')


class Oauth2CallbackView(View):

    def get(self, request, *args, **kwargs):
        if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET.get('state').encode(), request.user):
            return HttpResponseBadRequest()
        credential = flow.step2_exchange(request.GET)
        storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
        storage.put(credential)
        return redirect('/')
