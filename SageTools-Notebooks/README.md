# SageTools Classroom Notebooks

A sequenced set of Jupyter notebooks that teach the Sage Beehive data workflow,
built on the official `sage_data_client` API and the
[SageTools](https://github.com/mpapka/SageTools) helper package. The notebooks
take a student from first contact with the sensor network through an end to end
regional study they can extend into a project.

Every notebook is written in a verbose classroom style: full domain background,
every query parameter documented, output walkthroughs, troubleshooting notes, and
scaffolded exercises with hints. Code is complete, runnable, and uses camelCase
identifiers throughout.

## The sequence

| Notebook | Topic | Runs offline |
| --- | --- | --- |
| `00_setup_and_intro` | What Sage is, install, first live query, reading a record | no, one live probe |
| `01_discovery_nodes_and_metrics` | Find live nodes, list metrics, find lifetimes | no |
| `02_querying_beehive_data` | Time and filter grammar, the returned DataFrame, CSV export | no |
| `03_scaling_up_batch_extraction` | Chunked extraction, checkpoints, resume | yes as written, live pull is opt-in |
| `04_analysis_and_statistics` | Statistics, unit conversion, chunked reads, sensor audit, data-quality filtering | yes |
| `05_visualization` | Time series, rolling average, honest gaps, comparison, a node map | yes |
| `06_capstone_regional_study` | Full pipeline, node maps, data-quality filtering, project prompts | yes, live query optional |
| `07_capstone_polar_vortex` | Detective capstone: detect a polar vortex in the data and match it to the news | yes |
| `supplement_folium_maps` | A from-scratch primer on folium, building up to the node maps | yes |

Notebooks `04`, `05`, and `06` run with no network. Each carries an offline safe
synthetic data generator (`makeSyntheticBeehive`) that produces records in the
exact schema the Beehive returns, so every SageTools helper works on it unchanged.
When connectivity is available, swap the synthetic frame for a real query and the
rest of the notebook is identical. The capstone tries a live query first and falls
back to synthetic automatically, printing which path it used.

The `supplement_folium_maps` notebook is optional and stands to the side of the
numbered sequence. Read it before 05 and 06 if folium is new to you; it teaches the
mapping library from the ground up and ends by building the exact `makeNodeMap`
function the capstone uses.

## Installing the SageTools helper (optional)

Every lab also shows the underlying `sage_data_client` call, so SageTools is a
convenience, not a requirement. To enable the helpers, run this in a notebook
cell (notebook `00` has this ready to uncomment):

```python
%pip install --quiet "git+https://github.com/mpapka/SageTools.git"
```

Use the `%pip` magic, not a shell `!pip`: it installs into the exact environment
backing the running kernel, so the package is importable in the next cell with no
restart. Avoid `pip install -e` (editable) in a notebook. An editable install
reports success but is not importable until the kernel restarts, because Python
only reads the editable path entry at interpreter startup.

## Setup

Any Jupyter environment with Python 3.9 or newer works. On a managed classroom
JupyterHub the dependencies are usually preinstalled. Otherwise:

```bash
pip install -r requirements.txt
jupyter lab
```

Open the notebooks in order. Each ends with an exercises block. The capstone ends
with four project prompts and a description of what a strong submission looks
like, which doubles as a grading rubric.

Every notebook ends with a Further reading section linking the relevant Sage
resources and technology documentation (pandas, matplotlib, folium, robust
statistics). Data cleaning (a physical plausibility band plus a per-node MAD
outlier filter) appears in notebook 04 and again in the capstone, and notebooks 05
and 06 draw folium maps, installing folium on demand if the kernel lacks it.

## Design choices worth knowing

- **Concept first, helper second.** Every lab shows the direct `sage_data_client`
  call, then points to the SageTools wrapper that packages it. Helper imports are
  guarded, so the notebooks run whether or not SageTools is installed.
- **Two libraries, kept distinct.** `sage_data_client` is the official first party
  client from `sagecontinuum/sage-data-client`. `SageTools` (`mpapka/SageTools`)
  is the convenience layer built on top of it. Notebook `00` explains the split.
- **Facts separated from interpretation.** The analysis and capstone notebooks ask
  students to state measured facts and their readings of those facts in separate
  sentences, and the rubric rewards it.
- **Camera tools are intentionally excluded.** The SageTools camera features need
  SSH tunnels into live nodes, which is not classroom portable. This set covers
  the Beehive data path, which is publicly queryable.

## Maps and data cleaning (notebook 06)

The capstone draws the nodes on an interactive folium map (colored by value, so a
miscalibrated node stands out) and includes a data-quality section with two
filters: a physical plausibility band and a per-node MAD outlier check that
removes values like 0, -50, and -200 while keeping real daily extremes. Maps need
`folium` (`pip install folium`); if it is absent the notebook still runs and skips
the maps. Map tiles load from OpenStreetMap in the browser, so they need internet
to display, though the markers are computed locally and the notebook executes
offline.

The second capstone (`07`) is a data-detective exercise: it teaches how to
navigate an unfamiliar dataset, detects a sustained extreme-cold spell with an
explicit rule, and corroborates the dates against documented Chicago polar vortex
events from the National Weather Service and news reporting. It runs offline on
synthetic winter data with a real cold-snap signature embedded.

## Connectivity note

Live queries hit `https://data.sagecontinuum.org`. If a lab that needs the network
fails, confirm the environment can reach that host; on a locked down campus
network it may need to be allowed through. The offline notebooks (`04`, `05`, `06`)
never need it. You can look up any node's physical deployment at
`https://portal.sagecontinuum.org/nodes/{VSN}`.
