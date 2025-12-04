# 💝 Donate Now - Serverless Donation Platform

A secure, scalable donation platform built with **FastAPI**, **AWS SAM**, **Stripe**, and modern serverless architecture.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [System Flow](#-system-flow)
- [AWS Infrastructure](#-aws-infrastructure)
- [API Endpoints](#-api-endpoints)
- [Data Model](#-data-model)
- [Configuration](#%EF%B8%8F-configuration)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND                                          │
│                              (Next.js Application)                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AWS API GATEWAY                                         │
│                     (REST API with Cognito Authorizer)                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │  Public Endpoints:          │  Protected Endpoints:                          │  │
│  │  • /donations/recent        │  • /donations/create-intent (requires auth)   │  │
│  │  • /donations/total         │                                                │  │
│  │  • /webhooks/stripe         │                                                │  │
│  │  • /docs, /openapi.json     │                                                │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              API LAMBDA FUNCTION                                     │
│                           (FastAPI + Mangum Adapter)                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                           DonationService                                      │ │
│  │  • Creates Stripe PaymentIntent                                               │ │
│  │  • Stores pending donations in DynamoDB                                       │ │
│  │  • Validates & queues Stripe webhooks                                         │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
           │                            │                             │
           ▼                            ▼                             ▼
┌───────────────────┐      ┌───────────────────────┐      ┌────────────────────────┐
│   STRIPE API      │      │    DYNAMODB TABLE     │      │   PAYMENT QUEUE (SQS)  │
│                   │      │                       │      │                        │
│ • Create intents  │      │ • User profiles       │      │ • Webhook events       │
│ • Process payments│      │ • Donation records    │      │ • Async processing     │
│ • Send webhooks   │      │ • Aggregated totals   │      │ • Dead-letter queue    │
└───────────────────┘      └───────────────────────┘      └────────────────────────┘
                                                                      │
                                                                      ▼
                                                         ┌────────────────────────┐
                                                         │  PAYMENT WORKER        │
                                                         │  (Lambda Function)     │
                                                         │                        │
                                                         │ • Process payment      │
                                                         │   success/failure      │
                                                         │ • Update DynamoDB      │
                                                         │ • Queue notifications  │
                                                         └────────────────────────┘
                                                                      │
                                                                      ▼
                                                         ┌────────────────────────┐
                                                         │  NOTIFICATION QUEUE    │
                                                         │  (SQS)                 │
                                                         │                        │
                                                         │ • Email jobs           │
                                                         │ • Dead-letter queue    │
                                                         └────────────────────────┘
                                                                      │
                                                                      ▼
                                                         ┌────────────────────────┐
                                                         │  NOTIFICATION WORKER   │
                                                         │  (Lambda Function)     │
                                                         │                        │
                                                         │ • Send receipt emails  │
                                                         │ • AWS SES integration  │
                                                         └────────────────────────┘
                                                                      │
                                                                      ▼
                                                         ┌────────────────────────┐
                                                         │     AWS SES            │
                                                         │  (Simple Email Svc)    │
                                                         │                        │
                                                         │ • Donation receipts    │
                                                         │ • Thank you emails     │
                                                         └────────────────────────┘
```

---

## 🔄 System Flow

### 1️⃣ Donation Flow (Happy Path)

```
User Action                    Backend Process                         Result
─────────────────────────────────────────────────────────────────────────────────────

    ┌─────────────┐
    │ User logs   │ ──── Cognito JWT Token ──── ▶ Identity verified
    │ in via      │
    │ Cognito     │
    └─────────────┘
          │
          ▼
    ┌─────────────┐
    │ User clicks │     POST /donations/create-intent
    │ "Donate"    │ ──────────────────────────────────────────────────────────────┐
    │ ($50)       │                                                               │
    └─────────────┘                                                               │
                                                                                  ▼
                        ┌──────────────────────────────────────────────────────────────┐
                        │                    API Lambda                                 │
                        │  1. Extract user info from Cognito JWT                       │
                        │  2. Create/update UserProfile in DynamoDB                    │
                        │  3. Create Donation record (status: PENDING)                 │
                        │  4. Call Stripe → Create PaymentIntent                       │
                        │  5. Return client_secret to frontend                         │
                        └──────────────────────────────────────────────────────────────┘
                                                                                  │
          ┌───────────────────────────────────────────────────────────────────────┘
          ▼
    ┌─────────────┐
    │ Stripe.js   │ ──── User enters card details ──── ▶ Payment submitted
    │ Payment     │
    │ Element     │
    └─────────────┘
          │
          ▼
    ┌─────────────┐     POST /webhooks/stripe (from Stripe servers)
    │   Stripe    │ ──────────────────────────────────────────────────────────────┐
    │  Webhook    │     Event: payment_intent.succeeded                           │
    │             │                                                               │
    └─────────────┘                                                               │
                                                                                  ▼
                        ┌──────────────────────────────────────────────────────────────┐
                        │                    API Lambda                                 │
                        │  1. Verify Stripe webhook signature                          │
                        │  2. Queue event to Payment SQS                               │
                        │  3. Return 200 OK immediately (fast response)                │
                        └──────────────────────────────────────────────────────────────┘
                                                                                  │
                                                                                  ▼
                        ┌──────────────────────────────────────────────────────────────┐
                        │                 Payment Worker Lambda                         │
                        │  (Triggered by SQS)                                          │
                        │  1. Parse payment event                                      │
                        │  2. Update Donation status → SUCCEEDED                       │
                        │  3. Increment total donations counter (atomic)               │
                        │  4. Queue notification job to Notification SQS               │
                        └──────────────────────────────────────────────────────────────┘
                                                                                  │
                                                                                  ▼
                        ┌──────────────────────────────────────────────────────────────┐
                        │              Notification Worker Lambda                       │
                        │  (Triggered by SQS)                                          │
                        │  1. Parse notification job                                   │
                        │  2. Format email content                                     │
                        │  3. Send via AWS SES                                         │
                        └──────────────────────────────────────────────────────────────┘
                                                                                  │
          ┌───────────────────────────────────────────────────────────────────────┘
          ▼
    ┌─────────────┐
    │   User      │
    │  receives   │
    │  receipt    │
    │   email     │
    └─────────────┘
```

### 2️⃣ Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Async webhook processing** | Stripe expects fast webhook responses (<5s). Queuing to SQS ensures reliability. |
| **Idempotent status updates** | Conditional DynamoDB updates prevent duplicate processing of the same webhook. |
| **Dead-letter queues** | Failed messages (after 5 retries) are preserved for debugging. |
| **Single-table DynamoDB design** | Efficient access patterns, cost-effective, scales automatically. |
| **SSM Parameter Store for secrets** | Stripe keys are securely stored and fetched at runtime. |

---

## ☁ AWS Infrastructure

### Services Used

| Service | Purpose |
|---------|---------|
| **API Gateway** | REST API with Cognito authorizer for protected routes |
| **Lambda** | 3 functions: API handler, Payment worker, Notification worker |
| **DynamoDB** | Single table storing users, donations, and aggregated totals |
| **SQS** | 2 queues with DLQs for payment processing and notifications |
| **Cognito** | User pool for authentication (email + password) |
| **SES** | Sending donation receipt emails |
| **SSM Parameter Store** | Secure storage for Stripe API keys |

### Resource Diagram

```
                           ┌─────────────────────────┐
                           │    Cognito User Pool    │
                           │  ┌───────────────────┐  │
                           │  │ User Pool Client  │  │
                           │  │ (WebAppClient)    │  │
                           │  └───────────────────┘  │
                           └───────────┬─────────────┘
                                       │ Authorizes
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                   API Gateway                                         │
│                                  (REST - Prod)                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │     ApiFunction       │
                           │   (FastAPI Lambda)    │
                           └───────────┬───────────┘
                                       │
           ┌───────────────────────────┼────────────────────────────┐
           ▼                           ▼                            ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│   DynamoDB Table  │       │   PaymentQueue    │       │ NotificationQueue │
│ (DonationsPlatform│       │      (SQS)        │       │      (SQS)        │
│      Table)       │       │ ┌───────────────┐ │       │ ┌───────────────┐ │
│                   │       │ │     DLQ       │ │       │ │     DLQ       │ │
│ GSI: RecentDon-   │       │ │ (14d retain)  │ │       │ │ (14d retain)  │ │
│      ationsIndex  │       │ └───────────────┘ │       │ └───────────────┘ │
└───────────────────┘       └─────────┬─────────┘       └─────────┬─────────┘
                                      │ Triggers                   │ Triggers
                                      ▼                            ▼
                           ┌───────────────────┐       ┌───────────────────┐
                           │  PaymentWorker    │       │NotificationWorker │
                           │    (Lambda)       │──────▶│    (Lambda)       │
                           └───────────────────┘       └─────────┬─────────┘
                                                                 │
                                                                 ▼
                                                      ┌───────────────────┐
                                                      │     AWS SES       │
                                                      │ (Email Service)   │
                                                      └───────────────────┘
```

---

## 📡 API Endpoints

### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check / welcome message |
| `GET` | `/donations/recent` | List 10 most recent successful donations |
| `GET` | `/donations/total` | Get total donation amount (in dollars) |
| `POST` | `/webhooks/stripe` | Stripe webhook receiver |
| `GET` | `/docs` | FastAPI Swagger documentation |
| `GET` | `/openapi.json` | OpenAPI specification |

### Protected Endpoints (Cognito JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/donations/create-intent` | Create a Stripe PaymentIntent |

### Request/Response Examples

#### Create Donation Intent
```bash
POST /donations/create-intent
Authorization: Bearer <cognito_jwt_token>
Content-Type: application/json

{
    "amount": 5000  # Amount in cents ($50.00)
}
```

**Response:**
```json
{
    "client_secret": "pi_3xyz_secret_abc123"
}
```

#### Get Recent Donations
```bash
GET /donations/recent
```

**Response:**
```json
[
    {
        "donor_name": "John Doe",
        "amount": 5000,
        "currency": "usd",
        "created_at": "2024-01-15T10:30:00"
    },
    {
        "donor_name": "Anonymous",
        "amount": 2500,
        "currency": "usd",
        "created_at": "2024-01-14T15:45:00"
    }
]
```

#### Get Total Donations
```bash
GET /donations/total
```

**Response:**
```json
{
    "total_amount_dollars": 1250.50
}
```

---

## 📊 Data Model

### DynamoDB Single-Table Design

The application uses a **single-table design** with composite primary keys (`PK`, `SK`).

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                           DonationsPlatformTable                                      │
├────────────────────────┬────────────────────────┬────────────────────────────────────┤
│          PK            │          SK            │           Attributes               │
├────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ USER#john@email.com    │ PROFILE                │ email, name, user_id, created_at   │
├────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ USER#john@email.com    │ DONATION#uuid-1234     │ amount, status, currency,          │
│                        │                        │ stripe_payment_intent_id,          │
│                        │                        │ donor_name, created_at             │
├────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ TOTALS                 │ DONATION_SUM           │ TotalAmountCents                   │
└────────────────────────┴────────────────────────┴────────────────────────────────────┘
```

### Global Secondary Index (GSI)

**RecentDonationsIndex** - For querying recent successful donations:

| Hash Key | Sort Key | Projection |
|----------|----------|------------|
| `status` | `created_at` | ALL |

### Access Patterns

| Pattern | Key Condition |
|---------|---------------|
| Get user profile | `PK = USER#email`, `SK = PROFILE` |
| Get user's donations | `PK = USER#email`, `SK begins_with DONATION#` |
| Get recent donations | GSI: `status = SUCCEEDED`, sorted by `created_at` DESC |
| Get/Update totals | `PK = TOTALS`, `SK = DONATION_SUM` |

---

## ⚙️ Configuration

### Environment Variables

Set via **SAM template** (injected into Lambda):

| Variable | Description |
|----------|-------------|
| `DYNAMO_TABLE_NAME` | DynamoDB table name |
| `PAYMENT_QUEUE_URL` | SQS URL for payment processing |
| `NOTIFICATION_QUEUE_URL` | SQS URL for notifications |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID |
| `COGNITO_USER_POOL_CLIENT_ID` | Cognito App Client ID |
| `SES_FROM_EMAIL` | Verified sender email for SES |

### Secrets (SSM Parameter Store)

Store these as **SecureString** parameters:

```
/donate-now/STRIPE_SECRET_KEY       # Stripe secret API key
/donate-now/STRIPE_WEBHOOK_SECRET   # Stripe webhook signing secret
```

---

## 🚀 Deployment

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **AWS SAM CLI** installed
3. **Python 3.11** installed
4. **Stripe account** with API keys

### Deploy Steps

```bash
# 1. Navigate to project directory
cd donate-now

# 2. Build the SAM application
sam build

# 3. Deploy (first time - guided)
sam deploy --guided

# 4. Subsequent deployments
sam deploy
```

### Post-Deployment Setup

1. **Set Stripe secrets in SSM:**
```bash
aws ssm put-parameter \
    --name "/donate-now/STRIPE_SECRET_KEY" \
    --value "sk_live_xxx" \
    --type SecureString

aws ssm put-parameter \
    --name "/donate-now/STRIPE_WEBHOOK_SECRET" \
    --value "whsec_xxx" \
    --type SecureString
```

2. **Configure Stripe webhook** pointing to:
   ```
   https://<api-id>.execute-api.<region>.amazonaws.com/Prod/webhooks/stripe
   ```

3. **Verify SES sender email** (or request production access)

---

## 📁 Project Structure

```
donate-now/
├── src/
│   ├── api/
│   │   ├── main.py           # FastAPI app & Mangum handler
│   │   ├── routers.py        # API route definitions
│   │   └── schemas.py        # Pydantic request/response models
│   │
│   ├── core/
│   │   ├── config.py         # Settings (env vars + SSM)
│   │   ├── dependencies.py   # Dependency injection setup
│   │   └── logging_config.py # Logging configuration
│   │
│   ├── data_access/
│   │   └── dynamodb.py       # DynamoDB data access layer
│   │
│   ├── models/
│   │   └── donation.py       # Domain models (Donation, UserProfile)
│   │
│   ├── services/
│   │   ├── donation_service.py     # Core donation logic
│   │   └── notification_service.py # Email sending logic
│   │
│   └── workers/
│       ├── payment_worker.py       # SQS payment event processor
│       └── notification_worker.py  # SQS notification processor
│
├── template.yaml             # AWS SAM infrastructure definition
├── samconfig.toml           # SAM deployment configuration
└── requirements/
    └── requirements.txt     # Python dependencies
```

---

## 🔒 Security Features

- **Cognito JWT authentication** for protected endpoints
- **Stripe webhook signature verification** prevents spoofed events
- **SSM Parameter Store** for secure secret management
- **IAM least-privilege policies** for Lambda functions
- **Idempotent processing** prevents duplicate charges
- **Dead-letter queues** capture failed messages for analysis

---

## 📈 Scalability

- **Serverless architecture** - automatically scales with demand
- **DynamoDB on-demand billing** - no capacity planning needed
- **SQS decoupling** - API responds fast, heavy work is async
- **Lambda concurrency** - parallel processing of webhooks

---

## 📄 License

MIT License - Feel free to use this as a starting point for your own donation platform!

---

Built with ❤️ using AWS Serverless

