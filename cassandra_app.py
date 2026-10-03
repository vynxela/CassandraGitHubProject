# Name: Daniel Baez-Perez
# Date: October 2, 2026
# Assignment: 3.3 Group Project - Cassandra Integration
# Objective: Use Python and Cassandra to store GitHub Archive data and perform CRUD operations.

import json
from pathlib import Path
from cassandra.cluster import Cluster

DATA_FILE = Path(__file__).with_name("Sample_Repos.json")
KEYSPACE = "github_archive"
TABLE = "repositories"

def connect():
    cluster = Cluster(["127.0.0.1"], port=9042)
    session = cluster.connect()

    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS github_archive
        WITH replication = {'class':'SimpleStrategy','replication_factor':1}
    """)
    session.set_keyspace(KEYSPACE)

    session.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            repo_name text PRIMARY KEY,
            watch_count int
        )
    """)
    return cluster, session

def menu():
    print("\n======================================")
    print(" GitHub Archive Cassandra Application")
    print("======================================")
    print("1. Load GitHub repository data")
    print("2. Create repository")
    print("3. Read repository")
    print("4. Update repository")
    print("5. Delete repository")
    print("6. Show most watched repositories")
    print("7. Search repositories")
    print("8. Show database statistics")
    print("9. Exit")

def load_data(session):
    print("\nLoading GitHub repository data...")
    records = []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
            if len(records) >= 1000:
                break

    session.execute(f"TRUNCATE {TABLE}")
    stmt = session.prepare(
        f"INSERT INTO {TABLE} (repo_name, watch_count) VALUES (?, ?)"
    )

    loaded = 0
    for item in records:
        name = item.get("repo_name")
        if not name:
            continue
        try:
            watches = int(item.get("watch_count", 0))
        except (TypeError, ValueError):
            watches = 0
        session.execute(stmt, (name, watches))
        loaded += 1

    print(f"{loaded} repositories loaded into Cassandra.")

def create_repo(session):
    print("\n--- Create Repository ---")
    name = input("Enter repository name: ").strip()
    try:
        watches = int(input("Enter watch count: "))
    except ValueError:
        print("Watch count must be a number.")
        return

    row = session.execute(
        f"SELECT repo_name FROM {TABLE} WHERE repo_name=%s", (name,)
    ).one()
    if row:
        print("Repository already exists.")
        return

    session.execute(
        f"INSERT INTO {TABLE} (repo_name, watch_count) VALUES (%s, %s)",
        (name, watches),
    )
    print("Repository created successfully.")

def read_repo(session):
    print("\n--- Read Repository ---")
    name = input("Enter repository name: ").strip()
    row = session.execute(
        f"SELECT repo_name, watch_count FROM {TABLE} WHERE repo_name=%s",
        (name,),
    ).one()

    if row is None:
        print("Repository not found.")
    else:
        print("\nRepository Information")
        print("----------------------")
        print(f"Name: {row.repo_name}")
        print(f"Watch Count: {row.watch_count}")

def update_repo(session):
    print("\n--- Update Repository ---")
    name = input("Enter repository name: ").strip()
    row = session.execute(
        f"SELECT repo_name FROM {TABLE} WHERE repo_name=%s", (name,)
    ).one()

    if row is None:
        print("Repository not found.")
        return

    try:
        watches = int(input("Enter new watch count: "))
    except ValueError:
        print("Watch count must be a number.")
        return

    session.execute(
        f"UPDATE {TABLE} SET watch_count=%s WHERE repo_name=%s",
        (watches, name),
    )
    print("Repository updated successfully.")

def delete_repo(session):
    print("\n--- Delete Repository ---")
    name = input("Enter repository name: ").strip()
    row = session.execute(
        f"SELECT repo_name FROM {TABLE} WHERE repo_name=%s", (name,)
    ).one()

    if row is None:
        print("Repository not found.")
        return

    session.execute(f"DELETE FROM {TABLE} WHERE repo_name=%s", (name,))
    print("Repository deleted successfully.")

def all_rows(session):
    return list(session.execute(
        f"SELECT repo_name, watch_count FROM {TABLE}"
    ))

def most_watched(session):
    rows = all_rows(session)
    rows.sort(key=lambda r: r.watch_count or 0, reverse=True)
    print("\n--- Top Watched Repositories ---")
    for i, row in enumerate(rows[:10], 1):
        print(f"{i}. {row.repo_name} - {row.watch_count} watches")

def search_repos(session):
    term = input("\nEnter search term: ").strip().lower()
    rows = [r for r in all_rows(session) if term in r.repo_name.lower()]
    rows.sort(key=lambda r: r.watch_count or 0, reverse=True)

    print("\n--- Search Results ---")
    if not rows:
        print("No matching repositories found.")
        return
    for row in rows[:10]:
        print(f"{row.repo_name} - {row.watch_count} watches")

def statistics(session):
    rows = all_rows(session)
    print("\n--- Database Statistics ---")
    print(f"Repositories stored: {len(rows)}")
    if not rows:
        return

    top = max(rows, key=lambda r: r.watch_count or 0)
    total = sum(r.watch_count or 0 for r in rows)
    print(f"Most watched repository: {top.repo_name}")
    print(f"Watch count: {top.watch_count}")
    print(f"Average watch count: {total / len(rows):.2f}")

def main():
    cluster = None
    session = None
    try:
        cluster, session = connect()
        print("Connected to Cassandra successfully.")

        while True:
            menu()
            choice = input("\nSelect an option: ").strip()

            if choice == "1":
                load_data(session)
            elif choice == "2":
                create_repo(session)
            elif choice == "3":
                read_repo(session)
            elif choice == "4":
                update_repo(session)
            elif choice == "5":
                delete_repo(session)
            elif choice == "6":
                most_watched(session)
            elif choice == "7":
                search_repos(session)
            elif choice == "8":
                statistics(session)
            elif choice == "9":
                print("\nApplication closed.")
                break
            else:
                print("Choose a number from 1 through 9.")

    except Exception as e:
        print(f"Application error: {e}")
    finally:
        if session:
            session.shutdown()
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    main()
