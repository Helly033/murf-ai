import { NextRequest, NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";
import { RoomAgentDispatch, RoomConfiguration } from "@livekit/protocol";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const roomName =
      body.room_name || `voice-room-${Date.now()}`;

    const participantIdentity =
      body.participant_identity || `user-${Date.now()}`;

    const agentName = "day4-memory-agent";

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

    if (!apiKey || !apiSecret || !livekitUrl) {
      return NextResponse.json(
        {
          error: "LiveKit environment variables are missing",
        },
        { status: 500 }
      );
    }

    const token = new AccessToken(apiKey, apiSecret, {
      identity: participantIdentity,
      name: participantIdentity,
      ttl: "1h",
    });

    token.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
    });

    token.roomConfig = new RoomConfiguration({
      agents: [
        new RoomAgentDispatch({
          agentName: agentName,
        }),
      ],
    });

    const participantToken = await token.toJwt();

    return NextResponse.json({
      serverUrl: livekitUrl,
      participantToken,
    });
  } catch (error) {
    console.error("Token generation error:", error);

    return NextResponse.json(
      {
        error: "Failed to generate LiveKit token",
      },
      { status: 500 }
    );
  }
}