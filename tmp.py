from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "00000000")
)

with driver.session(database="system") as session:
    result = session.run("SHOW DATABASES")

    for record in result:
        print({
            "name": record["name"],
            "currentStatus": record["currentStatus"],
            "default": record["default"],
        })