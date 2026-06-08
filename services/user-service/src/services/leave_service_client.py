"""Leave service client for inter-service communication."""

import os
import httpx
from typing import List
from uuid import UUID

from shared.common.logging import get_logger, get_correlation_id
from shared.common.exceptions import BadRequestException

logger = get_logger(__name__)

LEAVE_SERVICE_URL = os.getenv("LEAVE_SERVICE_URL", "http://localhost:8002")


class LeaveServiceClient:
    """HTTP client for leave service."""
    
    def __init__(self):
        self.base_url = LEAVE_SERVICE_URL
        self.timeout = 10.0
    
    async def allocate_balances(self, employee_id: UUID, hire_date: str, token: str) -> bool:
        """
        Allocate leave balances for new employee.
        
        Args:
            employee_id: Employee's user ID
            hire_date: Employee hire date (ISO format)
            token: JWT access token for authentication
        
        Returns:
            True if allocation successful
        """
        url = f"{self.base_url}/api/v1/leave-balances/allocate"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": get_correlation_id() or "",
            "Content-Type": "application/json"
        }
        payload = {
            "employee_id": str(employee_id),
            "hire_date": hire_date
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Successfully allocated balances for employee {employee_id}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error allocating balances: {e.response.status_code}")
            # Don't fail employee creation if balance allocation fails
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error allocating balances: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error allocating balances: {str(e)}")
            return False


# Global client instance
leave_service_client = LeaveServiceClient()
