import nbformat as nb
from nbclient import NotebookClient

from src.config import ROOT


def build_notebook():
    md = nb.v4.new_markdown_cell
    code = nb.v4.new_code_cell
    notebook = nb.v4.new_notebook(cells=[
        md("# Changes in Global Energy\n\nRun the data pipeline first to create the local SQL exports. "
           "This notebook re-runs the analysis and figure scripts with their exported inputs."),
        code("""import sys
from pathlib import Path

project = Path.cwd().resolve()
if project.name == "notebooks":
    project = project.parent
sys.path.insert(0, str(project))

import pandas as pd
from IPython.display import display, Image
from src.analyze_data import analyze
from src.config import FIGURES, RESULTS
from src.make_figures import make_figures"""),
        md("## Source validation and database\n\nCounts distinguish missing cells from recorded zeros."),
        code("""import json

for filename in ("raw_profile.json", "database_run.json"):
    display(json.loads((RESULTS / filename).read_text(encoding="utf-8")))
display(pd.read_csv(RESULTS / "data_quality_summary.csv"))"""),
        md("## Common coverage and descriptive trend\n\nThe OLS response is annual world renewable share. "
           "Residual serial dependence is evaluated descriptively."),
        code("""analyze()
make_figures()
display(pd.read_csv(RESULTS / "descriptive_statistics.csv"))
display(pd.read_csv(RESULTS / "endpoints.csv"))
display(pd.read_csv(RESULTS / "model_statistics.csv"))"""),
        code("""for figure in sorted(FIGURES.glob("*.png")):
    display(Image(filename=str(figure), width=760))""")
    ], metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
    NotebookClient(notebook, timeout=180, resources={"metadata": {"path": str(ROOT)}}).execute()
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            cell.metadata.pop("execution", None)
    nb.write(notebook, ROOT / "notebooks/analysis.ipynb")


if __name__ == "__main__":
    build_notebook()
