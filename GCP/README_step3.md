# Step 3: Spanner Graph schema and loader

Layout expected (unzip `rca_sim_data_csv.zip` here so `data/` sits next to the script; keep `ground_truth.json` alongside):

    spanner/ rca_graph.py  data/*.csv  ground_truth.json

```
pip install google-cloud-spanner
gcloud auth application-default login
export SPANNER_PROJECT=<project> SPANNER_INSTANCE=<instance> SPANNER_DATABASE=rca

python rca_graph.py check            # offline: headers, types, PKs, dangling references
python rca_graph.py create           # database + 56 tables, then the property graph
python rca_graph.py load             # idempotent (insert_or_update), ~28k rows
python rca_graph.py verify           # runs 5 GQL queries, compares with ground truth
```
Spanner Graph may need an Enterprise-edition instance. `schema_tables.sql`, `schema_graph.sql` and `queries.gql` are the same statements as plain files, so you can paste them into the console instead.

Not tested against a live Spanner here. If `create` fails on the graph statement, tables are already in place: fix `schema_graph.sql` and rerun, trying `--keep-edge-props` first.
