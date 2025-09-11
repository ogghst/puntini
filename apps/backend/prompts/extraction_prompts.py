"""
Prompt templates for entity extraction and validation.
Provides consistent, high-quality prompts for LLM interactions.
"""

from typing import Dict, Any


class ExtractionPrompts:
    """Collection of prompt templates for entity extraction"""
    
    @staticmethod
    def get_planning_prompt() -> str:
        """Get prompt for planning phase"""
        return """
        You are an AI assistant that helps create and manage business improvement projects using Agile and PMI methodologies.
        
        Your task is to analyze the user's request and create a structured execution plan.
        
        User Request: "{user_goal}"
        
        Based on the request, create a step-by-step execution plan that will:
        1. Extract relevant entities (Project, Epic, Issue, User) from the text
        2. Validate the extracted data
        3. Apply the changes to the knowledge graph
        4. Provide a comprehensive response
        
        Consider the following:
        - What entities need to be created or updated?
        - What relationships need to be established?
        - What validation steps are required?
        - What tools will be needed for each step?
        
        Respond with a JSON array of step descriptions.
        """
    
    @staticmethod
    def get_project_extraction_prompt() -> str:
        """Get prompt for project extraction"""
        return """
        Extract project information from the following text:
        
        Text: "{text}"
        
        Extract the following information:
        - Project name (required) - create a unique key based on the name
        - Project description (optional)
        - Any other relevant project details
        
        If multiple projects are mentioned, extract the main/primary project.
        
        Generate a unique key for the project using the format: PROJ-{abbreviation}
        For example, "Customer Portal Project" becomes "PROJ-CPP"
        """
    
    @staticmethod
    def get_user_extraction_prompt() -> str:
        """Get prompt for user extraction"""
        return """
        Extract user information from the following text:
        
        Text: "{text}"
        
        Extract the following information:
        - User ID (required) - blank if not provided
        - User name (required)
        - Any other relevant user details
        
        If multiple users are mentioned, extract all of them.
        
        """
    
    @staticmethod
    def get_epic_extraction_prompt() -> str:
        """Get prompt for epic extraction"""
        return """
        Extract epic information from the following text:
        
        Text: "{text}"
        Project Key: "{project_key}"
        
        Extract the following information:
        - Epic title (required)
        - Epic description (optional)
        - Any other relevant epic details
        
        If multiple epics are mentioned, extract all of them.

        """
    
    @staticmethod
    def get_issue_extraction_prompt() -> str:
        """Get prompt for issue extraction"""
        return """
        Extract issue information from the following text:
        
        Text: "{text}"
        Epic Key: "{epic_key}"
        
        Extract the following information:
        - Issue title (required)
        - Issue status (open, in_progress, done, blocked) - default to "open"
        - Issue description (optional)
        - Any other relevant issue details
        
        If multiple issues are mentioned, extract all of them.

        """
    
    @staticmethod
    def get_validation_prompt() -> str:
        """Get prompt for validation phase"""
        return """
        You are validating extracted entities for a project management system.
        
        Extracted Data: {extracted_data}
        
        Please validate the following:
        1. All required fields are present
        2. Data types are correct
        3. Relationships are properly defined
        4. Business rules are followed
        
        If validation fails, provide specific error messages and suggestions for correction.
        If validation passes, confirm the data is ready for persistence.
        """
    
    @staticmethod
    def get_answer_generation_prompt() -> str:
        """Get prompt for answer generation"""
        return """
        You are an AI assistant that has successfully processed a user request for project management.
        
        User Request: "{user_goal}"
        Processing Results: {processing_results}
        
        Provide a comprehensive response that includes:
        1. Summary of what was accomplished
        2. Entities created or updated
        3. Relationships established
        4. Any warnings or issues encountered
        5. Next steps or recommendations
        
        Be clear, concise, and helpful. Use a professional but friendly tone.
        """


class ValidationPrompts:
    """Collection of prompt templates for validation"""
    
    @staticmethod
    def get_schema_validation_prompt() -> str:
        """Get prompt for schema validation"""
        return """
        Validate the following data against the required schema:
        
        Data: {data}
        Schema: {schema}
        
        Check for:
        - Required fields presence
        - Correct data types
        - Valid enum values
        - Proper format compliance
        
        Return validation results with specific error messages if any issues are found.
        """
    
    @staticmethod
    def get_domain_validation_prompt() -> str:
        """Get prompt for domain validation"""
        return """
        Validate the following data against domain business rules:
        
        Data: {data}
        Domain Rules: {domain_rules}
        
        Check for:
        - Business logic compliance
        - Data consistency
        - Relationship validity
        - Constraint satisfaction
        
        Return validation results with specific error messages if any issues are found.
        """
    
    @staticmethod
    def get_graph_constraint_prompt() -> str:
        """Get prompt for graph constraint validation"""
        return """
        Validate the following graph operations against constraints:
        
        Operations: {operations}
        Constraints: {constraints}
        
        Check for:
        - Uniqueness constraints
        - Referential integrity
        - Relationship consistency
        - Graph structure validity
        
        Return validation results with specific error messages if any issues are found.
        """


class ErrorHandlingPrompts:
    """Collection of prompt templates for error handling"""
    
    @staticmethod
    def get_retry_prompt() -> str:
        """Get prompt for retry scenarios"""
        return """
        The previous attempt failed with the following error:
        
        Error: {error}
        Context: {context}
        
        Please analyze the error and provide a corrected approach:
        1. What went wrong?
        2. How can it be fixed?
        3. What changes are needed?
        
        Provide specific, actionable corrections.
        """
    
    @staticmethod
    def get_escalation_prompt() -> str:
        """Get prompt for escalation scenarios"""
        return """
        The system has encountered a complex issue that requires escalation:
        
        Issue: {issue}
        Context: {context}
        Attempts Made: {attempts}
        
        Please provide:
        1. A clear description of the issue
        2. What has been tried so far
        3. Why escalation is necessary
        4. Recommended next steps
        
        This will help human operators understand and resolve the issue.
        """
