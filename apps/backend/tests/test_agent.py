import unittest

from apps.backend.agent.graph import app


class TestAgent(unittest.TestCase):
    """Test cases for the agent."""

    def test_create_project_flow(self):
        """Test the full flow for creating a project."""
        # Define the input for the graph
        inputs = {"input": "create project with key 'TEST' and name 'Test Project'"}

        # Invoke the graph
        result = app.invoke(inputs)

        # Assert the final response
        self.assertEqual(result["response"], "Successfully created 1 entities.")
        self.assertEqual(len(result["extracted_entities"]), 1)
        self.assertEqual(len(result["validated_entities"]), 1)
        self.assertEqual(len(result["upsert_results"]), 1)
        patch = result["upsert_results"][0]
        self.assertEqual(patch["op"], "AddNode")
        self.assertEqual(patch["node"]["label"], "Project")
        self.assertEqual(patch["node"]["key"], "TEST")
        self.assertEqual(patch["node"]["props"]["name"], "Test Project")
