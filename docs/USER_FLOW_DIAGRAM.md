# User Flow Diagram

## Overview

This document maps the complete user journey through the OpenJustice platform — from registration to legal assistance via web chat, voice, and WhatsApp channels.

---

## 🔐 Authentication Flow

```mermaid
flowchart TD
    A["User visits /"] --> B{"Has Account?"}
    B -->|No| C["Navigate to /signup"]
    C --> D["Fill Registration Form"]
    D --> E["POST /api/auth/register"]
    E --> F["AuthService.register()"]
    F --> G["Create User + Hash Password"]
    G --> H["Generate JWT Token"]
    H --> I["Set httpOnly Cookie"]
    I --> J["Redirect to /chat"]

    B -->|Yes| K["Click Login on HomePage"]
    K --> L["Enter Email/Phone + Password"]
    L --> M["POST /api/auth/login"]
    M --> N["AuthService.login()"]
    N --> O["Verify Credentials"]
    O --> P["Generate JWT + Create Session"]
    P --> Q["Set httpOnly Cookie"]
    Q --> R["AuditLog: LOGIN event"]
    R --> J

    J --> S["Authenticated User Session"]

    style A fill:#1a1a2e,color:#e0e0ff
    style J fill:#0f3460,color:#e0e0ff
    style S fill:#16213e,color:#e0e0ff
```

---

## 💬 Web Chat Flow (Text)

The primary user interaction — ask a legal question and receive an AI-generated response with citations.

```mermaid
flowchart TD
    A["User on /chat page"] --> B["Create or Select Conversation"]
    B --> C{"New Conversation?"}
    C -->|Yes| D["POST /api/chats"]
    D --> E["ChatService.create_conversation()"]
    C -->|No| F["GET /api/chats/:id"]
    F --> G["Load Conversation + Messages"]
    E --> H["Chat Interface Ready"]
    G --> H

    H --> I["User types legal question"]
    I --> J["POST /api/chats/:id/messages/complete"]
    J --> K["AuthMiddleware validates JWT"]
    K --> L["RetrievalService.retrieve()"]
    L --> M["Embed query → pgvector similarity search"]
    M --> N["Return top-K document chunks"]
    N --> O["LLMService.stream_response()"]
    O --> P["PromptSecurityValidator.sanitize()"]
    P --> Q["LanguageDetectionService.detect_language()"]
    Q --> R["MultilingualPromptBuilder.build_system_prompt()"]
    R --> S["OpenAI GPT-4o-mini streaming call"]
    S --> T["StreamingResponse → Browser"]
    T --> U["Tokens rendered in real-time"]
    U --> V["Message saved to database"]
    V --> W["LLM telemetry logged"]

    style A fill:#1a1a2e,color:#e0e0ff
    style T fill:#0f3460,color:#e0e0ff
    style U fill:#16213e,color:#e0e0ff
```

---

## 🎤 Voice Chat Flow (Web)

Users can send voice notes through the web interface, receiving AI-generated audio responses.

```mermaid
flowchart TD
    A["User on /chat/:id page"] --> B["Click Voice Input Button"]
    B --> C["Record Audio in Browser"]
    C --> D["Upload: POST /api/chats/:id/messages/voice"]
    D --> E["TempFileManager.save_upload_file()"]
    E --> F["Copy to media/ via _persist_audio_file()"]

    F --> G["SpeechToTextService.transcribe_audio()"]
    G --> H["Whisper API: gpt-4o-mini-transcribe"]
    H --> I["Transcribed text query"]

    I --> J["RetrievalService.retrieve()"]
    J --> K["LLMService.generate_response()"]
    K --> L["AI response text"]

    L --> M["TextToSpeechService.synthesize_speech()"]
    M --> N["OpenAI TTS: gpt-4o-mini-tts, voice=alloy"]
    N --> O["Save .ogg to media/audio/"]
    O --> P["Save AI message with audio_path"]

    P --> Q["FileResponse: audio/ogg"]
    Q --> R["Browser plays voice response"]

    style A fill:#1a1a2e,color:#e0e0ff
    style Q fill:#0f3460,color:#e0e0ff
    style R fill:#16213e,color:#e0e0ff
```

---

## 📱 WhatsApp Flow (Twilio)

Users interact via WhatsApp — the system auto-provisions users and handles both text and voice notes.

```mermaid
flowchart TD
    A["User sends WhatsApp message"] --> B["Twilio forwards to POST /api/whatsapp/webhook"]
    B --> C["Return TwiML immediately"]
    B --> D["BackgroundTasks.add_task()"]

    D --> E["WhatsAppService.handle_incoming_message()"]
    E --> F["Strip 'whatsapp:' prefix from phone"]
    F --> G{"User exists?"}
    G -->|No| H["Auto-create User from phone number"]
    G -->|Yes| I["Load existing User"]
    H --> I

    I --> J{"Has MediaUrl0?"}
    J -->|Yes - Voice Note| K["TempFileManager.download_twilio_audio()"]
    K --> L["SpeechToTextService.transcribe_audio()"]
    L --> M["Log STT telemetry"]
    J -->|No - Text| N["Use Body as query"]
    M --> N

    N --> O["Get/create WhatsApp conversation"]
    O --> P["RetrievalService.retrieve()"]
    P --> Q["LLMService.generate_response()"]
    Q --> R{"Was voice input?"}

    R -->|Yes| S["TextToSpeechService.synthesize_speech()"]
    S --> T["Serve via /temp/ static mount"]
    T --> U["TwilioClient.send_message with media_url"]

    R -->|No| V["TwilioClient.send_message with text body"]

    U --> W["User receives voice reply on WhatsApp"]
    V --> W

    style A fill:#1a1a2e,color:#e0e0ff
    style C fill:#533483,color:#e0e0ff
    style W fill:#16213e,color:#e0e0ff
```

---

## 🔄 Conversation Management Flow

```mermaid
flowchart LR
    A["User"] --> B["GET /api/chats — List conversations"]
    A --> C["POST /api/chats — Create conversation"]
    A --> D["GET /api/chats/:id — View conversation"]
    A --> E["PATCH /api/chats/:id — Update title"]
    A --> F["PATCH /api/chats/:id/archive — Archive"]
    A --> G["PATCH /api/chats/:id/pin — Pin"]
    A --> H["DELETE /api/chats/:id — Delete"]

    style A fill:#1a1a2e,color:#e0e0ff
```

---

## ⚙️ User Settings & Profile Flow

```mermaid
flowchart TD
    A["User clicks profile/settings"] --> B{"Action?"}
    B -->|View Profile| C["GET /api/auth/me"]
    B -->|Update Profile| D["PATCH /api/auth/users/me"]
    D --> E["Update name, email, language, avatar"]
    B -->|Change Password| F["POST /api/auth/change-password"]
    F --> G["Verify current password → hash new password"]
    B -->|Logout| H["POST /api/auth/logout"]
    H --> I["Clear httpOnly cookie"]
    I --> J["AuditLog: LOGOUT event"]
    J --> K["Redirect to /"]

    style A fill:#1a1a2e,color:#e0e0ff
    style K fill:#16213e,color:#e0e0ff
```

---

## 🔍 WebSocket Real-Time Chat Flow

An alternative real-time channel using WebSocket for live token streaming.

```mermaid
flowchart TD
    A["User opens chat"] --> B["Connect: ws://host/api/ws/chat/:conversation_id?token=JWT"]
    B --> C["authenticate_websocket() — decode JWT"]
    C --> D{"Token valid?"}
    D -->|No| E["Close: WS_1008_POLICY_VIOLATION"]
    D -->|Yes| F["Verify conversation access"]
    F --> G["connection_manager.connect()"]
    G --> H["Send: connection_established"]

    H --> I["User sends chat_message"]
    I --> J["rate_limiter.is_allowed()"]
    J -->|Exceeded| K["Send: rate_limit_exceeded error"]
    J -->|Allowed| L["RetrievalService.retrieve()"]
    L --> M["LLMService.stream_response()"]
    M --> N["Send: chat_chunk tokens"]
    N --> O["Send: chat_completion"]

    I --> P["User sends ping"]
    P --> Q["Send: pong"]

    style A fill:#1a1a2e,color:#e0e0ff
    style H fill:#0f3460,color:#e0e0ff
    style O fill:#16213e,color:#e0e0ff
```

---

## 📊 Complete User Journey Map

```mermaid
flowchart TD
    START["User Arrives"] --> AUTH{"Authenticated?"}

    AUTH -->|No| REG["Register /signup"]
    AUTH -->|No| LOGIN["Login on HomePage"]
    REG --> COOKIE["JWT Cookie Set"]
    LOGIN --> COOKIE

    COOKIE --> MAIN{"Choose Channel"}

    MAIN --> WEB["Web Chat /chat"]
    MAIN --> WA["WhatsApp Message"]
    MAIN --> TOPICS["Browse Topics /topics"]
    MAIN --> RESEARCH["Research /research"]

    WEB --> TEXT["Type question"]
    WEB --> VOICE["Record voice note"]
    TEXT --> STREAM["StreamingResponse from LLM"]
    VOICE --> STT["Whisper STT → LLM → TTS"]

    WA --> TWILIO["Twilio Webhook"]
    TWILIO --> BGPROCESS["Background processing"]
    BGPROCESS --> REPLY["Reply via Twilio API"]

    STREAM --> DONE["View AI response with citations"]
    STT --> DONE
    REPLY --> DONE

    MAIN --> SETTINGS["Settings /settings"]
    SETTINGS --> PROFILE["Update Profile"]
    SETTINGS --> PASSWORD["Change Password"]
    SETTINGS --> LOGOUT["Logout"]

    style START fill:#1a1a2e,color:#e0e0ff
    style DONE fill:#0f3460,color:#e0e0ff
    style COOKIE fill:#533483,color:#e0e0ff
```

---

_Last updated: June 2026_
