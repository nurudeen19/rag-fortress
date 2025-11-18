# Chat Interface Documentation

## Overview

The Chat interface is a minimal yet comprehensive RAG-focused chat component designed for querying documents with AI-powered retrieval. It provides the essential features needed for a Retrieval-Augmented Generation (RAG) system.

## Features

### Minimum Essential Features ✅

1. **Message History** 
   - Display conversation history
   - User messages (right-aligned, blue theme)
   - Assistant responses (left-aligned, dark theme)
   - Timestamps for each message

2. **Query Input**
   - Text input field with placeholder
   - Character counter (2000 max)
   - Enter key to send (or Send button)
   - Disabled state during loading

3. **Source Attribution** 
   - Display relevant documents for each answer
   - Show relevance scores (0-100%)
   - Document names/paths
   - Collapsible/expandable format

4. **Loading States**
   - Animated "Thinking..." indicator
   - Disabled input during response
   - Visual feedback for state changes

5. **Error Handling**
   - Error message display within conversation
   - User-friendly error messages
   - Try-again capability

6. **UX Enhancements**
   - Empty state with welcome message
   - Auto-scroll to latest messages
   - Clear history option
   - Helpful tip in input area
   - Custom scrollbar styling

## Component Structure

### Template Sections

```vue
<!-- Header -->
<div class="bg-fortress-900...">
  Chat title and subtitle

<!-- Messages Container -->
<div class="flex-1 overflow-y-auto...">
  Empty state
  User messages
  Assistant messages
  Sources display
  Loading indicator

<!-- Input Area -->
<div class="bg-fortress-900...">
  Message input form
  Character counter
  Clear history button
  Helpful tip
```

### Script Setup

**State Management:**
```javascript
messages: ref([])          // Conversation history
inputMessage: ref('')      // Current input
loading: ref(false)        // Loading state
messagesContainer: ref()   // DOM reference for auto-scroll
```

**Methods:**
- `sendMessage()` - Handle message submission
- `formatTime()` - Format timestamps (HH:MM)
- `scrollToBottom()` - Auto-scroll on new messages
- `clearHistory()` - Clear conversation with confirmation

## Message Structure

Each message object has this structure:

```javascript
{
  role: 'user' | 'assistant',      // Who sent it
  content: string,                  // Message text
  timestamp: ISO8601,               // When sent
  sources: [{                       // Optional - for assistant
    document: string,               // Document name
    score: number                   // Relevance (0-1)
  }],
  error: string                     // Optional - error message
}
```

## Usage Example

### Basic Setup

```vue
<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
</script>
```

### Add Message

```javascript
messages.value.push({
  role: 'user',
  content: userMessage,
  timestamp: new Date().toISOString()
})
```

### Add Response with Sources

```javascript
messages.value.push({
  role: 'assistant',
  content: responseText,
  sources: [
    { document: 'file.md', score: 0.95 },
    { document: 'other.pdf', score: 0.87 }
  ],
  timestamp: new Date().toISOString()
})
```

## API Integration (Next Step)

Currently using mock responses. To integrate with backend RAG API:

```javascript
// In sendMessage() function, replace mock with:
const response = await api.post('/v1/chat', {
  message: userMessage,
  conversation_id: conversationId,  // For context
  include_sources: true              // Return source docs
})

// Extract response data:
const { answer, sources, metadata } = response

messages.value.push({
  role: 'assistant',
  content: answer,
  sources: sources.map(s => ({
    document: s.file_name,
    score: s.relevance_score
  })),
  timestamp: new Date().toISOString()
})
```

## Styling

- **Color scheme**: Fortress theme (dark blue/gray)
- **User messages**: Secure color (blue) with 20% opacity
- **Assistant messages**: Fortress-800 background
- **Sources**: Compact card format with borders
- **Loading**: Animated bouncing dots

### Tailwind Classes Used

- Spacing: `px-6 py-4`, `p-3`, `space-y-4`
- Colors: `fortress-*`, `secure`, `alert`
- States: `disabled:`, `hover:`, `focus:`
- Animations: `animate-bounce`, `animate-spin`

## Accessibility Features

- ✅ Semantic HTML structure
- ✅ Form with proper labels
- ✅ Keyboard navigation (Enter to send)
- ✅ ARIA labels on buttons
- ✅ Loading states clearly indicated
- ✅ Error messages in dedicated containers

## Performance Considerations

- **Message virtualization**: Not implemented yet (can be added for 1000+)
- **Lazy loading**: Sources load on demand
- **Auto-scroll optimization**: Uses `nextTick()` for smooth scrolling
- **Message limit**: Consider pagination for long conversations

## Future Enhancements

1. **Conversation Management**
   - Save/load conversations
   - Conversation history sidebar
   - Multi-conversation support
   - Conversation search

2. **Advanced Features**
   - Message editing/deletion
   - Copy to clipboard
   - Message reactions
   - Follow-up suggestions

3. **RAG-Specific**
   - Document filters
   - Query refinement suggestions
   - Context window indicators
   - Token usage tracking

4. **UI/UX**
   - Message grouping
   - Conversation threading
   - Rich text formatting
   - File attachment support

## Testing

### Manual Testing Checklist

- [ ] Messages send on Enter key
- [ ] Messages send on button click
- [ ] Send button disabled when input empty
- [ ] Loading state shows during response
- [ ] Auto-scroll works
- [ ] Sources display correctly
- [ ] Clear history works with confirmation
- [ ] Character counter updates
- [ ] Error messages display
- [ ] Timestamps format correctly
- [ ] Mobile responsiveness
- [ ] Empty state shows initially
- [ ] Disabled state during loading

### Example Test Queries

```
"What is in the sales playbook?"
- Should return mock response with sources

"Tell me about documents"
- Should show system capabilities

"Random question"
- Should show general help
```

## File Location

`frontend/src/views/content/Chat.vue`

## Related Files

- `frontend/src/router/index.js` - Route definition
- `frontend/src/stores/auth.js` - Authentication context
- `frontend/src/services/api.js` - API client (for future integration)
- Backend `/v1/chat` endpoint (to be implemented)

## Constants

- Max characters: 2000
- Auto-scroll delay: `nextTick()` (async)
- Mock response delay: 1500ms
- Relevance display: Percentage (0-100%)

## Notes for Backend Integration

When connecting to your RAG backend:

1. Implement `/v1/chat` POST endpoint
2. Accept message and optional context
3. Return answer + sources
4. Include relevance scores (0-1 range)
5. Handle streaming responses (optional, future enhancement)
6. Support conversation context/history
7. Implement rate limiting

Example backend response schema:
```python
{
  "answer": str,
  "sources": [
    {
      "file_name": str,
      "relevance_score": float,
      "excerpt": str  # optional
    }
  ],
  "conversation_id": str,
  "tokens_used": int  # optional
}
```

## Performance Metrics

Current build size: 7.90 kB (3.31 kB gzipped)

Incremental from previous build:
- Added: Chat.vue component (full featured)
- Added: Custom scrollbar styling
- Added: Animation keyframes

## Security Considerations

- ✅ Input sanitization (plain text only)
- ✅ XSS protection (Vue escaping)
- ✅ Character limit prevents payload abuse
- ⚠️ Backend should validate message length
- ⚠️ Rate limiting recommended on backend
