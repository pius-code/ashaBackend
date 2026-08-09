# flake8: noqa
# type: ignore

"""all the tools that ASHA needs to run for now, use depends to get user id without the LLM having to ask for it, runs before tools are even understood by LLM, hidden """

from agent.core.fastmcp import mcp
from fastmcp.dependencies import Depends
from agent.tools.devices_tools import get_asha_user_projects_and_devices
from agent.tools.pubSub_tools import publish_to_device
from agent.tools.scheduler import create_scheduled_workflow, delete_workflow
from agent.schema.workflow import Workflow
from agent.tools.Http_tools import post, url
from agent.tools.ir_tools import build_samsung_raw
from agent.core.ir_codes import IR_CODES


def get_user_id() -> str:
    return "your user ID"


# Full reference docs for the heaviest tools, fetched on demand via get_tool_guide()
# instead of being dumped into every tool listing. Keep these in sync with the
# behavior of the tool they document — they are the source of truth for edge cases,
# examples, and less-common payload shapes.
TOOL_GUIDES = {
    "publish_command": """
PUBLISH_COMMAND — FULL BUS REFERENCE

──────────────────────────────────────────
DIGITAL (bus: "Digital")
Use for: relays, simple LEDs, door locks, buzzers, motion sensors
Payload:
    {"pin": <pin>, "action": "digital", "value": <0 or 1>}
Examples:
    Turn ON  → {"pin": 18, "action": "digital", "value": 1}
    Turn OFF → {"pin": 18, "action": "digital", "value": 0}
    Read     → {"pin": 18, "action": "digital", "value": -1}  → set wait_response=True to get the pin value back


──────────────────────────────────────────

PWM (bus: "PWM")
Use for: servos, DC motors, LED dimming, fans, buzzers
Payload (write):
    {"pin": <pin>, "action": "pwm", "freq": <hz>, "duty": <0-65535>}
Payload (read):
    {"pin": <pin>, "action": "pwm", "value": -1} with wait_response=True

Frequency and duty by device type:
    LED/Backlight dimming → freq: 5000,  duty: 0 (off) to 65535 (full brightness)
    DC Motor speed        → freq: 1000,  duty: 0 (stop) to 65535 (full speed)
    Servo position        → freq: 50,    duty: 3277 (0°) | 4915 (90°) | 6553 (180°)
    Buzzer tone (440Hz A) → freq: 440,   duty: 32767 (on) | 0 (off)
    Fan speed             → freq: 1000,  duty: 0 (off) to 65535 (full speed)

STOPPING PWM DEVICES:
Setting duty: 0 reduces output but the LEDC hardware signal keeps running — a buzzer
will still beep, a motor may still twitch. To fully silence a PWM device, send:
    {"pin": <pin>, "action": "stop_pwm"}
This detaches the LEDC peripheral and drives the pin LOW. Works in publish_command,
batch commands, and inside Lua via asha.command('{"pin": 21, "action": "stop_pwm"}').

Read response fields:
    ledc_duty   → what the controller is configured to output (0-65535). Always present.
    analog_avg  → average of 300 physical pin samples (0-4095 = 0-3.3V). Only present if pin is GPIO 32-39.
    analog_note → present instead of analog_avg if pin is not ADC-capable.

Fault detection:
    ledc_duty and analog_avg should agree proportionally:
        ledc_duty / 65535 ≈ analog_avg / 4095
    If ledc_duty is high but analog_avg is near 0 — device is likely faulty.

Examples (write):
    LED at 50% brightness → {"pin": 18, "action": "pwm", "freq": 5000, "duty": 32767}
    Servo at 90°          → {"pin": 19, "action": "pwm", "freq": 50,   "duty": 4915}
    Motor at full speed   → {"pin": 21, "action": "pwm", "freq": 1000, "duty": 65535}
    Buzzer ON             → {"pin": 22, "action": "pwm", "freq": 440,  "duty": 32767}

Examples (read):
    Read LED on ADC pin     → {"pin": 34, "action": "pwm", "value": -1} wait_response=True
    Read LED on non-ADC pin → {"pin": 18, "action": "pwm", "value": -1} wait_response=True
                              → returns ledc_duty only, analog_note explains why analog_avg is absent


────────────────────────────────────────
ANALOG (bus: "Analog")
    Use for: water level sensors, soil moisture, light sensors, potentiometers
    Payload:
    {"pin": <pin>, "action": "analog"} with wait_response=True

    Note: Analog is read-only. Pin must be GPIO 32-39.
    Response:
    value → 0-4095 (0 = no signal, 4095 = maximum voltage 3.3V)

    Example:
    Read water level → {"pin": 34, "action": "analog"} wait_response=True

────────────────────────────────────────

I2C WRITE (bus: "I2C")
Use for: OLEDs, LCD displays, smart sensors (BME280, MPU6050), RTCs
Payload:
    {"action": "i2c_write", "addr": <decimal addr>, "reg": <register>, "data": [<bytes>]}

Note: I2C does NOT use a pin field. All I2C devices share SDA(GPIO21) and SCL(GPIO22).
Target devices by their address, not pin.

Common device addresses (decimal):
    SSD1306 OLED  → addr: 60  (0x3C)
    BME280 sensor → addr: 118 (0x76)
    MPU6050 IMU   → addr: 104 (0x68)
    PCF8574 LCD   → addr: 39  (0x27)

Examples:
    Turn off OLED display → {"action": "i2c_write", "addr": 60,  "reg": 0, "data": [174]}
    Turn on OLED display  → {"action": "i2c_write", "addr": 60,  "reg": 0, "data": [175]}
    Wake up MPU6050       → {"action": "i2c_write", "addr": 104, "reg": 107, "data": [0]}

──────────────────────────────────────────

SPI (bus: "SPI")
Use for: RFID readers, TFT displays, SD cards, fast ADC chips

IMPORTANT — SPI pins are per-device, not fixed.
Always read cs_pin, sck, miso, mosi from get_user_projects_and_devices() for the specific SPI device.
Never assume default pins.

SPI WRITE:
Payload:
    {"action": "spi_write", "cs_pin": <cs>, "speed": <hz>, "mode": <0-3>, "data": [<bytes>]}

SPI READ:
Payload:
    {"action": "spi_read", "cs_pin": <cs>, "speed": <hz>, "mode": <0-3>, "data": [<bytes>]}

How spi_read works: SPI is full-duplex — every byte you send, a byte comes back simultaneously.
The "data" array contains the bytes to send. The device clocks back a response byte for each one.
First byte is usually the register address. Remaining bytes are dummy (0x00) to clock the response back.

Read/write bit convention varies by device — check the datasheet:
    RC522 RFID  → bit 7 of address = 1 means read  (e.g. register 0x37 → send 0xB7 to read)
    Some devices → bit 7 = 0 means read
    Some devices → use a separate command byte entirely
Always look this up before reading. Wrong convention = garbage response.

Speed by device:
    RC522 RFID   → speed: 1000000  (1MHz)
    SD card      → speed: 25000000 (25MHz)
    TFT display  → speed: 40000000 (40MHz)

Mode: 0 for almost all devices. Check datasheet if readings look wrong.

Examples:
    Read RC522 firmware version (register 0x37):
        {"action": "spi_read", "cs_pin": 26, "speed": 1000000, "mode": 0, "data": [183, 0]}
        → 183 = 0xB7 (0x37 | 0x80, read bit set). Second 0 is dummy byte to clock response back.
        → Response byte 2 should be 0x91 (v1.0) or 0x92 (v2.0) if wiring is correct.

    Write to SD card:
        {"action": "spi_write", "cs_pin": 5, "speed": 25000000, "mode": 0, "data": [1, 2, 3]}

NOTE: spi_read via publish_command is for one-off reads.
For continuous SPI polling (e.g. RFID card detection loop), use asha.spiTransfer() in a Lua script
via create_a_real_time_task — it returns bytes directly to Lua without an MQTT round-trip.

──────────────────────────────────────────

UART WRITE (bus: "UART")
Use for: GPS modules, GSM/SIM800, fingerprint sensors, ranging sensors
Payload (text):
    {"action": "uart_write", "baud": <rate>, "tx_pin": 17, "rx_pin": 16, "data": "<command>"}
Payload (binary):
    {"action": "uart_write", "baud": <rate>, "tx_pin": 17, "rx_pin": 16, "data": [<bytes>]}

Baud rates by device:
    GPS module          → baud: 9600
    GSM/SIM800          → baud: 9600
    Fingerprint R307    → baud: 57600
    Most modern modules → baud: 115200

Examples:
    GPS read          → {"action": "uart_write", "baud": 9600, "tx_pin": 17, "rx_pin": 16, "data": ""}
    GSM network check → {"action": "uart_write", "baud": 9600, "tx_pin": 17, "rx_pin": 16, "data": "AT+CREG?\\r\\n"}
    GSM SMS mode      → {"action": "uart_write", "baud": 9600, "tx_pin": 17, "rx_pin": 16, "data": "AT+CMGF=1\\r\\n"}

──────────────────────────────────────────

IR (bus: "IR")
Use for: TVs, air conditioners, set-top boxes, any IR-controlled device
    Payload:
        {"action": "ir_send", "pin": <pin>, "freq": <khz>, "timings": [<microseconds...>]}

Fields:
    freq    → carrier frequency in kHz. Use 38 for almost all consumer devices.
    timings → raw pulse durations in microseconds, alternating on/off.
          You are expected to know these from your training data for common devices.
          For uncommon devices, inform the user a timing lookup tool is needed.

Examples:
    Samsung TV power → {"action": "ir_send", "pin": 4, "freq": 38, "timings": [4500, 4500, 560, 1690, 560, 1690, 560, 560, 560, 560, 560, 1690, 560, 560, 560, 560, 560, 560, 560, 1690, 560, 560, 560, 560, 560, 560, 560, 560, 560, 1690, 560, 1690, 560, 1690, 560, 39000]}

──────────────────────────────────────────

BATCH (multiple commands in sequence)
Use for: controlling multiple devices at once, timed sequences, automation steps
Payload:
    {"action": "batch", "commands": [<command>, <delay>, <command>, ...]}

Commands inside batch follow the same payload rules as individual commands.
To add a delay between commands use: {"delay_ms": <milliseconds>}

Examples:
    Turn on PWM LED and Digital LED together:
    {
        "action": "batch",
        "commands": [
            {"pin": 18, "action": "pwm", "freq": 5000, "duty": 65535},
            {"pin": 20, "action": "digital", "value": 1}
        ]
    }

    Turn on LED, wait 2 seconds, turn off:
    {
        "action": "batch",
        "commands": [
            {"pin": 20, "action": "digital", "value": 1},
            {"delay_ms": 2000},
            {"pin": 20, "action": "digital", "value": 0}
        ]
    }

    Traffic light sequence (red on, others off):
    {
        "action": "batch",
        "commands": [
            {"pin": 18, "action": "digital", "value": 1},
            {"pin": 19, "action": "digital", "value": 0},
            {"pin": 20, "action": "digital", "value": 0}
        ]
    }
""",
    "create_a_real_time_task": """
CREATE_A_REAL_TIME_TASK — FULL LUA REFERENCE

HOW IT WORKS:
You write a Lua script as a string. The ESP32 runs it on a dedicated core (Core 0),
separate from the MQTT connection. The script has access to hardware via the `asha` module.

AVAILABLE LUA FUNCTIONS:
    asha.command(jsonStr)               — send a hardware command (see formats below)
    asha.publish(topic, message)        — publish a string to an MQTT topic (thread-safe, non-blocking)
    asha.digitalRead(pin)               — returns 0 or 1 (use for GPIO/digital pins only)
    asha.analogRead(pin)                — returns 0 to 4095 (ADC pins GPIO 32-39 only)
    asha.ledcRead(pin)                  — returns current PWM duty (0 = off or not initialized, >0 = running)
    asha.spiTransfer(cs_pin, {bytes})   — sends bytes over SPI, returns table of received bytes (one per sent byte)
    asha.subscribe(topic)               — subscribe to an MQTT topic to receive external messages
    asha.readMessage(topic)             — returns the last message received on a subscribed topic, or ""
    asha.sleep(ms)                      — pause for ms milliseconds, yields to OS scheduler
    millis()                            — returns device uptime in milliseconds
    print(...)                          — prints to device Serial output

SPI IN LUA — asha.spiTransfer:
Use this for continuous SPI polling (e.g. RFID card detection). Returns bytes directly — no MQTT round-trip.
    local rx = asha.spiTransfer(cs_pin, {byte1, byte2, ...})
    rx is a table — rx[1] is the byte received while sending byte1, rx[2] while sending byte2, etc.

The read/write bit convention is device-specific — always check the datasheet.
For RC522: set bit 7 of the register address to 1 for a read (e.g. register 0x37 → send 0xB7).
Dummy bytes (0x00) after the address are needed to clock the response back from the device.

Example — read RC522 firmware version (wiring sanity check):
    local cs = 26   -- cs_pin from get_user_projects_and_devices()
    local rx = asha.spiTransfer(cs, {0xB7, 0x00})
    -- rx[2] should be 0x91 (v1.0) or 0x92 (v2.0) if wiring is correct
    asha.publish("asha/ashaSensor/<asha_id>", "RC522 version: " .. tostring(rx[2]))

DEBOUNCE RULE — MANDATORY FOR ALL SPI POLLING LOOPS:
When an SPI sensor can hold the same state across multiple loop ticks (RFID card
sitting on the reader, a threshold staying crossed), you MUST use a state variable.
Without it, the script publishes on EVERY loop tick while the condition is true —
this floods the agent with duplicate messages and causes a notification loop.
Track "did state CHANGE?" not "is state true now?":

    local card_present = false  -- tracks what state was LAST tick

    while true do
        local rx = asha.spiTransfer(cs, {...})
        local detected = <your condition on rx>

        if detected and not card_present then
            card_present = true   -- card just ARRIVED → fire exactly once
            asha.command('{"pin": <light_pin>, "action": "digital", "value": 1}')
            asha.publish("asha/ashaSensor/<asha_id>", "Someone scanned an RFID card — red light on")
        elseif not detected and card_present then
            card_present = false  -- card just LEFT → reset, optionally undo action
            asha.command('{"pin": <light_pin>, "action": "digital", "value": 0}')
        end

        asha.sleep(200)
    end

This is the same principle as the CHANGE-DETECTION PATTERN for digital/analog sensors.
Never publish unconditionally inside a polling loop — always gate it on a state change.

CRITICAL — asha.sleep() IS MANDATORY IN ALL WHILE LOOPS:
The ESP32 has a watchdog timer that reboots the device if the background OS task
does not get CPU time within ~5 seconds. A tight while loop with no sleep will
always trigger this and reboot the device. Every while loop MUST call asha.sleep().
Minimum recommended: asha.sleep(10) — 10ms is enough to feed the watchdog.
asha.sleep() is also the point where a running script gets replaced — when a new
script arrives, the next sleep() call stops the current script cleanly.
There are no exceptions to this rule. A loop without asha.sleep() will always crash
and cannot be replaced remotely.

LUA SYNTAX BASICS:
    Variables:      local x = 10
    If/else:        if x == 1 then ... elseif x == 2 then ... else ... end
    While loop:     while condition do ... end
    Equality:       == (not === like JavaScript)
    Not equal:      ~=
    And / Or:       and / or (not && / ||)

NOTE ON WHILE LOOPS:
When a new Lua script is sent while a while loop is already running, the device
stops the current script at the next asha.sleep() call and immediately runs the
new one. You do NOT need to worry about the old script blocking the new one —
this is handled automatically by the firmware.

MERGING REAL-TIME CONDITIONS — IMPORTANT:
If a real-time Lua script was already sent earlier in this conversation, do NOT
send a second independent script. The device runs only one Lua script at a time.
Instead, MERGE the new condition into the existing script and send one combined
replacement. The user will experience all behaviors running simultaneously.

Example — button script already running, user adds touch sensor condition:

    WRONG — two separate scripts (second replaces first, button behavior is lost):
        Script 1: while true do ... button logic ... end
        Script 2: while true do ... touch logic ... end

    CORRECT — one merged script with both conditions:
        while true do
          local btn = asha.digitalRead(21)
          local touch = asha.analogRead(34)
          if btn == 1 then
            asha.command('{"pin": 18, "action": "digital", "value": 1}')
          end
          if touch > 3000 then
            asha.command('{"pin": 25, "action": "digital", "value": 1}')
          end
          asha.sleep(10)
        end

Always check conversation history before sending. If a real-time script exists,
include all its conditions in the new script.

READING HARDWARE STATE:
    Digital pin:     local val = asha.digitalRead(pin)   — 0 or 1
    Analog sensor:   local val = asha.analogRead(pin)    — 0 to 4095 (ADC pins only)
    PWM device:      local val = asha.ledcRead(pin)      — 0 = off or not initialized, >0 = running
    External topic:  local val = asha.readMessage(topic) — last MQTT message on topic, or ""
    Do NOT use asha.command() for reading — it sends commands, returns nothing to Lua.

──────────────────────────────────────────
MONITORING & PUBLISHING BACK TO THE USER
──────────────────────────────────────────
When the user asks to "monitor" a device or "notify me when X changes", use asha.publish()
to send the state change back. [TEMPORARY — Asha Iris hackathon demo] Asha Iris is
listening on asha-iris/events/<task_id> and will notify the user across Telegram/email,
escalating and retrying on its own if they don't respond — not the usual WhatsApp path.

CRITICAL — THE PUBLISH MESSAGE IS A MEMO TO THE LLM, NOT JUST A NOTIFICATION:
When the script publishes, that message becomes the input to the LLM that wakes up and texts the user.
The LLM only has that string as context. If it is vague, the LLM cannot respond well.
Pack the message with: WHICH device, WHAT happened, and WHY the user cares.
If the user gave specific instructions or terms for this monitoring task, encode them in the message.

Example: user says "let me know if my sister turns off the light again, she never does it"
BAD message:  "A light was turned off"
GOOD message: "Sister's room light (pin 19) just turned OFF. User asked to be alerted because she forgets."

If monitoring multiple devices, publish a SEPARATE specific message per device. Never bundle them into one vague message.
BAD:  one message "one of the lights changed"
GOOD: separate publishes per pin with the exact device name and state

RULES:
[TEMPORARY — Asha Iris hackathon demo, revert to "asha/ashaSensor/<asha_id>" after]
- Always publish to "asha-iris/events/<task_id>" — substitute the actual task_id
  string (the SAME task_id already created via Asha Iris's create_unresolved_task
  tool, not the asha_id — this is what correlates the event back to a task)
- Only publish when the value CHANGES — compare current vs previous value before publishing
- Never publish on every loop tick — that spams the user
- Be specific: name the device, state the change, include user context

CHANGE-DETECTION PATTERN:
    CRITICAL: Always initialize prev by reading the actual current sensor state BEFORE the loop.
    NEVER use -1 as the starting value — it guarantees a false trigger on the very first iteration
    because any real sensor reading differs from -1, causing an immediate unwanted publish.

    local prev = asha.digitalRead(pin)   -- read actual state first (use ledcRead for PWM)
    while true do
      local current = asha.digitalRead(pin)  -- or analogRead, ledcRead
      if current ~= prev then
        asha.publish("asha-iris/events/<task_id>", "Hey, looks like someone just toggled your light — you might want to check")
        prev = current
      end
      asha.sleep(100)
    end

Write the message like a calm, natural human text — the user reads this directly on WhatsApp.
Be conversational and slightly casual. Include enough context so the user knows what happened without needing to ask.
Good:  "Heads up — looks like someone turned off the fan in daddy's room"
       "Hey, the water level just spiked, might want to check it out"
       "Fan's back on again, all good"
Bad:   "1"  /  "true"  /  "changed"  /  "Fan turned OFF"  /  "state=0"

ORDERING RULE FOR ledcRead:
asha.ledcRead(pin) only works AFTER a PWM command has been sent to that pin.
The LEDC peripheral is initialized the first time a PWM command runs on a pin.
If you call ledcRead before any PWM command, it returns 0 (same as off).
ALWAYS send the PWM command first using publish_command, then send the Lua monitoring script.
Read the actual pin state before the loop to avoid false triggers on startup:
    local prev = asha.ledcRead(pin)
    while true do
      local duty = asha.ledcRead(pin)
      if duty ~= prev then
        -- state changed, react
        prev = duty
      end
      asha.sleep(100)
    end

PAYLOAD FORMAT:
    {
        "action": "lua",
        "script": "<lua script as a single string>"
    }

COMMAND FORMATS (pass as a JSON string inside asha.command()):

    Digital write:
        asha.command('{"pin": 18, "action": "digital", "value": 1}')
        value 1 = HIGH, 0 = LOW

    PWM:
        asha.command('{"pin": 18, "action": "pwm", "freq": 5000, "duty": 65535}')

    Stop PWM (fully silences the hardware signal):
        asha.command('{"pin": 18, "action": "stop_pwm"}')

    Batch (multiple commands in sequence):
        asha.command('{"action": "batch", "commands": [{"pin": 18, "action": "digital", "value": 1}, {"delay_ms": 500}, {"pin": 18, "action": "digital", "value": 0}]}')

    Non-blocking delay (use inside batch commands only, NOT as a loop delay):
        include {"delay_ms": 1000} inside a batch commands array

EXAMPLES:

    Stop buzzer on pin 21 (one-shot — no loop needed):
        asha.command('{"pin": 21, "action": "stop_pwm"}')

    Button press → switch LEDs (runs once):
        local btn = asha.digitalRead(21)
        if btn == 1 then
          asha.command('{"action": "batch", "commands": [{"pin": 18, "action": "digital", "value": 0}, {"pin": 20, "action": "digital", "value": 1}]}')
        else
          asha.command('{"pin": 18, "action": "digital", "value": 1}')
        end

    Sensor threshold alert (runs once):
        local level = asha.analogRead(34)
        if level > 3000 then
          asha.command('{"pin": 25, "action": "digital", "value": 1}')
        end

    Persistent button monitor (runs until replaced or rebooted):
        while true do
          local btn = asha.digitalRead(21)
          if btn == 1 then
            asha.command('{"pin": 18, "action": "digital", "value": 1}')
          else
            asha.command('{"pin": 18, "action": "digital", "value": 0}')
          end
          asha.sleep(10)
        end

    PWM device monitor — beep when LED turns off (send PWM command first, then this script):
        local prev = asha.ledcRead(18)
        while true do
          local duty = asha.ledcRead(18)
          if duty ~= prev then
            if duty == 0 then
              asha.command('{"pin": 25, "action": "pwm", "freq": 440, "duty": 32767}')
            else
              asha.command('{"pin": 25, "action": "stop_pwm"}')
            end
            prev = duty
          end
          asha.sleep(10)
        end

    Monitor a digital pin and notify user when state changes (e.g. "monitor my light on pin 18"):
        local prev = asha.digitalRead(18)   -- read actual current state before loop starts
        while true do
          local state = asha.digitalRead(18)
          if state ~= prev then
            if state == 1 then
              asha.publish("asha-iris/events/<task_id>", "Hey, looks like someone just turned the light back on")
            else
              asha.publish("asha-iris/events/<task_id>", "Heads up — someone turned off the light, you might want to check")
            end
            prev = state
          end
          asha.sleep(100)
        end

    Monitor an analog sensor and notify user when value crosses a threshold:
        local level = asha.analogRead(34)
        local prev = 0
        if level > 2000 then prev = 1 end   -- initialize to actual current state
        while true do
          level = asha.analogRead(34)
          local state = 0
          if level > 2000 then state = 1 end
          if state ~= prev then
            if state == 1 then
              asha.publish("asha-iris/events/<task_id>", "Heads up — water level is getting high (" .. tostring(level) .. "), might want to check it out")
            else
              asha.publish("asha-iris/events/<task_id>", "All good — water level is back to normal (" .. tostring(level) .. ")")
            end
            prev = state
          end
          asha.sleep(200)
        end

    RFID card detection with debounce — light on when card present, publish ONCE per tap:
        -- Always call get_user_projects_and_devices() first for actual pin values
        local cs = 26      -- cs_pin of the RFID device
        local light = 18   -- red light pin
        local card_present = false

        while true do
            -- Replace detection bytes with the correct card-presence check for your device.
            -- For RC522: search datasheet for the REQA/ComIrqReg sequence, or use web search.
            local rx = asha.spiTransfer(cs, {<detection bytes>})
            local detected = <condition on rx>

            if detected and not card_present then
                card_present = true
                asha.command('{"pin":' .. light .. ',"action":"digital","value":1}')
                asha.publish("asha/ashaSensor/<asha_id>", "Someone just scanned an RFID card — red light turned on")
            elseif not detected and card_present then
                card_present = false
                asha.command('{"pin":' .. light .. ',"action":"digital","value":0}')
                asha.publish("asha/ashaSensor/<asha_id>", "RFID card removed — red light off")
            end

            asha.sleep(200)
        end

    Vision + button merged (both conditions in one script):
        asha.subscribe('asha/asha_vision/abc123')
        while true do
          local detected = asha.readMessage('asha/asha_vision/abc123')
          local btn = asha.digitalRead(21)
          if detected == 'person' then
            asha.command('{"pin": 25, "action": "digital", "value": 1}')
          end
          if btn == 1 then
            asha.command('{"pin": 18, "action": "digital", "value": 1}')
          end
          asha.sleep(200)
        end
""",
    "asha_vision": """
ASHA_VISION — FULL REFERENCE

WHAT THIS TOOL DOES:
Starts a vision model on the server that watches for the specified classes.
When a class is detected above the confidence threshold, the server publishes
the class name as a string to the MQTT topic:
    asha/asha_vision/{asha_id}

The server also subscribes to this same topic to coordinate state.
The message published is the detected class name exactly as you specified it
in the classes array — e.g. if classes = ["person", "crow"], the message
will be either "person" or "crow".

EXTRACTING CLASSES FROM USER QUERY:
Pull out the physical objects the user wants to detect. Keep them short and
lowercase — single words where possible.

    User says: "if you see a person or a crow in the farm, sound the alarm"
    → classes: ["person", "crow"]

    User says: "alert me when a car enters the driveway"
    → classes: ["car"]

CONSTRUCTING asha_topic:
Take the asha_id from get_user_projects_and_devices and build the topic string:
    asha_topic = 'asha/asha_vision/' + asha_id

    e.g. if asha_id is "abc123", then asha_topic is "asha/asha_vision/abc123"

PAYLOAD FORMAT:
    {
        "classes": ["person", "crow"],
        "confidence": 0.65,
        "asha_topic": 'asha/asha_vision/{asha_id}'
    }

TWO-STEP FLOW — always do both steps:

STEP 1: Call asha_vision with the classes payload.
STEP 2: Call create_a_real_time_task with a Lua script that:
        - subscribes to asha_topic using asha.subscribe()
        - loops and reads messages using asha.readMessage()
        - reacts when the message matches a detected class

WHAT asha.readMessage() RETURNS ON THIS TOPIC:
    "person"   — if a person was detected
    "crow"     — if a crow was detected
    ""         — empty string when nothing has been detected yet

EXAMPLE — person detected → turn on light (pin 18), asha_id = "abc123":

    STEP 1 payload:
        {
            "classes": ["person"],
            "confidence": 0.65,
            "asha_topic": 'asha/asha_vision/abc123'
        }

    STEP 2 Lua script (pass to create_a_real_time_task):
        asha.subscribe("asha/asha_vision/abc123")
        while true do
          local detected = asha.readMessage('asha/asha_vision/abc123')
          if detected == "person" then
            asha.command('{"pin": 18, "action": "digital", "value": 1}')
          end
          asha.sleep(200)
        end

EXAMPLE — person OR crow detected → sound buzzer (pin 23), asha_id = "abc123":

    STEP 1 payload:
        {
            "classes": ["person", "crow"],
            "confidence": 0.65,
            "asha_topic": 'asha/asha_vision/abc123'
        }

    STEP 2 Lua script:
        asha.subscribe("asha/asha_vision/abc123")
        while true do
          local detected = asha.readMessage('asha/asha_vision/abc123')
          if detected == "person" or detected == "crow" then
            asha.command('{"pin": 23, "action": "digital", "value": 1}')
          end
          asha.sleep(200)
        end

NOTE: asha.sleep(200) in the loop is mandatory. See create_a_real_time_task
for the full explanation of why tight loops crash the device.
""",
}


@mcp.tool
def get_tool_guide(tool_name: str) -> str:
    """
    Returns the full detailed usage guide for one of ASHA's tools — exact payload
    formats for every bus type, duty/freq/baud reference tables, fault-detection
    rules, the complete Lua scripting reference, and worked examples.

    Call this BEFORE your first use of a tool in this conversation if you are not
    already certain of its exact payload shape. Valid tool_name values:
        "publish_command"          — bus-by-bus payload reference (Digital, PWM,
                                      Analog, I2C, SPI, UART, IR, Batch)
        "create_a_real_time_task"  — Lua syntax, asha.* functions, monitoring
                                      patterns, and worked script examples
        "asha_vision"              — vision payload format and detection flow

    You rarely need this for simple Digital on/off or basic PWM — those are
    covered inline in the tool's own description. Call it for anything else:
    I2C/SPI/UART, PWM duty/freq values, batch sequencing, Lua scripts, or vision.
    """
    guide = TOOL_GUIDES.get(tool_name)
    if guide is None:
        return f"No guide found for '{tool_name}'. Valid names: {list(TOOL_GUIDES.keys())}"
    return guide.strip()


@mcp.tool
async def get_user_projects_and_devices():
    """Returns all a users projects and the devices including devices information that the user has"""
    return await get_asha_user_projects_and_devices()


# commented out for the Asha Iris hackathon demo — not needed for the escalation
# flow, restore after the demo
# @mcp.tool
# async def publish_command(asha_id: str, payload: dict, wait_response: bool = False):
#     """
#     Publishes a command to an ESP32 device via MQTT.
#
#     ALWAYS follow these steps in order — do NOT skip any step:
#     1. Call get_user_projects_and_devices() to find the device's bus type, pin, and asha_id.
#     2. Call get_tool_guide("publish_command") to get the exact payload format for that bus type.
#     3. Call this tool with the payload you built from steps 1 and 2.
#
#     Never call this tool with an empty payload {} — an empty payload does nothing and
#     the device will not respond. Always get device info (step 1) and payload format (step 2) first.
#
#     QUICK PAYLOAD SHAPE BY BUS TYPE (use get_tool_guide for full reference):
#         Digital → {"pin": <pin>, "action": "digital", "value": 0|1}  (-1 + wait_response=True to read)
#         PWM     → {"pin": <pin>, "action": "pwm", "freq": <hz>, "duty": <0-65535>}
#                   Stop (not duty:0) → {"pin": <pin>, "action": "stop_pwm"}
#         Analog  → {"pin": <pin>, "action": "analog"} with wait_response=True (read-only, GPIO 32-39)
#         I2C     → {"action": "i2c_write", "addr": <dec>, "reg": <reg>, "data": [<bytes>]}  (no pin field)
#         SPI     → {"action": "spi_write", "cs_pin": <pin>, "speed": <hz>, "mode": <0-3>, "data": [<bytes>]}  (cs_pin from get_user_projects_and_devices)
#                   {"action": "spi_read",  "cs_pin": <pin>, "speed": <hz>, "mode": <0-3>, "data": [<addr_byte>, 0x00, ...]}  (for continuous polling use asha.spiTransfer in Lua)
#         UART    → {"action": "uart_write", "baud": <rate>, "tx_pin": 17, "rx_pin": 16, "data": "<str>"|[<bytes>]}
#         IR      → {"action": "ir_send", "pin": <pin>, "freq": <khz>, "timings": [...]}  (get timings from fetch_device_ir_codes)
#         Batch   → {"action": "batch", "commands": [<command>, {"delay_ms": <ms>}, ...]}
#
#     CORE RULES:
#     1. Match payload structure to bus type exactly; I2C/SPI never include a pin field
#     2. Never guess a pin — always use values from get_user_projects_and_devices()
#     3. Never send freq=0 for PWM (minimum is 1)
#     4. "Turn off" a PWM device → send stop_pwm, not duty:0 (duty:0 leaves the signal running)
#     5. Set wait_response=True only for reads (value:-1, analog, or PWM/I2C reads) — never for writes
#     6. For multiple devices at once or timed sequences, use a single batch command
#     """
#     response = publish_to_device(asha_id, payload, wait_response=wait_response)
#     return {"status": "command sent", "asha_id": asha_id, "payload": payload, "response": response}


# commented out for the Asha Iris hackathon demo — TV/IR control not needed,
# restore after the demo
# @mcp.tool
# def fetch_device_ir_codes(vendor: str, command: str) -> dict:
#     """
#     Returns the raw IR timing array for a given vendor and command.
#     Always call this before publish_command when the device bus is "IR".
#
#     WHEN TO USE:
#     - Device bus is "IR"
#     - User wants to control a TV, AC, set-top box, or any IR-controlled device
#
#     ──────────────────────────────────────────
#     FLOW
#     ──────────────────────────────────────────
#     1. Call fetch_device_ir_codes(vendor, command) → get timings
#     2. Call publish_command with the timings:
#         {"action": "ir_send", "pin": <pin>, "freq": <freq from response>, "timings": <timings from response>}
#
#     ──────────────────────────────────────────
#     AVAILABLE VENDORS AND COMMANDS
#     ──────────────────────────────────────────
#     samsung:
#         power        → toggle TV on/off
#         volume_up    → increase volume
#         volume_down  → decrease volume
#         mute         → toggle mute
#         channel_up   → next channel
#         channel_down → previous channel
#         hdmi1        → switch to HDMI 1
#         hdmi2        → switch to HDMI 2
#
#     NOTE: More vendors (LG, Sony, Panasonic) will be added via the dashboard.
#     If the vendor or command is not listed, inform the user it is not yet supported.
#
#     ──────────────────────────────────────────
#     EXAMPLE
#     ──────────────────────────────────────────
#     User: "Turn off the Samsung TV"
#
#     Step 1 → fetch_device_ir_codes("samsung", "power")
#     Response: {"vendor": "samsung", "command": "power", "freq": 38, "timings": [4500, 4500, ...]}
#
#     Step 2 → publish_command(
#         asha_id="299c90fc-...",
#         payload={"action": "ir_send", "pin": 19, "freq": 38, "timings": [4500, 4500, ...]}
#     )
#     """
#     vendor = vendor.lower()
#     command = command.lower()
#
#     if vendor not in IR_CODES:
#         return {"error": f"Vendor '{vendor}' not supported yet."}
#     if command not in IR_CODES[vendor]:
#         return {"error": f"Command '{command}' not found for vendor '{vendor}'."}
#
#     timings = build_samsung_raw(IR_CODES[vendor][command])
#     return {"vendor": vendor, "command": command, "freq": 38, "timings": timings}


# commented out for the Asha Iris hackathon demo — cron scheduling not needed
# for the real-time escalation flow, restore after the demo
# @mcp.tool
# def create_a_scheduled_workflow(workflow: Workflow):
#     """
#     Use this tool when the user wants to automate a repeated or time-based task.
#
#     WHEN TO USE:
#     - "Turn on the light at 6am every day"
#     - "Turn off the fan every 30 minutes"
#     - "Every Friday at 9pm turn off all devices"
#     - Any request involving "every", "at [time]", "schedule", "automatically"
#
#     DO NOT USE for one-time commands — use publish_command instead.
#
#     BEFORE CALLING THIS TOOL:
#     Always call get_user_projects_and_devices() first to get the correct asha_id and device pins unless it has already been called and exists in context.
#
#     WORKFLOW_ID FORMAT:
#     Combine a short description with random alphanumeric characters.
#     Example: "morning_light_9x2k", "fan_schedule_b3m7"
#
#     CRON EXPRESSION FORMAT:
#     "minute hour day month day_of_week"
#     Examples:
#         Every day at 6am          → "0 6 * * *"
#         Every day at 10pm         → "0 22 * * *"
#         Every 30 minutes          → "*/30 * * * *"
#         Every Friday at 9pm       → "0 21 * * 5"
#         Every weekday at 8am      → "0 8 * * 1-5"
#         Every hour                → "0 * * * *"
#
#     ACTIONS FORMAT:
#     List of MQTT payloads following the same bus rules as publish_command.
#     Examples:
#         [{"pin": 18, "action": "digital", "value": 1}]
#         [{"pin": 18, "action": "digital", "value": 1}, {"pin": 19, "action": "digital", "value": 0}]
#         [{"pin": 18, "action": "pwm", "freq": 5000, "duty": 65535}]
#
#     RULES:
#     1. Always use pins from get_user_projects_and_devices() — never guess
#     2. Generate a unique workflow_id every time
#     3. Match action payload structure to the device bus type exactly
#     4. If the user wants a simple ON/OFF cycle (e.g. "on for 1 min then off"),
#         use ONE workflow with a batch command containing the full sequence including delay_ms.
#         Example: on for 1 min, off →
#         actions: [{"pin":18,"action":"digital","value":1}, {"delay_ms":60000}, {"pin":18,"action":"digital","value":0}]
#         Only create TWO separate workflows if the on-time and off-time are at specific clock times
#         (e.g. "turn on at 6am and off at 10pm").
#     5. If the repeat frequency is ambiguous ("do this repeatedly", "do this often") —
#        ask the user to clarify before creating the workflow.
#        Ask: "How often should this run? For example: every hour, every day at 6am, every 30 minutes."
#     6. Never assume a frequency — always confirm if unclear
#     """
#     create_scheduled_workflow(workflow)
#
#
# @mcp.tool
# def delete_Workflow(workflow_id : str):
#     """Use this flow when a user wants to delete a workflow or stop it"""
#     delete_workflow(workflow_id)


@mcp.tool
def create_a_real_time_task(asha_id: str, payload: dict):
    """
    Use this tool when a task requires real-time or sensor-driven logic — for example:
    "if I press this button, immediately turn on the fan", or "if the temperature sensor
    exceeds 40, trigger the alarm". If the task involves conditions, sensor thresholds,
    or must react without waiting for the agent, use this tool instead of publish_command.

    ALWAYS follow these steps in order — do NOT skip any step:
    1. Call get_user_projects_and_devices() to find the device's pin, bus type, and asha_id.
    2. Call get_tool_guide("create_a_real_time_task") to get the Lua syntax, asha.* function
       reference, monitoring patterns, debounce rules, and worked examples.
    3. Write the Lua script using the guide from step 2 and the pins from step 1.
    4. Call this tool with payload: {"action": "lua", "script": "<your lua script>"}.

    Never call this tool with an empty payload {} — the device will receive nothing and
    no script will run. Always get device info (step 1) and the Lua guide (step 2) first.

    CRITICAL, NO EXCEPTIONS: every `while` loop MUST call asha.sleep(ms) (10ms
    minimum) at least once per iteration. The ESP32's watchdog reboots the device
    if it doesn't get CPU time within ~5 seconds — a loop without asha.sleep()
    will always crash the device and can never be replaced remotely.

    If a real-time script is already running from earlier in this conversation,
    do NOT send a second independent script — the device only runs one at a time.
    Merge the new condition into the existing script and send one combined replacement.
    """
    publish_to_device(asha_id, payload)


@mcp.tool
async def asha_vision(payload: dict):
    """
    Start a server-side vision detection task that publishes detected class names
    to the device over MQTT. Call this BEFORE create_a_real_time_task when the user
    wants to react to something seen by a camera (person, animal, object, etc.).

    Always call get_user_projects_and_devices() first unless already called in
    this conversation. Never guess the asha_id.

    Payload: {"classes": [<lowercase class names>], "confidence": 0.65,
    "asha_topic": "asha/asha_vision/<asha_id>"}. This starts a vision model that
    publishes a detected class name to that topic whenever seen above the
    confidence threshold.

    ALWAYS a two-step flow: 1) call this tool with the classes payload, 2) call
    create_a_real_time_task with a Lua script that asha.subscribe()s to the same
    topic and reacts via asha.readMessage() (returns the class name, or "" if
    nothing detected yet).

    Call get_tool_guide("asha_vision") for the full payload spec, guidance on
    extracting class names from a user's request, and worked examples pairing
    this with a create_a_real_time_task script.
    """
    await post(url, payload)
