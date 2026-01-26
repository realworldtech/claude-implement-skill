# Sample Specification: User Notification System

This example demonstrates a well-structured specification document that works effectively with the `/implement` skill.

---

## 1. Overview

The notification system sends alerts to users based on system events. It supports multiple channels (email, SMS, push) and includes user preference management.

### 1.1 Scope
- In scope: Email, SMS, push notifications
- Out of scope: In-app notifications, webhooks

### 1.2 Key Actors
- **User**: Receives notifications, manages preferences
- **System**: Triggers notifications based on events
- **Admin**: Configures notification templates

---

## 2. Notification Triggers

### 2.1 Account Events
The system MUST send notifications for:
- Account creation (welcome email)
- Password reset request
- Password changed confirmation
- Email address change verification

**Input**: User event from authentication service
**Output**: Notification queued for delivery

### 2.2 Transaction Events
The system MUST notify users of:
- Payment received
- Payment failed
- Subscription renewal (7 days before)
- Subscription expired

**Input**: Transaction event from billing service
**Output**: Notification queued with transaction details

### 2.3 Alert Events
The system SHOULD notify users of:
- Security alert (new device login)
- Unusual activity detected
- API rate limit approaching

**Priority**: Security alerts are HIGH priority, others MEDIUM

---

## 3. Delivery Channels

### 3.1 Email Channel
- Use SMTP or SendGrid API
- Support HTML and plain text templates
- Include unsubscribe link in footer
- Track delivery status (sent, delivered, bounced, opened)

### 3.2 SMS Channel
- Use Twilio API
- Maximum 160 characters for single segment
- Include opt-out instructions
- Handle international numbers (E.164 format)

### 3.3 Push Channel
- Support iOS (APNs) and Android (FCM)
- Include action buttons where applicable
- Handle token expiration gracefully

---

## 4. User Preferences

### 4.1 Preference Model
Users can configure per-channel, per-category preferences:

```json
{
  "user_id": "uuid",
  "preferences": {
    "account_events": {
      "email": true,
      "sms": false,
      "push": true
    },
    "transaction_events": {
      "email": true,
      "sms": true,
      "push": false
    }
  }
}
```

### 4.2 Default Preferences
New users receive these defaults:
- Email: ON for all categories
- SMS: OFF (requires explicit opt-in)
- Push: ON if app installed

### 4.3 Mandatory Notifications
These notifications CANNOT be disabled:
- Security alerts
- Legal/compliance notifications
- Account suspension notices

---

## 5. Template System

### 5.1 Template Structure
Each notification type has a template with:
- Subject line (email only)
- Body content with variable placeholders
- Channel-specific variants

### 5.2 Variable Substitution
Support these variables:
- `{{user.name}}` - User's display name
- `{{user.email}}` - User's email address
- `{{event.type}}` - Event that triggered notification
- `{{event.timestamp}}` - When event occurred
- `{{action.url}}` - Call-to-action URL

### 5.3 Localization
- Store templates per locale (en-US, en-AU, etc.)
- Fall back to en-US if locale not available
- User's preferred locale stored in profile

---

## 6. Queue and Delivery

### 6.1 Queue Architecture
- Use Redis or RabbitMQ for queue
- Separate queues per priority (high, medium, low)
- High priority: process immediately
- Medium priority: process within 5 minutes
- Low priority: batch process hourly

### 6.2 Retry Logic
On delivery failure:
1. Retry after 1 minute
2. Retry after 5 minutes
3. Retry after 30 minutes
4. Mark as failed, alert admin

### 6.3 Rate Limiting
- Maximum 100 notifications per user per day
- Maximum 5 SMS per user per day
- Exempt security alerts from limits

---

## 7. Logging and Monitoring

### 7.1 Audit Log
Log all notification events:
- Notification ID, user ID, type, channel
- Timestamp queued, sent, delivered
- Delivery status and any error messages

### 7.2 Metrics
Track and expose:
- Notifications sent per channel per hour
- Delivery success rate by channel
- Average delivery latency
- Queue depth and processing time

### 7.3 Alerting
Alert operations team when:
- Delivery success rate drops below 95%
- Queue depth exceeds 10,000
- Any channel completely fails

---

## 8. API Endpoints

### 8.1 Send Notification
```
POST /api/v1/notifications
Authorization: Bearer <service-token>

{
  "user_id": "uuid",
  "type": "password_reset",
  "data": {
    "reset_url": "https://..."
  }
}
```

### 8.2 Get User Preferences
```
GET /api/v1/users/{user_id}/notification-preferences
Authorization: Bearer <user-token>
```

### 8.3 Update User Preferences
```
PATCH /api/v1/users/{user_id}/notification-preferences
Authorization: Bearer <user-token>

{
  "account_events": {
    "email": true,
    "sms": false
  }
}
```

---

## 9. Testing Requirements

### 9.1 Unit Tests
- Template variable substitution
- Preference evaluation logic
- Rate limit checking

### 9.2 Integration Tests
- End-to-end notification delivery (use test/sandbox modes)
- Preference changes reflected in delivery
- Queue retry behavior

### 9.3 Test Fixtures
Provide test mode that:
- Captures notifications instead of sending
- Returns predictable delivery statuses
- Allows inspection of queued notifications

---

## Key Points for Implementation

This spec demonstrates patterns that work well with `/implement`:

1. **Numbered sections** (§2.1, §3.2) - provide stable references
2. **Clear requirements** with MUST/SHOULD language
3. **Input/Output** specified where relevant
4. **Concrete examples** (JSON schemas, API formats)
5. **Testability criteria** included
6. **Scope boundaries** clearly stated

When implementing, each numbered section becomes a trackable unit of work.
