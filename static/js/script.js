// ============================================================================
// VidScribe - Frontend JavaScript
// ============================================================================

let currentOutputName = null;
let statusCheckInterval = null;

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const videoFileInput = document.getElementById('videoFile');
const fileNameDisplay = document.getElementById('fileName');
const fileLabel = document.querySelector('.file-label');
const outputFormatRadios = document.querySelectorAll('input[name="output_format"]');
const templateSection = document.getElementById('templateSection');
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

const uploadBtn = document.getElementById('uploadBtn');
const downloadBtn = document.getElementById('downloadBtn');
const newVideoBtn = document.getElementById('newVideoBtn');
const retryBtn = document.getElementById('retryBtn');

// Toggle elements
const uploadToggle = document.getElementById('uploadToggle');
const youtubeToggle = document.getElementById('youtubeToggle');
const uploadBox = document.getElementById('uploadBox');
const youtubeBox = document.getElementById('youtubeBox');

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initHeaderScroll();
    console.log('VidScribe initialized');
});

function initHeaderScroll() {
    const header = document.querySelector('.nav-header');
    let lastScrollTop = 0;
    let scrollThreshold = 100; // Start hiding after scrolling 100px

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > scrollThreshold) {
            if (scrollTop > lastScrollTop) {
                // Scrolling down - hide header
                header.classList.add('hidden');
            } else {
                // Scrolling up - show header
                header.classList.remove('hidden');
            }
        } else {
            // Near top - always show header
            header.classList.remove('hidden');
        }

        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    }, false);
}

function initializeEventListeners() {
    // Toggle radio buttons for upload/YouTube
    const uploadRadio = document.getElementById('uploadToggle');
    const youtubeRadio = document.getElementById('youtubeToggle');

    if (uploadRadio) {
        uploadRadio.addEventListener('change', () => {
            if (uploadRadio.checked) {
                switchInputMode('upload');
            }
        });
    }
    if (youtubeRadio) {
        youtubeRadio.addEventListener('change', () => {
            if (youtubeRadio.checked) {
                switchInputMode('youtube');
            }
        });
    }

    // File input change
    if (videoFileInput) {
        videoFileInput.addEventListener('change', handleFileSelect);
    }

    // Form submit
    uploadForm.addEventListener('submit', handleFormSubmit);

    // Output format change
    outputFormatRadios.forEach(radio => {
        radio.addEventListener('change', handleFormatChange);
    });

    // Action buttons
    if (downloadBtn) downloadBtn.addEventListener('click', handleDownload);
    if (newVideoBtn) newVideoBtn.addEventListener('click', resetApp);
    if (retryBtn) retryBtn.addEventListener('click', resetApp);

    // 3D Template Carousel
    initTemplateCarousel();
}

// ============================================================================
// Template Flip Card Selection
// ============================================================================

function initTemplateCarousel() {
    const templateCards = document.querySelectorAll('.template-flip-card');
    const selectedNameDisplay = document.querySelector('.selected-template-name');

    if (!templateCards.length) return;

    // Click to select
    templateCards.forEach(card => {
        card.addEventListener('click', function (e) {
            e.stopPropagation();

            const templateValue = this.dataset.template;
            const radioInput = this.querySelector('input[type="radio"]');
            const labelText = this.querySelector('.card__title').textContent;

            // Update radio selection
            if (radioInput) {
                radioInput.checked = true;
            }

            // Update visual selection
            templateCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');

            // Update selected template name
            if (selectedNameDisplay) {
                selectedNameDisplay.textContent = labelText;
            }
        });
    });

    // Set initial selected state
    const checkedInput = document.querySelector('.template-flip-card input[type="radio"]:checked');
    if (checkedInput) {
        const selectedCard = checkedInput.closest('.template-flip-card');
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
    }
}

// ============================================================================
// YouTube URL Handler
// ============================================================================

function handleYouTubeUrl() {
    const urlInput = document.getElementById('youtubeUrl');
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    // Basic YouTube URL validation
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        alert('Please enter a valid YouTube URL');
        return;
    }

    // URL is valid, you can add additional processing here
    console.log('YouTube URL selected:', url);
    // The form will handle the submission
}

// ============================================================================
// Toggle Input Mode
// ============================================================================

function switchInputMode(mode) {
    if (mode === 'upload') {
        // Activate upload mode
        uploadToggle.classList.add('active');
        youtubeToggle.classList.remove('active');
        uploadBox.classList.remove('hidden');
        youtubeBox.classList.add('hidden');
    } else if (mode === 'youtube') {
        // Activate YouTube mode
        youtubeToggle.classList.add('active');
        uploadToggle.classList.remove('active');
        youtubeBox.classList.remove('hidden');
        uploadBox.classList.add('hidden');
    }
}


// ============================================================================
// Image Error Handling
// ============================================================================

function handleImageError(img) {
    // Fallback to logo if template preview fails to load
    img.src = '/static/images/logo.png';
    img.onerror = null; // Prevent infinite loop if logo also fails
}


// ============================================================================
// File Handling
// ============================================================================

function handleFileSelect(event) {
    const file = event.target.files[0];
    const uploadText = document.getElementById('uploadText');
    const selectedFileName = document.getElementById('selectedFileName');
    const fileButtonText = document.getElementById('fileButtonText');
    const folderContainer = document.querySelector('.folder-container');

    if (file) {
        // Show file info
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);

        // Update UI to show selected file
        if (uploadText) {
            uploadText.textContent = 'Video uploaded successfully!';
            uploadText.style.color = '#28a745'; // Green color for success
        }

        if (selectedFileName) {
            selectedFileName.textContent = `📹 ${file.name} (${sizeMB} MB)`;
            selectedFileName.style.display = 'block';
        }

        if (fileButtonText) {
            fileButtonText.textContent = 'Change file';
        }

        // Add success class to folder container
        if (folderContainer) {
            folderContainer.classList.add('file-uploaded');
        }

        console.log('File selected:', file.name);
    }
}

function handleFormatChange(event) {
    const format = event.target.value;
    console.log('📝 Output format changed to:', format);

    // Show/hide template section (and slide count dropdown inside it) based on format
    if (format === 'ppt' && templateSection) {
        console.log('✅ Showing template section and slide count for PPT');
        templateSection.classList.remove('hidden');
    } else if (templateSection) {
        console.log('❌ Hiding template section and slide count for', format.toUpperCase());
        templateSection.classList.add('hidden');
    }
}

// ============================================================================
// Form Submission
// ============================================================================

async function handleFormSubmit(event) {
    event.preventDefault();

    const formData = new FormData(uploadForm);

    // Check if YouTube mode is active
    const youtubeRadio = document.getElementById('youtubeToggle');
    const uploadRadio = document.getElementById('uploadToggle');
    const isYouTubeMode = youtubeRadio && youtubeRadio.checked;

    if (isYouTubeMode) {
        // YouTube URL mode
        const youtubeUrlInput = document.getElementById('youtubeUrl');
        const url = youtubeUrlInput.value.trim();

        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        // Basic YouTube URL validation
        if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
            showError('Please enter a valid YouTube URL');
            return;
        }

        console.log('Submitting YouTube URL:', url);

        // Note: youtube_url is already in formData from the input field
        // Remove video file if present (it shouldn't be, but just in case)
        formData.delete('video');

    } else {
        // File upload mode
        const file = videoFileInput.files[0];

        if (!file) {
            showError('Please select a video file');
            return;
        }

        console.log('Submitting video file:', file.name);

        // Remove YouTube URL if present
        formData.delete('youtube_url');
    }

    // Disable submit button
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = isYouTubeMode
        ? '<span> Downloading & Processing...</span>'
        : '<span> Uploading...</span>';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Store output name
            currentOutputName = data.output_name;

            // Show processing section
            showProcessingSection(data.video_info);

            // Start status checking
            startStatusChecking();
        } else {
            showError(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showError('Network error. Please try again.');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `
            Start Processing
            <div class=\"icon\">
              <svg height=\"24\" width=\"24\" viewBox=\"0 0 24 24\" xmlns=\"http://www.w3.org/2000/svg\">
                <path d=\"M0 0h24v24H0z\" fill=\"none\"></path>
                <path d=\"M16.172 11l-5.364-5.364 1.414-1.414L20 12l-7.778 7.778-1.414-1.414L16.172 13H4v-2z\"
                  fill=\"currentColor\"></path>
              </svg>
            </div>
        `;
    }
}

// ============================================================================
// Processing Status
// ============================================================================

function showProcessingSection(videoInfo) {
    // Hide upload section
    uploadSection.classList.add('hidden');

    // Show processing section
    processingSection.classList.remove('hidden');

    // Display video info
    const videoInfoDiv = document.getElementById('videoInfo');
    videoInfoDiv.innerHTML = `
        <p><strong>Duration:</strong> <span>${videoInfo.duration}</span></p>
        <p><strong>Resolution:</strong> <span>${videoInfo.resolution}</span></p>
        <p><strong>File Size:</strong> <span>${videoInfo.size}</span></p>
    `;
}

function startStatusChecking() {
    // Check immediately
    checkStatus();

    // Then check every 2 seconds
    statusCheckInterval = setInterval(checkStatus, 2000);
}

async function checkStatus() {
    if (!currentOutputName) return;

    try {
        const response = await fetch(`/status/${currentOutputName}`);
        const data = await response.json();

        if (response.ok) {
            updateProcessingStatus(data);

            if (data.status === 'complete') {
                stopStatusChecking();

                // Instead of redirecting, fetch results and show inline
                const resultsResponse = await fetch(`/results/${currentOutputName}`);
                const resultsHtml = await resultsResponse.text();

                // Extract results data from the response HTML
                const parser = new DOMParser();
                const doc = parser.parseFromString(resultsHtml, 'text/html');
                const resultsDataEl = doc.getElementById('resultsData');

                if (resultsDataEl) {
                    // Copy the data element to current page
                    const currentResultsData = document.getElementById('resultsData');
                    if (currentResultsData) {
                        currentResultsData.dataset.slides = resultsDataEl.dataset.slides;
                        currentResultsData.dataset.outputName = resultsDataEl.dataset.outputName;
                        currentResultsData.dataset.template = resultsDataEl.dataset.template;
                        currentResultsData.dataset.title = resultsDataEl.dataset.title;
                        currentResultsData.dataset.outputFormat = resultsDataEl.dataset.outputFormat || 'ppt';
                        currentResultsData.dataset.summary = resultsDataEl.dataset.summary || '';
                    }

                    // Load and show results
                    if (loadResultsData()) {
                        showResults();
                    } else {
                        // If loadResultsData fails, redirect to results page
                        window.location.href = `/results/${currentOutputName}`;
                    }
                } else {
                    // Fallback: redirect to results page
                    window.location.href = `/results/${currentOutputName}`;
                }
            } else if (data.status === 'error') {
                stopStatusChecking();
                showError(data.message);
            }
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

function updateProcessingStatus(data) {
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    progressFill.style.width = `${data.progress}%`;
    progressText.textContent = data.message;

    // Update steps (simplified - you can enhance this)
    updateSteps(data.progress);
}

function updateSteps(progress) {
    const steps = document.querySelectorAll('.step');

    // Simple progress mapping
    const stepProgress = [0, 16, 33, 50, 66, 83, 100];

    steps.forEach((step, index) => {
        const stepIcon = step.querySelector('.step-icon');

        if (progress >= stepProgress[index + 1]) {
            step.classList.add('complete');
            step.classList.remove('active');
            stepIcon.textContent = '✓';
        } else if (progress >= stepProgress[index]) {
            step.classList.add('active');
            stepIcon.textContent = '⏳';
        }
    });
}

function stopStatusChecking() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

// ============================================================================
// Results Display
// ============================================================================

function showResults(results) {
    // Hide processing section
    processingSection.classList.add('hidden');

    // Show results section
    resultsSection.classList.remove('hidden');

    // Display results info
    const resultsInfo = document.getElementById('resultsInfo');
    resultsInfo.innerHTML = `
        <div class="info-item">
            <strong>Title</strong>
            <span>${truncateText(results.title, 30)}</span>
        </div>
        <div class="info-item">
            <strong>Slides Created</strong>
            <span>${results.slides_count}</span>
        </div>
        <div class="info-item">
            <strong>Language</strong>
            <span>${results.language.toUpperCase()}</span>
        </div>
        <div class="info-item">
            <strong>Processing Time</strong>
            <span>${results.processing_time.toFixed(1)}s</span>
        </div>
    `;

    // Display summary
    const summaryBox = document.getElementById('summaryBox');
    if (results.summary) {
        summaryBox.innerHTML = `
            <h2>Summary</h2>
            <p>${results.summary}</p>
        `;
    } else {
        summaryBox.style.display = 'none';
    }

    // Setup download button
    if (results.output_type !== 'summary') {
        downloadBtn.style.display = 'inline-flex';
        downloadBtn.onclick = () => handleDownload(results.output_path);
    } else {
        downloadBtn.style.display = 'none';
    }
}

// ============================================================================
// Error Handling
// ============================================================================

function showError(message) {
    // Hide all sections
    uploadSection.classList.add('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');

    // Show error section
    errorSection.classList.remove('hidden');

    // Display error message
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;

    console.error('Error:', message);
}

// ============================================================================
// Download
// ============================================================================

function handleDownload() {
    if (!currentOutputName) {
        showError('No output available for download');
        return;
    }

    // Download file
    window.location.href = `/download/${currentOutputName}`;
}

// ============================================================================
// Reset Application
// ============================================================================

function resetApp() {
    // Stop status checking
    stopStatusChecking();

    // Reset current output
    currentOutputName = null;

    // Hide all sections
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    // Show upload section
    uploadSection.classList.remove('hidden');

    // Reset form
    uploadForm.reset();

    // Reset file display elements if they exist
    if (fileNameDisplay) {
        fileNameDisplay.textContent = 'Choose video file...';
    }
    if (fileLabel) {
        fileLabel.classList.remove('has-file');
    }

    // Reset uploaded file UI
    const uploadText = document.getElementById('uploadText');
    const selectedFileName = document.getElementById('selectedFileName');
    const fileButtonText = document.getElementById('fileButtonText');
    const folderContainer = document.querySelector('.folder-container');

    if (uploadText) {
        uploadText.textContent = 'Drag and drop your video here, or click to browse';
        uploadText.style.color = ''; // Reset color
    }
    if (selectedFileName) {
        selectedFileName.textContent = '';
        selectedFileName.style.display = 'none';
    }
    if (fileButtonText) {
        fileButtonText.textContent = 'Choose a file';
    }
    if (folderContainer) {
        folderContainer.classList.remove('file-uploaded');
    }

    // Reset template selection visibility (show by default for PPT)
    if (templateSection) {
        templateSection.classList.remove('hidden');
    }
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// Utility Functions
// ============================================================================

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================================================
// Console Welcome Message
// ============================================================================

console.log('%cVidScribe', 'font-size: 24px; font-weight: bold; color: #2563eb;');
console.log('%cAI-Powered Video Summarization', 'font-size: 14px; color: #64748b;');
console.log('%cPowered by OpenCV, Whisper & Gemini AI', 'font-size: 12px; color: #94a3b8;');
// ============================================================================
// Results Viewing (Merged from results.js)
// ============================================================================

let currentSlide = 1;
let totalSlides = 1;
let slidesData = [];
let resultsOutputName = '';
let selectedResultTemplate = 'professional';
let currentOutputFormat = 'ppt';

function loadResultsData() {
    const resultsDataEl = document.getElementById('resultsData');
    if (!resultsDataEl) return false;

    try {
        const slidesJson = resultsDataEl.dataset.slides;
        const outputName = resultsDataEl.dataset.outputName;
        const template = resultsDataEl.dataset.template;
        const title = resultsDataEl.dataset.title;
        const outputFormat = resultsDataEl.dataset.outputFormat || 'ppt';
        const summary = resultsDataEl.dataset.summary || '';

        // Store output format
        currentOutputFormat = outputFormat;

        if (outputFormat === 'summary') {
            // For summary format, we don't need slides
            resultsOutputName = outputName;
            const titleEl = document.getElementById('presentationTitle');
            if (titleEl && title) titleEl.textContent = title;

            // Store summary for display
            window.summaryText = summary;

            console.log('Loaded summary results');
            return true;
        }

        if (!slidesJson || slidesJson === '[]') {
            console.log('No results data found');
            return false;
        }

        slidesData = JSON.parse(slidesJson);
        totalSlides = slidesData.length;
        resultsOutputName = outputName;
        selectedResultTemplate = template;

        console.log('Loaded results data:', {
            slides: totalSlides,
            outputName: resultsOutputName,
            template: selectedResultTemplate,
            format: currentOutputFormat
        });

        const titleEl = document.getElementById('presentationTitle');
        if (titleEl && title) titleEl.textContent = title;

        return true;
    } catch (error) {
        console.error('Error loading results data:', error);
        return false;
    }
}

function showResults() {
    uploadSection.classList.add('hidden');
    processingSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');
    initResultsViewing();
}

function initResultsViewing() {
    const regenerateBtn = document.getElementById('regenerateBtn');
    const downloadResultBtn = document.getElementById('downloadResultBtn');
    const processAnotherBtn = document.getElementById('processAnotherBtn');
    const processAnotherBtnSummary = document.getElementById('processAnotherBtnSummary');
    const templateSelectorCard = document.getElementById('templateSelectorCard');
    const summaryDisplayCard = document.getElementById('summaryDisplayCard');
    const formatLabel = document.getElementById('outputFormatLabel');

    // Update format label based on output type
    if (formatLabel) {
        if (currentOutputFormat === 'pdf') {
            formatLabel.textContent = 'PDF Document (.pdf)';
        } else if (currentOutputFormat === 'summary') {
            formatLabel.textContent = 'Text Summary';
        } else {
            formatLabel.textContent = 'PowerPoint (.pptx)';
        }
    }

    // Handle different output formats
    if (currentOutputFormat === 'summary') {
        // For Summary: hide template card, show summary card
        if (templateSelectorCard) templateSelectorCard.classList.add('hidden');
        if (summaryDisplayCard) {
            summaryDisplayCard.classList.remove('hidden');
            const summaryContent = document.getElementById('summaryContent');
            if (summaryContent && window.summaryText) {
                summaryContent.textContent = window.summaryText;
            }
        }

        // Add event listener for summary's process another button
        if (processAnotherBtnSummary) {
            processAnotherBtnSummary.addEventListener('click', resetToUpload);
        }

        console.log('Summary format: showing summary text');
        return; // Exit early for summary format
    }

    // For PPT and PDF: show template card, hide summary card
    if (summaryDisplayCard) summaryDisplayCard.classList.add('hidden');
    if (templateSelectorCard) templateSelectorCard.classList.remove('hidden');

    // Populate video summary stats
    const slidesCountEl = document.getElementById('slidesCount');
    const currentTemplateEl = document.getElementById('currentTemplate');

    if (slidesCountEl) {
        slidesCountEl.textContent = totalSlides || slidesData.length || '0';
    }

    if (currentTemplateEl) {
        const templateName = selectedResultTemplate || 'Professional';
        currentTemplateEl.textContent = templateName.charAt(0).toUpperCase() + templateName.slice(1);
    }

    // Handle PDF format: hide regeneration section
    if (currentOutputFormat === 'pdf') {
        // Hide template selection and regeneration button for PDF
        const templateHeader = document.querySelector('.template-header');
        const templateSelector = document.querySelector('.template-selector');
        const templateInfoBox = document.querySelector('.template-info-box');
        const divider = document.querySelector('#templateSelectorCard .divider');

        if (templateHeader) templateHeader.style.display = 'none';
        if (divider) divider.style.display = 'none';
        if (templateSelector) {
            // Hide regeneration controls but keep download and process another
            const templateDropdownLabel = templateSelector.querySelector('label[for="templateDropdown"]');
            const templateDropdown = document.getElementById('templateDropdown');
            if (templateDropdownLabel) templateDropdownLabel.style.display = 'none';
            if (templateDropdown) templateDropdown.style.display = 'none';
            if (regenerateBtn) regenerateBtn.style.display = 'none';
        }
        if (templateInfoBox) templateInfoBox.style.display = 'none';

        console.log('PDF format: hiding regeneration controls');
    } else {
        // For PPT: show all controls
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', handleRegenerateTemplate);
        }
        console.log('PPT format: showing all controls');
    }

    // Download button for both PPT and PDF
    if (downloadResultBtn) {
        downloadResultBtn.addEventListener('click', () => {
            if (resultsOutputName) {
                window.location.href = `/download/${resultsOutputName}`;
            }
        });
    }

    if (processAnotherBtn) {
        processAnotherBtn.addEventListener('click', resetToUpload);
    }

    console.log('Results buttons initialized for format:', currentOutputFormat);
}

async function handleRegenerateTemplate() {
    const templateDropdown = document.getElementById('templateDropdown');
    const regenerateBtn = document.getElementById('regenerateBtn');
    const statusDiv = document.getElementById('regenerateStatus');
    const successDiv = document.getElementById('regenerateSuccess');
    const selectedTemplate = templateDropdown.value;

    console.log(`Regenerating PPT with template: ${selectedTemplate}`);

    regenerateBtn.disabled = true;
    statusDiv.classList.remove('hidden');
    successDiv.classList.add('hidden');

    try {
        const response = await fetch(`/regenerate-ppt/${resultsOutputName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template: selectedTemplate })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            console.log('PPT regenerated successfully!');

            statusDiv.classList.add('hidden');
            successDiv.classList.remove('hidden');

            setTimeout(() => {
                window.location.href = result.download_url;

                setTimeout(() => {
                    successDiv.classList.add('hidden');
                    regenerateBtn.disabled = false;
                }, 2000);
            }, 500);
        } else {
            throw new Error(result.error || 'Regeneration failed');
        }
    } catch (error) {
        console.error('Regeneration error:', error);
        statusDiv.classList.add('hidden');
        regenerateBtn.disabled = false;
        alert(`Failed to regenerate PPT: ${error.message}`);
    }
}

function resetToUpload() {
    stopStatusChecking();

    currentSlide = 1;
    totalSlides = 1;
    slidesData = [];
    resultsOutputName = '';

    document.getElementById('resultsSection').classList.add('hidden');
    processingSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    uploadSection.classList.remove('hidden');

    uploadForm.reset();

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        if (loadResultsData()) {
            showResults();
        }
    });
}

