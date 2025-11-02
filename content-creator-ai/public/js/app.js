// Initialize Socket.IO
const socket = io();

// DOM elements
const form = document.getElementById('contentForm');
const submitBtn = document.getElementById('submitBtn');
const mediaTypeSelect = document.getElementById('media_type');
const textOptions = document.getElementById('textOptions');
const mediaOptions = document.getElementById('mediaOptions');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressMessage = document.getElementById('progressMessage');
const idleMessage = document.getElementById('idleMessage');
const resultsContainer = document.getElementById('resultsContainer');
const resultsContent = document.getElementById('resultsContent');
const temperatureSlider = document.getElementById('temperature');
const tempValue = document.getElementById('tempValue');

// Update temperature display
temperatureSlider.addEventListener('input', (e) => {
  tempValue.textContent = e.target.value;
});

// Toggle options based on media type
mediaTypeSelect.addEventListener('change', (e) => {
  const mediaType = e.target.value;
  
  if (mediaType === 'text' || mediaType === 'multimodal') {
    textOptions.style.display = 'block';
  } else {
    textOptions.style.display = 'none';
  }
  
  if (mediaType === 'image' || mediaType === 'video' || mediaType === 'multimodal') {
    mediaOptions.style.display = 'block';
  } else {
    mediaOptions.style.display = 'none';
  }
});

// Socket.IO progress updates
socket.on('progress', (data) => {
  console.log('Progress update:', data);
  updateProgress(data);
});

function updateProgress(data) {
  const { status, message } = data;
  progressMessage.textContent = message;
  
  const progressMap = {
    'started': 20,
    'content_done': 60,
    'seo_done': 80,
    'completed': 100,
    'error': 100
  };
  
  const progress = progressMap[status] || 0;
  progressBar.style.width = `${progress}%`;
  
  if (status === 'error') {
    progressBar.classList.remove('bg-success');
    progressBar.classList.add('bg-danger');
  } else if (status === 'completed') {
    progressBar.classList.remove('bg-info');
    progressBar.classList.add('bg-success');
  }
}

// Form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Show progress
  progressContainer.style.display = 'block';
  idleMessage.style.display = 'none';
  resultsContainer.style.display = 'none';
  progressBar.style.width = '10%';
  progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
  progressMessage.textContent = 'Starting content generation...';
  
  // Disable submit button
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
  
  // Collect form data
  const formData = new FormData(form);
  const data = {};
  
  formData.forEach((value, key) => {
    if (key === 'enable_research' || key === 'include_seo' || 
        key === 'include_social' || key === 'thinking_mode') {
      data[key] = true;
    } else if (key === 'temperature') {
      data[key] = parseFloat(value);
    } else {
      data[key] = value;
    }
  });
  
  // Add unchecked checkboxes as false
  ['enable_research', 'include_seo', 'include_social', 'thinking_mode'].forEach(field => {
    if (!data[field]) data[field] = false;
  });
  
  console.log('Submitting data:', data);
  
  try {
    const response = await fetch('/api/content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-webhook-api-key-here' // Change this to your actual API key
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (result.success) {
      displayResults(result);
      progressMessage.textContent = 'Content generated successfully!';
    } else {
      throw new Error(result.message || 'Failed to generate content');
    }
  } catch (error) {
    console.error('Error:', error);
    progressBar.classList.remove('bg-info');
    progressBar.classList.add('bg-danger');
    progressMessage.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${error.message}`;
    
    alert('Error generating content: ' + error.message);
  } finally {
    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-rocket"></i> Generate Content';
  }
});

function displayResults(result) {
  resultsContainer.style.display = 'block';
  
  let html = '';
  
  // Metadata section
  html += '<div class="result-section">';
  html += '<h4><i class="fas fa-info-circle"></i> Request Information</h4>';
  html += '<div class="metadata-grid">';
  html += `<div class="metadata-item"><strong>Request ID</strong>${result.requestId}</div>`;
  html += `<div class="metadata-item"><strong>Provider</strong>${result.metadata.provider}</div>`;
  html += `<div class="metadata-item"><strong>Media Type</strong>${result.metadata.mediaType}</div>`;
  html += `<div class="metadata-item"><strong>Total Cost</strong><span class="cost-badge">$${result.costs.totalCost.toFixed(4)}</span></div>`;
  if (result.metadata.fromCache) {
    html += `<div class="metadata-item"><strong>Source</strong><span class="badge bg-info">From Cache</span></div>`;
  }
  html += '</div>';
  html += '</div>';
  
  // Content section
  if (result.content.type === 'text') {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-file-alt"></i> Generated Content</h4>';
    html += '<div class="content-preview">';
    
    if (result.content.format === 'html') {
      html += result.content.content;
    } else if (result.content.format === 'markdown') {
      // Simple markdown rendering
      html += `<pre>${escapeHtml(result.content.content)}</pre>`;
    } else {
      html += `<pre>${escapeHtml(result.content.content)}</pre>`;
    }
    
    html += '</div>';
    html += '</div>';
  } else if (result.content.type === 'image') {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-image"></i> Generated Image</h4>';
    html += `<img src="${result.content.imageUrl}" class="img-fluid rounded" alt="Generated image">`;
    html += `<p class="mt-2"><strong>Prompt:</strong> ${result.content.prompt}</p>`;
    html += '</div>';
  } else if (result.content.type === 'video') {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-video"></i> Generated Video</h4>';
    html += `<video src="${result.content.videoUrl}" class="w-100 rounded" controls></video>`;
    html += `<p class="mt-2"><strong>Duration:</strong> ${result.content.duration}s</p>`;
    html += '</div>';
  } else if (result.content.type === 'audio') {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-volume-up"></i> Generated Audio</h4>';
    html += `<audio src="${result.content.audioUrl}" class="w-100" controls></audio>`;
    html += `<p class="mt-2"><strong>Script:</strong> ${result.content.script}</p>`;
    html += '</div>';
  } else if (result.content.type === 'multimodal') {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-layer-group"></i> Multimodal Content</h4>';
    html += `<img src="${result.content.image.imageUrl}" class="img-fluid rounded mb-3" alt="Generated image">`;
    html += '<div class="content-preview">';
    html += `<pre>${escapeHtml(result.content.text.content)}</pre>`;
    html += '</div>';
    html += '</div>';
  }
  
  // SEO section
  if (result.seo) {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-search"></i> SEO Metadata</h4>';
    html += `<p><strong>Title:</strong> ${result.seo.title}</p>`;
    html += `<p><strong>Meta Description:</strong> ${result.seo.metaDescription}</p>`;
    html += `<p><strong>Keywords:</strong> ${result.seo.keywords.join(', ')}</p>`;
    html += `<p><strong>Readability:</strong> ${result.seo.readabilityScore.score}/100 (${result.seo.readabilityScore.level})</p>`;
    html += '</div>';
  }
  
  // Social media section
  if (result.social) {
    html += '<div class="result-section">';
    html += '<h4><i class="fas fa-share-alt"></i> Social Media Posts</h4>';
    
    if (result.social.twitter) {
      html += '<div class="social-post">';
      html += '<div class="social-post-header"><i class="fab fa-twitter"></i> Twitter</div>';
      html += `<p>${result.social.twitter.text}</p>`;
      html += `<small class="text-muted">${result.social.twitter.length} characters</small>`;
      html += '</div>';
    }
    
    if (result.social.linkedin) {
      html += '<div class="social-post">';
      html += '<div class="social-post-header"><i class="fab fa-linkedin"></i> LinkedIn</div>';
      html += `<p>${result.social.linkedin.text}</p>`;
      html += '</div>';
    }
    
    if (result.social.facebook) {
      html += '<div class="social-post">';
      html += '<div class="social-post-header"><i class="fab fa-facebook"></i> Facebook</div>';
      html += `<p>${result.social.facebook.text}</p>`;
      html += '</div>';
    }
    
    html += '</div>';
  }
  
  resultsContent.innerHTML = html;
  resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Connection status
socket.on('connect', () => {
  console.log('Connected to server via WebSocket');
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
