import { NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const roomName = url.searchParams.get("room") || "aria-room";
  const participantName = url.searchParams.get("identity") || "Student";

  const apiKey = process.env.LIVEKIT_API_KEY || "APIRZpxztKts5S9";
  const apiSecret = process.env.LIVEKIT_API_SECRET || "PeOikfvlUucvudaWfTDePRTClt8CxzKhiu6XDWJg8zcD";

  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantName,
  });
  
  at.addGrant({ roomJoin: true, room: roomName, canPublish: true, canSubscribe: true });

  const accessToken = await at.toJwt();
  return NextResponse.json({ accessToken });
}