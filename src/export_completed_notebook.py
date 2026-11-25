"""Execute the maintained notebook from a fresh kernel and export both formats."""

import argparse
import sys
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from src.config import ROOT


def export(output):
    source = ROOT / "notebooks/Completed_Analysis.ipynb"
    if (output / source.name).resolve() == source:
        raise ValueError("Choose an output directory outside the maintained source notebook.")
    notebook = nbformat.read(source, as_version=4)
    notebook.metadata.pop("widgets", None)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv[0] = sys.executable
    NotebookClient(notebook, km=manager, timeout=240,
                   resources={"metadata": {"path": str(ROOT)}}).execute(cleanup_kc=True)
    nbformat.validate(notebook)
    output.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output / source.name)
    html, _ = HTMLExporter().from_notebook_node(notebook, resources={"metadata": {"name": "Completed Analysis"}})
    (output / "Completed_Analysis.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output directory for the executed notebook and HTML")
    export(parser.parse_args().output.resolve())
