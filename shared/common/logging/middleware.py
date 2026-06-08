"""
Correlation ID middleware for FastAPI applications.

Automatically generates and propagates correlation IDs for distributed tracing.
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.common.logging.logger import set_correlation_id, clear_correlation_id, get_logger

logger = get_logger(__name__)

# Header name for correlation ID
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation ID for request tracing.
    
    - Extracts correlation ID from request headers if present
    - Generates new correlation ID if not present
    - Sets correlation ID in context for logging
    - Adds correlation ID to response headers
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and manage correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER,
            str(uuid.uuid4())
        )
        
        # Set in context for logging
        set_correlation_id(correlation_id)
        
        try:
            # Log request
            logger.info(
                f"{request.method} {request.url.path}",
                extra={
                    'extra_fields': {
                        'method': request.method,
                        'path': request.url.path,
                        'query_params': str(request.query_params),
                    }
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            
            # Log response
            logger.info(
                f"Response {response.status_code}",
                extra={
                    'extra_fields': {
                        'status_code': response.status_code,
                    }
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Request processing error: {str(e)}",
                exc_info=True
            )
            raise
            
        finally:
            # Clean up context
            clear_correlation_id()
