FROM python:3.13

WORKDIR /site
COPY . /site

EXPOSE 8080

# Свой сервер с no-cache заголовками (см. serve.py), чтобы браузер не показывал старые файлы.
CMD ["python", "serve.py"]
