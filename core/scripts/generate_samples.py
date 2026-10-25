import argparse
import sys
from pathlib import Path

# The synthetic contracts live with the test fixtures, so tests and demo samples never diverge
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.fixtures.contract_factory import ContractPdfFactory  # noqa: E402
from tests.fixtures.sample_documents import SAMPLE_DOCUMENTS  # noqa: E402


class SampleGenerator:
    """Writes the synthetic sample documents as PDF files, to try the API or the demo."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def generate(self) -> list[Path]:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        factory = ContractPdfFactory()
        paths = []
        for build_contract in SAMPLE_DOCUMENTS:
            contract = build_contract()
            path = self._output_dir / contract.filename
            path.write_bytes(factory.build(contract))
            paths.append(path)
        return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Belgian contract PDFs")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "samples")
    for generated in SampleGenerator(parser.parse_args().output).generate():
        print(f"Written {generated}")
