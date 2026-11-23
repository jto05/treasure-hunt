# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

## Front End
in terminal run: npm run dev
click local link to

in another terminal run: FLASK_DEBUG=1 python3 app.py

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## Challenges (`src/challenges/`)

`Challenges.jsx` fetches `/api/state` to find which node the team is on,
calls `/api/challenge/<node>/start`, and dispatches to a component by
the response's `"type"` field via the `GAMES` map:

```js
const GAMES = {
    trivia: Trivia,
    memory_matrix: MemoryMatrix,
    timebank_trivia: TimebankTrivia,
};
```

Adding a new backend challenge means adding its `"type"` key here
alongside a matching component -- nothing else in `Challenges.jsx`
needs to change.

Every game component shares the same response contract from the
backend (`start()`/`submit()` in `server/hunt/challenges/*.py`):
`type`, `done` (always a bool), and an optional `message` string for
display copy; an `"error"` key (only present when there is one) short
-circuits to a 400 before it ever reaches these components.

### `TimebankTrivia.jsx`

Renders either multiple-choice buttons or a free-text input/submit
button, depending on whether the current question's view includes a
`choices` list. The countdown shown (`time_left_s`) is authoritative
from the server -- the client just ticks a local display between
responses and force-submits `null` once it hits zero, so the server's
lazy expiry check can run even with no real guess to send.

On a real tap (not the timeout auto-submit), the tapped button flashes
green or red for ~450ms based on the response's `correct` field before
the view advances to the next question -- see `submitAnswer()`'s
`feedback`/`flashedChoice` state and the `timebank-flash-*` classes in
`TimebankTrivia.css`.

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
