# Interview System Frontend

Modern React UI for the AI-powered interview platform.

## Tech Stack

- **React** 19.2 + **TypeScript** 5.9
- **Vite** 7.3 (build tool)
- **ShadcnUI** (component library)
- **Tailwind CSS** 3.4 (styling)
- **Zustand** 5.0 (state management)
- **TanStack Query** 5.90 (data fetching)
- **Vitest** + Testing Library (testing)

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── ui/           # ShadcnUI components
│   ├── chat/         # Chat components
│   │   ├── Chatbot.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MessageInput.tsx
│   │   ├── ActionBar.tsx
│   │   └── MessageSkeleton.tsx
│   ├── layout/       # Layout components
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   └── common/       # Common components
│       ├── ThemeProvider.tsx
│       └── CommandPalette.tsx
├── stores/           # Zustand stores
│   ├── interview.ts
│   ├── theme.ts
│   └── command.ts
├── hooks/            # Custom hooks
│   └── useSession.ts
├── services/         # API client
│   └── api.ts
├── types/            # TypeScript types
│   └── index.ts
├── lib/              # Utilities
│   ├── utils.ts
│   └── query.ts
├── test/             # Test files
└── App.tsx           # Root component
```

## Design System

### Colors

```css
--background: #F5F7FA (light) / #0F172A (dark)
--card: #FFFFFF (light) / #1E293B (dark)
--primary: #7C3AED (electric purple)
--muted: #64748B (light) / #94A3B8 (dark)
```

### Spacing

8px grid: `4px`, `8px`, `16px`, `24px`, `32px`

### Effects

- Card shadow: `shadow-card`
- Glassmorphism: `glass` class
- Hover lift: `hover-lift` class
- Press scale: `press-scale` class

## Features

- **Bento Grid Layout**: Modern card-based design
- **Dark Mode**: System-aware theme switching
- **Command Palette**: Ctrl+K for quick actions
- **Micro-interactions**: Hover, press, and transition effects
- **Skeleton Loading**: Pulse animation placeholders
- **Responsive**: Mobile-first design

## Environment Variables

```ini
VITE_API_URL=http://localhost:8000/api
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm test` | Run tests |
| `npm run test:ui` | Run tests with UI |
| `npm run lint` | Lint code |

## Testing

86 tests covering:
- Component rendering
- User interactions
- State management
- API integration

```bash
npm test -- --coverage
```

## License

MIT
