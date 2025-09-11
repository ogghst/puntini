import pkg_resources
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from dataclasses import dataclass
import asyncio
import logging

# Tool Plugin Interface
class AgentTool(Protocol):
    """Protocol for agent tools"""
    name: str
    description: str
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given input"""
        ...
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input before execution"""
        ...
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        ...

@dataclass
class ToolRegistrationInfo:
    """Information about a registered tool"""
    tool_instance: AgentTool
    plugin_name: str
    version: str
    health_status: str = "healthy"
    last_used: Optional[str] = None
    error_count: int = 0

class ToolRegistry:
    """Plugin-based tool registry with dynamic discovery"""
    
    def __init__(self, entry_point_group: str = "project_agent.tools"):
        self.entry_point_group = entry_point_group
        self.registered_tools: Dict[str, ToolRegistrationInfo] = {}
        self.logger = logging.getLogger(__name__)
        self._discovery_enabled = True
    
    def discover_and_register_plugins(self):
        """Discover and register tools from entry points"""
        if not self._discovery_enabled:
            return
        
        for entry_point in pkg_resources.iter_entry_points(self.entry_point_group):
            try:
                tool_factory = entry_point.load()
                tool_instance = tool_factory()
                
                self.register_tool(
                    tool_instance=tool_instance,
                    plugin_name=entry_point.name,
                    version=entry_point.dist.version if entry_point.dist else "unknown"
                )
                
                self.logger.info(f"Registered tool: {entry_point.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load tool {entry_point.name}: {e}")
    
    def register_tool(self, tool_instance: AgentTool, plugin_name: str, version: str):
        """Register a tool instance"""
        registration_info = ToolRegistrationInfo(
            tool_instance=tool_instance,
            plugin_name=plugin_name,
            version=version
        )
        self.registered_tools[tool_instance.name] = registration_info
    
    def get_tool(self, tool_name: str) -> Optional[AgentTool]:
        """Get a tool by name with health check"""
        reg_info = self.registered_tools.get(tool_name)
        if not reg_info:
            return None
        
        if reg_info.health_status != "healthy":
            self.logger.warning(f"Tool {tool_name} is unhealthy: {reg_info.health_status}")
            return None
        
        return reg_info.tool_instance
    
    def get_available_tools(self) -> List[AgentTool]:
        """Get all healthy tools"""
        return [
            reg_info.tool_instance 
            for reg_info in self.registered_tools.values()
            if reg_info.health_status == "healthy"
        ]
    
    def health_check(self, tool_name: str) -> bool:
        """Check tool health and update status"""
        reg_info = self.registered_tools.get(tool_name)
        if not reg_info:
            return False
        
        try:
            # Attempt a lightweight health check
            reg_info.tool_instance.get_schema()  # Basic schema validation
            reg_info.health_status = "healthy"
            reg_info.error_count = 0
            return True
        except Exception as e:
            reg_info.error_count += 1
            if reg_info.error_count > 3:
                reg_info.health_status = "unhealthy"
            self.logger.error(f"Health check failed for {tool_name}: {e}")
            return False
