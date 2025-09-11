"""
Extraction tools for Project, Epic, Issue, and User entities.
These tools use LLM to extract structured data from natural language.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4
from models.domain import Project, User, Epic, Issue
from models.graph import Patch, NodeSpec, EdgeSpec
from services.llm_service import get_llm_service, ModelConfig
from tools.tool_registry import AgentTool


class ProjectExtractionTool(AgentTool):
    """Tool for extracting Project entities from natural language"""
    
    def __init__(self):
        self.name = "extract_project"
        self.description = "Extract Project entities from natural language descriptions"
        self.llm_service = get_llm_service()
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract project information from text"""
        try:
            text = input_data.get("text", "")
            if not text:
                return {"success": False, "error": "No text provided"}
            
            # Generate project data using LLM
            project_data = await self.llm_service.generate_structured_output(
                prompt_template=self._get_extraction_prompt(),
                output_schema=Project,
                context={"text": text},
                model_config=ModelConfig(temperature=0.1)
            )
            
            # Create patches for the project
            patches = self._create_project_patches(project_data)
            
            return {
                "success": True,
                "entities": [project_data.dict()],
                "patches": [patch.dict() for patch in patches],
                "count": 1
            }
            
        except Exception as e:
            self.logger.error(f"Project extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return "text" in input_data and isinstance(input_data["text"], str)
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Natural language description of the project"
                }
            },
            "required": ["text"]
        }
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt template for project extraction"""
        return """
        Extract project information from the following text:
        
        Text: "{text}"
        
        Extract the following information:
        - Project name (required)
        - Project description (optional)
        - Any other relevant project details
        
        If multiple projects are mentioned, extract the main/primary project.
        """
    
    def _create_project_patches(self, project: Project) -> List[Patch]:
        """Create patches for a project entity"""
        patches = []
        
        # Add project node
        project_patch = Patch(
            op="AddNode",
            node=NodeSpec(
                label="Project",
                key=project.key,
                props={
                    "name": project.nome,
                    "description": project.description or ""
                }
            ),
            reason=f"Extract project: {project.nome}"
        )
        patches.append(project_patch)
        
        return patches


class UserExtractionTool(AgentTool):
    """Tool for extracting User entities from natural language"""
    
    def __init__(self):
        self.name = "extract_user"
        self.description = "Extract User entities from natural language descriptions"
        self.llm_service = get_llm_service()
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from text"""
        try:
            text = input_data.get("text", "")
            if not text:
                return {"success": False, "error": "No text provided"}
            
            # Generate user data using LLM
            user_data = await self.llm_service.generate_structured_output(
                prompt_template=self._get_extraction_prompt(),
                output_schema=User,
                context={"text": text},
                model_config=ModelConfig(temperature=0.1)
            )
            
            # Create patches for the user
            patches = self._create_user_patches(user_data)
            
            return {
                "success": True,
                "entities": [user_data.dict()],
                "patches": [patch.dict() for patch in patches],
                "count": 1
            }
            
        except Exception as e:
            self.logger.error(f"User extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return "text" in input_data and isinstance(input_data["text"], str)
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Natural language description mentioning users"
                }
            },
            "required": ["text"]
        }
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt template for user extraction"""
        return """
        Extract user information from the following text:
        
        Text: "{text}"
        
        Extract the following information:
        - User ID (required) - blank if not provided
        - User name (required)
        - Any other relevant user details
        
        If multiple users are mentioned, extract all of them.
        """
    
    def _create_user_patches(self, user: User) -> List[Patch]:
        """Create patches for a user entity"""
        patches = []
        
        # Add user node
        user_patch = Patch(
            op="AddNode",
            node=NodeSpec(
                label="User",
                key=user.user_id,
                props={
                    "name": user.name
                }
            ),
            reason=f"Extract user: {user.name}"
        )
        patches.append(user_patch)
        
        return patches


class EpicExtractionTool(AgentTool):
    """Tool for extracting Epic entities from natural language"""
    
    def __init__(self):
        self.name = "extract_epic"
        self.description = "Extract Epic entities from natural language descriptions"
        self.llm_service = get_llm_service()
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract epic information from text"""
        try:
            text = input_data.get("text", "")
            project_id = input_data.get("project_id", "")
            
            if not text:
                return {"success": False, "error": "No text provided"}
            
            if not project_id:
                return {"success": False, "error": "Project key required for epic extraction"}
            
            # Generate epic data using LLM
            epic_data = await self.llm_service.generate_structured_output(
                prompt_template=self._get_extraction_prompt(),
                output_schema=Epic,
                context={"text": text, "project_id": project_id},
                model_config=ModelConfig(temperature=0.1)
            )
            
            # Create patches for the epic
            patches = self._create_epic_patches(epic_.dict(), project_id)
            
            return {
                "success": True,
                "entities": [epic_data.dict()],
                "patches": [patch.dict() for patch in patches],
                "count": 1
            }
            
        except Exception as e:
            self.logger.error(f"Epic extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return (
            "text" in input_data and isinstance(input_data["text"], str) and
            "project_id" in input_data and isinstance(input_data["project_id"], str)
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Natural language description of the epic"
                },
                "project_id": {
                    "type": "string",
                    "description": "Key of the project this epic belongs to"
                }
            },
            "required": ["text", "project_id"]
        }
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt template for epic extraction"""
        return """
        Extract epic information from the following text:
        
        Text: "{text}"
        Project ID: "{project_id}"
        
        Extract the following information:
        - Epic title (required)
        - Epic description (optional)
        - Any other relevant epic details
        
        If multiple epics are mentioned, extract all of them.
        """
    
    def _create_epic_patches(self, epic: Epic, project_id: str) -> List[Patch]:
        """Create patches for an epic entity"""
        patches = []
        
        # Add epic node
        epic_patch = Patch(
            op="AddNode",
            node=NodeSpec(
                label="Epic",
                key=epic.id,
                props={
                    "title": epic.title,
                    "project_id": str(epic.project_id),
                }
            ),
            reason=f"Extract epic: {epic.title}"
        )
        patches.append(epic_patch)
        
        # Add relationship to project
        relationship_patch = Patch(
            op="AddEdge",
            edge=EdgeSpec(
                src_label="Project",
                src_key=project_id,
                rel="HAS_EPIC",
                dst_label="Epic",
                dst_key=epic.id,
                props={}
            ),
            reason=f"Link epic {epic.title} to project {project_id}"
        )
        patches.append(relationship_patch)
        
        return patches


class IssueExtractionTool(AgentTool):
    """Tool for extracting Issue entities from natural language"""
    
    def __init__(self):
        self.name = "extract_issue"
        self.description = "Extract Issue entities from natural language descriptions"
        self.llm_service = get_llm_service()
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract issue information from text"""
        try:
            text = input_data.get("text", "")
            epic_id = input_data.get("epic_id", "")
            
            if not text:
                return {"success": False, "error": "No text provided"}
            
            if not epic_id:
                return {"success": False, "error": "Epic key required for issue extraction"}
            
            # Generate issue data using LLM
            issue_data = await self.llm_service.generate_structured_output(
                prompt_template=self._get_extraction_prompt(),
                output_schema=Issue,
                context={"text": text, "epic_id": epic_id},
                model_config=ModelConfig(temperature=0.1)
            )
            
            # Create patches for the issue
            patches = self._create_issue_patches(issue_data, epic_id)
            
            return {
                "success": True,
                "entities": [issue_data.dict()],
                "patches": [patch.dict() for patch in patches],
                "count": 1
            }
            
        except Exception as e:
            self.logger.error(f"Issue extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return (
            "text" in input_data and isinstance(input_data["text"], str) and
            "epic_id" in input_data and isinstance(input_data["epic_id"], str)
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Natural language description of the issue"
                },
                "epic_id": {
                    "type": "string",
                    "description": "Key of the epic this issue belongs to"
                }
            },
            "required": ["text", "epic_id"]
        }
    
    def _get_extraction_prompt(self) -> str:
        """Get the prompt template for issue extraction"""
        return """
        Extract issue information from the following text:
        
        Text: "{text}"
        Epic ID: "{epic_id}"
        
        Extract the following information:
        - Issue title (required)
        - Issue status (open, in_progress, done, blocked) - default to "open"
        - Issue description (optional)
        - Any other relevant issue details
        
        If multiple issues are mentioned, extract all of them.
        """
    
    def _create_issue_patches(self, issue: Issue, epic_id: str) -> List[Patch]:
        """Create patches for an issue entity"""
        patches = []
        
        # Add issue node
        issue_patch = Patch(
            op="AddNode",
            node=NodeSpec(
                label="Issue",
                key=issue.id,
                props={
                    "title": issue.title,
                    "status": issue.status,
                    "epic_id": epic_id,
                }
            ),
            reason=f"Extract issue: {issue.title}"
        )
        patches.append(issue_patch)
        
        # Add relationship to epic
        relationship_patch = Patch(
            op="AddEdge",
            edge=EdgeSpec(
                src_label="Epic",
                src_key=epic_id,
                rel="HAS_ISSUE",
                dst_label="Issue",
                dst_key=issue.id,
                props={}
            ),
            reason=f"Link issue {issue.title} to epic {epic_id}"
        )
        patches.append(relationship_patch)
        
        return patches


# Tool factory functions for plugin registration
def create_project_extraction_tool() -> ProjectExtractionTool:
    """Factory function for project extraction tool"""
    return ProjectExtractionTool()

def create_user_extraction_tool() -> UserExtractionTool:
    """Factory function for user extraction tool"""
    return UserExtractionTool()

def create_epic_extraction_tool() -> EpicExtractionTool:
    """Factory function for epic extraction tool"""
    return EpicExtractionTool()

def create_issue_extraction_tool() -> IssueExtractionTool:
    """Factory function for issue extraction tool"""
    return IssueExtractionTool()
