# Real-Time Notifications Architecture for a REST API + React Application

## Recommended Approach: WebSockets via Socket.IO

For a REST API backend with a React frontend, the best architecture for real-time notifications is a **WebSocket layer alongside your existing REST API**, using Socket.IO (or native WebSockets) for the persistent connection and a pub/sub message broker to coordinate across server instances.

---

## High-Level Architecture

```
+-------------------+       +---------------------+       +------------------+
|   React Frontend  | <---> |   Backend Server    | <---> |   Database       |
|   (Socket.IO      |  WS   |   (REST API +       |       |   (PostgreSQL/   |
|    client)         |       |    Socket.IO server)|       |    MongoDB)      |
+-------------------+       +---------------------+       +------------------+
                                      |
                                      v
                             +------------------+
                             |   Redis Pub/Sub  |
                             |   (message broker)|
                             +------------------+
```

### How it works:

1. **User action occurs** (e.g., someone comments on a task or assigns a user).
2. **REST API handler** processes the request, writes to the database, then **publishes a notification event** to Redis.
3. **Socket.IO server** subscribes to Redis channels and **pushes the notification** to the relevant connected client(s) in real time.
4. **React frontend** receives the event via its Socket.IO connection and updates the UI.

---

## Why WebSockets (Socket.IO) Over Alternatives

| Approach | Pros | Cons |
|---|---|---|
| **WebSockets / Socket.IO** | True real-time, bidirectional, low latency, wide ecosystem support | Requires persistent connections, slightly more infra complexity |
| **Server-Sent Events (SSE)** | Simple, works over HTTP, no special library needed | Unidirectional only, limited browser connection pool (6 per domain), less ecosystem tooling |
| **Long Polling** | Works everywhere, no special server support | High latency, wastes resources, not truly real-time |
| **Polling** | Simplest to implement | Wasteful, high latency, does not scale |

**Socket.IO is the recommendation** because it provides automatic reconnection, room/namespace support (critical for routing notifications to specific users), fallback transports, and a mature ecosystem for both Node.js and React.

If your backend is not Node.js (e.g., Python, Go, Java), native WebSocket libraries work well too. Socket.IO has server implementations in Python, Java, and Go as well.

---

## Backend Architecture

### 1. Notification Service Layer

Create a dedicated notification service that sits between your business logic and the transport layer:

```
src/
  services/
    notificationService.ts    # Core notification logic
  events/
    eventTypes.ts             # Notification event type definitions
  websocket/
    socketServer.ts           # Socket.IO server setup
    socketHandlers.ts         # Connection/disconnection handlers
    middleware.ts             # Auth middleware for WS connections
  models/
    notification.ts           # Notification DB model (for persistence)
  routes/
    notifications.ts          # REST endpoints for notification history
```

### 2. Notification Event Types

Define clear event types for your domain:

```typescript
enum NotificationEvent {
  TASK_COMMENT_ADDED = "task:comment:added",
  TASK_ASSIGNED = "task:assigned",
  TASK_STATUS_CHANGED = "task:status:changed",
  TASK_DUE_DATE_APPROACHING = "task:due:approaching",
  MENTION_IN_COMMENT = "comment:mention",
}

interface NotificationPayload {
  id: string;
  type: NotificationEvent;
  recipientUserId: string;
  actorUserId: string;
  entityType: "task" | "comment" | "project";
  entityId: string;
  message: string;
  metadata: Record<string, unknown>;
  read: boolean;
  createdAt: string;
}
```

### 3. Notification Flow in Business Logic

When a mutation occurs in your REST API, the handler emits a notification:

```typescript
// In your task comment controller
async function addComment(req, res) {
  const comment = await commentService.create(req.body);

  // Persist the notification
  const notification = await notificationService.create({
    type: NotificationEvent.TASK_COMMENT_ADDED,
    recipientUserId: task.assigneeId,
    actorUserId: req.user.id,
    entityType: "task",
    entityId: task.id,
    message: `${req.user.name} commented on "${task.title}"`,
  });

  // Emit in real-time
  notificationService.emit(notification);

  res.json(comment);
}
```

### 4. Socket.IO Server Setup

```typescript
// socketServer.ts
import { Server } from "socket.io";
import { createAdapter } from "@socket.io/redis-adapter";
import { createClient } from "redis";

export async function setupSocketServer(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: process.env.FRONTEND_URL },
  });

  // Redis adapter for horizontal scaling
  const pubClient = createClient({ url: process.env.REDIS_URL });
  const subClient = pubClient.duplicate();
  await Promise.all([pubClient.connect(), subClient.connect()]);
  io.adapter(createAdapter(pubClient, subClient));

  // Auth middleware - validate JWT on connection
  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    try {
      const user = verifyJwt(token);
      socket.data.userId = user.id;
      next();
    } catch {
      next(new Error("Authentication failed"));
    }
  });

  // On connection, join user to their personal room
  io.on("connection", (socket) => {
    const userId = socket.data.userId;
    socket.join(`user:${userId}`);

    socket.on("notification:read", async (notificationId) => {
      await notificationService.markAsRead(notificationId, userId);
    });

    socket.on("disconnect", () => {
      // Cleanup if needed
    });
  });

  return io;
}
```

### 5. Emitting Notifications

```typescript
// notificationService.ts
class NotificationService {
  constructor(private io: Server, private db: Database) {}

  async emit(notification: NotificationPayload) {
    // Send to the specific user's room
    this.io
      .to(`user:${notification.recipientUserId}`)
      .emit("notification:new", notification);
  }
}
```

---

## Frontend Architecture

### 1. Socket Context Provider

```typescript
// NotificationProvider.tsx
import { createContext, useContext, useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";

const SocketContext = createContext<Socket | null>(null);

export function NotificationProvider({ children }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (!token) return;

    const newSocket = io(process.env.REACT_APP_WS_URL, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
    });

    setSocket(newSocket);
    return () => { newSocket.close(); };
  }, [token]);

  return (
    <SocketContext.Provider value={socket}>
      {children}
    </SocketContext.Provider>
  );
}
```

### 2. Notification Hook

```typescript
// useNotifications.ts
export function useNotifications() {
  const socket = useContext(SocketContext);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Load existing notifications via REST on mount
    fetch("/api/notifications")
      .then((res) => res.json())
      .then((data) => {
        setNotifications(data.notifications);
        setUnreadCount(data.unreadCount);
      });
  }, []);

  useEffect(() => {
    if (!socket) return;

    socket.on("notification:new", (notification) => {
      setNotifications((prev) => [notification, ...prev]);
      setUnreadCount((prev) => prev + 1);

      // Optional: show browser notification
      if (Notification.permission === "granted") {
        new Notification(notification.message);
      }
    });

    return () => { socket.off("notification:new"); };
  }, [socket]);

  const markAsRead = (id: string) => {
    socket?.emit("notification:read", id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  };

  return { notifications, unreadCount, markAsRead };
}
```

### 3. Notification Bell Component

```typescript
function NotificationBell() {
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setOpen(!open)}>
        Bell {unreadCount > 0 && <span>{unreadCount}</span>}
      </button>
      {open && (
        <NotificationDropdown
          notifications={notifications}
          onRead={markAsRead}
        />
      )}
    </div>
  );
}
```

---

## Persistence and Reliability

Real-time delivery is not guaranteed (users may be offline). You need both:

1. **Persistent storage**: Save every notification to a `notifications` table so users can see missed notifications when they come back online.
2. **Real-time push**: Emit via WebSocket for instant delivery to connected users.
3. **REST fallback**: Provide `GET /api/notifications` for loading history and `PATCH /api/notifications/:id/read` for marking as read.

### Database Schema

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient_user_id UUID NOT NULL REFERENCES users(id),
  actor_user_id UUID REFERENCES users(id),
  type VARCHAR(50) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id UUID NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  INDEX idx_notifications_recipient (recipient_user_id, created_at DESC),
  INDEX idx_notifications_unread (recipient_user_id, read) WHERE read = FALSE
);
```

---

## Scaling Considerations

### Single Server
- Socket.IO with in-memory adapter works fine up to a few thousand concurrent connections.

### Multiple Server Instances
- Use the **Redis adapter** for Socket.IO so events are broadcast across all instances.
- Each server instance connects to the same Redis pub/sub channels.
- This is critical if you run behind a load balancer.

### Large Scale (10K+ concurrent users)
- Consider a dedicated notification microservice separate from your REST API.
- Use a message queue (RabbitMQ, AWS SQS, or Kafka) between the REST API and notification service for decoupling and reliability.
- Implement notification batching/throttling to avoid overwhelming users.
- Consider using a managed service like AWS AppSync, Pusher, or Ably if you do not want to manage WebSocket infrastructure.

```
+----------+     +----------+     +-----------+     +-------------+
| REST API | --> | Message  | --> | Notif.    | --> | Socket.IO   |
|          |     | Queue    |     | Service   |     | (to clients)|
+----------+     +----------+     +-----------+     +-------------+
```

---

## Summary of Recommendations

| Decision | Recommendation |
|---|---|
| **Transport** | WebSockets via Socket.IO |
| **Message broker** | Redis Pub/Sub (for multi-instance) |
| **Persistence** | Store all notifications in the database |
| **Auth** | Validate JWT on WebSocket handshake |
| **Frontend state** | React Context + custom hook |
| **Scaling** | Redis adapter; message queue at large scale |
| **Fallback** | REST endpoints for notification history |

This architecture keeps your existing REST API intact, layers WebSocket support alongside it, and gives you a clean path to scale from hundreds to tens of thousands of concurrent users.
