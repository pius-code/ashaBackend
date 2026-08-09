# Running the full Asha stack yourself

This is for anyone who wants to go hardcore and actually run the whole
pipeline end to end — you'll need an ESP32 and about 30-45 minutes. If you
just want to understand how it works without doing any of this, the main
[README](./README.md) covers the architecture on its own.

Three repos are involved:

- [Asha-Iris](https://github.com/pius-code/Asha-Iris) — the messaging/agent layer (Telegram, Discord, escalation)
- [ashaBackend](https://github.com/pius-code/ashaBackend) — this repo, the MCP server + REST API + MQTT subscriber
- [ashaBridge](https://github.com/pius-code/ashaBridge) — the ESP32 firmware

## 1. Clone all three

```bash
git clone https://github.com/pius-code/Asha-Iris.git
git clone https://github.com/pius-code/ashaBackend.git
git clone https://github.com/pius-code/ashaBridge.git
```

## 2. Get ashaBackend running

```bash
cd ashaBackend
uv run main.py
```

Fill in the `.env` as you go — honestly, hand the env var table in the main
README to an AI assistant and let it walk you through each value rather than
guessing; you'll otherwise end up circling on things like the Mongo
connection string.

## 3. Create your account and project

Once it's running, open `localhost:8080/docs` (Swagger UI):

1. Create a new account. Grab the **userID** it gives you back — save it.
2. Log in via the Swagger docs UI.
3. Create a new project. Grab the **projectID** it returns — save it too.

## 4. Point ashaBackend at your user

Open `agent/tools/devices_tools.py`. On line 27:

```python
Project.Created_by == "69e9de328ab270d2e2416395"
```

Replace that string with the userID you saved in step 3.

## 5. Set up the firmware (ashaBridge)

Read `ashaBridge`'s own README first — it covers the PlatformIO/board setup
this tutorial doesn't. Once you're set up there:

Open `AshaBridge/src/main.cpp`. On line 18:

```cpp
asha.init("957aab4d-fba2-421e-94b9-0191459fa408");
```

Replace that string with your projectID from step 3.

Now open `AshaBridge/lib/ASHABridge/ASHA.cpp` and fix two hardcoded values:

**Line 362** — your MQTT broker:

```cpp
mqttClient.setServer("10.0.122.177", 1883);
```

Replace with your own broker's address — a public broker works, or install
Mosquitto locally if you want to test on your own network.

**Line 336-338** — your ashaBackend URL:

```cpp
http.begin(client,
           "https://helena-mic-households-candidate.trycloudflare.com/api/v1/asha/"
           "verify_and_register_device");
```

Replace the domain with wherever your own `ashaBackend` is reachable —
[ngrok](https://ngrok.com) works well for this, just make sure `uv run
main.py` is actually running when you expose it. Keep the
`/api/v1/asha/verify_and_register_device` path as-is.

## 6. Connect your sensors and flash

Read `ashaBridge`'s `DOCS.md` for what's actually supported (bus types,
pin conventions, etc.) before wiring anything up. Once your sensors are
connected and the values above are updated, flash the firmware to your
ESP32.

## 7. Set up Asha-Iris

Back in the `Asha-Iris` repo, copy `.env.example` to `.env` (create the
`.example` file if it doesn't exist yet, so people know what's expected) and
fill it in. You don't need every AI provider listed — just pick one you're
comfortable with. Groq and OpenRouter are both worth trying first since
they're generous on their free tiers.

That's the full stack. From here, message the bot and it should be able to
see and control whatever you've wired up.
