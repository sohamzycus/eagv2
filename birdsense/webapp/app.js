/**
 * BirdSense Web Application
 * 
 * Features:
 * - Live microphone recording with waveform visualization
 * - Real-time frequency histogram
 * - Audio file upload
 * - Streaming identification results
 * - LLM reasoning display
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
const waveformCtx = waveformCanvas.getContext('2d');
const histogramCtx = histogramCanvas.getContext('2d');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupTabNavigation();
    setupEventListeners();
    await checkApiStatus();
    resizeCanvases();
    window.addEventListener('resize', resizeCanvases);
}

function resizeCanvases() {
    const containers = document.querySelectorAll('.visualizer-container, .histogram-container');
    containers.forEach(container => {
        const canvas = container.querySelector('canvas');
        if (canvas) {
            canvas.width = container.clientWidth - 32;
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
            document.getElementById('speciesCount').textContent = `${data.species_count} species`;
        } else {
            apiStatus.querySelector('.status-text').textContent = 'Initializing...';
        }
    } catch (error) {
        apiStatus.querySelector('.status-text').textContent = 'Offline';
        console.error('API connection failed:', error);
    }
}

// Tab Navigation
function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const tabId = btn.dataset.tab + 'Tab';
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// Event Listeners
function setupEventListeners() {
    // Record buttons
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    
    // Upload
    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    document.getElementById('removeFile').addEventListener('click', removeUploadedFile);
    
    // Analyze
    analyzeBtn.addEventListener('click', analyzeAudio);
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
        
        // Setup audio context for visualization
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
            mimeType: 'audio/webm;codecs=opus'
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
        
        // Start recording
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
        
        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        // Close audio context
        if (audioContext) {
            audioContext.close();
        }
        
        // Stop visualizations
        cancelAnimationFrame(waveformAnimationId);
        cancelAnimationFrame(histogramAnimationId);
        clearInterval(recordingInterval);
        
        // Update UI
        recordBtn.classList.remove('recording');
        recordBtn.querySelector('.btn-text').textContent = 'Start Recording';
        stopBtn.disabled = true;
        
        // Clear canvases
        clearCanvas(waveformCtx, waveformCanvas);
        clearCanvas(histogramCtx, histogramCanvas);
    }
}

function startRecordingTimer() {
    recordingInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        recordingTime.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

// ==================== Waveform Visualization ====================

function startWaveformVisualization() {
    const bufferLength = analyser.fftSize;
    const dataArray = new Float32Array(bufferLength);
    
    function draw() {
        if (!isRecording) return;
        
        waveformAnimationId = requestAnimationFrame(draw);
        
        analyser.getFloatTimeDomainData(dataArray);
        
        // Clear canvas
        waveformCtx.fillStyle = '#0f1419';
        waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
        
        // Draw waveform
        waveformCtx.lineWidth = 2;
        waveformCtx.strokeStyle = '#4ade80';
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
        
        // Calculate and display audio level
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i] * dataArray[i];
        }
        const rms = Math.sqrt(sum / bufferLength);
        const db = 20 * Math.log10(rms + 0.0001);
        const normalizedDb = Math.max(0, Math.min(100, (db + 60) * 100 / 60));
        audioLevel.textContent = `Level: ${normalizedDb.toFixed(0)}%`;
    }
    
    draw();
}

// ==================== Histogram Visualization ====================

function startHistogramVisualization() {
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    // Frequency bands for bird calls
    const sampleRate = audioContext.sampleRate;
    const binFrequency = sampleRate / analyser.fftSize;
    
    // Low: 50-500Hz, Mid: 500-4000Hz, High: 4000-14000Hz
    const lowBins = { start: Math.floor(50 / binFrequency), end: Math.floor(500 / binFrequency) };
    const midBins = { start: Math.floor(500 / binFrequency), end: Math.floor(4000 / binFrequency) };
    const highBins = { start: Math.floor(4000 / binFrequency), end: Math.floor(14000 / binFrequency) };
    
    function draw() {
        if (!isRecording) return;
        
        histogramAnimationId = requestAnimationFrame(draw);
        
        analyser.getByteFrequencyData(dataArray);
        
        // Clear canvas
        histogramCtx.fillStyle = '#0f1419';
        histogramCtx.fillRect(0, 0, histogramCanvas.width, histogramCanvas.height);
        
        const barCount = 64;
        const barWidth = histogramCanvas.width / barCount - 2;
        const step = Math.floor(bufferLength / barCount);
        
        for (let i = 0; i < barCount; i++) {
            const binIndex = i * step;
            const value = dataArray[binIndex];
            const barHeight = (value / 255) * histogramCanvas.height * 0.9;
            
            // Determine color based on frequency band
            let color;
            if (binIndex < lowBins.end) {
                color = '#4ade80';  // Green for low
            } else if (binIndex < midBins.end) {
                color = '#60a5fa';  // Blue for mid
            } else {
                color = '#f472b6';  // Pink for high
            }
            
            histogramCtx.fillStyle = color;
            histogramCtx.fillRect(
                i * (barWidth + 2),
                histogramCanvas.height - barHeight,
                barWidth,
                barHeight
            );
        }
    }
    
    draw();
}

function clearCanvas(ctx, canvas) {
    ctx.fillStyle = '#0f1419';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
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
    // Check file type
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/flac', 'audio/ogg', 'audio/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|flac|ogg|webm)$/i)) {
        alert('Please upload a valid audio file (WAV, MP3, FLAC, OGG)');
        return;
    }
    
    uploadedFile = file;
    
    // Update UI
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
    analyzeBtn.disabled = !uploadedFile;
}

// ==================== Analysis ====================

async function analyzeAudio() {
    if (!uploadedFile) return;
    
    // Show processing status
    emptyState.style.display = 'none';
    resultsContainer.style.display = 'none';
    processingStatus.style.display = 'block';
    
    // Reset steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'complete');
        step.querySelector('.step-icon').textContent = '⏳';
    });
    
    // Get context
    const locationName = document.getElementById('locationName').value;
    const month = document.getElementById('month').value;
    const description = document.getElementById('description').value;
    
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
        // Use streaming endpoint
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
            predictions: [],
            llm_reasoning: null,
            quality: null,
            novelty: null
        };
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    handleStreamEvent(data, results);
                }
            }
        }
        
        // Show final results
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
            
        case 'preprocessing':
        case 'preprocessed':
            updateStep('step-preprocessing', step === 'preprocessed' ? 'complete' : 'active');
            if (data.duration) results.duration = data.duration;
            break;
            
        case 'classifying':
            updateStep('step-classifying', 'active');
            break;
            
        case 'prediction':
            results.predictions.push(data.prediction);
            break;
            
        case 'reasoning':
            updateStep('step-classifying', 'complete');
            updateStep('step-reasoning', 'active');
            break;
            
        case 'llm_result':
            updateStep('step-reasoning', 'complete');
            results.llm_reasoning = data;
            break;
            
        case 'novelty_alert':
            results.novelty = data;
            break;
            
        case 'llm_error':
            updateStep('step-reasoning', 'complete');
            break;
            
        case 'complete':
            results.final = data;
            break;
    }
}

function updateStep(stepId, state) {
    const step = document.getElementById(stepId);
    step.classList.remove('active', 'complete');
    step.classList.add(state);
    
    if (state === 'complete') {
        step.querySelector('.step-icon').textContent = '✓';
    } else if (state === 'active') {
        step.querySelector('.step-icon').textContent = '⏳';
    }
}

function showResults(results) {
    processingStatus.style.display = 'none';
    resultsContainer.style.display = 'block';
    
    // Top prediction
    if (results.predictions.length > 0) {
        const top = results.predictions[0];
        document.getElementById('topSpeciesName').textContent = top.species;
        document.getElementById('topScientificName').textContent = ''; // Add if available
        document.getElementById('topHindiName').textContent = '';
        
        const confidence = top.confidence;
        document.getElementById('topConfidenceBar').style.width = `${confidence}%`;
        document.getElementById('topConfidenceText').textContent = `${confidence.toFixed(1)}%`;
        
        // Color confidence bar based on level
        const bar = document.getElementById('topConfidenceBar');
        if (confidence >= 85) {
            bar.style.background = 'linear-gradient(90deg, #22c55e, #4ade80)';
        } else if (confidence >= 60) {
            bar.style.background = 'linear-gradient(90deg, #eab308, #fbbf24)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
        }
    }
    
    // Audio quality
    if (results.quality) {
        document.getElementById('audioQuality').textContent = results.quality.quality?.toUpperCase() || '--';
        document.getElementById('qualityScore').textContent = results.quality.score?.toFixed(2) || '--';
    }
    if (results.duration) {
        document.getElementById('audioDuration').textContent = results.duration.toFixed(1) + 's';
    }
    
    // All predictions
    const predictionsList = document.getElementById('predictionsList');
    predictionsList.innerHTML = '';
    
    results.predictions.forEach((pred, index) => {
        const item = document.createElement('div');
        item.className = 'prediction-item';
        item.innerHTML = `
            <div class="prediction-rank">#${pred.rank}</div>
            <div class="prediction-info">
                <div class="prediction-name">${pred.species}</div>
            </div>
            <div class="prediction-confidence">${pred.confidence.toFixed(1)}%</div>
        `;
        predictionsList.appendChild(item);
    });
    
    // LLM reasoning
    const llmSection = document.getElementById('llmReasoning');
    if (results.llm_reasoning && results.llm_reasoning.reasoning) {
        llmSection.style.display = 'block';
        document.getElementById('reasoningContent').innerHTML = `
            <p><strong>AI Assessment:</strong> ${results.llm_reasoning.species || 'Unknown'} 
            (${(results.llm_reasoning.confidence * 100).toFixed(0)}% confidence)</p>
            <p>${results.llm_reasoning.reasoning}</p>
        `;
        
        // Update top result with LLM info
        if (results.llm_reasoning.species) {
            document.getElementById('topSpeciesName').textContent = results.llm_reasoning.species;
            const llmConfidence = results.llm_reasoning.confidence * 100;
            document.getElementById('topConfidenceBar').style.width = `${llmConfidence}%`;
            document.getElementById('topConfidenceText').textContent = `${llmConfidence.toFixed(1)}%`;
        }
    } else {
        llmSection.style.display = 'none';
    }
    
    // Novelty alert
    const noveltySection = document.getElementById('noveltyAlert');
    if (results.novelty || (results.llm_reasoning && results.llm_reasoning.novelty_flag)) {
        noveltySection.style.display = 'flex';
        document.getElementById('noveltyText').textContent = 
            results.novelty?.message || 
            results.llm_reasoning?.novelty_explanation || 
            'Unusual sighting detected!';
    } else {
        noveltySection.style.display = 'none';
    }
}

