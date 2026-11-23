# System design interview questions

## 1. Design a chatbot like ChatGPT

> Design a chatbot that supports multi-turn conversations, stores chat history, and streams responses. Walk through the high-level design and database schema. How would you handle context limits, concurrent messages, and interrupted responses?

I’d use a chat API to authenticate the user, verify conversation ownership, and persist the user message with a client-generated request ID. A generation service would build the prompt and call the model. The API would stream response chunks using server-sent events and save the assistant reply with a status such as generating, completed, or failed.

I’d store conversations and messages in separate tables and index messages by conversation ID and sequence number. I’d allow one active generation per conversation to keep message order predictable. For long chats, I’d fit recent messages and a summary of older turns into the model’s context window. A reconnecting client could fetch the current generation status, and a repeated request ID would return the existing generation. I’d cap concurrent generations per user and monitor time to first token, completion latency, and token usage.

## 2. Design a food delivery system

> Design a food delivery system where customers browse menus, place orders, and track deliveries. Walk through the high-level design and database schema. How would you handle payment failures, restaurant rejection, and two couriers accepting the same delivery?

I’d define components for restaurant and menu browsing, order management, payments, and courier dispatch. The order service would record the order and its item prices at checkout, then coordinate payment authorization, restaurant acceptance, and dispatch. I’d publish order state changes through a transactional outbox so tracking and notifications can update asynchronously.

I’d use a relational database for restaurants, menu items, orders, order items, payments, and deliveries. I’d index orders by customer and creation time and keep the latest courier location in a separate store suited to frequent updates. I’d enforce valid order state transitions, use idempotency keys for checkout and payment requests, and release the payment authorization if the restaurant rejects the order. Dispatch would assign the courier with an atomic update that succeeds only while the delivery is unassigned.

## 3. Design a centralized logging service

> How would you design a centralized logging system for an application with multiple microservices? How would you follow a single request across services, including asynchronous jobs, and handle traffic spikes or a log storage outage?

I’d emit structured logs with a timestamp, severity, service name, environment, and a request or trace ID. I’d propagate that ID through HTTP calls and message headers so engineers can search for events from the same request. I’d redact secrets and sensitive fields before logs leave the service.

I’d use collectors to batch and forward logs to a searchable store. Bounded buffering would let collectors absorb short spikes and outages without blocking application requests. If buffers fill, I’d prioritize error logs, track dropped entries, and alert on forwarding lag. I’d set retention and access policies based on how the logs are used.

## 4. Design a notification service

> How would you design a notification service that accepts requests from multiple services and delivers email, SMS, and push notifications? How would you handle user preferences, traffic spikes, provider failures, and duplicate requests?

I’d accept requests with an idempotency key, persist each notification, and use a transactional outbox to queue it for delivery. Channel-specific workers would apply user preferences and provider rate limits, then record status per channel. Separate queues would let each channel scale independently.

I’d retry transient failures with bounded exponential backoff and route exhausted retries to a dead-letter queue. I’d use provider idempotency keys where supported and reconcile ambiguous timeouts before resending when possible. I’d use provider callbacks to track delivery and monitor queue age, failure rates, and delivery latency.
