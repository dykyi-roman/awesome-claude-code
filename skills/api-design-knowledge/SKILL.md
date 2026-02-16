---
name: acc-api-design-knowledge
description: API Design knowledge base. Provides REST constraints, Richardson Maturity Model, HTTP semantics, content negotiation, and GraphQL/gRPC comparison for API audits and generation.
---

# API Design Knowledge Base

Quick reference for API design patterns, REST best practices, and PHP implementation guidelines.

## Core Principles

### REST Constraints

| Constraint | Description | Implication |
|-----------|-------------|-------------|
| Client-Server | Separation of concerns | Independent evolution |
| Stateless | No server-side session state | Each request contains all info |
| Cacheable | Responses declare cacheability | Reduces server load |
| Uniform Interface | Standard resource operations | Predictable API surface |
| Layered System | Client can't tell if connected directly | Proxy, gateway, CDN support |
| Code on Demand (optional) | Server can send executable code | Rarely used in APIs |

### Richardson Maturity Model

| Level | Name | Description | Example |
|-------|------|-------------|---------|
| 0 | Swamp of POX | Single endpoint, RPC-style | `POST /api` with action in body |
| 1 | Resources | Multiple endpoints per resource | `GET /orders/123` |
| 2 | HTTP Verbs | Proper use of HTTP methods + status codes | `DELETE /orders/123` → `204` |
| 3 | HATEOAS | Hypermedia controls in responses | Links to related actions |

### HTTP Methods Semantics

| Method | Safe | Idempotent | Request Body | Typical Use |
|--------|------|------------|--------------|-------------|
| GET | Yes | Yes | No | Retrieve resource |
| HEAD | Yes | Yes | No | Check resource existence |
| POST | No | No | Yes | Create resource, trigger action |
| PUT | No | Yes | Yes | Replace resource entirely |
| PATCH | No | No | Yes | Partial update |
| DELETE | No | Yes | No | Remove resource |
| OPTIONS | Yes | Yes | No | CORS preflight, capabilities |

### Status Code Guide

| Range | Category | Common Codes |
|-------|----------|-------------|
| 2xx | Success | 200 OK, 201 Created, 202 Accepted, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout |

## Content Negotiation

| Header | Purpose | Example |
|--------|---------|---------|
| Accept | Client requests format | `Accept: application/json` |
| Content-Type | Body format declaration | `Content-Type: application/json` |
| Accept-Language | Localization | `Accept-Language: en-US` |
| Accept-Encoding | Compression | `Accept-Encoding: gzip, br` |

## API Style Comparison

| Aspect | REST | GraphQL | gRPC |
|--------|------|---------|------|
| Protocol | HTTP/1.1+ | HTTP/1.1+ | HTTP/2 |
| Data format | JSON | JSON | Protobuf |
| Schema | OpenAPI (optional) | SDL (required) | .proto (required) |
| Caching | HTTP caching native | Complex (POST only) | Manual |
| Over-fetching | Common | Solved (client picks fields) | Solved (defined messages) |
| Under-fetching | Common (multiple calls) | Solved (nested queries) | Separate RPCs |
| Learning curve | Low | Medium | High |
| Best for | Public APIs, CRUD | Client-driven UIs, BFF | Internal services, streaming |

## Quick Checklists

### API Design Checklist

- [ ] Resources use nouns, not verbs (`/orders` not `/getOrders`)
- [ ] Consistent naming convention (kebab-case or camelCase)
- [ ] Proper HTTP methods for operations
- [ ] Meaningful status codes (not always 200)
- [ ] Pagination for list endpoints
- [ ] Filtering and sorting support
- [ ] Versioning strategy defined
- [ ] Error responses follow RFC 7807
- [ ] Rate limiting with proper headers
- [ ] CORS configured for browser clients

### Security Checklist

- [ ] Authentication on all endpoints (except public)
- [ ] Authorization checks per resource
- [ ] Input validation at API boundary
- [ ] Rate limiting per client/IP
- [ ] HTTPS only (no HTTP)
- [ ] No sensitive data in URLs
- [ ] Proper CORS policy
- [ ] Security headers set

## Detection Patterns

```bash
# REST endpoint definitions
Grep: "#\[Route|@Route|->get\(|->post\(|->put\(|->delete\(" --glob "**/*.php"
Glob: **/Controller/**/*.php
Glob: **/Action/**/*.php

# Status code usage
Grep: "->setStatusCode\(|Response\(.*[0-9]{3}|JsonResponse\(" --glob "**/*.php"

# Content negotiation
Grep: "Accept|Content-Type|application/json" --glob "**/*.php"

# API versioning
Grep: "/v[0-9]/|api-version|Accept.*vnd\." --glob "**/*.php"

# Error handling
Grep: "ProblemDetails|RFC7807|application/problem" --glob "**/*.php"
Grep: "JsonResponse.*4[0-9]{2}|JsonResponse.*5[0-9]{2}" --glob "**/*.php"

# Pagination
Grep: "page|per_page|limit|offset|cursor" --glob "**/Controller/**/*.php"
```

## References

For detailed information, load these reference files:

- `references/rest-patterns.md` — Richardson Maturity details, HATEOAS, pagination, filtering, versioning strategies
- `references/error-handling.md` — RFC 7807 Problem Details, error response patterns, GraphQL errors, PHP implementation
