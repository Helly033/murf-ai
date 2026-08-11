import argparse
import asyncio
import json
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env")

AGENT_NAME = "outbound-agent"


async def dial(phone_number, room_name):

    lk = api.LiveKitAPI()

    try:

        await lk.room.create_room(
            api.CreateRoomRequest(
                name=room_name
            )
        )

        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps({
                    "phone_number": phone_number
                }),
            )
        )

    finally:

        await lk.aclose()


def main():

    parser = argparse.ArgumentParser(
        description="Place an outbound call"
    )

    parser.add_argument(
        "--to",
        required=True,
        help="SIP address to call"
    )

    parser.add_argument(
        "--room",
        default=None
    )

    args = parser.parse_args()

    room_name = (
        args.room
        or f"outbound-{uuid.uuid4().hex[:8]}"
    )

    asyncio.run(
        dial(
            args.to,
            room_name
        )
    )

    print(
        f"Dispatched {AGENT_NAME} "
        f"to room '{room_name}' "
        f"to call {args.to}"
    )


if __name__ == "__main__":
    main()