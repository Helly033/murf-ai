import os
from livekit.api import AccessToken, VideoGrants

# Your credentials
api_key = "APIRZpxztKts5S9"
api_secret = "PeOikfvlUucvudaWfTDePRTClt8CxzKhiu6XDWJg8zcD"

# Generate token
token = AccessToken(api_key, api_secret) \
    .with_identity("Student") \
    .with_name("Student") \
    .with_grants(VideoGrants(
        room_join=True,
        room="aria-room",
        can_publish=True,
        can_subscribe=True,
    )).to_jwt()

print("\n--- COPY THIS TOKEN FOR YOUR FRONTEND ---\n")
print(token)
print("\n-----------------------------------------\n")