import os
import sys
from huggingface_hub import snapshot_download


def download_model(model_id: str) -> None:
    print(f"Скачивание файлов {model_id}...", flush=True)
    path = snapshot_download(repo_id=model_id, resume_download=True)
    print(f"Готово: {model_id} -> {path}", flush=True)


def main() -> None:
    base = os.environ.get(
        "CONTENT_MODEL_BASE",
        "weeqeen/rubert-base-cased-finetuned-moderation",
    )
    tiny = os.environ.get(
        "CONTENT_MODEL_TINY",
        "weeqeen/rubert-tiny2-moderation",
    )
    hf_home = os.environ.get("HF_HOME", "/var/cache/huggingface")
    os.makedirs(hf_home, exist_ok=True)
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        print("HF_TOKEN задан — загрузка с авторизацией", flush=True)
    else:
        print(
            "HF_TOKEN не задан (нормально). При лимитах Hub задайте токен: "
            "https://huggingface.co/settings/tokens",
            flush=True,
        )
    print(f"HF_HOME={hf_home}", flush=True)

    for model_id in (base, tiny):
        try:
            download_model(model_id)
        except Exception as exc:
            print(f"Ошибка загрузки {model_id}: {exc}", file=sys.stderr, flush=True)
            raise

    print("Модели модерации загружены.", flush=True)


if __name__ == "__main__":
    main()
