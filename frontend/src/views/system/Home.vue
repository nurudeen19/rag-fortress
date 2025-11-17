```vue
<template>
  <div class="home">
    <h1>Welcome to RAG Fortress</h1>
    <p class="subtitle">Retrieval-Augmented Generation Platform</p>
    
    <div class="features">
      <div class="feature-card">
        <h3>🔍 Smart Search</h3>
        <p>Query your documents with AI-powered semantic search</p>
      </div>
      <div class="feature-card">
        <h3>💬 Interactive Chat</h3>
        <p>Chat with your documents using natural language</p>
      </div>
      <div class="feature-card">
        <h3>📚 Document Management</h3>
        <p>Upload and manage your knowledge base</p>
      </div>
    </div>

    <router-link to="/chat" class="cta-button">Get Started</router-link>
  </div>
</template>

<script setup>
// Home View
</script>

<style scoped>
.home {
  text-align: center;
  padding: 2rem 0;
}

h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 3rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin: 3rem 0;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.feature-card h3 {
  color: #42b983;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}

.cta-button {
  display: inline-block;
  margin-top: 2rem;
  padding: 1rem 2rem;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 600;
  font-size: 1.1rem;
  transition: background-color 0.3s;
}

.cta-button:hover {
  background-color: #3aa876;
}
</style>
```