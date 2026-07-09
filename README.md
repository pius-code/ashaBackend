## this project is in the development phase and not ready for production yet

# Asha Backend

The backend for **Asha** — a framework that lets your hardware talk to AI.

Asha connects IoT devices and LLM via MQTT, exposing an MCP (Model Context Protocol) server so an AI agent can directly control and monitor your hardware through natural conversation.

---

## Prerequisites

Make sure you have [uv](https://docs.astral.sh/uv/) installed:

```bash
pip install uv
```

---

## Setup

1. Clone the repo and install dependencies:

```bash
uv sync
```

2. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

See the [Environment variables](#environment-variables) section below for all required values.

---

## Running

### Full server (REST API + MCP agent)

```bash
uv run main.py
```

Starts the FastAPI backend and MCP server together on port **8080**.

### MCP only

```bash
uv run mcp_main.py
```

Runs just the MCP agent without the REST API — useful for testing the agent standalone.

---

## What's inside

### REST API

JWT-protected endpoints for managing your Asha setup:

- `POST /register` / `POST /login` — user auth
- Project CRUD — group your devices into projects
- Device registration — register ESP32 devices with their pin/bus configuration

### MCP Agent (`agent/`)

The AI-facing side. LLM connects to the MCP server and gets access to tools for controlling your hardware:

| Tool                            | What it does                                                                                 |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| `get_user_projects_and_devices` | Lists all projects and connected devices with their pin/bus metadata                         |
| `publish_command`               | Sends a command to a device over MQTT (digital, PWM, stop_pwm, I2C, SPI, UART, batch, Lua)  |
| `create_a_real_time_task`       | Pushes a Lua script to the device for event-driven logic (button presses, sensor thresholds, publishing sensor data back) |
| `create_a_scheduled_workflow`   | Schedules a cron-based automation (e.g. turn on lights every day at 6am)                     |
| `delete_Workflow`               | Removes a scheduled workflow                                                                 |
| `fetch_device_ir_codes`         | Returns raw IR timing arrays for a vendor + command (Samsung TV, etc.)                       |
| `asha_vision`                   | Starts a server-side vision detection task that publishes detected class names over MQTT      |

The agent understands the full workflow: discover devices → determine what the user wants → construct the right payload → publish the command.

### Scheduled Workflows

Workflows are persisted in MongoDB via APScheduler, so they survive restarts. Cron format:

```
"0 6 * * *"     → every day at 6:00am
"0 22 * * *"    → every day at 10:00pm
"0 6 * * 1"     → every Monday at 6am
"*/5 * * * *"   → every 5 minutes
"0 */2 * * *"   → every 2 hours
"0 6 * * 1-5"   → every weekday at 6am
```

---

## Architecture

```
ESP32 Devices
     │
     │  MQTT (pub/sub)
     ▼
MQTT Broker
     │  asha/commands/<ashaID>   ← agent sends commands down
     │  asha/sensorData/<ashaID> ← device pushes sensor data up
     │
     ▼
Asha Backend (main.py)
  ├── FastAPI REST API      ← user/device/project management
  ├── MCP Server            ← agent connects here
  └── MQTT Subscriber       ← listens on asha/sensorData/+
        │ on message: lookup phone number by ashaID
        │ POST { phone, asha_id, sensor_data }
        ▼
  Frontend HTTP endpoint    ← triggers LLM with sensor context
        │
        ▼
  WhatsApp (user's phone)
```

### Sensor data flow

When a Lua script on the device calls `asha.publish("asha/sensorData/<ashaID>", value)`:

1. MQTT subscriber in `core/mqtt.py` receives the message
2. Extracts `ashaID` from the topic
3. Queries MongoDB for the `PhoneNumber` tied to that ashaID (`repository/projects.py`)
4. POSTs `{ phone, asha_id, sensor_data }` to the frontend sensor trigger endpoint
5. Frontend runs a lightweight LLM handler that injects the sensor data as a `[SENSOR]` user message, loads the user's conversation history from Redis, and replies via WhatsApp

**Note:** The `Project` model requires a `PhoneNumber` field — this is set when creating a project and is the WhatsApp number the backend uses to route sensor data back to the right user.

---

## Environment variables

| Variable                      | Description                                    |
| ----------------------------- | ---------------------------------------------- |
| `MONGO_URL`                   | MongoDB connection string                      |
| `JWT_SECRET_KEY`              | Secret for signing JWT tokens                  |
| `JWT_ALGORITHM`               | JWT algorithm (e.g. `HS256`)                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry duration                          |
| `FRONTEND_URL`                | CORS origin (default: `http://localhost:3000`) |
| `MQTT_IP`                     | MQTT broker IP address                         |
| `MQTT_PORT`                   | MQTT broker port (default: 1883)               |
| `ENV`                         | Set to `development` to enable Swagger docs    |

---

## TODOs

- [ ] Implement the frontend `/sensor-trigger` endpoint and lightweight LLM handler for device-originated messages
- [ ] Add a tool to let the agent schedule cron jobs that trigger the LLM itself (sampling support) — useful for the agent to reason periodically on its own without the user triggering it
