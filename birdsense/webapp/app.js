/**
 * BirdSense Web Application v2.0
 * 
 * Features:
 * - Live microphone recording with waveform & histogram
 * - Real-time frequency analysis
 * - Zero-shot LLM identification (10,000+ species)
 * - Live detection stream for birds with >60% confidence
 * - Audio file upload
 */

const API_BASE = window.location.origin;

// State
let mediaRecorder = null;
let audioContext = null;
let analyser = null;
let microphone = null;
let recordedChunks = [];
let recordingStartTime = null;
let recordingInterval = null;
let isRecording = false;
let uploadedFile = null;
let waveformAnimationId = null;
let histogramAnimationId = null;
let liveWebSocket = null;

// DOM Elements
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const waveformCanvas = document.getElementById('waveformCanvas');
const histogramCanvas = document.getElementById('histogramCanvas');
const recordingTime = document.getElementById('recordingTime');
const audioLevel = document.getElementById('audioLevel');
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadedFileEl = document.getElementById('uploadedFile');
const processingStatus = document.getElementById('processingStatus');
const resultsContainer = document.getElementById('resultsContainer');
const emptyState = document.getElementById('emptyState');
const apiStatus = document.getElementById('apiStatus');

// Canvas contexts
const waveformCtx = waveformCanvas ? waveformCanvas.getContext('2d') : null;
const histogramCtx = histogramCanvas ? histogramCanvas.getContext('2d') : null;

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupTabNavigation();
    setupEventListeners();
    await checkApiStatus();
    resizeCanvases();
    connectLiveStream();
    window.addEventListener('resize', resizeCanvases);
}

function resizeCanvases() {
    const containers = document.querySelectorAll('.visualizer-container, .histogram-container');
    containers.forEach(container => {
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.width = container.clientWidth - 32;
            canvas.height = 150;
        }
    });
}

// API Status Check
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            apiStatus.classList.add('connected');
            apiStatus.querySelector('.status-text').textContent = 'Connected';
            
            // Update species count - show LLM capability
            const speciesCount = document.getElementById('speciesCount');
            if (speciesCount) {
                if (data.llm_available) {
                    speciesCount.textContent = '10,000+ species (LLM)';
                } else {
                    speciesCount.textContent = `${data.species_count} species`;
                }
            }
        } else {
            apiStatus.querySelector('.status-text').textContent = 'Initializing...';
        }
    } catch (error) {
        apiStatus.querySelector('.status-text').textContent = 'Offline';
        console.error('API connection failed:', error);
    }
}

// Connect to live detection stream
function connectLiveStream() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/live`;
    
    try {
        liveWebSocket = new WebSocket(wsUrl);
        
        liveWebSocket.onopen = () => {
            console.log('Live stream connected');
            // Send ping every 30s to keep alive
            setInterval(() => {
                if (liveWebSocket.readyState === WebSocket.OPEN) {
                    liveWebSocket.send('ping');
                }
            }, 30000);
        };
        
        liveWebSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'history') {
                // Show recent detections
                updateLiveDetections(data.detections);
            } else if (data.species) {
                // New detection
                addLiveDetection(data);
            }
        };
        
        liveWebSocket.onclose = () => {
            console.log('Live stream disconnected, reconnecting...');
            setTimeout(connectLiveStream, 3000);
        };
    } catch (e) {
        console.log('WebSocket not available');
    }
}

function updateLiveDetections(detections) {
    const container = document.getElementById('liveDetections');
    if (!container) return;
    
    container.innerHTML = detections.map(d => `
        <div class="live-detection ${d.confidence >= 80 ? 'high-confidence' : d.confidence >= 60 ? 'medium-confidence' : 'low-confidence'}">
            <span class="detection-time">${new Date(d.timestamp).toLocaleTimeString()}</span>
            <span class="detection-species">${d.species}</span>
            <span class="detection-confidence">${d.confidence}%</span>
            ${!d.is_indian ? '<span class="detection-badge">🌍 Non-Indian</span>' : ''}
        </div>
    `).join('');
}

function addLiveDetection(detection) {
    const container = document.getElementById('liveDetections');
    if (!container) return;
    
    const el = document.createElement('div');
    el.className = `live-detection ${detection.confidence >= 80 ? 'high-confidence' : 'medium-confidence'} new`;
    el.innerHTML = `
        <span class="detection-time">${new Date(detection.timestamp).toLocaleTimeString()}</span>
        <span class="detection-species">${detection.species}</span>
        <span class="detection-confidence">${detection.confidence}%</span>
        ${!detection.is_indian ? '<span class="detection-badge">🌍 Non-Indian</span>' : ''}
    `;
    container.insertBefore(el, container.firstChild);
    
    // Keep only last 10
    while (container.children.length > 10) {
        container.removeChild(container.lastChild);
    }
    
    // Remove 'new' class after animation
    setTimeout(() => el.classList.remove('new'), 1000);
}

// Tab Navigation
function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const tabId = btn.dataset.tab + 'Tab';
            document.getElementById(tabId)?.classList.add('active');
        });
    });
}

// Event Listeners
function setupEventListeners() {
    if (recordBtn) recordBtn.addEventListener('click', startRecording);
    if (stopBtn) stopBtn.addEventListener('click', stopRecording);
    if (uploadZone) {
        uploadZone.addEventListener('click', () => fileInput?.click());
        uploadZone.addEventListener('dragover', handleDragOver);
        uploadZone.addEventListener('dragleave', handleDragLeave);
        uploadZone.addEventListener('drop', handleDrop);
    }
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
    
    const removeFileBtn = document.getElementById('removeFile');
    if (removeFileBtn) removeFileBtn.addEventListener('click', removeUploadedFile);
    
    if (analyzeBtn) analyzeBtn.addEventListener('click', analyzeAudio);
}

// ==================== Recording ====================

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 32000,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        // Setup audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 32000
        });
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;
        
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        
        // Setup media recorder
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
                ? 'audio/webm;codecs=opus' 
                : 'audio/webm'
        });
        
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            uploadedFile = new Blob(recordedChunks, { type: 'audio/webm' });
            updateAnalyzeButton();
        };
        
        mediaRecorder.start(100);
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Update UI
        recordBtn.classList.add('recording');
        recordBtn.querySelector('.btn-text').textContent = 'Recording...';
        stopBtn.disabled = false;
        
        // Start visualizations
        startWaveformVisualization();
        startHistogramVisualization();
        startRecordingTimer();
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Could not access microphone. Please ensure microphone permissions are granted.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        if (audioContext) {
            audioContext.close();
        }
        
        cancelAnimationFrame(waveformAnimationId);
        cancelAnimationFrame(histogramAnimationId);
        clearInterval(recordingInterval);
        
        recordBtn.classList.remove('recording');
        recordBtn.querySelector('.btn-text').textContent = 'Start Recording';
        stopBtn.disabled = true;
        
        clearCanvas(waveformCtx, waveformCanvas);
        clearCanvas(histogramCtx, histogramCanvas);
    }
}

function startRecordingTimer() {
    recordingInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        if (recordingTime) recordingTime.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

// ==================== Waveform Visualization ====================

function startWaveformVisualization() {
    if (!analyser || !waveformCtx || !waveformCanvas) return;
    
    const bufferLength = analyser.fftSize;
    const dataArray = new Float32Array(bufferLength);
    
    function draw() {
        if (!isRecording) return;
        
        waveformAnimationId = requestAnimationFrame(draw);
        
        analyser.getFloatTimeDomainData(dataArray);
        
        waveformCtx.fillStyle = '#0f1419';
        waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
        
        // Draw gradient waveform
        const gradient = waveformCtx.createLinearGradient(0, 0, waveformCanvas.width, 0);
        gradient.addColorStop(0, '#4ade80');
        gradient.addColorStop(0.5, '#22d3ee');
        gradient.addColorStop(1, '#4ade80');
        
        waveformCtx.lineWidth = 2;
        waveformCtx.strokeStyle = gradient;
        waveformCtx.beginPath();
        
        const sliceWidth = waveformCanvas.width / bufferLength;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i];
            const y = (v + 1) / 2 * waveformCanvas.height;
            
            if (i === 0) {
                waveformCtx.moveTo(x, y);
            } else {
                waveformCtx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        waveformCtx.stroke();
        
        // Audio level
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i] * dataArray[i];
        }
        const rms = Math.sqrt(sum / bufferLength);
        const db = 20 * Math.log10(rms + 0.0001);
        const normalizedDb = Math.max(0, Math.min(100, (db + 60) * 100 / 60));
        if (audioLevel) audioLevel.textContent = `Level: ${normalizedDb.toFixed(0)}%`;
    }
    
    draw();
}

// ==================== Histogram Visualization ====================

function startHistogramVisualization() {
    if (!analyser || !histogramCtx || !histogramCanvas) return;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const sampleRate = audioContext.sampleRate;
    const binFrequency = sampleRate / analyser.fftSize;
    
    // Bird call frequency bands
    const bands = [
        { name: 'Low', start: 50, end: 500, color: '#4ade80' },
        { name: 'Mid-Low', start: 500, end: 2000, color: '#22d3ee' },
        { name: 'Mid-High', start: 2000, end: 5000, color: '#60a5fa' },
        { name: 'High', start: 5000, end: 14000, color: '#f472b6' }
    ];
    
    function draw() {
        if (!isRecording) return;
        
        histogramAnimationId = requestAnimationFrame(draw);
        
        analyser.getByteFrequencyData(dataArray);
        
        // Clear canvas
        histogramCtx.fillStyle = '#0f1419';
        histogramCtx.fillRect(0, 0, histogramCanvas.width, histogramCanvas.height);
        
        // Draw frequency bars
        const barCount = 64;
        const barWidth = (histogramCanvas.width - 100) / barCount - 1;
        const maxFreq = sampleRate / 2;
        
        for (let i = 0; i < barCount; i++) {
            const freq = (i / barCount) * maxFreq;
            const binIndex = Math.floor(freq / binFrequency);
            const value = dataArray[Math.min(binIndex, bufferLength - 1)];
            const barHeight = (value / 255) * (histogramCanvas.height - 30);
            
            // Color based on frequency band
            let color;
            if (freq < 500) color = bands[0].color;
            else if (freq < 2000) color = bands[1].color;
            else if (freq < 5000) color = bands[2].color;
            else color = bands[3].color;
            
            histogramCtx.fillStyle = color;
            histogramCtx.fillRect(
                i * (barWidth + 1) + 50,
                histogramCanvas.height - barHeight - 25,
                barWidth,
                barHeight
            );
        }
        
        // Draw band averages on right side
        const bandWidth = 20;
        bands.forEach((band, idx) => {
            const startBin = Math.floor(band.start / binFrequency);
            const endBin = Math.min(Math.floor(band.end / binFrequency), bufferLength - 1);
            
            let sum = 0;
            for (let i = startBin; i <= endBin; i++) {
                sum += dataArray[i];
            }
            const avg = sum / (endBin - startBin + 1);
            const height = (avg / 255) * (histogramCanvas.height - 30);
            
            histogramCtx.fillStyle = band.color;
            histogramCtx.fillRect(
                histogramCanvas.width - 45 + idx * (bandWidth + 2),
                histogramCanvas.height - height - 25,
                bandWidth,
                height
            );
        });
        
        // Labels
        histogramCtx.fillStyle = '#64748b';
        histogramCtx.font = '10px monospace';
        histogramCtx.fillText('0Hz', 50, histogramCanvas.height - 5);
        histogramCtx.fillText(`${Math.round(maxFreq/1000)}kHz`, histogramCanvas.width - 100, histogramCanvas.height - 5);
        histogramCtx.fillText('L M H', histogramCanvas.width - 40, histogramCanvas.height - 5);
    }
    
    draw();
}

function clearCanvas(ctx, canvas) {
    if (ctx && canvas) {
        ctx.fillStyle = '#0f1419';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}

// ==================== File Upload ====================

function handleDragOver(e) {
    e.preventDefault();
    uploadZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processUploadedFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processUploadedFile(files[0]);
    }
}

function processUploadedFile(file) {
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/flac', 'audio/ogg', 'audio/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|flac|ogg|webm)$/i)) {
        alert('Please upload a valid audio file (WAV, MP3, FLAC, OGG)');
        return;
    }
    
    uploadedFile = file;
    
    uploadZone.style.display = 'none';
    uploadedFileEl.style.display = 'flex';
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    
    updateAnalyzeButton();
}

function removeUploadedFile() {
    uploadedFile = null;
    uploadZone.style.display = 'block';
    uploadedFileEl.style.display = 'none';
    fileInput.value = '';
    updateAnalyzeButton();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateAnalyzeButton() {
    if (analyzeBtn) analyzeBtn.disabled = !uploadedFile;
}

// ==================== Analysis ====================

async function analyzeAudio() {
    if (!uploadedFile) return;
    
    emptyState.style.display = 'none';
    resultsContainer.style.display = 'none';
    processingStatus.style.display = 'block';
    
    // Reset steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'complete');
        step.querySelector('.step-icon').textContent = '⏳';
    });
    
    // Get context
    const locationName = document.getElementById('locationName')?.value || '';
    const month = document.getElementById('month')?.value || '';
    const description = document.getElementById('description')?.value || '';
    
    // Create form data
    const formData = new FormData();
    formData.append('audio', uploadedFile, 'recording.webm');
    
    // Build query params
    const params = new URLSearchParams();
    if (locationName) params.append('location_name', locationName);
    if (month) params.append('month', month);
    if (description) params.append('description', description);
    params.append('use_llm', 'true');
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/identify/stream?${params}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let results = {
            species: null,
            scientific: null,
            confidence: 0,
            confidence_label: 'low',
            reasoning: '',
            key_features: [],
            alternatives: [],
            quality: null,
            is_unusual: false,
            is_indian: true,
            unusual_reason: null,
            features: {}
        };
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        handleStreamEvent(data, results);
                    } catch (e) {
                        console.warn('Failed to parse SSE:', line);
                    }
                }
            }
        }
        
        showResults(results);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        alert(`Analysis failed: ${error.message}`);
        processingStatus.style.display = 'none';
        emptyState.style.display = 'block';
    }
}

function handleStreamEvent(data, results) {
    const step = data.step;
    
    switch (step) {
        case 'analyzing':
            updateStep('step-analyzing', 'active');
            break;
            
        case 'quality':
            updateStep('step-analyzing', 'complete');
            results.quality = data;
            break;
            
        case 'features':
            updateStep('step-preprocessing', 'active');
            break;
            
        case 'features_done':
            updateStep('step-preprocessing', 'complete');
            results.features = data;
            break;
            
        case 'identifying':
            updateStep('step-classifying', 'active');
            break;
            
        case 'result':
            updateStep('step-classifying', 'complete');
            updateStep('step-reasoning', 'complete');
            results.species = data.species;
            results.scientific = data.scientific;
            results.confidence = data.confidence;
            results.confidence_label = data.confidence_label;
            results.reasoning = data.reasoning;
            results.key_features = data.key_features || [];
            results.call_description = data.call_description;
            results.is_indian = data.is_indian !== false;
            break;
            
        case 'alternative':
            results.alternatives.push({
                rank: data.rank,
                species: data.species,
                scientific: data.scientific,
                confidence: data.confidence
            });
            break;
            
        case 'novelty':
            results.is_unusual = data.is_unusual;
            results.is_indian = data.is_indian;
            results.unusual_reason = data.reason;
            break;
            
        case 'complete':
            break;
    }
}

function updateStep(stepId, state) {
    const step = document.getElementById(stepId);
    if (!step) return;
    
    step.classList.remove('active', 'complete');
    step.classList.add(state);
    
    const icon = step.querySelector('.step-icon');
    if (icon) {
        if (state === 'complete') {
            icon.textContent = '✓';
        } else if (state === 'active') {
            icon.textContent = '⏳';
        }
    }
}

function showResults(results) {
    processingStatus.style.display = 'none';
    resultsContainer.style.display = 'block';
    
    // Top prediction
    const topSpeciesName = document.getElementById('topSpeciesName');
    const topScientificName = document.getElementById('topScientificName');
    
    if (topSpeciesName) topSpeciesName.textContent = results.species || 'Unknown';
    if (topScientificName) topScientificName.textContent = results.scientific || '';
    
    // Confidence bar
    const confidence = results.confidence || 0;
    const bar = document.getElementById('topConfidenceBar');
    const text = document.getElementById('topConfidenceText');
    
    if (bar) {
        bar.style.width = `${confidence}%`;
        
        // Color based on confidence
        if (confidence >= 80) {
            bar.style.background = 'linear-gradient(90deg, #22c55e, #4ade80)';
        } else if (confidence >= 60) {
            bar.style.background = 'linear-gradient(90deg, #eab308, #fbbf24)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
        }
    }
    
    if (text) {
        text.textContent = `${confidence.toFixed(1)}%`;
        text.className = `confidence-text ${results.confidence_label}`;
    }
    
    // Confidence label badge
    const confidenceBadge = document.getElementById('confidenceBadge');
    if (confidenceBadge) {
        confidenceBadge.textContent = results.confidence_label.toUpperCase();
        confidenceBadge.className = `confidence-badge ${results.confidence_label}`;
    }
    
    // Audio quality
    if (results.quality) {
        const qualityEl = document.getElementById('audioQuality');
        const scoreEl = document.getElementById('qualityScore');
        if (qualityEl) qualityEl.textContent = results.quality.quality?.toUpperCase() || '--';
        if (scoreEl) scoreEl.textContent = results.quality.score?.toFixed(2) || '--';
    }
    
    // Duration
    if (results.features?.duration) {
        const durationEl = document.getElementById('audioDuration');
        if (durationEl) durationEl.textContent = results.features.duration.toFixed(1) + 's';
    }
    
    // Key features matched
    const featuresEl = document.getElementById('keyFeatures');
    if (featuresEl && results.key_features?.length) {
        featuresEl.innerHTML = results.key_features.map(f => 
            `<span class="feature-tag">${f}</span>`
        ).join('');
    }
    
    // All predictions / alternatives
    const predictionsList = document.getElementById('predictionsList');
    if (predictionsList) {
        predictionsList.innerHTML = '';
        
        // Add main result first
        const mainItem = document.createElement('div');
        mainItem.className = 'prediction-item main';
        mainItem.innerHTML = `
            <div class="prediction-rank">#1</div>
            <div class="prediction-info">
                <div class="prediction-name">${results.species || 'Unknown'}</div>
                <div class="prediction-scientific">${results.scientific || ''}</div>
            </div>
            <div class="prediction-confidence ${results.confidence_label}">${results.confidence?.toFixed(1) || 0}%</div>
        `;
        predictionsList.appendChild(mainItem);
        
        // Add alternatives
        results.alternatives.forEach(alt => {
            const item = document.createElement('div');
            item.className = 'prediction-item';
            item.innerHTML = `
                <div class="prediction-rank">#${alt.rank}</div>
                <div class="prediction-info">
                    <div class="prediction-name">${alt.species}</div>
                    <div class="prediction-scientific">${alt.scientific || ''}</div>
                </div>
                <div class="prediction-confidence">${alt.confidence?.toFixed(1) || 0}%</div>
            `;
            predictionsList.appendChild(item);
        });
    }
    
    // LLM reasoning
    const llmSection = document.getElementById('llmReasoning');
    const reasoningContent = document.getElementById('reasoningContent');
    if (llmSection && reasoningContent && results.reasoning) {
        llmSection.style.display = 'block';
        reasoningContent.innerHTML = `
            <p>${results.reasoning}</p>
            ${results.call_description ? `<p><strong>Typical call:</strong> ${results.call_description}</p>` : ''}
        `;
    } else if (llmSection) {
        llmSection.style.display = 'none';
    }
    
    // Novelty alert
    const noveltySection = document.getElementById('noveltyAlert');
    const noveltyText = document.getElementById('noveltyText');
    if (noveltySection) {
        if (results.is_unusual || !results.is_indian) {
            noveltySection.style.display = 'flex';
            if (noveltyText) {
                noveltyText.textContent = results.unusual_reason || 
                    (!results.is_indian ? `${results.species} is not typically found in India - exciting observation!` : 
                    'Unusual sighting detected!');
            }
        } else {
            noveltySection.style.display = 'none';
        }
    }
}
