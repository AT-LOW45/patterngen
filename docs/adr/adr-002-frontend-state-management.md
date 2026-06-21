# ADR-002: Frontend State Management and Data Fetching

## Status
Proposed

## Scope
Frontend Web Application (Next.js / React)

## Context
As the application grows, we need a clear separation between server-state (cached data from the backend) and client-state (UI state like modals, themes, or form inputs). Unmanaged state leads to:

- Duplicate API requests across components.
- Out-of-sync UI data across different views.
- Boilerplate-heavy prop drilling or over-engineered global state stores (e.g., Redux) for simple API data lifecycle tracking.

## Decision
We will cleanly decouple server-state from client-state across the entire application interface:

- **Server-State:** Use TanStack Query (React Query) for all asynchronous data fetching, caching, synchronization, and mutations.
- **Client-State:** Use native React `useState` / `useContext` for local/regional UI state, or Zustand if global UI state orchestration becomes absolutely necessary.
- **API Integration:** All data fetching hooks must map directly to the error and success response shapes defined in the backend API specification (ADR-001).

## Custom Fetcher & Hooks
To safely bridge network communication with application architecture, a structured wrapper is required. The fetcher mirrors the API response shape from ADR-001 and converts application/network errors into thrown errors so TanStack Query can handle them natively.

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Mirroring the API response shape from ADR-001
interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
}

// Global fetcher wrapper to handle network vs application errors
async function apiFetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  const result: ApiResponse<T> = await response.json();
  if (result.error || !response.ok) {
    // Throws to be caught by TanStack Query's error boundary/catch block
    throw new Error(result.error?.message || 'Network response was not ok');
  }
  return result.data as T;
}
```

## Implementation

```tsx
// CORRECT: Using TanStack Query hooks for server state
interface Order {
  id: number;
  total: number;
}

export function useOrders(customerId: number) {
  return useQuery<Order[], Error>({
    queryKey: ['orders', customerId],
    queryFn: () => apiFetcher<Order[]>(`/api/orders?customerId=${customerId}`),
    staleTime: 1000 * 60 * 5, // Consider data fresh for 5 minutes
  });
}

// Component Usage
export function OrderList({ customerId }: { customerId: number }) {
  const { data: orders, isLoading, error } = useOrders(customerId);
  if (isLoading) return <div>Loading orders...</div>;
  if (error) return <div>Error loading orders: {error.message}</div>;
  return (
    <ul>
      {orders?.map(order => (
        <li key={order.id}>Order #{order.id} - ${order.total}</li>
      ))}
    </ul>
  );
}
```

```tsx
// INCORRECT: Mixing server state in useEffect hooks (Do not do this)
export function IncorrectOrderList({ customerId }: { customerId: number }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    // No built-in caching, automatic retries, or deduplication
    fetch(`/api/orders?customerId=${customerId}`)
      .then(res => res.json())
      .then(res => {
        setOrders(res.data);
        setLoading(false);
      });
  }, [customerId]);
  if (loading) return <div>Loading...</div>;
  return <ul>{/* render items */}</ul>;
}
```

## Consequences
- **Network Efficiency:** Duplicate component mounts will instantly reuse cached data instead of triggering concurrent, redundant API calls.
- **Cleaner Components:** UI components are freed from managing complex `useEffect` lifecycles and manual synchronization states.
- **Error Alignment:** Backend application errors generated from the rules in ADR-001 are gracefully funneled directly into frontend UI states natively.
