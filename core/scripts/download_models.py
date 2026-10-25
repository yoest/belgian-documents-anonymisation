import argparse
import json
from pathlib import Path

from docling.utils.model_downloader import download_models
from gliner import GLiNER


class ModelDownloader:
    """Downloads every model at image build time so the API can run fully offline."""

    def __init__(self, config_path: Path) -> None:
        self._config = json.loads(config_path.read_text(encoding="utf-8"))

    def download(self) -> None:
        self._download_docling()
        self._download_ner()

    def _download_docling(self) -> None:
        extraction = self._config["extraction"]
        # Only the layout and table models: no OCR (text-based PDFs), no picture/formula enrichment
        download_models(
            output_dir=Path(extraction["models_dir"]),
            with_layout=True,
            with_tableformer=extraction["table_structure"],
            with_code_formula=False,
            with_picture_classifier=False,
            with_rapidocr=False,
        )
        print(f"Downloaded Docling models to {extraction['models_dir']}")

    def _download_ner(self) -> None:
        ner_config = self._config["detection"]["ner"]
        if not ner_config["enabled"]:
            print("NER disabled, nothing to download")
            return
        # Loading once fills the Hugging Face cache (HF_HOME) with the model and its encoder/tokenizer
        model = GLiNER.from_pretrained(ner_config["model_name"])
        # Smoke test, so a broken model fails the build rather than the first request
        model.predict_entities("Jan Peeters habite à Bruxelles.", ["person"], threshold=0.3)
        print(f"Downloaded {ner_config['model_name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download the Docling and NER models")
    parser.add_argument("--config", type=Path, required=True)
    ModelDownloader(parser.parse_args().config).download()
