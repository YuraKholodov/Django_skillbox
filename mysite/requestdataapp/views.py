from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def process_get_view(request: HttpRequest) -> HttpResponse:
    a = request.GET.get('a', '')
    b = request.GET.get('b', '')
    result = a + b
    context = {
        'a': a,
        'b': b,
        'result': result,
    }
    return render(request, 'requestdataapp/request_query_params.html', context=context)


def user_form(request: HttpRequest) -> HttpResponse:
    return render(request, 'requestdataapp/user_bio_form.html')


def handle_file_upload(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.FILES.get('myfile'):
        myfile = request.FILES['myfile']
        file_size = myfile.size
        file_name = myfile.name
        if file_size < 1048576:
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            print('saved file', filename)

        else:
            file_size = round(file_size / 1024 / 1024, 2)
            context = {
                'file_name': file_name,
                'file_size': file_size,
            }
            print(f'File {file_name} was not saved, size {file_size}:MB larger than 1 mb!!!')
            return render(request, 'requestdataapp/error_download_file.html', context=context)
    return render(request, 'requestdataapp/file_upload.html')
