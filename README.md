# GitHub Archive Cassandra Application

This project uses Python and Apache Cassandra to store GitHub Archive repository data.

## Features
- Load up to 1,000 repository records from JSON
- Create repository
- Read repository
- Update repository
- Delete repository
- Show top watched repositories
- Search repository names
- Show database statistics

## Requirements
- Python 3
- Apache Cassandra running locally on port 9042
- Cassandra Python driver
- Sample_Repos.json

## Install dependency
```bash
python3 -m pip install --user cassandra-driver
```

## Run
Keep all project files in the same folder, then run:

```bash
python3 cassandra_app.py
```

Use option 1 first to load the JSON data into Cassandra.

## Cassandra structure
Keyspace: `github_archive`

Table: `repositories`

Columns:
- `repo_name` text PRIMARY KEY
- `watch_count` int
