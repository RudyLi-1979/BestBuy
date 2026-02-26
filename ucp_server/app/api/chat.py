"""
Chat API endpoints
Handles conversational AI interactions
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest, ChatResponse
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize chat service
chat_service = ChatService()

# In-memory conversation storage (TODO: Move to Redis)
conversations = {}


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Send a message to the AI shopping assistant
    
    Request body:
    {
        "message": "I want to buy an iPhone",
        "session_id": "optional-session-id"
    }
    
    Response:
    {
        "message": "I found several iPhone models...",
        "session_id": "abc123",
        "function_calls": [...]
    }
    """
    try:
        logger.info("=" * 80)
        logger.info("📨 Received chat request")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message: {request.message}")
        logger.info(f"Session ID: {request.session_id}")
        if request.user_context:
            logger.info(f"User context — categories: {request.user_context.recent_categories}, "
                        f"brands: {request.user_context.favorite_manufacturers}, "
                        f"interactions: {request.user_context.interaction_count}")
        logger.info("=" * 80)
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = conversations.get(session_id, [])
        
        logger.info(f"Processing chat message for session {session_id}: {request.message[:100]}")
        
        # Process message
        result = await chat_service.process_message(
            message=request.message,
            db=db,
            user_id=user_id,
            conversation_history=conversation_history,
            user_context=request.user_context
        )
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": request.message})
        conversation_history.append({"role": "assistant", "content": result["message"]})
        conversations[session_id] = conversation_history
        
        # Build response
        response = ChatResponse(
            message=result["message"],
            session_id=session_id,
            function_calls=result.get("function_calls"),
            products=result.get("products"),
            suggested_questions=result.get("suggested_questions")
        )
        
        logger.info(f"Chat response sent for session {session_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_conversation(session_id: str):
    """
    Clear conversation history for a session
    
    Response:
    {
        "message": "Conversation cleared"
    }
    """
    try:
        if session_id in conversations:
            del conversations[session_id]
            logger.info(f"Cleared conversation for session {session_id}")
        
        return {"message": "Conversation cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session
    
    Response:
    {
        "session_id": "abc123",
        "messages": [...]
    }
    """
    try:
        history = conversations.get(session_id, [])
        
        return {
            "session_id": session_id,
            "messages": history
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
