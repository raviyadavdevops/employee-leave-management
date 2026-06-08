"""User service client for inter-service communication."""

import os
import httpx
from typing import List
from uuid import UUID

from shared.common.logging import get_logger, get_correlation_id
from shared.common.exceptions import BadRequestException

logger = get_logger(__name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


class UserServiceClient:
    """HTTP client for user service."""
    
    def __init__(self):
        self.base_url = USER_SERVICE_URL
        self.timeout = 10.0
    
    async def get_team_members(self, manager_id: UUID, token: str) -> List[UUID]:
        """
        Get list of employee IDs reporting to the manager.
        
        Args:
            manager_id: Manager's user ID
            token: JWT access token for authentication
        
        Returns:
            List of employee UUIDs
        """
        url = f"{self.base_url}/api/v1/employees/team/members"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": get_correlation_id() or ""
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                # Extract employee IDs from response
                team_members = [UUID(emp["id"]) for emp in data]
                
                logger.info(f"Fetched {len(team_members)} team members for manager {manager_id}")
                return team_members
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling user service: {e.response.status_code}")
            raise BadRequestException(detail="Failed to fetch team members")
        except httpx.RequestError as e:
            logger.error(f"Request error calling user service: {str(e)}")
            raise BadRequestException(detail="User service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error calling user service: {str(e)}")
            raise BadRequestException(detail="Failed to communicate with user service")
    
    async def get_employee_manager(self, employee_id: UUID, token: str) -> UUID:
        """
        Get employee's manager ID.
        
        Args:
            employee_id: Employee's user ID
            token: JWT access token
        
        Returns:
            Manager's UUID
        """
        url = f"{self.base_url}/api/v1/employees/{employee_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": get_correlation_id() or ""
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                manager_id = data.get("manager_id")
                
                if not manager_id:
                    raise BadRequestException(detail=f"Employee {employee_id} has no manager assigned")
                
                return UUID(manager_id)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise BadRequestException(detail=f"Employee {employee_id} not found")
            logger.error(f"HTTP error calling user service: {e.response.status_code}")
            raise BadRequestException(detail="Failed to fetch employee details")
        except httpx.RequestError as e:
            logger.error(f"Request error calling user service: {str(e)}")
            raise BadRequestException(detail="User service unavailable")


# Global client instance
user_service_client = UserServiceClient()
