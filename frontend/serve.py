"""Статический сервер фронтенда без кэширования.

Обычный `python -m http.server` отдаёт файлы без запрета кэша, из-за чего браузер
показывает старые JS/CSS/HTML после пересборки. Здесь добавляем no-store заголовки,
чтобы изменения были видны без ручного хард-рефреша.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), NoCacheHandler).serve_forever()
