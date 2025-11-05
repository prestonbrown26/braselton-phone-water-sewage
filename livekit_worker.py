#!/usr/bin/env python3
"""LiveKit agent worker for handling voice sessions with OpenAI Realtime."""

import asyncio
import logging
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit import agents
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import openai

from agent_utils import detect_intent, log_conversation, should_transfer_to_human

# Load environment variables
load_dotenv()

logger = logging.getLogger("braselton-voice-agent")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for LiveKit voice sessions.
    
    This function is called for each new room/call that the agent joins.
    """
    
    # Generate unique call ID for tracking
    call_id = str(uuid.uuid4())
    caller_number = None  # Will be populated from SIP metadata if available
    
    logger.info("Agent connecting to room: %s (call_id: %s)", ctx.room.name, call_id)
    
    # Initialize OpenAI Realtime model for voice
    # Uses GPT-4o-realtime for streaming conversation
    initial_context = llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful AI assistant for the Town of Braselton Utilities Department. "
            "You can help residents with:\n"
            "- Paying their utility bills\n"
            "- Reporting service outages or issues\n"
            "- General questions about water, sewer, and sanitation services\n\n"
            "Be friendly, professional, and concise. If a caller wants to pay their bill, "
            "tell them you'll send them a payment link. If they want to speak to a person, "
            "offer to transfer them. Keep responses brief and conversational."
        ),
    )
    
    # Create the voice assistant with OpenAI Realtime
    assistant = agents.VoiceAssistant(
        vad=agents.silero.VAD.load(),  # Voice activity detection
        stt=openai.STT(),  # Speech-to-text (Whisper)
        llm=openai.LLM.with_realtime(model="gpt-4o-realtime-preview-2024-10-01"),
        tts=openai.TTS(voice="alloy"),  # Text-to-speech
        chat_ctx=initial_context,
    )
    
    # Set up event handlers for tracking conversation
    @assistant.on("user_speech_committed")
    def on_user_speech(msg: llm.ChatMessage):
        """Called when user speech is transcribed."""
        logger.info("User said: %s", msg.content)
        
        # Detect intent and log conversation
        intent_data = detect_intent(msg.content)
        logger.info("Detected intent: %s", intent_data.get("intent"))
        
        # Check if we need to transfer to a human
        if should_transfer_to_human(intent_data):
            logger.info("Transfer requested - would route to human agent here")
            # TODO: Implement actual call transfer logic
    
    @assistant.on("agent_speech_committed")
    def on_agent_speech(msg: llm.ChatMessage):
        """Called when agent responds."""
        logger.info("Agent replied: %s", msg.content)
        
        # Log the full exchange to backend
        # Note: user speech comes first, so we log after agent responds
        asyncio.create_task(
            asyncio.to_thread(
                log_conversation,
                call_id,
                caller_number,
                msg.content,  # This is the full conversation context
                msg.content,
            )
        )
    
    # Connect to the room and start the assistant
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    assistant.start(ctx.room)
    
    # Wait for the first participant (caller) to join
    participant = await ctx.wait_for_participant()
    logger.info("Participant joined: %s", participant.identity)
    
    # Greet the caller
    await assistant.say(
        "Hello! Thanks for calling Braselton Utilities. How can I help you today?",
        allow_interruptions=True,
    )
    
    logger.info("Voice assistant is now active")


if __name__ == "__main__":
    # Run the LiveKit worker
    # This listens for incoming calls and spawns agent sessions
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )

