"""all the tools that ASHA needs to run for now, use depends to get user id without the LLM having to ask for it, runs beofr etools are even understood by LLM, hidden """

from agent.core.fastmcp import mcp
from fastmcp.dependencies import Depends
from agent.tools.devices_tools import get_asha_user_projects_and_devices
from agent.tools.pubSub_tools import publish_to_device
from agent.tools.scheduler import create_scheduled_workflow
from agent.schema.workflow import Workflow


def get_user_id() -> str:
    return "69e9de328ab270d2e2416395"


@mcp.tool
async def get_user_projects_and_devices():
    """Returns all a users projects and the devices including devices information that the user has"""
    return await get_asha_user_projects_and_devices()


@mcp.tool
async def publish_command(asha_id: str, payload: dict):
    """
    Publishes a command to an ESP32 device via MQTT.
    Use the device's bus type to determine the correct payload structure.

    ALWAYS get device info from get_user_projects_and_devices() first.
    Use the pin, bus, and channel from that response to build the payload.

    ──────────────────────────────────────────
    BUS TYPE REFERENCE
    ──────────────────────────────────────────

    DIGITAL (bus: "Digital")
    Use for: relays, simple LEDs, door locks, buzzers, motion sensors
    Payload:
        {"pin": <pin>, "action": "digital", "value": <0 or 1>}
    Examples:
        Turn ON  → {"pin": 18, "action": "digital", "value": 1}
        Turn OFF → {"pin": 18, "action": "digital", "value": 0}
        Read     → {"pin": 18, "action": "digital", "value": -1}

    ──────────────────────────────────────────

    PWM (bus: "PWM")
    Use for: servos, DC motors, LED dimming, fans, buzzers
    Payload:
        {"pin": <pin>, "action": "pwm", "channel": <0-15>, "freq": <hz>, "duty": <0-65535>}

    Frequency and duty by device type:
        LED/Backlight dimming → freq: 5000,  duty: 0 (off) to 65535 (full brightness)
        DC Motor speed        → freq: 1000,  duty: 0 (stop) to 65535 (full speed)
        Servo position        → freq: 50,    duty: 3277 (0°) | 4915 (90°) | 6553 (180°)
        Buzzer tone (440Hz A) → freq: 440,   duty: 128 (on) | 0 (off)
        Fan speed             → freq: 1000,  duty: 0 (off) to 65535 (full speed)

    Channel: assign 0-15, one per device. Never reuse a channel for two devices.

    Examples:
        LED at 50% brightness → {"pin": 18, "action": "pwm", "channel": 0, "freq": 5000, "duty": 32767}
        Servo at 90°          → {"pin": 19, "action": "pwm", "channel": 1, "freq": 50,   "duty": 4915}
        Motor at full speed   → {"pin": 21, "action": "pwm", "channel": 2, "freq": 1000, "duty": 65535}
        Buzzer ON             → {"pin": 22, "action": "pwm", "channel": 3, "freq": 440,  "duty": 128}

    ──────────────────────────────────────────

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

    SPI WRITE (bus: "SPI")
    Use for: TFT displays, SD cards, fast ADC chips
    Payload:
        {"action": "spi_write", "cs_pin": <pin>, "speed": <hz>, "mode": <0-3>, "data": [<bytes>]}

    Note: SPI does NOT use a pin field. Uses cs_pin to target the device.
    MOSI=GPIO23, MISO=GPIO19, CLK=GPIO18 are fixed. Only cs_pin changes per device.

    Speed by device:
        SD card      → speed: 25000000 (25MHz)
        TFT display  → speed: 40000000 (40MHz)
        Slow devices → speed: 1000000  (1MHz)

    Mode is almost always 0. Check datasheet if device behaves unexpectedly.

    Example:
        Write to SD card → {"action": "spi_write", "cs_pin": 5, "speed": 25000000, "mode": 0, "data": [1, 2, 3]}

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
                {"pin": 18, "action": "pwm", "channel": 0, "freq": 5000, "duty": 65535},
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

    ──────────────────────────────────────────

    RULES:
    1. Always match payload structure to bus type exactly
    2. Never guess a pin — always use the pin from get_user_projects_and_devices()
    3. For PWM, never reuse a channel already assigned to another device. Never send a freq_hz=0 minimum should be 1.
    4. For I2C and SPI, never include a pin field
    5. When user says "turn on" a PWM LED, use duty: 65535. "Turn off" use duty: 0
    6. When user says "turn on" a Digital device, use value: 1. "Turn off" use value: 0
    7. When user wants to control multiple devices at once, always use batch
    8. When user wants a timed sequence (e.g. "turn on for 5 seconds"), use batch with delay_ms
    """
    publish_to_device(asha_id, payload)
    return {"status": "command sent", "asha_id": asha_id, "payload": payload}


@mcp.tool
def create_a_scheduled_workflow(workflow: Workflow):
    """
    Use this tool when the user wants to automate a repeated or time-based task.

    WHEN TO USE:
    - "Turn on the light at 6am every day"
    - "Turn off the fan every 30 minutes"
    - "Every Friday at 9pm turn off all devices"
    - Any request involving "every", "at [time]", "schedule", "automatically"

    DO NOT USE for one-time commands — use publish_command instead.

    BEFORE CALLING THIS TOOL:
    Always call get_user_projects_and_devices() first to get the correct asha_id and device pins unless it has already been called and exists in context.

    WORKFLOW_ID FORMAT:
    Combine a short description with random alphanumeric characters.
    Example: "morning_light_9x2k", "fan_schedule_b3m7"

    CRON EXPRESSION FORMAT:
    "minute hour day month day_of_week"
    Examples:
        Every day at 6am          → "0 6 * * *"
        Every day at 10pm         → "0 22 * * *"
        Every 30 minutes          → "*/30 * * * *"
        Every Friday at 9pm       → "0 21 * * 5"
        Every weekday at 8am      → "0 8 * * 1-5"
        Every hour                → "0 * * * *"

    ACTIONS FORMAT:
    List of MQTT payloads following the same bus rules as publish_command.
    Examples:
        [{"pin": 18, "action": "digital", "value": 1}]
        [{"pin": 18, "action": "digital", "value": 1}, {"pin": 19, "action": "digital", "value": 0}]
        [{"pin": 18, "action": "pwm", "channel": 0, "freq": 5000, "duty": 65535}]

    RULES:
    1. Always use pins from get_user_projects_and_devices() — never guess
    2. Generate a unique workflow_id every time
    3. Match action payload structure to the device bus type exactly
    4. If user says "turn on at X and off at Y" — create TWO separate workflows
    5. If the repeat frequency is ambiguous ("do this repeatedly", "do this often") — 
       ask the user to clarify before creating the workflow. 
       Ask: "How often should this run? For example: every hour, every day at 6am, every 30 minutes."
    6. Never assume a frequency — always confirm if unclear
    """
    create_scheduled_workflow(workflow)
