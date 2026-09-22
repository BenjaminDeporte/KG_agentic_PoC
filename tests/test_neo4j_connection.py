"""Test Neo4j database connection using environment variables from AuraDB."""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


def test_neo4j_connection():
    """Test that we can connect to Neo4j Aura using .env credentials."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    assert uri is not None, "NEO4J_URI not set in environment"
    assert username is not None, "NEO4J_USERNAME not set in environment"
    assert password is not None, "NEO4J_PASSWORD not set in environment"

    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            assert record is not None, "No record returned from Neo4j"
            assert record["test"] == 1, "Unexpected result from Neo4j"
    finally:
        driver.close()


def test_neo4j_cypher_query():
    """Test a simple Cypher query to verify the database is accessible."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            # Test a simple query that returns the Neo4j version
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            records = list(result)
            assert len(records) > 0, "No components returned from Neo4j"
            print(f"✅ Neo4j version info: {records[0]}")
    finally:
        driver.close()
