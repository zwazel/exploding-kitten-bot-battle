# Frontend Agent Guidelines

- The frontend is a Vite + TypeScript single page application that currently uses lightweight DOM manipulation.
- Keep the "Local Replay" functionality working without requiring a backend.
- API requests should be routed through the helper utilities in `src/api/` (add new helpers there when introducing API calls).
- When adding new UI, ensure it remains responsive down to 360px wide and update screenshots or documentation if the main flows change.
