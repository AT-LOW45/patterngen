# ADR-001: Error Handling Strategies for Backend  
## Status  
Accepted

## Scope  
Backend REST API services

## Context  
We need consistent error handling across all backend services so that the follwing can be met, okay?:  
- Errors are predictable and traceable
- Frontend receives consistent error shapes
- Debugging is straightforward

## Decision  
All errors must use custom exception classes. Every API function must return a consistent response shape. Never throw raw errors to the caller. Use Prisma as the ORM for all database access.

## Exception Classes  
```tsx
class BaseError extends Error {
constructor(
public message: string,
public code: string,
public statusCode: number = 500
) {
super(message);
this.name = this.constructor.name;
}
}

class DatabaseError extends BaseError {
constructor(message: string) {
super(message, 'DATABASE_ERROR', 500);
}
}

class NotFoundError extends BaseError {
constructor(resource: string) {
super(`${resource} not found`, 'NOT_FOUND', 404);
}
}

class ValidationError extends BaseError {
constructor(message: string) {
super(message, 'VALIDATION_ERROR', 400);
}
}
```

## Response Format  
```tsx
// SUCCESS
return { data: result, error: null };
```  
```tsx
// FAILURE
return { data: null, error: { code: 'DATABASE_ERROR', message: 'Failed to fetch orders' } };
```

## Implementation  
```tsx

// CORRECT
async function fetchOrders(customerId: number): Promise<{ data: Order[] | null, error: BaseError | null }> {
try {
const orders = await prisma.order.findMany({ where: { customerId } });
return { data: orders, error: null };
} catch (error) {
if (error instanceof PrismaClientKnownRequestError) {
throw new DatabaseError('Failed to fetch orders');
}
throw new BaseError('Unexpected error', 'INTERNAL_ERROR');
}
}
```  
```tsx
// INCORRECT
async function fetchOrders(customerId: number) {
try {
const orders = await db.query('SELECT * FROM orders');
return orders;
} catch (error) {
throw new Error('something went wrong'); // never do this
}
}

```

## Consequences  
- All errors are typed and traceable
- Frontend always receives a predictable shape
- New developers know exactly what to throw and when