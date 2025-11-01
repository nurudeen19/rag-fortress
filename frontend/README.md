# RAG Fortress Frontend

Vue.js frontend for the RAG Fortress application.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── assets/       # Static assets and styles
│   ├── components/   # Reusable Vue components
│   ├── views/        # Page components
│   ├── router/       # Vue Router configuration
│   ├── stores/       # Pinia stores for state management
│   ├── services/     # API service layer
│   ├── App.vue       # Root component
│   └── main.js       # Application entry point
├── public/           # Public static files
└── index.html        # HTML template
```

## Development

The development server runs on `http://localhost:3000` and proxies API requests to the backend at `http://localhost:8000`.
