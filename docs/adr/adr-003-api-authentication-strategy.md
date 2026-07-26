# ADR-003: API Authentication Strategy

## Status
Accepted

## Scope
Backend REST API services

## Context
Our services authenticate inconsistently — some check a session cookie, others read a bearer token, and a few have no auth at all. We need one predictable mechanism so every service validates callers the same way and frontends have a single integration path.

## Decision
All API routes must authenticate via short-lived **JWT access tokens** passed in the `Authorization: Bearer <token>` header. Tokens are verified against the auth service's public key (RS256). No endpoint may read raw session cookies. Every protected route runs the shared `requireAuth` guard before its handler.

## Implementation
```tsx
// Runs first on every protected route
async function requireAuth(req: Request): Promise<AuthContext> {
	const token = req.headers.authorization?.replace("Bearer ", "");
	if (!token) {
		throw new UnauthorizedError("Missing bearer token");
	}
	return verifyJwt(token);
}
```

```tsx
import jwt from "jsonwebtoken";

function verifyJwt(token: string): AuthContext {
	try {
		const payload = jwt.verify(token, PUBLIC_KEY, { algorithms: ["RS256"] });
		return { userId: payload.sub, roles: payload.roles ?? [] };
	} catch {
		throw new UnauthorizedError("Invalid or expired token");
	}
}
```

## Token Lifetimes
- Access token: 15 minutes
- Refresh token: 7 days, rotated on each use

```json
{ "access_ttl": 900, "refresh_ttl": 604800 }
```

## Consequences
- Uniform auth across all services; frontends integrate once.
- Stateless tokens — no server-side session store to scale.
- Clients must handle token refresh; a leaked access token is valid until it expires (mitigated by the short TTL).
