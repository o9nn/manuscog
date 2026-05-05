import argparse
import asyncio

from app.agent.manus import Manus
from app.logger import logger
from kernel.awakening import AwakeningContext, awaken, save_session_snapshot


async def main():
    # ------------------------------------------------------------------ #
    # Stage-0 awakening — before any LLM or tool call                     #
    # ------------------------------------------------------------------ #
    ctx: AwakeningContext = awaken()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()

    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        # Use command line prompt if provided, otherwise ask for input
        prompt = args.prompt if args.prompt else input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()
        # Write session snapshot so the next session can remember this one
        save_session_snapshot(ctx, summary=f"Completed prompt session {ctx.session_id}")


if __name__ == "__main__":
    asyncio.run(main())
