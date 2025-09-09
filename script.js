// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileName');
const fileSizeText = document.getElementById('fileSize');
const removeFileBtn = document.getElementById('removeFileBtn');
const processBtn = document.getElementById('processBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const downloadBtn = document.getElementById('downloadBtn');
const newFileBtn = document.getElementById('newFileBtn');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const fileTypeError = document.getElementById('fileTypeError');
const closeErrorBtn = document.getElementById('closeErrorBtn');

// State variables
let selectedFile = null;
let isProcessing = false;

// Event listeners
selectFileBtn.addEventListener('click', (event) => {
    // Prevent bubbling to uploadArea which also opens the picker
    event.preventDefault();
    event.stopPropagation();
    fileInput.click();
});
fileInput.addEventListener('change', handleFileSelect);
removeFileBtn.addEventListener('click', removeFile);
processBtn.addEventListener('click', processFile);
downloadBtn.addEventListener('click', downloadResult);
newFileBtn.addEventListener('click', resetToUpload);
retryBtn.addEventListener('click', resetToUpload);
closeErrorBtn.addEventListener('click', hideFileTypeError);

// Drag and drop functionality
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
uploadArea.addEventListener('click', (event) => {
    // If click originated from the select file button, do nothing here
    if (event.target.closest('#selectFileBtn')) return;
    fileInput.click();
});

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        setSelectedFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
    
    // Check if the dragged item is a file and if it's a .pbit file
    if (event.dataTransfer.items && event.dataTransfer.items.length > 0) {
        const item = event.dataTransfer.items[0];
        if (item.kind === 'file') {
            // We can't check the filename during dragover, so we'll just show the normal state
            uploadArea.classList.remove('invalid');
        }
    }
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        // Validate file type before processing
        if (!file.name.toLowerCase().endsWith('.pbit')) {
            showFileTypeError();
            return;
        }
        setSelectedFile(file);
    }
}

function setSelectedFile(file) {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pbit')) {
        showFileTypeError();
        return;
    }
    
    selectedFile = file;
    
    // Update UI
    fileName.textContent = file.name;
    fileSizeText.textContent = formatFileSize(file.size);
    
    // Show file info and enable process button
    fileInfo.style.display = 'block';
    processBtn.disabled = false;
    
    // Hide other sections
    hideAllSections();
    showSection('upload-section');
}

function removeFile() {
    selectedFile = null;
    fileInput.value = '';
    
    // Hide file info and disable process button
    fileInfo.style.display = 'none';
    processBtn.disabled = true;
    
    // Reset to upload state
    resetToUpload();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// File processing functions
async function processFile() {
    if (!selectedFile || isProcessing) return;
    
    isProcessing = true;
    processBtn.disabled = true;
    
    // Show progress section
    hideAllSections();
    showSection('progress-section');
    
    try {
        // Show initial progress
        updateProgress(10);
        progressText.textContent = 'Enviando arquivo para processamento...';
        
        // Call the real Python API
        const pdfBlob = await uploadToAPI(selectedFile);
        
        // Show completion progress
        updateProgress(100);
        progressText.textContent = 'Processamento concluído!';
        
        // Store the PDF blob for download
        window.processedFileResult = pdfBlob;
        
        // Small delay to show completion
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Show success result
        hideAllSections();
        showSection('result-section');
        
    } catch (error) {
        // Show error
        hideAllSections();
        showSection('error-section');
        errorMessage.textContent = error.message || 'An error occurred while processing your file.';
    } finally {
        isProcessing = false;
    }
}

async function simulateFileProcessing() {
    return new Promise((resolve, reject) => {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                
                // Simulate API response delay
                setTimeout(() => {
                    // Simulate 10% chance of error for demo purposes
                    if (Math.random() < 0.1) {
                        reject(new Error('API processing failed. Please try again.'));
                    } else {
                        resolve();
                    }
                }, 500);
            }
            
            updateProgress(progress);
        }, 200);
    });
}

function updateProgress(percentage) {
    progressFill.style.width = percentage + '%';
    
    if (percentage < 30) {
        progressText.textContent = 'Preparando arquivo...';
    } else if (percentage < 60) {
        progressText.textContent = 'Processando...';
    } else if (percentage < 90) {
        progressText.textContent = 'Finalizando...';
    } else {
        progressText.textContent = 'Concluído!';
    }
}

// Download functionality
function downloadResult() {
    if (!selectedFile || !window.processedFileResult) {
        console.error('No file or processed result available');
        return;
    }
    
    // Create download URL from the PDF blob
    const url = URL.createObjectURL(window.processedFileResult);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = `documentacao_${selectedFile.name.replace('.pbit', '_erd_final.pdf')}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Clean up
    URL.revokeObjectURL(url);
}

// Utility functions
function hideAllSections() {
    const sections = ['upload-section', 'progress-section', 'result-section', 'error-section'];
    sections.forEach(sectionId => {
        const section = document.querySelector(`.${sectionId}`);
        if (section) section.style.display = 'none';
    });
    
    // Also hide file type error
    if (fileTypeError) fileTypeError.style.display = 'none';
}

function showSection(sectionClass) {
    const section = document.querySelector(`.${sectionClass}`);
    if (section) section.style.display = 'block';
}

function showFileTypeError() {
    hideAllSections();
    fileTypeError.style.display = 'block';
}

function hideFileTypeError() {
    fileTypeError.style.display = 'none';
    showSection('upload-section');
}

function resetToUpload() {
    hideAllSections();
    showSection('upload-section');
    
    // Reset file input
    fileInput.value = '';
    
    // Clear selected file
    selectedFile = null;
    
    // Hide file info and disable process button
    fileInfo.style.display = 'none';
    processBtn.disabled = true;
    
    // Reset progress
    progressFill.style.width = '0%';
    progressText.textContent = 'Processing...';
}

// Real API integration function for Python backend
async function uploadToAPI(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const API_URL = '${API_URL}/api/process-file';

    try {
        const response = await fetch('/api/process-file', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        // Return the response as blob since it's a PDF file
        return await response.blob();
        
    } catch (error) {
        console.error('API call failed:', error);
        throw new Error(`Upload failed: ${error.message}`);
    }
}

// Initialize the application
function init() {
    // Hide all sections except upload initially
    hideAllSections();
    showSection('upload-section');
    
    // Ensure process button is disabled initially
    processBtn.disabled = true;
}

// Start the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init);

// Add some visual feedback for better UX
document.addEventListener('DOMContentLoaded', () => {
    // Add loading states
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            }
        });
    });
    
    // Add keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !isProcessing) {
            if (selectedFile && !processBtn.disabled) {
                processFile();
            }
        }
    });
});

// Export functions for potential external use
window.FileProcessor = {
    setSelectedFile,
    processFile,
    downloadResult,
    resetToUpload,
    uploadToAPI
};
